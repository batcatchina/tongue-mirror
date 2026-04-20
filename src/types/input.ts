// 舌象特征类型定义
export interface TongueColor {
  value: string;
  confidence?: number;
  distributionFeatures?: DistributionFeature[];
}

export interface DistributionFeature {
  part: '舌尖' | '舌边' | '舌中' | '舌根';
  feature: '红点' | '瘀斑' | '红赤' | '淡白';
  degree?: '轻微' | '中等' | '明显' | '严重';
}

export interface TongueShape {
  value: '胖大' | '瘦薄' | '正常';
  confidence?: number;
}

export interface Crack {
  value: '是' | '否';
  degree?: '轻微' | '中等' | '明显' | '严重';
  distribution?: '舌尖' | '舌边' | '舌中' | '舌根';
}

export interface TeethMark {
  value: '是' | '否';
  degree?: '轻微' | '中等' | '明显' | '严重';
  distribution?: '单侧' | '双侧' | '全舌';
}

export interface TongueState {
  value: '强硬' | '痿软' | '歪斜' | '颤动' | '正常';
  degree?: '轻微' | '中等' | '明显' | '严重';
}

export interface TongueCoating {
  color: '薄白' | '白厚' | '黄' | '灰黑' | '剥落';
  texture: '薄' | '厚' | '正常';
  moisture: '润' | '燥' | '正常';
  greasy?: '腻' | '腐' | '否';
}

export interface TongueSurface {
  value: '是' | '否';
  degree?: '轻微' | '中等' | '明显' | '严重';
}

export interface Ecchymosis {
  value: '是' | '否';
  part?: '舌尖' | '舌边' | '舌中' | '舌根';
  size?: '点状' | '小片状' | '大片状' | '弥漫';
  count?: '单个' | '2-3个' | '多个' | '散在';
}

export interface InputFeatures {
  tongueColor: TongueColor;
  tongueShape: TongueShape;
  crack?: Crack;
  teethMark?: TeethMark;
  tongueState: TongueState;
  coating: TongueCoating;
  tongueSurface?: TongueSurface;
  ecchymosis?: Ecchymosis;
}

// 伴随症状类型
export interface Symptom {
  symptom: string;
  degree?: '轻度' | '中度' | '重度';
  duration?: string;
  frequency?: '持续' | '间歇' | '偶尔';
  aggravatingFactor?: string;
}

// 患者信息类型
export interface PatientInfo {
  age: number;
  gender: '男' | '女' | '其他';
  chiefComplaint: string;
  medicalHistory?: string;
  constitution?: string;
  allergyHistory?: string;
  medicationHistory?: string;
}

// 辨证分析选项
export interface DiagnosisOptions {
  mode: '快速模式' | '详细模式';
  language: '中文' | '英文';
  confidenceThreshold: number;
  includeExplanation: boolean;
  includeTreatmentAdvice: boolean;
  personalization: '基础' | '标准' | '高级';
  acupuncturePointCount: number;
}

// 完整输入数据
export interface DiagnosisInput {
  input_features: InputFeatures;
  symptoms?: Symptom[];
  patientInfo: PatientInfo;
  options?: Partial<DiagnosisOptions>;
  imageData?: string; // 舌象图片的base64数据
  metadata?: {
    submissionTime?: string;
    userType?: '中医师' | '学生' | '研究者';
    clientVersion?: string;
    sessionId?: string;
    requestId?: string;
    sourcePlatform?: 'Web' | 'iOS' | 'Android';
  };
}
