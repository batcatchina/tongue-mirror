import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Toaster, toast } from 'react-hot-toast';
import NavBar from '@/components/common/NavBar';
import {
  TongueColorSelector,
  TongueShapeSelector,
  TongueCoatingSelector,
  TongueStateSelector,
} from '@/components/tongue-input/TongueFeatureSelectors';
import ImageUpload from '@/components/tongue-input/ImageUpload';
import SymptomInput from '@/components/tongue-input/SymptomInput';
import PatientInfoForm from '@/components/tongue-input/PatientInfoForm';
import DiagnosisResultDisplay from '@/components/result-display/DiagnosisResultDisplay';
import AcupunctureDisplay from '@/components/result-display/AcupunctureDisplay';
import LifeCareDisplay from '@/components/result-display/LifeCareDisplay';
import { useDiagnosisStore } from '@/stores/diagnosisStore';
import { submitDiagnosis } from '@/services/api';

const DiagnosisPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'diagnosis' | 'acupuncture' | 'care'>('diagnosis');
  
  const {
    inputFeatures,
    symptoms,
    patientInfo,
    diagnosisResult,
    isAnalyzing,
    currentStep,
    stepProgress,
    setTongueColor,
    setTongueShape,
    setTongueState,
    setCoating,
    addSymptom,
    removeSymptom,
    updateSymptom,
    setPatientInfo,
    setImageData,
    setDiagnosisResult,
    setIsAnalyzing,
    setError,
    setCurrentStep,
    resetProgress,
    resetInput,
    getDiagnosisInput,
    saveCase,
  } = useDiagnosisStore();

  // 提交辨证
  const handleSubmit = async () => {
    // 验证必填项
    if (!inputFeatures.tongueColor.value) {
      toast.error('请选择舌色');
      return;
    }
    if (!inputFeatures.tongueShape.value) {
      toast.error('请选择舌形');
      return;
    }
    if (!inputFeatures.tongueState.value) {
      toast.error('请选择舌态');
      return;
    }
    if (!inputFeatures.coating.color) {
      toast.error('请选择苔色');
      return;
    }
    if (!patientInfo.chiefComplaint) {
      toast.error('请填写主诉');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setCurrentStep('validating', 10);

    try {
      const input = getDiagnosisInput();
      setCurrentStep('recognizing', 25);
      
      const result = await submitDiagnosis(input, (step) => {
        switch (step) {
          case 'recognizing':
            setCurrentStep('recognizing', 40);
            break;
          case 'analyzing':
            setCurrentStep('analyzing', 55);
            break;
          case 'reasoning':
            setCurrentStep('reasoning', 70);
            break;
          case 'matching':
            setCurrentStep('matching', 85);
            break;
        }
      });
      
      setCurrentStep('matching', 95);
      setDiagnosisResult(result);
      toast.success('辨证分析完成！');
    } catch (error) {
      const message = error instanceof Error ? error.message : '辨证分析失败';
      setError(message);
      toast.error(message);
    } finally {
      setIsAnalyzing(false);
      resetProgress();
    }
  };

  // 保存病例
  const handleSaveCase = () => {
    if (!diagnosisResult) {
      toast.error('请先完成辨证分析');
      return;
    }
    saveCase(diagnosisResult);
    toast.success('病例已保存');
  };

  // 清空输入
  const handleReset = () => {
    resetInput();
    toast.success('已清空所有输入');
  };

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      <Toaster position="top-center" />
      <NavBar currentPath="/" onNavigate={(path) => navigate(path)} />
      
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：输入区域 */}
          <div className="space-y-6">
            {/* 舌象特征输入 */}
            <div className="tcm-card p-5">
              <h2 className="tcm-section-title">舌象特征输入</h2>
              
              {/* 图片上传 */}
              <div className="mb-6">
                <ImageUpload onChange={(imageData) => setImageData(imageData)} />
              </div>
              
              <div className="tcm-divider" />
              
              {/* 舌色选择 */}
              <div className="mb-6">
                <TongueColorSelector
                  value={inputFeatures.tongueColor.value}
                  onChange={setTongueColor}
                />
              </div>
              
              <div className="tcm-divider" />
              
              {/* 舌形选择 */}
              <div className="mb-6">
                <TongueShapeSelector
                  value={inputFeatures.tongueShape.value}
                  onChange={setTongueShape}
                />
              </div>
              
              <div className="tcm-divider" />
              
              {/* 舌苔选择 */}
              <div className="mb-6">
                <h3 className="block text-sm font-medium text-stone-700 mb-3">舌苔</h3>
                <TongueCoatingSelector
                  color={inputFeatures.coating.color}
                  texture={inputFeatures.coating.texture}
                  moisture={inputFeatures.coating.moisture}
                  onColorChange={(color) => setCoating(color, inputFeatures.coating.texture, inputFeatures.coating.moisture)}
                  onTextureChange={(texture) => setCoating(inputFeatures.coating.color, texture, inputFeatures.coating.moisture)}
                  onMoistureChange={(moisture) => setCoating(inputFeatures.coating.color, inputFeatures.coating.texture, moisture)}
                />
              </div>
              
              <div className="tcm-divider" />
              
              {/* 舌态选择 */}
              <div>
                <TongueStateSelector
                  value={inputFeatures.tongueState.value}
                  onChange={setTongueState}
                />
              </div>
            </div>

            {/* 伴随症状 */}
            <div className="tcm-card p-5">
              <SymptomInput
                symptoms={symptoms}
                onAdd={addSymptom}
                onRemove={removeSymptom}
                onUpdate={updateSymptom}
              />
            </div>

            {/* 患者信息 */}
            <div className="tcm-card p-5">
              <PatientInfoForm
                patientInfo={patientInfo}
                onChange={setPatientInfo}
              />
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="tcm-btn-secondary flex-1 flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                清空
              </button>
              <button
                onClick={handleSubmit}
                disabled={isAnalyzing}
                className="tcm-btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isAnalyzing ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    分析中...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    提交辨证
                  </>
                )}
              </button>
            </div>

            {/* 分步进度显示 */}
            {isAnalyzing && (
              <div className="tcm-card p-4 bg-gradient-to-r from-primary-50 to-secondary-50">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-stone-700">辨证分析进度</span>
                    <span className="text-primary-600 font-medium">{stepProgress}%</span>
                  </div>
                  
                  {/* 进度条 */}
                  <div className="w-full bg-stone-200 rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-primary-500 to-secondary-500 h-2 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${stepProgress}%` }}
                    />
                  </div>
                  
                  {/* 步骤列表 */}
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <StepIndicator 
                      label="识别舌象特征" 
                      step="recognizing" 
                      currentStep={currentStep} 
                    />
                    <StepIndicator 
                      label="分析舌色舌苔" 
                      step="analyzing" 
                      currentStep={currentStep} 
                    />
                    <StepIndicator 
                      label="辨证推理" 
                      step="reasoning" 
                      currentStep={currentStep} 
                    />
                    <StepIndicator 
                      label="匹配针灸方案" 
                      step="matching" 
                      currentStep={currentStep} 
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 右侧：结果展示 */}
          <div className="space-y-6">
            {/* Tab切换 */}
            <div className="tcm-card p-1">
              <div className="flex">
                <button
                  onClick={() => setActiveTab('diagnosis')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === 'diagnosis'
                      ? 'bg-primary-500 text-white'
                      : 'text-stone-600 hover:bg-stone-100'
                  }`}
                >
                  辨证结果
                </button>
                <button
                  onClick={() => setActiveTab('acupuncture')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === 'acupuncture'
                      ? 'bg-primary-500 text-white'
                      : 'text-stone-600 hover:bg-stone-100'
                  }`}
                >
                  针灸方案
                </button>
                <button
                  onClick={() => setActiveTab('care')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === 'care'
                      ? 'bg-primary-500 text-white'
                      : 'text-stone-600 hover:bg-stone-100'
                  }`}
                >
                  生活调护
                </button>
              </div>
            </div>

            {/* 结果内容 */}
            {diagnosisResult ? (
              <div className="space-y-4">
                {activeTab === 'diagnosis' && (
                  <DiagnosisResultDisplay result={diagnosisResult.diagnosisResult} />
                )}
                {activeTab === 'acupuncture' && (
                  <AcupunctureDisplay plan={diagnosisResult.acupuncturePlan} />
                )}
                {activeTab === 'care' && (
                  <LifeCareDisplay advice={diagnosisResult.lifeCareAdvice} />
                )}
                
                {/* 保存按钮 */}
                <button
                  onClick={handleSaveCase}
                  className="w-full tcm-btn-secondary flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  保存此病例
                </button>
              </div>
            ) : (
              <div className="tcm-card p-12 flex flex-col items-center justify-center text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-lg font-medium text-stone-600 mb-2">
                  等待辨证分析
                </h3>
                <p className="text-sm text-stone-400">
                  请填写左侧的舌象特征和症状信息，然后点击"提交辨证"开始分析
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

// 分步进度指示器组件
interface StepIndicatorProps {
  label: string;
  step: string;
  currentStep: string;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({ label, step, currentStep }) => {
  const stepOrder = ['recognizing', 'analyzing', 'reasoning', 'matching'];
  const currentIndex = stepOrder.indexOf(currentStep);
  const stepIndex = stepOrder.indexOf(step);
  
  const isCompleted = stepIndex < currentIndex;
  const isCurrent = stepIndex === currentIndex;
  
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${
      isCompleted 
        ? 'bg-green-100 text-green-700' 
        : isCurrent 
          ? 'bg-primary-100 text-primary-700' 
          : 'bg-stone-100 text-stone-400'
    }`}>
      {isCompleted ? (
        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ) : isCurrent ? (
        <svg className="w-4 h-4 flex-shrink-0 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : (
        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
        </svg>
      )}
      <span className="truncate">{label}</span>
    </div>
  );
};

export default DiagnosisPage;
