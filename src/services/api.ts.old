import type { DiagnosisInput, DiagnosisOutput, DiagnosisEvidence, AcupuncturePoint } from '@/types';

// 扣子API配置
const API_BASE_URL = 'https://api.coze.cn';
const BOT_ID = '7630373624734236672';
const API_TOKEN = 'pat_RpduRPvBPQIbpRLtAXy9NBFruewZlVKN4gH4aLgby6z2MgjNEejR2E7X8PV1L2iJ';

/**
 * 从Markdown格式解析辨证结果
 */
function parseMarkdownDiagnosis(markdown: string): DiagnosisOutput {
  // 提取主要证型
  const primaryMatch = markdown.match(/\*\*主要证型\*\*[：:]\s*([^\n]+)/);
  const primarySyndrome = primaryMatch ? primaryMatch[1].trim() : '辨证分析完成';

  // 提取证型得分
  const scoreMatch = markdown.match(/\*\*证型得分\*\*[：:]\s*(\d+)/);
  const syndromeScore = scoreMatch ? parseInt(scoreMatch[1]) : 5;

  // 提取病机分析
  const pathogenesisMatch = markdown.match(/\*\*病机分析\*\*[：:]\s*([^\n]+)/);
  const pathogenesis = pathogenesisMatch ? pathogenesisMatch[1].trim() : '';

  // 提取辨证依据 - 转换为正确类型
  const evidenceMatches = markdown.matchAll(/\d+\.\s*([^\n]+)/g);
  const diagnosisEvidence: DiagnosisEvidence[] = Array.from(evidenceMatches, (m, idx) => ({
    feature: m[1].trim(),
    weight: 1,
    contribution: '主要依据',
    matchDegree: 0.9,
    ruleId: `rule_${idx + 1}`
  })).slice(0, 5);

  // 提取主穴 - 转换为正确类型
  const mainPointsMatch = markdown.match(/\*\*主穴\*\*[：:]\s*([^\n]+)/);
  const mainPointsText = mainPointsMatch ? mainPointsMatch[1].trim() : '';
  const mainPoints: AcupuncturePoint[] = mainPointsText.split(/[、,，]/)
    .map(s => s.trim())
    .filter(s => s)
    .map(point => ({
      point,
      meridian: '待确认',
      effect: '主穴',
      technique: '平补平泻'
    }));

  // 提取配穴 - 转换为正确类型
  const secondaryPointsMatch = markdown.match(/\*\*配穴\*\*[：:]\s*([^\n]+)/);
  const secondaryPointsText = secondaryPointsMatch ? secondaryPointsMatch[1].trim() : '';
  const secondaryPoints: AcupuncturePoint[] = secondaryPointsText.split(/[、,，]/)
    .map(s => s.trim())
    .filter(s => s)
    .map(point => ({
      point,
      meridian: '待确认',
      effect: '配穴',
      technique: '平补平泻'
    }));

  // 提取刺法
  const techniqueMatch = markdown.match(/\*\*刺法\*\*[：:]\s*([^\n]+)/);
  const techniquePrinciple = techniqueMatch ? techniqueMatch[1].trim() : '';

  // 提取治疗频次
  const frequencyMatch = markdown.match(/\*\*治疗频次\*\*[：:]\s*([^\n]+)/);
  const treatmentFrequency = frequencyMatch ? frequencyMatch[1].trim() : '';

  // 提取生活调护
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

export async function submitDiagnosis(input: DiagnosisInput): Promise<DiagnosisOutput> {
  const requestPayload = {
    bot_id: BOT_ID,
    user_id: generateUserId(),
    stream: true,
    additional_messages: [{
      role: 'user',
      content: JSON.stringify({
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
      }, null, 2),
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

  if (!response.ok) throw new Error(`API请求失败: ${response.status}`);

  const reader = response.body?.getReader();
  if (!reader) throw new Error('无法读取响应流');

  let result = '';
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    result += decoder.decode(value, { stream: true });
  }

  const lines = result.split('\n');
  let finalContent = '';
  let reasoningContent = '';
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
        
        if (currentEvent === 'conversation.message.delta') {
          if (data.reasoning_content) reasoningContent += data.reasoning_content;
          if (data.content) finalContent += data.content;
        }
        if (currentEvent === 'conversation.message.completed' && data.content) {
          finalContent = data.content;
        }
      } catch {}
    }
  }
  
  if (!finalContent && reasoningContent) finalContent = reasoningContent;
  if (!finalContent) throw new Error('未获取到辨证结果');

  try {
    return typeof finalContent === 'string' ? JSON.parse(finalContent) : finalContent;
  } catch {
    return parseMarkdownDiagnosis(finalContent);
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
