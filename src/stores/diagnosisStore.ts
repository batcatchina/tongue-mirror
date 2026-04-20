import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { 
  DiagnosisInput, 
  DiagnosisOutput, 
  CaseRecord,
  InputFeatures,
  PatientInfo,
  Symptom
} from '@/types';

// 初始舌象特征 - 使用合法的联合类型值
const initialFeatures: InputFeatures = {
  tongueColor: { value: '' as const },
  tongueShape: { value: '正常' as const },
  tongueState: { value: '正常' as const },
  coating: { color: '薄白' as const, texture: '薄' as const, moisture: '润' as const },
};

// 初始患者信息
const initialPatientInfo: PatientInfo = {
  age: 0,
  gender: '男' as const,
  chiefComplaint: '',
};

// 进度步骤枚举
export type DiagnosisStep = 
  | 'idle'           // 空闲
  | 'validating'     // 验证输入
  | 'recognizing'    // 识别舌象特征
  | 'analyzing'      // 分析舌色舌苔
  | 'reasoning'      // 辨证推理
  | 'matching';      // 匹配针灸方案

interface DiagnosisState {
  // 输入状态
  inputFeatures: InputFeatures;
  symptoms: Symptom[];
  patientInfo: PatientInfo;
  imageData: string | null; // 舌象图片base64数据
  
  // 输出状态
  diagnosisResult: DiagnosisOutput | null;
  isAnalyzing: boolean;
  error: string | null;
  
  // 进度状态
  currentStep: DiagnosisStep;
  stepProgress: number; // 0-100
  
  // 病例列表
  caseList: CaseRecord[];
  
  // 操作方法
  setImageData: (data: string | null) => void;
  setInputFeatures: (features: Partial<InputFeatures>) => void;
  setTongueColor: (color: string, confidence?: number) => void;
  setTongueShape: (shape: string, confidence?: number) => void;
  setTongueState: (stateValue: string, degree?: string) => void;
  setCoating: (color: string, texture: string, moisture?: string, greasy?: string) => void;
  setCrack: (value: '是' | '否', degree?: string, distribution?: string) => void;
  setTeethMark: (value: '是' | '否', degree?: string, distribution?: string) => void;
  setTongueSurface: (value: '是' | '否', degree?: string) => void;
  setEcchymosis: (value: '是' | '否', part?: string, size?: string, count?: string) => void;
  
  addSymptom: (symptom: Symptom) => void;
  removeSymptom: (index: number) => void;
  updateSymptom: (index: number, symptom: Partial<Symptom>) => void;
  
  setPatientInfo: (info: Partial<PatientInfo>) => void;
  
  setDiagnosisResult: (result: DiagnosisOutput | null) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  setError: (error: string | null) => void;
  
  // 进度方法
  setCurrentStep: (step: DiagnosisStep, progress?: number) => void;
  resetProgress: () => void;
  
  resetInput: () => void;
  getDiagnosisInput: () => DiagnosisInput;
  
  saveCase: (result: DiagnosisOutput) => void;
  loadCases: () => CaseRecord[];
  deleteCase: (id: string) => void;
}

export const useDiagnosisStore = create<DiagnosisState>()(
  persist(
    (set, get) => ({
      // 初始状态
      inputFeatures: initialFeatures,
      symptoms: [],
      patientInfo: initialPatientInfo,
      imageData: null,
      diagnosisResult: null,
      isAnalyzing: false,
      error: null,
      caseList: [],
      
      // 进度状态
      currentStep: 'idle',
      stepProgress: 0,
      
      // 设置图片数据
      setImageData: (data) => set({ imageData: data }),
      
      // 设置舌象特征
      setInputFeatures: (features) =>
        set((state) => ({
          inputFeatures: { ...state.inputFeatures, ...features },
        })),
      
      setTongueColor: (color, confidence) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            tongueColor: { value: color, confidence },
          },
        })),
      
      setTongueShape: (shape, confidence) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            tongueShape: { value: shape as '胖大' | '瘦薄' | '正常', confidence },
          },
        })),
      
      setTongueState: (stateValue, degree) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            tongueState: { value: stateValue as '强硬' | '痿软' | '歪斜' | '颤动' | '正常', degree: degree as any },
          },
        })),
      
      setCoating: (color, texture, moisture, greasy) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            coating: {
              color: color as any,
              texture: texture as any,
              moisture: moisture as any,
              greasy: greasy as any,
            },
          },
        })),
      
      setCrack: (value, degree, distribution) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            crack: { value, degree: degree as any, distribution: distribution as any },
          },
        })),
      
      setTeethMark: (value, degree, distribution) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            teethMark: { value, degree: degree as any, distribution: distribution as any },
          },
        })),
      
      setTongueSurface: (value, degree) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            tongueSurface: { value, degree: degree as any },
          },
        })),
      
      setEcchymosis: (value, part, size, count) =>
        set((state) => ({
          inputFeatures: {
            ...state.inputFeatures,
            ecchymosis: { value, part: part as any, size: size as any, count: count as any },
          },
        })),
      
      // 伴随症状操作
      addSymptom: (symptom) =>
        set((state) => ({
          symptoms: [...state.symptoms, symptom],
        })),
      
      removeSymptom: (index) =>
        set((state) => ({
          symptoms: state.symptoms.filter((_, i) => i !== index),
        })),
      
      updateSymptom: (index, symptom) =>
        set((state) => ({
          symptoms: state.symptoms.map((s, i) =>
            i === index ? { ...s, ...symptom } : s
          ),
        })),
      
      // 患者信息
      setPatientInfo: (info) =>
        set((state) => ({
          patientInfo: { ...state.patientInfo, ...info },
        })),
      
      // 辨证结果
      setDiagnosisResult: (result) => set({ diagnosisResult: result }),
      setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
      setError: (error) => set({ error }),
      
      // 进度方法
      setCurrentStep: (step, progress) => set({ 
        currentStep: step, 
        stepProgress: progress ?? (step === 'idle' ? 0 : 100) 
      }),
      resetProgress: () => set({ currentStep: 'idle', stepProgress: 0 }),
      
      // 重置输入
      resetInput: () =>
        set({
          inputFeatures: initialFeatures,
          symptoms: [],
          patientInfo: initialPatientInfo,
          imageData: null,
          diagnosisResult: null,
          error: null,
          currentStep: 'idle',
          stepProgress: 0,
        }),
      
      // 获取完整输入数据
      getDiagnosisInput: () => {
        const state = get();
        return {
          input_features: state.inputFeatures,
          symptoms: state.symptoms,
          patientInfo: state.patientInfo,
          imageData: state.imageData || undefined,
        };
      },
      
      // 保存病例
      saveCase: (result) =>
        set((state) => {
          const newCase: CaseRecord = {
            id: `case_${Date.now()}`,
            patientInfo: state.patientInfo,
            inputFeatures: state.inputFeatures,
            symptoms: state.symptoms,
            diagnosisResult: result.diagnosisResult,
            acupuncturePlan: result.acupuncturePlan,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
          return { caseList: [newCase, ...state.caseList] };
        }),
      
      loadCases: () => get().caseList,
      
      deleteCase: (id) =>
        set((state) => ({
          caseList: state.caseList.filter((c) => c.id !== id),
        })),
    }),
    {
      name: 'tongue-diagnosis-storage',
    }
  )
);
