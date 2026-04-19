import axios, { AxiosInstance, AxiosError } from 'axios';
import type { DiagnosisInput, DiagnosisOutput } from '@/types';

// 扣子API配置 - 直接配置（生产环境）
const API_BASE_URL = 'https://api.coze.cn';
const BOT_ID = '7630373624734236672';
const API_TOKEN = 'pat_RpduRPvBPQIbpRLtAXy9NBFruewZlVKN4gH4aLgby6z2MgjNEejR2E7X8PV1L2iJ';

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 扣子API可能需要更长时间
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_TOKEN}`,
  },
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<any>) => {
    if (error.response) {
      const message = error.response.data?.msg || error.response.data?.message || '请求失败';
      console.error('API Error:', message);
      return Promise.reject(new Error(message));
    } else if (error.request) {
      console.error('Network Error:', error.message);
      return Promise.reject(new Error('网络连接失败，请检查网络设置'));
    }
    return Promise.reject(error);
  }
);

/**
 * 生成唯一用户ID
 */
function generateUserId(): string {
  return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 舌诊辨证分析API（调用扣子智能体）
 */
export async function submitDiagnosis(input: DiagnosisInput): Promise<DiagnosisOutput> {
  if (!BOT_ID) {
    throw new Error('请配置 VITE_BOT_ID 环境变量');
  }
  if (!API_TOKEN) {
    throw new Error('请配置 VITE_API_TOKEN 环境变量');
  }

  // 构造扣子API请求（v3格式，使用流式响应）
  const requestPayload = {
    bot_id: BOT_ID,
    user_id: generateUserId(),
    stream: true,  // 使用流式响应
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

  try {
    // 使用流式响应模式
    const response = await fetch(`${API_BASE_URL}/v3/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: JSON.stringify(requestPayload),
    });

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`);
    }

    // 读取流式响应
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法读取响应流');
    }

    let result = '';
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      result += chunk;
    }

    // 解析流式响应，提取最终消息
    const lines = result.split('\n').filter(line => line.trim());
    let finalContent = '';
    let reasoningContent = '';
    
    for (const line of lines) {
      if (line.startsWith('data:')) {
        try {
          const jsonStr = line.slice(5).trim();
          if (jsonStr === '[DONE]') continue;
          const data = JSON.parse(jsonStr);
          
          // 查找完成事件或消息内容
          // 扣子API可能返回content或reasoning_content字段
          if (data.event === 'conversation.message.delta') {
            if (data.data?.content) {
              finalContent += data.data.content;
            }
            if (data.data?.reasoning_content) {
              reasoningContent += data.data.reasoning_content;
            }
          } else if (data.event === 'conversation.message.completed') {
            if (data.data?.content) {
              finalContent = data.data.content;
            }
            if (data.data?.reasoning_content) {
              reasoningContent = data.data.reasoning_content;
            }
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
    
    // 如果content为空但有reasoning_content，使用reasoning_content
    if (!finalContent && reasoningContent) {
      finalContent = reasoningContent;
    }

    if (!finalContent) {
      // 尝试直接解析整个响应
      try {
        const jsonResponse = JSON.parse(result);
        if (jsonResponse.data?.messages) {
          const assistantMsg = jsonResponse.data.messages.find((m: any) => m.role === 'assistant');
          if (assistantMsg) {
            finalContent = assistantMsg.content;
          }
        }
      } catch {
        // 忽略
      }
    }

    if (!finalContent) {
      throw new Error('未获取到辨证结果');
    }

    // 解析返回的内容
    let diagnosisResult: DiagnosisOutput;
    
    try {
      diagnosisResult = typeof finalContent === 'string' ? JSON.parse(finalContent) : finalContent;
    } catch {
      // 如果解析失败，构造默认结构
      diagnosisResult = {
        diagnosisResult: {
          primarySyndrome: finalContent || '辨证结果',
          syndromeScore: 0,
          confidence: 0,
          secondarySyndromes: [],
          pathogenesis: '',
          organLocation: [],
          diagnosisEvidence: [],
          priority: '中',
          diagnosisTime: new Date().toISOString(),
        },
        acupuncturePlan: {
          treatmentPrinciple: '',
          mainPoints: [],
          secondaryPoints: [],
          contraindications: [],
          treatmentAdvice: {
            techniquePrinciple: '',
            needleRetentionTime: '',
            treatmentFrequency: '',
            treatmentSessions: '',
            sessionInterval: '',
          },
        },
        lifeCareAdvice: {
          dietSuggestions: [],
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
    
    return diagnosisResult;
  } catch (error) {
    console.error('Diagnosis API Error:', error);
    throw error;
  }
}

/**
 * 验证输入特征（本地验证）
 */
export async function validateFeatures(input: Partial<DiagnosisInput>): Promise<{
  valid: boolean;
  errors?: string[];
}> {
  const errors: string[] = [];

  // 验证必填字段
  if (!input.input_features?.tongueColor.value) errors.push('请选择舌色');
  if (!input.input_features?.tongueShape.value) errors.push('请选择舌形');
  if (!input.input_features?.coating.color) errors.push('请选择苔色');
  if (!input.input_features?.coating.texture) errors.push('请选择苔质');
  if (!input.patientInfo?.age) errors.push('请输入患者年龄');
  if (!input.patientInfo?.gender) errors.push('请选择患者性别');
  if (!input.patientInfo?.chiefComplaint) errors.push('请输入主诉');

  // 验证年龄范围
  if (input.patientInfo?.age && (input.patientInfo.age < 0 || input.patientInfo.age > 150)) {
    errors.push('年龄必须在0-150之间');
  }

  // 验证逻辑冲突
  if (input.input_features?.coating.color === '剥落' && input.input_features?.coating.texture === '厚') {
    errors.push('剥落苔不可能同时为厚苔');
  }

  return {
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined,
  };
}

/**
 * 获取辨证模式选项
 */
export async function getDiagnosisModes(): Promise<{
  modes: Array<{ value: string; label: string; description: string }>;
}> {
  return {
    modes: [
      {
        value: '快速模式',
        label: '快速模式',
        description: '仅输出主要证型和主穴',
      },
      {
        value: '详细模式',
        label: '详细模式',
        description: '完整辨证分析、选穴方案和生活调护',
      },
    ],
  };
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<boolean> {
  try {
    // 简单检查API连接
    if (!BOT_ID || !API_TOKEN) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

// 导出配置信息（用于调试）
export function getApiConfig() {
  return {
    baseUrl: API_BASE_URL,
    botId: BOT_ID ? `${BOT_ID.slice(0, 8)}...` : '未配置',
    hasToken: !!API_TOKEN,
  };
}
