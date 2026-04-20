/**
 * 针灸配穴解析测试脚本
 * 用于验证不同格式的Bot输出能否被正确解析
 */

import { getMeridian, getEffect } from './acupoint_data';

interface AcupuncturePoint {
  point: string;
  meridian: string;
  effect: string;
  technique: string;
}

// 测试用例
const testCases = [
  {
    name: '标准格式（有**粗体**）',
    markdown: `## 辨证结果
**主要证型**：脾虚湿盛
**证型得分**：8
**病机分析**：舌淡胖边有齿痕，苔白腻

## 针灸方案
**治疗原则**：健脾祛湿
**主穴**：足三里、阴陵泉、脾俞、三阴交、中脘
**配穴**：湿重加水分、丰隆

## 生活调护
- 饮食调理：忌生冷油腻`
  },
  {
    name: '无粗体格式',
    markdown: `## 辨证结果
主要证型：脾虚湿盛
证型得分：7

## 针灸方案
治疗原则：健脾祛湿
主穴：足三里、阴陵泉、脾俞
配穴：湿重加水分、丰隆`
  },
  {
    name: '完整格式带刺法',
    markdown: `## 针灸方案

**治疗原则**：健脾祛湿

**主穴**：足三里、阴陵泉、脾俞、三阴交、中脘

**配穴**：
- 湿重：加水分、丰隆
- 脾虚：加胃俞、气海

**刺法**：足三里、阴陵泉用平补平泻；脾俞、三阴交用补法

**治疗频次**：每周3次，10次为一疗程`
  },
  {
    name: '无配穴格式',
    markdown: `## 针灸方案
**主穴**：足三里、阴陵泉
配穴：无
刺法：平补平泻`
  }
];

function parseAcupoints(markdown: string): { mainPoints: AcupuncturePoint[], secondaryPoints: AcupuncturePoint[] } {
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
  
  return { mainPoints, secondaryPoints };
}

// 运行测试
console.log('🧪 针灸配穴解析测试\n');
console.log('=' .repeat(50));

testCases.forEach((testCase, index) => {
  console.log(`\n测试 ${index + 1}: ${testCase.name}`);
  console.log('-'.repeat(30));
  
  const result = parseAcupoints(testCase.markdown);
  
  console.log(`主穴 (${result.mainPoints.length}个):`);
  if (result.mainPoints.length > 0) {
    result.mainPoints.forEach(p => {
      console.log(`  - ${p.point} (${p.meridian})`);
    });
  } else {
    console.log('  (无主穴)');
  }
  
  console.log(`配穴 (${result.secondaryPoints.length}个):`);
  if (result.secondaryPoints.length > 0) {
    result.secondaryPoints.forEach(p => {
      console.log(`  - ${p.point} (${p.meridian})`);
    });
  } else {
    console.log('  (无配穴)');
  }
});

console.log('\n' + '='.repeat(50));
console.log('✅ 测试完成');
