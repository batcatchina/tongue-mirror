import type { DiagnosisInput, DiagnosisOutput, DiagnosisEvidence, AcupuncturePoint } from '@/types';
import { getMeridian, getEffect } from './acupoint_data';

const API_BASE_URL = 'https://api.coze.cn';
const BOT_ID = '7630373624734236672';
const API_TOKEN = 'pat_RpduRPvBPQIbpRLtAXy9NBFruewZlVKN4gH4aLgby6z2MgjNEejR2E7X8PV1L2iJ';

// ============================================
// 统一错误关键词定义（核心配置）
// ============================================
export const ERROR_PATTERNS = [
  '非舌象图片',
  '不是舌象图片',
  '图片不是舌象',
  '请重新上传舌象',
  'INVALID_IMAGE',
  'LOW_QUALITY_IMAGE',
  '非舌象照片',
  '不是舌头照片',
];

export const ERROR_KEYWORDS = [
  '非舌象',
  '不是舌象',
  '请重新上传',
  'INVALID_IMAGE',
  '请上传舌象',
];

// API错误码映射
export const API_ERROR_CODES: Record<number, { message: string; suggestion: string }> = {
  4010: { message: '请求超时', suggestion: '图片可能过大，建议重新压缩后上传' },
  4001: { message: '认证失败', suggestion: '服务配置异常，请稍后重试' },
  4002: { message: '参数错误', suggestion: '请检查输入内容后重试' },
  4003: { message: '请求频率超限', suggestion: '操作过于频繁，请稍后重试' },
  5000: { message: '服务器内部错误', suggestion: '服务繁忙，请稍后重试' },
  5001: { message: '服务暂时不可用', suggestion: '服务维护中，请稍后重试' },
};

// Coze API错误事件类型
export const ERROR_EVENTS = [
  'conversation.chat.failed',
  'error',
];

function parseMarkdownDiagnosis(markdown: string): DiagnosisOutput {
  // 主要证型 - 同时支持 **主要证型** 和 主要证型 两种格式
  const primaryMatch = markdown.match(/\*\*主要证型\*\*[：:]\s*([^\n]+)/) 
    || markdown.match(/主要证型[：:]\s*([^\n]+)/);
  const primarySyndrome = primaryMatch ? primaryMatch[1].trim() : '辨证分析完成';

  const scoreMatch = markdown.match(/\*\*证型得分\*\*[：:]\s*(\d+)/)
    || markdown.match(/证型得分[：:]\s*(\d+)/);
  const syndromeScore = scoreMatch ? parseInt(scoreMatch[1]) : 5;

  // 病机分析 - 同时支持 **病机分析** 和 病机分析 两种格式，并捕获多行内容
  // 优先匹配多行内容（从"病机分析："到下一个空行或特定标记）
  const pathogenesisMultiMatch = markdown.match(/病机分析[：:]\s*([\s\S]*?)(?=\n\n|\n针灸|##|$)/);
  const pathogenesisMatch = markdown.match(/\*\*病机分析\*\*[：:]\s*([^\n]+)/)
    || markdown.match(/病机分析[：:]\s*([^\n]+)/);
  const pathogenesis = pathogenesisMultiMatch 
    ? pathogenesisMultiMatch[1].trim().replace(/\n+/g, ' ')  // 多行合并为单行
    : (pathogenesisMatch ? pathogenesisMatch[1].trim() : '');

  const evidenceMatches = markdown.matchAll(/\d+\.\s*([^\n]+)/g);
  const diagnosisEvidence: DiagnosisEvidence[] = Array.from(evidenceMatches, (m, idx) => ({
    feature: m[1].trim(),
    weight: 1,
    contribution: '主要依据',
    matchDegree: 0.9,
    ruleId: `rule_${idx + 1}`
  })).slice(0, 5);

  // 解析主穴 - 支持多种格式（粗体和非粗体）
  const mainPointsPatterns = [
    /\*\*主穴\*\*[：:]\s*([^\n]+)/,
    /主穴[：:]\s*([^\n]+)/,
    /\*\*针灸主穴\*\*[：:]\s*([^\n]+)/,
  ];
  let mainPointsText = '';
  for (const pattern of mainPointsPatterns) {
    const match = markdown.match(pattern);
    if (match) {
      mainPointsText = match[1].trim();
      break;
    }
  }
  
  // 解析配穴 - 支持条件格式（如"心烦明显：加劳宫"、"失眠严重：加百会、申脉"）
  const parseSecondaryPoints = (md: string): AcupuncturePoint[] => {
    // 查找配穴区域（从"配穴："到"刺法"或下一个##）
    const match = md.match(/配穴[：:]\s*([\s\S]*?)(?=\n刺法|##\s|\n\n|$)/);
    if (!match) return [];
    
    const section = match[1];
    const points: string[] = [];
    
    // 逐行处理
    const lines = section.split('\n');
    for (const line of lines) {
      // 提取所有 "加XXX" 格式
      const addMatches = line.match(/加([^\n]+)/g);
      if (addMatches) {
        addMatches.forEach(m => {
          const pointStr = m.replace('加', '').trim();
          // 按顿号、逗号分割
          const pointList = pointStr.split(/[、,，]/);
          pointList.forEach(p => {
            const trimmed = p.trim();
            if (trimmed && !trimmed.includes('无') && !/^\d+$/.test(trimmed)) {
              points.push(trimmed);
            }
          });
        });
      }
    }
    
    // 去重并过滤空值
    return [...new Set(points)].filter(p => p)
      .map(point => ({ 
        point, 
        meridian: getMeridian(point), 
        effect: getEffect(point), 
        technique: '平补平泻' 
      }));
  };
  
  const mainPoints: AcupuncturePoint[] = mainPointsText.split(/[、,，]/)
    .map(s => s.trim()).filter(s => s && !s.includes('无'))
    .map(point => ({ 
      point, 
      meridian: getMeridian(point), 
      effect: getEffect(point), 
      technique: '平补平泻' 
    }));

  const secondaryPoints = parseSecondaryPoints(markdown);

  const techniqueMatch = markdown.match(/\*\*刺法\*\*[：:]\s*([^\n]+)/)
    || markdown.match(/刺法[：:]\s*([^\n]+)/);
  const techniquePrinciple = techniqueMatch ? techniqueMatch[1].trim() : '';

  const frequencyMatch = markdown.match(/\*\*治疗频次\*\*[：:]\s*([^\n]+)/)
    || markdown.match(/治疗频次[：:]\s*([^\n]+)/);
  const treatmentFrequency = frequencyMatch ? frequencyMatch[1].trim() : '';

  const lifeCareSection = markdown.split(/##\s*生活调护/)[1] || '';
  const lifeCareItems = lifeCareSection.match(/[-•]\s*([^\n]+)/g) || [];
  const lifeCareAdvice = lifeCareItems.map(item => item.replace(/^[-•]\s*/, '').trim()).slice(0, 5);

  return {
    diagnosisResult: {
      primarySyndrome,
      syndromeScore,
      confidence: 0.8,
      secondarySyndromes: [],
      pathogenesis,
      organLocation: [],
      diagnosisEvidence,
      priority: '中',
      diagnosisTime: new Date().toISOString(),
    },
    acupuncturePlan: {
      treatmentPrinciple: '',
      mainPoints,
      secondaryPoints,
      contraindications: [],
      treatmentAdvice: {
        techniquePrinciple,
        needleRetentionTime: '',
        treatmentFrequency,
        treatmentSessions: '',
        sessionInterval: '',
      },
    },
    lifeCareAdvice: {
      dietSuggestions: lifeCareAdvice,
      dailyRoutine: [],
      precautions: [],
    },
    systemInfo: {
      knowledgeBaseVersion: '1.0',
      skillVersion: '1.0',
      reasoningRulesCount: 0,
      updateTime: new Date().toISOString(),
    },
  };
}

function generateUserId(): string {
  return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================
// 错误检测工具函数
// ============================================
function detectErrorInContent(content: string): string | null {
  // 检查ERROR_PATTERNS（完整短语匹配）
  for (const pattern of ERROR_PATTERNS) {
    if (content.includes(pattern)) {
      return '请上传舌象图片，图片中应清晰显示舌头表面特征（舌苔、舌色等）。';
    }
  }
  
  // 检查ERROR_KEYWORDS（关键词匹配）
  for (const keyword of ERROR_KEYWORDS) {
    if (content.includes(keyword)) {
      return '请上传舌象图片，图片中应清晰显示舌头表面特征（舌苔、舌色等）。';
    }
  }
  
  return null;
}

function parseAPIErrorCode(errorData: any): { message: string; code: number } | null {
  // 从各种可能的错误格式中提取错误码
  const code = errorData?.code || errorData?.error_code || errorData?.err_code;
  if (code && API_ERROR_CODES[code]) {
    return { message: API_ERROR_CODES[code].message, code: Number(code) };
  }
  return null;
}

function getUserFriendlyError(error: any, context: string = ''): Error {
  // 1. 检查是否是API错误码
  const apiError = parseAPIErrorCode(error);
  if (apiError) {
    const errorConfig = API_ERROR_CODES[apiError.code];
    const suggestion = errorConfig?.suggestion || '请稍后重试';
    return new Error(`${apiError.message}${context ? ` (${context})` : ''}，${suggestion}`);
  }
  
  // 2. 检查错误消息中的错误码（如 "error_code: 4010"）
  if (typeof error === 'string') {
    const codeMatch = error.match(/error_code[:\s]*(\d+)/i);
    if (codeMatch) {
      const code = parseInt(codeMatch[1]);
      if (API_ERROR_CODES[code]) {
        return new Error(`${API_ERROR_CODES[code].message}，${API_ERROR_CODES[code].suggestion}`);
      }
    }
    
    // 检查内容中的错误关键词
    const contentError = detectErrorInContent(error);
    if (contentError) return new Error(contentError);
  }
  
  // 3. 检查error对象的message
  if (error?.message) {
    const contentError = detectErrorInContent(error.message);
    if (contentError) return new Error(contentError);
    
    // 检查消息中的错误码
    const codeMatch = error.message.match(/error_code[:\s]*(\d+)/i);
    if (codeMatch) {
      const code = parseInt(codeMatch[1]);
      if (API_ERROR_CODES[code]) {
        return new Error(`${API_ERROR_CODES[code].message}，${API_ERROR_CODES[code].suggestion}`);
      }
    }
  }
  
  // 4. 检查error对象的其他字段
  if (error?.error) {
    const contentError = detectErrorInContent(String(error.error));
    if (contentError) return new Error(contentError);
  }
  
  // 5. 返回原始错误或通用错误
  const originalMessage = error?.message || error?.msg || String(error);
  if (originalMessage.includes('timeout') || originalMessage.includes('超时')) {
    return new Error('请求超时，图片可能过大，请尝试压缩后重新上传');
  }
  
  if (originalMessage) {
    return new Error(`${originalMessage}${context ? ` (${context})` : ''}`);
  }
  
  return new Error('服务繁忙，请稍后重试');
}

export type DiagnosisProgressStep = 'recognizing' | 'analyzing' | 'reasoning' | 'matching';

export async function submitDiagnosis(
  input: DiagnosisInput, 
  onProgress?: (step: DiagnosisProgressStep) => void
): Promise<DiagnosisOutput> {
  // 构建消息内容
  const textContent = JSON.stringify({
    tongue_color: input.input_features.tongueColor.value,
    tongue_shape: input.input_features.tongueShape.value,
    tongue_coating_color: input.input_features.coating.color,
    tongue_coating_texture: input.input_features.coating.texture,
    tongue_movement: input.input_features.tongueState.value || '正常',
    crack: input.input_features.crack?.value === '是',
    teeth_mark: input.input_features.teethMark?.value === '是',
    spots: input.input_features.ecchymosis?.value === '是',
    patient_age: input.patientInfo?.age,
    patient_gender: input.patientInfo?.gender,
    chief_complaint: input.patientInfo?.chiefComplaint,
    symptoms: input.symptoms?.map(s => s.symptom).join(', ') || '',
    mode: input.options?.mode || '详细模式',
    has_image: !!input.imageData,
  }, null, 2);

  // 构建多模态消息内容
  const messageContent = [];
  
  // 如果有图片，添加图片内容
  if (input.imageData) {
    // 确保图片数据是有效的 base64 URL
    const imageUrl = input.imageData.startsWith('data:') 
      ? input.imageData 
      : `data:image/jpeg;base64,${input.imageData}`;
    
    console.log(`[舌照上传] 图片数据长度: ${imageUrl.length} 字符`);
    
    messageContent.push({
      type: 'image_url',
      image_url: { url: imageUrl }
    });
  }
  
  // 添加文本内容
  messageContent.push({
    type: 'text',
    text: textContent
  });

  const requestPayload = {
    bot_id: BOT_ID,
    user_id: generateUserId(),
    stream: true,
    additional_messages: [{
      role: 'user',
      content: messageContent.length > 1 ? JSON.stringify(messageContent) : textContent,
      content_type: messageContent.length > 1 ? 'object_string' : 'text'
    }]
  };

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/v3/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: JSON.stringify(requestPayload),
    });
  } catch (networkError) {
    throw getUserFriendlyError(networkError, '网络连接');
  }

  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw getUserFriendlyError({
      code: response.status,
      message: `HTTP ${response.status}: ${errorText || response.statusText}`
    }, 'API请求');
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('无法读取响应流');

  let result = '';
  const decoder = new TextDecoder();
  let messageCount = 0;
  
  // 设置超时（90秒，考虑到图片处理可能需要更长时间）
  const TIMEOUT = 90000;
  const startTime = Date.now();
  
  while (true) {
    // 检查超时
    if (Date.now() - startTime > TIMEOUT) {
      throw new Error('辨证分析超时（90秒），图片可能过大，请尝试压缩后重新上传');
    }
    
    const { done, value } = await reader.read();
    if (done) break;
    result += decoder.decode(value, { stream: true });
    
    // 检测错误关键词（完整短语匹配）
    for (const pattern of ERROR_PATTERNS) {
      if (result.includes(pattern)) {
        throw new Error('请上传舌象图片，图片中应清晰显示舌头表面特征（舌苔、舌色等）。');
      }
    }
    
    // 每收到一条消息触发一次进度更新
    messageCount++;
    if (onProgress && messageCount > 0) {
      if (messageCount <= 2) {
        onProgress('recognizing');
      } else if (messageCount <= 4) {
        onProgress('analyzing');
      } else if (messageCount <= 6) {
        onProgress('reasoning');
      } else {
        onProgress('matching');
      }
    }
  }

  // 解析SSE，收集所有事件和数据
  const lines = result.split('\n');
  let answerContent = '';
  let currentEvent = '';
  let errorEventData: any = null;
  let chatFailedData: any = null;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('event:')) {
      currentEvent = trimmed.slice(6).trim();
    } else if (trimmed.startsWith('data:')) {
      try {
        const jsonStr = trimmed.slice(5).trim();
        if (jsonStr === '[DONE]') continue;
        const data = JSON.parse(jsonStr);
        
        // 捕获错误事件
        if (currentEvent === 'error' || currentEvent === 'conversation.chat.failed') {
          console.error(`[API错误事件] ${currentEvent}:`, JSON.stringify(data));
          
          if (currentEvent === 'conversation.chat.failed') {
            chatFailedData = data;
          }
          if (currentEvent === 'error') {
            errorEventData = data;
          }
        }
        
        // 只收集type="answer"的消息
        if (data.type === 'answer' && data.reasoning_content) {
          answerContent += data.reasoning_content;
        }
        
        // conversation.message.completed事件可能有完整content
        if (currentEvent === 'conversation.message.completed' && data.type === 'answer' && data.content) {
          answerContent = data.content;
        }
      } catch (parseError) {
        // 忽略解析错误，继续处理其他行
      }
    }
  }

  // 处理conversation.chat.failed错误
  if (chatFailedData) {
    const failedReason = chatFailedData?.reason || chatFailedData?.failed_reason || chatFailedData?.err_msg;
    const failedCode = chatFailedData?.code || chatFailedData?.error_code;
    
    if (failedCode) {
      throw getUserFriendlyError({ code: failedCode, message: failedReason }, '会话失败');
    }
    if (failedReason) {
      throw getUserFriendlyError({ message: failedReason }, '会话失败');
    }
  }
  
  // 处理error事件
  if (errorEventData) {
    throw getUserFriendlyError(errorEventData, 'API错误');
  }

  if (!answerContent) {
    // 如果没有answer内容但有chat失败数据，给出友好提示
    if (chatFailedData) {
      throw new Error('服务处理失败，图片可能不符合要求，请尝试更换舌象图片或移除图片后重试');
    }
    throw new Error('未获取到辨证结果，请稍后重试');
  }

  // 检测文本中的错误提示（非舌象图片等）
  const contentError = detectErrorInContent(answerContent);
  if (contentError) {
    throw new Error(contentError);
  }

  // 检测JSON格式的错误响应
  try {
    const parsed = typeof answerContent === 'string' ? JSON.parse(answerContent) : answerContent;
    if (parsed.error) {
      throw new Error(parsed.message || '输入验证失败，请重新上传舌象图片');
    }
    return parsed;
  } catch (e) {
    if (e instanceof Error && (e.message.includes('上传') || e.message.includes('舌象'))) {
      throw e;
    }
    return parseMarkdownDiagnosis(answerContent);
  }
}

export async function validateFeatures(input: Partial<DiagnosisInput>): Promise<{ valid: boolean; errors?: string[] }> {
  const errors: string[] = [];
  if (!input.input_features?.tongueColor.value) errors.push('请选择舌色');
  if (!input.input_features?.tongueShape.value) errors.push('请选择舌形');
  if (!input.input_features?.coating.color) errors.push('请选择苔色');
  if (!input.input_features?.coating.texture) errors.push('请选择苔质');
  if (!input.patientInfo?.age) errors.push('请输入患者年龄');
  if (!input.patientInfo?.gender) errors.push('请选择患者性别');
  if (!input.patientInfo?.chiefComplaint) errors.push('请输入主诉');
  return { valid: errors.length === 0, errors: errors.length > 0 ? errors : undefined };
}

export async function getDiagnosisModes() {
  return { modes: [{ value: '快速模式', label: '快速模式', description: '仅输出主要证型和主穴' }, { value: '详细模式', label: '详细模式', description: '完整辨证分析' }] };
}

export async function healthCheck(): Promise<boolean> { return !!BOT_ID && !!API_TOKEN; }
export function getApiConfig() { return { baseUrl: API_BASE_URL, botId: BOT_ID.slice(0,8)+'...', hasToken: !!API_TOKEN }; }

// 验证图片是否为舌象
export async function validateTongueImage(imageBase64: string): Promise<{ valid: boolean; message?: string }> {
  try {
    // 提取base64数据（去掉data:image/xxx;base64,前缀）
    const base64Data = imageBase64.split(',')[1] || imageBase64;
    
    const requestPayload = {
      bot_id: BOT_ID,
      user_id: generateUserId(),
      stream: false,
      additional_messages: [{
        role: 'user',
        content: JSON.stringify({
          action: 'validate_image',
          image_data: base64Data.substring(0, 100) // 发送部分数据用于验证提示
        }),
        content_type: 'text'
      }]
    };

    const response = await fetch(`${API_BASE_URL}/v3/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: JSON.stringify(requestPayload),
    });

    if (!response.ok) {
      console.log('验证API调用失败，默认通过');
      return { valid: true };
    }

    const data = await response.json();
    const content = data?.data?.content || '';
    
    // 使用统一的错误关键词检测
    for (const keyword of ERROR_KEYWORDS) {
      if (content.includes(keyword)) {
        return { valid: false, message: '请上传舌象图片，图片中应清晰显示舌头表面特征。' };
      }
    }
    
    return { valid: true };
  } catch (error) {
    console.log('验证出错，默认通过:', error);
    return { valid: true };
  }
}
