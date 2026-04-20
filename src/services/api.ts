import type { DiagnosisInput, DiagnosisOutput, DiagnosisEvidence, AcupuncturePoint } from '@/types';
import { getMeridian, getEffect } from './acupoint_data';

const API_BASE_URL = 'https://api.coze.cn';
const BOT_ID = '7630373624734236672';
const API_TOKEN = 'pat_RpduRPvBPQIbpRLtAXy9NBFruewZlVKN4gH4aLgby6z2MgjNEejR2E7X8PV1L2iJ';

function parseMarkdownDiagnosis(markdown: string): DiagnosisOutput {
  const primaryMatch = markdown.match(/\*\*主要证型\*\*[：:]\s*([^\n]+)/);
  const primarySyndrome = primaryMatch ? primaryMatch[1].trim() : '辨证分析完成';

  const scoreMatch = markdown.match(/\*\*证型得分\*\*[：:]\s*(\d+)/);
  const syndromeScore = scoreMatch ? parseInt(scoreMatch[1]) : 5;

  const pathogenesisMatch = markdown.match(/\*\*病机分析\*\*[：:]\s*([^\n]+)/);
  const pathogenesis = pathogenesisMatch ? pathogenesisMatch[1].trim() : '';

  const evidenceMatches = markdown.matchAll(/\d+\.\s*([^\n]+)/g);
  const diagnosisEvidence: DiagnosisEvidence[] = Array.from(evidenceMatches, (m, idx) => ({
    feature: m[1].trim(),
    weight: 1,
    contribution: '主要依据',
    matchDegree: 0.9,
    ruleId: `rule_${idx + 1}`
  })).slice(0, 5);

  // 解析主穴 - 支持多种格式
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
  
  // 解析配穴 - 支持多种格式
  const secondaryPointsPatterns = [
    /\*\*配穴\*\*[：:]\s*([^\n]+)/,
    /配穴[：:]\s*([^\n]+)/,
    /\*\*随证配穴\*\*[：:]\s*([^\n]+)/,
  ];
  let secondaryPointsText = '';
  for (const pattern of secondaryPointsPatterns) {
    const match = markdown.match(pattern);
    if (match) {
      secondaryPointsText = match[1].trim();
      break;
    }
  }
  
  const mainPoints: AcupuncturePoint[] = mainPointsText.split(/[、,，]/)
    .map(s => s.trim()).filter(s => s && !s.includes('无'))
    .map(point => ({ 
      point, 
      meridian: getMeridian(point), 
      effect: getEffect(point), 
      technique: '平补平泻' 
    }));

  const secondaryPoints: AcupuncturePoint[] = secondaryPointsText.split(/[、,，]/)
    .map(s => s.trim()).filter(s => s && !s.includes('无'))
    .map(point => ({ 
      point, 
      meridian: getMeridian(point), 
      effect: getEffect(point), 
      technique: '平补平泻' 
    }));

  const techniqueMatch = markdown.match(/\*\*刺法\*\*[：:]\s*([^\n]+)/);
  const techniquePrinciple = techniqueMatch ? techniqueMatch[1].trim() : '';

  const frequencyMatch = markdown.match(/\*\*治疗频次\*\*[：:]\s*([^\n]+)/);
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
    messageContent.push({
      type: 'image_url',
      image_url: { url: input.imageData }
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

  const response = await fetch(`${API_BASE_URL}/v3/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_TOKEN}`,
    },
    body: JSON.stringify(requestPayload),
  });

  if (!response.ok) throw new Error(`API请求失败: ${response.status}`);

  const reader = response.body?.getReader();
  if (!reader) throw new Error('无法读取响应流');

  let result = '';
  const decoder = new TextDecoder();
  let messageCount = 0;
  const errorKeywords = ['非舌象', '不是舌象', '请重新上传', 'INVALID_IMAGE', 'LOW_QUALITY_IMAGE'];
  
  // 设置超时（60秒）
  const TIMEOUT = 60000;
  const startTime = Date.now();
  
  while (true) {
    // 检查超时
    if (Date.now() - startTime > TIMEOUT) {
      throw new Error('辨证分析超时，请稍后重试。如果是图片问题，请确保上传的是舌象照片。');
    }
    
    const { done, value } = await reader.read();
    if (done) break;
    result += decoder.decode(value, { stream: true });
    
    // 实时检测错误关键词，立即停止
    for (const keyword of errorKeywords) {
      if (result.includes(keyword)) {
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

  // 解析SSE，只收集type="answer"的reasoning_content
  const lines = result.split('\n');
  let answerContent = '';
  let currentEvent = '';
  
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('event:')) {
      currentEvent = trimmed.slice(6).trim();
    } else if (trimmed.startsWith('data:')) {
      try {
        const jsonStr = trimmed.slice(5).trim();
        if (jsonStr === '[DONE]') continue;
        const data = JSON.parse(jsonStr);
        
        // 只收集type="answer"的消息
        if (data.type === 'answer' && data.reasoning_content) {
          answerContent += data.reasoning_content;
        }
        
        // conversation.message.completed事件可能有完整content
        if (currentEvent === 'conversation.message.completed' && data.type === 'answer' && data.content) {
          answerContent = data.content;
        }
      } catch {}
    }
  }
  
  if (!answerContent) throw new Error('未获取到辨证结果');

  // 检测文本中的错误提示（非舌象图片等）
  for (const keyword of errorKeywords) {
    if (answerContent.includes(keyword)) {
      throw new Error('请上传舌象图片，图片中应清晰显示舌头表面特征（舌苔、舌色等）。');
    }
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
    
    // 检测错误关键词
    const errorKeywords = ['非舌象', '不是舌象', '请重新上传', 'INVALID_IMAGE'];
    for (const keyword of errorKeywords) {
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