---
name: tongue-diagnosis-assistant
version: 1.0.0
description: 中医舌诊辨证辅助技能，基于舌象特征进行辨证分析和针灸选穴推荐
author: 舌诊专项提升双轨计划
homepage: https://tongue-diagnosis.example.com
tags: [中医, 舌诊, 辨证, 针灸, 健康]
category: healthcare
language: zh-CN

permissions:
  network: 
    - api.tongue-diagnosis.example.com
  storage: session

required_env:
  - TONGUE_API_KEY

config:
  api_base_url:
    type: string
    default: https://api.tongue-diagnosis.example.com/v1
    description: 舌诊API服务地址
  default_mode:
    type: select
    options: [快速模式, 详细模式]
    default: 详细模式
    description: 默认辨证模式
  default_language:
    type: select
    options: [中文, 英文]
    default: 中文
    description: 默认输出语言
---

# 舌诊辨证辅助技能

## 功能概述

本技能为AI Agent提供中医舌诊辨证能力，能够：
- 分析舌象特征（舌色、舌形、舌苔等）
- 进行证型判断和辨证论治
- 推荐针灸选穴方案
- 提供生活调护建议

## 使用场景

### 场景1：用户提供舌象图片
```
用户：我拍了一张舌象照片，帮我看看
Agent：请问您能描述一下舌头的颜色、形状和舌苔情况吗？
      或者我可以根据您上传的图片进行分析（如果支持图像输入）
用户：舌头发红，苔黄，有点裂纹
Agent：[调用舌诊辨证接口]
```

### 场景2：用户描述症状
```
用户：我最近口干舌燥，失眠多梦
Agent：了解，为了更好地帮助您判断体质，能否描述一下您的舌象？
      比如舌头的颜色（淡红/红/淡白等）、舌苔情况（薄/厚/颜色等）
用户：舌头比较红，舌苔黄而薄
Agent：[调用舌诊辨证接口]
```

### 场景3：健康咨询
```
用户：我想了解一下自己的体质
Agent：了解，我来帮您做一次舌诊分析。
      请描述一下您的舌象情况，包括：
      1. 舌头的颜色（淡红/淡白/红/绛/紫/青紫）
      2. 舌头的形状（胖大/瘦薄/正常）
      3. 舌苔的颜色和厚薄（薄白/黄/薄/厚等）
      4. 其他特征如裂纹、齿痕等
用户：舌头淡红，苔薄白，形状正常
Agent：[调用舌诊辨证接口]
```

## 工具使用

### analyze_tongue
执行舌诊辨证分析。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tongue_color | string | 是 | 舌色：淡红/淡白/红/绛/紫/青紫 |
| tongue_shape | string | 是 | 舌形：胖大/瘦薄/正常 |
| tongue_coating_color | string | 是 | 苔色：薄白/白厚/黄/灰黑/剥落 |
| tongue_coating_texture | string | 是 | 苔质：薄/厚/正常 |
| patient_age | integer | 是 | 患者年龄 (0-150) |
| patient_gender | string | 是 | 性别：男/女 |
| chief_complaint | string | 是 | 主诉（不超过200字） |
| symptoms | string | 否 | 伴随症状描述 |
| tongue_texture | string | 否 | 舌面特征：正常/裂纹/齿痕 |
| tongue_movement | string | 否 | 舌态：强硬/痿软/歪斜/颤动/正常 |
| coating_moisture | string | 否 | 润燥：润/燥/正常 |
| coating_greasy | string | 否 | 腻腐：腻/腐/否 |
| mode | string | 否 | 辨证模式：快速模式/详细模式 |

**返回：**
```json
{
  "辨证结果": {
    "主要证型": "阴虚火旺证",
    "置信度": 0.85,
    "病机": "肝肾阴虚，虚火上炎"
  },
  "针灸方案": {
    "治疗原则": "滋阴清热",
    "主穴": [{"穴位": "太溪", "经络": "肾经"}]
  }
}
```

### validate_tongue_features
验证舌象特征的有效性。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| features | string | 是 | 舌象特征JSON字符串 |

**返回：**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["红舌通常与瘦薄舌相关"],
  "suggestions": []
}
```

### query_acupoints
根据证型查询穴位信息。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| syndrome | string | 是 | 中医证型 |
| symptom | string | 否 | 具体症状 |
| organ | string | 否 | 脏腑定位 |
| limit | integer | 否 | 返回数量限制（默认5） |

## 输出格式

技能返回结构化的JSON结果，Agent应将其转换为易读的自然语言：

```
根据您的舌象分析：

【辨证结果】
- 主要证型：阴虚火旺证（置信度：85%）
- 病机：肝肾阴虚，虚火上炎
- 涉及脏腑：肝、肾

【针灸方案】
- 治疗原则：滋阴清热，养心安神
- 主穴：太溪（肾经）、照海（肾经）、三阴交（脾经）
- 配穴：神门（心经）、合谷（大肠经）

【生活调护】
- 饮食：宜食银耳、百合、莲子等滋阴食物
- 起居：规律作息，避免熬夜
```

## 注意事项

1. **免责声明**：本技能仅供辅助参考，不能替代专业医师诊断
2. **信息完整性**：调用前确保收集足够的舌象信息
3. **复杂病例**：对于复杂或严重症状，建议转诊专业医师
4. **儿童用药**：儿童针灸需特别谨慎，建议专业医师操作

## 错误处理

技能可能返回以下错误码：
- `INVALID_FEATURES`：舌象特征格式错误
- `MISSING_REQUIRED`：缺少必填参数
- `SYNERGY_CONFLICT`：特征组合存在逻辑冲突
- `RATE_LIMIT`：请求频率超限

## 更新日志

### v1.0.0 (2026-04-22)
- 初始版本发布
- 支持舌诊辨证、特征验证、穴位查询三大功能
