import re

# 读取文件
with open('src/pages/Diagnosis/DiagnosisPage.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 在组件开头添加时间检查函数
time_check_code = '''
  // 服务时间检查（默认 8:00-22:00）
  const isServiceTime = (): boolean => {
    const now = new Date();
    const hour = now.getHours();
    const startHour = parseInt(import.meta.env.VITE_SERVICE_START_HOUR || '8');
    const endHour = parseInt(import.meta.env.VITE_SERVICE_END_HOUR || '22');
    return hour >= startHour && hour < endHour;
  };
  const isInServiceTime = isServiceTime();

'''

# 在 handleCompressionProgress 之前添加
content = content.replace(
    '  // 处理压缩状态更新',
    time_check_code + '  // 处理压缩状态更新'
)

# 在提交验证前添加服务时间检查
old_validate = '''    // 验证必填项
    if (!inputFeatures.tongueColor.value) {'''

new_validate = '''    // 检查服务时间
    if (!isInServiceTime) {
      toast.error('服务时间：8:00-22:00，当前暂停服务');
      return;
    }

    // 验证必填项
    if (!inputFeatures.tongueColor.value) {'''

content = content.replace(old_validate, new_validate)

# 写回文件
with open('src/pages/Diagnosis/DiagnosisPage.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("时间限制功能已添加")
