"""
舌镜 MCP Server - 核心服务器实现

基于Model Context Protocol的中医舌诊辨证辅助服务
"""

import json
import os
import sys
from typing import Any, Optional

# MCP SDK导入（兼容新旧版本）
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ResourceTemplate,
        Prompt,
        PromptMessage,
    )
    MCP_VERSION = "new"
except ImportError:
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import (
            Tool,
            TextContent,
            Resource,
            ResourceTemplate,
            Prompt,
            PromptMessage,
        )
        MCP_VERSION = "old"
    except ImportError:
        print("请安装MCP SDK: pip install mcp", file=sys.stderr)
        sys.exit(1)

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 服务器实例
APP_NAME = "tongue-mirror"
APP_VERSION = "1.0.0"

server = Server(APP_NAME)


# ============================================================
# 工具定义 (Tools)
# ============================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="analyze_tongue",
            description="执行舌诊辨证分析，基于舌象特征进行证型判断和针灸选穴推荐",
            inputSchema={
                "type": "object",
                "required": ["tongue_color", "tongue_shape", "tongue_coating_color", 
                            "tongue_coating_texture", "patient_age", "patient_gender", 
                            "chief_complaint"],
                "properties": {
                    "tongue_color": {
                        "type": "string",
                        "description": "舌色",
                        "enum": ["淡红", "淡白", "红", "绛", "紫", "青紫"]
                    },
                    "tongue_shape": {
                        "type": "string",
                        "description": "舌形",
                        "enum": ["胖大", "瘦薄", "正常"]
                    },
                    "tongue_coating_color": {
                        "type": "string",
                        "description": "苔色",
                        "enum": ["薄白", "白厚", "黄", "灰黑", "剥落"]
                    },
                    "tongue_coating_texture": {
                        "type": "string",
                        "description": "苔质",
                        "enum": ["薄", "厚", "正常"]
                    },
                    "patient_age": {
                        "type": "integer",
                        "description": "患者年龄 (0-150)",
                        "minimum": 0,
                        "maximum": 150
                    },
                    "patient_gender": {
                        "type": "string",
                        "description": "性别",
                        "enum": ["男", "女"]
                    },
                    "chief_complaint": {
                        "type": "string",
                        "description": "主诉，不超过200字",
                        "maxLength": 200
                    },
                    "symptoms": {
                        "type": "string",
                        "description": "伴随症状，自由文本描述"
                    },
                    "tongue_texture": {
                        "type": "string",
                        "description": "舌面特征",
                        "enum": ["正常", "裂纹", "齿痕"],
                        "default": "正常"
                    },
                    "tongue_movement": {
                        "type": "string",
                        "description": "舌态",
                        "enum": ["强硬", "痿软", "歪斜", "颤动", "正常"],
                        "default": "正常"
                    },
                    "coating_moisture": {
                        "type": "string",
                        "description": "润燥",
                        "enum": ["润", "燥", "正常"]
                    },
                    "coating_greasy": {
                        "type": "string",
                        "description": "腻腐",
                        "enum": ["腻", "腐", "否"]
                    },
                    "crack": {
                        "type": "string",
                        "description": "裂纹",
                        "enum": ["是", "否"],
                        "default": "否"
                    },
                    "teeth_mark": {
                        "type": "string",
                        "description": "齿痕",
                        "enum": ["是", "否"],
                        "default": "否"
                    },
                    "spots": {
                        "type": "string",
                        "description": "瘀斑",
                        "enum": ["是", "否"],
                        "default": "否"
                    },
                    "mode": {
                        "type": "string",
                        "description": "辨证模式",
                        "enum": ["快速模式", "详细模式"],
                        "default": "详细模式"
                    },
                    "language": {
                        "type": "string",
                        "description": "输出语言",
                        "enum": ["中文", "英文"],
                        "default": "中文"
                    }
                }
            }
        ),
        Tool(
            name="validate_tongue_features",
            description="验证舌象特征的有效性和逻辑一致性",
            inputSchema={
                "type": "object",
                "required": ["features"],
                "properties": {
                    "features": {
                        "type": "string",
                        "description": "舌象特征JSON字符串"
                    }
                }
            }
        ),
        Tool(
            name="query_acupoints",
            description="根据证型或症状查询推荐穴位",
            inputSchema={
                "type": "object",
                "required": ["syndrome"],
                "properties": {
                    "syndrome": {
                        "type": "string",
                        "description": "中医证型，如: 阴虚火旺证/湿热内蕴证"
                    },
                    "symptom": {
                        "type": "string",
                        "description": "具体症状（可选）"
                    },
                    "organ": {
                        "type": "string",
                        "description": "脏腑定位（可选）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """调用工具"""
    
    if name == "analyze_tongue":
        return await analyze_tongue_tool(arguments)
    elif name == "validate_tongue_features":
        return await validate_tongue_features_tool(arguments)
    elif name == "query_acupoints":
        return await query_acupoints_tool(arguments)
    else:
        raise ValueError(f"未知工具: {name}")


async def analyze_tongue_tool(args: dict) -> list[TextContent]:
    """舌诊辨证分析工具"""
    
    # 提取参数
    tongue_color = args.get("tongue_color")
    tongue_shape = args.get("tongue_shape")
    tongue_coating_color = args.get("tongue_coating_color")
    tongue_coating_texture = args.get("tongue_coating_texture")
    patient_age = args.get("patient_age")
    patient_gender = args.get("patient_gender")
    chief_complaint = args.get("chief_complaint")
    symptoms = args.get("symptoms", "")
    tongue_texture = args.get("tongue_texture", "正常")
    tongue_movement = args.get("tongue_movement", "正常")
    coating_moisture = args.get("coating_moisture")
    coating_greasy = args.get("coating_greasy")
    crack = args.get("crack", "否")
    teeth_mark = args.get("teeth_mark", "否")
    spots = args.get("spots", "否")
    mode = args.get("mode", "详细模式")
    language = args.get("language", "中文")
    
    # 调用核心辨证逻辑
    result = perform_tongue_analysis(
        tongue_color=tongue_color,
        tongue_shape=tongue_shape,
        tongue_coating_color=tongue_coating_color,
        tongue_coating_texture=tongue_coating_texture,
        patient_age=patient_age,
        patient_gender=patient_gender,
        chief_complaint=chief_complaint,
        symptoms=symptoms,
        tongue_texture=tongue_texture,
        tongue_movement=tongue_movement,
        coating_moisture=coating_moisture,
        coating_greasy=coating_greasy,
        crack=crack,
        teeth_mark=teeth_mark,
        spots=spots,
        mode=mode,
        language=language
    )
    
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def validate_tongue_features_tool(args: dict) -> list[TextContent]:
    """特征验证工具"""
    
    features_str = args.get("features", "{}")
    
    try:
        features = json.loads(features_str)
    except json.JSONDecodeError:
        return [TextContent(
            type="text",
            text=json.dumps({
                "is_valid": False,
                "errors": [{"field": "features", "message": "无效的JSON格式", "code": "INVALID_JSON"}]
            }, ensure_ascii=False, indent=2)
        )]
    
    result = validate_features(features)
    
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def query_acupoints_tool(args: dict) -> list[TextContent]:
    """穴位查询工具"""
    
    syndrome = args.get("syndrome")
    symptom = args.get("symptom")
    organ = args.get("organ")
    limit = args.get("limit", 5)
    
    result = search_acupoints(syndrome=syndrome, symptom=symptom, organ=organ, limit=limit)
    
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


# ============================================================
# 资源定义 (Resources)
# ============================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """列出所有可用资源"""
    return [
        Resource(
            uri="tongue://feature-categories",
            name="feature_categories",
            description="返回舌象特征分类的完整列表"
        ),
        Resource(
            uri="tongue://syndrome-list",
            name="syndrome_list",
            description="返回支持的证型列表"
        ),
        Resource(
            uri="tongue://api-docs",
            name="api_docs",
            description="返回服务API的完整文档URI"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    
    if uri == "tongue://feature-categories":
        return json.dumps({
            "舌色": ["淡红", "淡白", "红", "绛", "紫", "青紫"],
            "舌形": ["胖大", "瘦薄", "正常"],
            "舌态": ["强硬", "痿软", "歪斜", "颤动", "正常"],
            "苔色": ["薄白", "白厚", "黄", "灰黑", "剥落"],
            "苔质": ["薄", "厚", "正常"],
            "特征": {
                "裂纹": ["是", "否"],
                "齿痕": ["是", "否"],
                "瘀斑": ["是", "否"]
            },
            "润燥": ["润", "燥", "正常"],
            "腻腐": ["腻", "腐", "否"]
        }, ensure_ascii=False)
    
    elif uri == "tongue://syndrome-list":
        return json.dumps({
            "证型列表": [
                "阴虚火旺证", "湿热内蕴证", "气血两虚证", "肝郁气滞证",
                "心火上炎证", "胃阴不足证", "脾虚湿盛证", "肾阳虚证",
                "痰湿内阻证", "血瘀证", "气滞血瘀证", "寒湿困脾证"
            ]
        }, ensure_ascii=False)
    
    elif uri == "tongue://api-docs":
        api_base = os.getenv("API_BASE_URL", "https://api.example.com")
        return json.dumps({
            "openapi_url": f"{api_base}/tongue-diagnosis/openapi.json",
            "skill_md_url": "https://docs.example.com/skills/tongue-diagnosis/SKILL.md",
            "mcp_server_config": "https://docs.example.com/mcp/tongue-server.json",
            "version": APP_VERSION,
            "documentation": {
                "zh": "https://docs.example.com/tongue-diagnosis/zh",
                "en": "https://docs.example.com/tongue-diagnosis/en"
            }
        }, ensure_ascii=False)
    
    else:
        raise ValueError(f"未知资源: {uri}")


# ============================================================
# 提示模板定义 (Prompts)
# ============================================================

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """列出所有提示模板"""
    return [
        Prompt(
            name="tongue_diagnosis",
            description="舌诊辨证的标准化提示模板",
            arguments=[
                PromptMessage(
                    role="user",
                    content="请根据以下舌象特征进行分析"
                )
            ]
        ),
        Prompt(
            name="quick_tongue_check",
            description="快速舌诊检查的简化提示"
        )
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> Prompt:
    """获取提示内容"""
    
    if name == "tongue_diagnosis":
        return Prompt(
            name="tongue_diagnosis",
            description="舌诊辨证的标准化提示模板",
            messages=[
                PromptMessage(
                    role="user",
                    content="""你是一位专业的中医舌诊助手。当用户提供舌象描述时：

1. 首先识别舌象特征（舌色、舌形、舌苔等）
2. 询问必要的补充信息（年龄、性别、主诉）
3. 调用 analyze_tongue 工具进行辨证分析
4. 解释辨证结果的临床意义
5. 提供针灸选穴建议和生活调护指导

重要原则：
- 不确定时，宁可请用户补充信息，不要臆断
- 强调本系统仅供辅助参考，不能替代专业诊断
- 对于复杂病例，建议转诊专业医师"""
                )
            ]
        )
    
    elif name == "quick_tongue_check":
        return Prompt(
            name="quick_tongue_check",
            description="快速舌诊检查的简化提示",
            messages=[
                PromptMessage(
                    role="user",
                    content="""快速舌诊模式：
用户可能只提供简短的舌象描述，如"舌红苔黄"或"舌头有裂纹"。

处理流程：
1. 解析用户描述中的特征关键词
2. 补全缺失的必填字段（设为"正常"或询问用户）
3. 调用 analyze_tongue 进行分析
4. 以简洁方式呈现结果"""
                )
            ]
        )
    
    else:
        raise ValueError(f"未知提示: {name}")


# ============================================================
# 核心辨证逻辑
# ============================================================

def perform_tongue_analysis(
    tongue_color: str,
    tongue_shape: str,
    tongue_coating_color: str,
    tongue_coating_texture: str,
    patient_age: int,
    patient_gender: str,
    chief_complaint: str,
    symptoms: str = "",
    tongue_texture: str = "正常",
    tongue_movement: str = "正常",
    coating_moisture: str = None,
    coating_greasy: str = None,
    crack: str = "否",
    teeth_mark: str = "否",
    spots: str = "否",
    mode: str = "详细模式",
    language: str = "中文"
) -> dict:
    """
    执行舌诊辨证分析
    
    这是一个基于规则的简化辨证实现。
    生产环境中应调用真实的舌诊API。
    """
    
    # 证型评分规则（包含平和质）
    syndrome_scores = {
        "阴虚火旺证": 0,
        "湿热内蕴证": 0,
        "气血两虚证": 0,
        "肝郁气滞证": 0,
        "心火上炎证": 0,
        "胃阴不足证": 0,
        "脾虚湿盛证": 0,
        "肾阳虚证": 0,
        "痰湿内阻证": 0,
        "血瘀证": 0,
        "寒湿困脾证": 0,
        "平和质": 0
    }
    
    # 舌色评分
    color_scores = {
        "淡红": {"阴虚火旺证": 2, "气血两虚证": 1, "平和质": 2},
        "淡白": {"气血两虚证": 4, "肾阳虚证": 3},
        "红": {"阴虚火旺证": 4, "心火上炎证": 3, "湿热内蕴证": 2},
        "绛": {"阴虚火旺证": 5, "血瘀证": 3},
        "紫": {"血瘀证": 5, "肝郁气滞证": 3},
        "青紫": {"血瘀证": 6, "寒湿困脾证": 4},
        "正常": {"平和质": 3}
    }
    
    # 舌形评分
    shape_scores = {
        "胖大": {"脾虚湿盛证": 4, "湿热内蕴证": 3, "肾阳虚证": 2},
        "瘦薄": {"阴虚火旺证": 4, "气血两虚证": 3, "胃阴不足证": 2},
        "正常": {"平和质": 2}
    }
    
    # 苔色评分
    coating_color_scores = {
        "薄白": {"气血两虚证": 1, "平和质": 3},
        "白厚": {"脾虚湿盛证": 4, "湿热内蕴证": 2, "寒湿困脾证": 3},
        "黄": {"湿热内蕴证": 4, "心火上炎证": 3, "阴虚火旺证": 2},
        "灰黑": {"寒湿困脾证": 4, "肾阳虚证": 3},
        "剥落": {"胃阴不足证": 5, "阴虚火旺证": 3},
        "正常": {"平和质": 3}
    }
    
    # 苔质评分
    coating_texture_scores = {
        "薄": {"阴虚火旺证": 1, "平和质": 2},
        "厚": {"湿热内蕴证": 3, "脾虚湿盛证": 3},
        "正常": {"平和质": 3}
    }
    
    # 特殊特征评分
    if crack == "是":
        syndrome_scores["阴虚火旺证"] += 3
        syndrome_scores["胃阴不足证"] += 2
    
    if teeth_mark == "是":
        syndrome_scores["脾虚湿盛证"] += 3
        syndrome_scores["肾阳虚证"] += 2
    
    if spots == "是":
        syndrome_scores["血瘀证"] += 4
    
    # 汇总评分
    for syndrome, score in color_scores.get(tongue_color, {}).items():
        syndrome_scores[syndrome] += score
    
    for syndrome, score in shape_scores.get(tongue_shape, {}).items():
        syndrome_scores[syndrome] += score
    
    for syndrome, score in coating_color_scores.get(tongue_coating_color, {}).items():
        syndrome_scores[syndrome] += score
    
    for syndrome, score in coating_texture_scores.get(tongue_coating_texture, {}).items():
        syndrome_scores[syndrome] += score
    
    # 根据症状调整
    if symptoms:
        symptom_lower = symptoms.lower()
        if any(kw in symptom_lower for kw in ["口干", "咽干", "燥"]):
            syndrome_scores["阴虚火旺证"] += 2
            syndrome_scores["胃阴不足证"] += 2
        if any(kw in symptom_lower for kw in ["腹胀", "胀满", "纳呆"]):
            syndrome_scores["脾虚湿盛证"] += 2
            syndrome_scores["肝郁气滞证"] += 1
        if any(kw in symptom_lower for kw in ["失眠", "多梦", "心烦"]):
            syndrome_scores["心火上炎证"] += 2
            syndrome_scores["阴虚火旺证"] += 1
    
    # 找出最高分证型
    max_score = max(syndrome_scores.values()) if syndrome_scores else 0
    
    if max_score == 0:
        primary_syndrome = "平和质"
        confidence = 0.6
        pathogenesis = "舌象基本正常，无明显偏颇"
    else:
        # 获取最高分的证型
        primary_syndrome = max(syndrome_scores, key=syndrome_scores.get)
        confidence = min(0.95, 0.5 + (max_score / 20))
    
    # 生成辨证依据
    diagnostic_basis = []
    diagnostic_basis.append({"特征": f"舌色{ tongue_color}", "权重": 3, "贡献": "主要辨证依据"})
    diagnostic_basis.append({"特征": f"舌形{ tongue_shape}", "权重": 2, "贡献": "辅助辨证依据"})
    diagnostic_basis.append({"特征": f"苔色{ tongue_coating_color}", "权重": 2, "贡献": "辅助辨证依据"})
    if crack == "是":
        diagnostic_basis.append({"特征": "裂纹", "权重": 2, "贡献": "阴虚特征"})
    if teeth_mark == "是":
        diagnostic_basis.append({"特征": "齿痕", "权重": 2, "贡献": "脾虚特征"})
    
    # 获取穴位推荐
    acupoints = get_acupoints_for_syndrome(primary_syndrome)
    
    # 生成生活调护建议
    life_advice = generate_life_advice(primary_syndrome)
    
    # 构建结果
    result = {
        "辨证结果": {
            "主要证型": primary_syndrome,
            "证型得分": syndrome_scores.get(primary_syndrome, 0),
            "置信度": round(confidence, 2),
            "病机": get_pathogenesis(primary_syndrome),
            "脏腑定位": get_organ_localization(primary_syndrome),
            "辨证依据": diagnostic_basis if mode == "详细模式" else []
        },
        "针灸方案": {
            "治疗原则": get_treatment_principle(primary_syndrome),
            "主穴": acupoints["主穴"],
            "配穴": acupoints["配穴"],
            "刺法总则": acupoints.get("刺法", "实证用泻法，虚证用补法"),
            "留针时间": "成人20-30分钟，儿童10-15分钟",
            "治疗频次": "急性期每日1次，缓解期隔日1次"
        },
        "生活调护建议": life_advice,
        "系统信息": {
            "知识库版本": "v3.0",
            "技能版本": APP_VERSION,
            "推理规则数量": 50,
            "更新时间": "2026-04-22",
            "免责声明": "本系统仅供辅助参考，不能替代专业医师诊断"
        }
    }
    
    return result


def get_acupoints_for_syndrome(syndrome: str) -> dict:
    """获取证型对应的穴位"""
    
    acupoint_db = {
        "阴虚火旺证": {
            "主穴": [
                {"穴位": "太溪", "经络": "肾经", "功效": "滋阴降火", "定位": "内踝后方", "刺法": "直刺0.5-1寸"},
                {"穴位": "照海", "经络": "肾经", "功效": "滋阴清热", "定位": "内踝下缘", "刺法": "直刺0.3-0.5寸"},
                {"穴位": "三阴交", "经络": "脾经", "功效": "健脾滋阴", "定位": "内踝上3寸", "刺法": "直刺1-1.5寸"}
            ],
            "配穴": [
                {"穴位": "神门", "经络": "心经", "功效": "清心安神"},
                {"穴位": "合谷", "经络": "大肠经", "功效": "清热理气"}
            ]
        },
        "湿热内蕴证": {
            "主穴": [
                {"穴位": "阴陵泉", "经络": "脾经", "功效": "健脾祛湿", "定位": "胫骨内侧", "刺法": "直刺1-2寸"},
                {"穴位": "丰隆", "经络": "胃经", "功效": "化痰祛湿", "定位": "外踝上8寸", "刺法": "直刺1-1.5寸"},
                {"穴位": "内庭", "经络": "胃经", "功效": "清胃泻火", "定位": "足背2-3趾间", "刺法": "直刺0.3-0.5寸"}
            ],
            "配穴": [
                {"穴位": "曲池", "经络": "大肠经", "功效": "清热利湿"},
                {"穴位": "大椎", "经络": "督脉", "功效": "清热解表"}
            ]
        },
        "气血两虚证": {
            "主穴": [
                {"穴位": "足三里", "经络": "胃经", "功效": "补益气血", "定位": "犊鼻下3寸", "刺法": "直刺1-2寸"},
                {"穴位": "气海", "经络": "任脉", "功效": "补气固本", "定位": "脐下1.5寸", "刺法": "直刺1-1.5寸"},
                {"穴位": "血海", "经络": "脾经", "功效": "补血活血", "定位": "髌骨内上2寸", "刺法": "直刺1-1.5寸"}
            ],
            "配穴": [
                {"穴位": "关元", "经络": "任脉", "功效": "补肾固元"},
                {"穴位": "膈俞", "经络": "膀胱经", "功效": "活血补血"}
            ]
        },
        "肝郁气滞证": {
            "主穴": [
                {"穴位": "太冲", "经络": "肝经", "功效": "疏肝理气", "定位": "足背1-2趾间", "刺法": "直刺0.5-1寸"},
                {"穴位": "期门", "经络": "肝经", "功效": "疏肝解郁", "定位": "乳头直下", "刺法": "斜刺0.5-0.8寸"},
                {"穴位": "膻中", "经络": "任脉", "功效": "宽胸理气", "定位": "前正中线", "刺法": "平刺0.3-0.5寸"}
            ],
            "配穴": [
                {"穴位": "内关", "经络": "心包经", "功效": "理气宽胸"},
                {"穴位": "合谷", "经络": "大肠经", "功效": "理气止痛"}
            ]
        },
        "心火上炎证": {
            "主穴": [
                {"穴位": "神门", "经络": "心经", "功效": "清心安神", "定位": "腕横纹", "刺法": "直刺0.3-0.5寸"},
                {"穴位": "少府", "经络": "心经", "功效": "清心泻火", "定位": "握拳小指尖", "刺法": "直刺0.3-0.5寸"},
                {"穴位": "劳宫", "经络": "心包经", "功效": "清心开窍", "定位": "掌心", "刺法": "直刺0.3-0.5寸"}
            ],
            "配穴": [
                {"穴位": "大陵", "经络": "心包经", "功效": "清心泻热"},
                {"穴位": "通里", "经络": "心经", "功效": "宁心安神"}
            ]
        },
        "脾虚湿盛证": {
            "主穴": [
                {"穴位": "足三里", "经络": "胃经", "功效": "健脾祛湿", "定位": "犊鼻下3寸", "刺法": "直刺1-2寸"},
                {"穴位": "阴陵泉", "经络": "脾经", "功效": "健脾利湿", "定位": "胫骨内侧", "刺法": "直刺1-2寸"},
                {"穴位": "中脘", "经络": "任脉", "功效": "健脾化湿", "定位": "脐上4寸", "刺法": "直刺1-1.5寸"}
            ],
            "配穴": [
                {"穴位": "脾俞", "经络": "膀胱经", "功效": "健脾益气"},
                {"穴位": "胃俞", "经络": "膀胱经", "功效": "和胃化湿"}
            ]
        },
        "肾阳虚证": {
            "主穴": [
                {"穴位": "关元", "经络": "任脉", "功效": "温肾壮阳", "定位": "脐下3寸", "刺法": "直刺1-2寸"},
                {"穴位": "肾俞", "经络": "膀胱经", "功效": "补肾益精", "定位": "第2腰椎旁", "刺法": "直刺1-1.5寸"},
                {"穴位": "命门", "经络": "督脉", "功效": "温肾助阳", "定位": "第2腰椎下", "刺法": "直刺1-1.5寸"}
            ],
            "配穴": [
                {"穴位": "太溪", "经络": "肾经", "功效": "滋阴温阳"},
                {"穴位": "气海", "经络": "任脉", "功效": "补气助阳"}
            ]
        },
        "血瘀证": {
            "主穴": [
                {"穴位": "血海", "经络": "脾经", "功效": "活血化瘀", "定位": "髌骨内上2寸", "刺法": "直刺1-1.5寸"},
                {"穴位": "膈俞", "经络": "膀胱经", "功效": "活血通络", "定位": "第7胸椎旁", "刺法": "斜刺0.5-0.8寸"},
                {"穴位": "三阴交", "经络": "脾经", "功效": "活血祛瘀", "定位": "内踝上3寸", "刺法": "直刺1-1.5寸"}
            ],
            "配穴": [
                {"穴位": "合谷", "经络": "大肠经", "功效": "行气活血"},
                {"穴位": "太冲", "经络": "肝经", "功效": "疏肝活血"}
            ]
        },
        "平和质": {
            "主穴": [
                {"穴位": "足三里", "经络": "胃经", "功效": "保健强身", "定位": "犊鼻下3寸", "刺法": "直刺1-2寸"},
                {"穴位": "三阴交", "经络": "脾经", "功效": "调和气血", "定位": "内踝上3寸", "刺法": "直刺1-1.5寸"}
            ],
            "配穴": []
        }
    }
    
    return acupoint_db.get(syndrome, acupoint_db["平和质"])


def get_pathogenesis(syndrome: str) -> str:
    """获取病机描述"""
    pathogenesis_db = {
        "阴虚火旺证": "肝肾阴虚，虚火内扰",
        "湿热内蕴证": "湿热蕴结，脾胃失调",
        "气血两虚证": "气血亏虚，脏腑失养",
        "肝郁气滞证": "肝气郁结，气机不畅",
        "心火上炎证": "心火亢盛，扰乱心神",
        "胃阴不足证": "胃阴亏损，失于濡润",
        "脾虚湿盛证": "脾失健运，湿邪内停",
        "肾阳虚证": "肾阳不足，温煦失职",
        "痰湿内阻证": "痰湿壅盛，阻滞气机",
        "血瘀证": "瘀血内阻，气血不通",
        "寒湿困脾证": "寒湿外侵，困阻脾阳",
        "平和质": "阴阳平衡，气血调和"
    }
    return pathogenesis_db.get(syndrome, "")


def get_organ_localization(syndrome: str) -> list:
    """获取脏腑定位"""
    organ_db = {
        "阴虚火旺证": ["肝", "肾"],
        "湿热内蕴证": ["脾胃"],
        "气血两虚证": ["心", "脾"],
        "肝郁气滞证": ["肝", "胆"],
        "心火上炎证": ["心"],
        "胃阴不足证": ["胃"],
        "脾虚湿盛证": ["脾", "胃"],
        "肾阳虚证": ["肾"],
        "痰湿内阻证": ["脾", "肺"],
        "血瘀证": ["心", "肝"],
        "寒湿困脾证": ["脾", "肾"],
        "平和质": []
    }
    return organ_db.get(syndrome, [])


def get_treatment_principle(syndrome: str) -> str:
    """获取治疗原则"""
    principle_db = {
        "阴虚火旺证": "滋阴清热，养心安神",
        "湿热内蕴证": "清热利湿，健脾化浊",
        "气血两虚证": "补益气血，调理脾胃",
        "肝郁气滞证": "疏肝理气，解郁和中",
        "心火上炎证": "清心泻火，养阴安神",
        "胃阴不足证": "养阴生津，和胃止痛",
        "脾虚湿盛证": "健脾祛湿，化痰利水",
        "肾阳虚证": "温补肾阳，益火之源",
        "痰湿内阻证": "化痰祛湿，理气和中",
        "血瘀证": "活血化瘀，通络止痛",
        "寒湿困脾证": "温中散寒，健脾祛湿",
        "平和质": "平衡阴阳，调和气血"
    }
    return principle_db.get(syndrome, "")


def generate_life_advice(syndrome: str) -> dict:
    """生成生活调护建议"""
    
    advice_db = {
        "阴虚火旺证": {
            "饮食建议": ["宜食银耳、百合、莲子等滋阴食物", "忌食辛辣刺激食物", "多食新鲜蔬果"],
            "生活起居": ["规律作息，避免熬夜", "保持心情舒畅", "适度运动，以柔和运动为主"],
            "注意事项": ["戒烟限酒", "避免过度劳累", "注意口腔卫生"]
        },
        "湿热内蕴证": {
            "饮食建议": ["宜食薏苡仁、冬瓜、绿豆等清热利湿食物", "忌食油腻、甜腻食物", "饮食清淡易消化"],
            "生活起居": ["保持居住环境干燥通风", "适当运动排汗", "避免久坐潮湿之地"],
            "注意事项": ["注意皮肤清洁", "避免潮湿环境", "适度晒太阳"]
        },
        "气血两虚证": {
            "饮食建议": ["宜食红枣、桂圆、山药等补益食物", "适当食用动物肝脏", "少食生冷寒凉"],
            "生活起居": ["保证充足睡眠", "适度休息，避免过度劳累", "注意保暖"],
            "注意事项": ["避免剧烈运动", "保持情绪稳定", "循序渐进增强体质"]
        },
        "肝郁气滞证": {
            "饮食建议": ["宜食疏肝理气食物如陈皮、玫瑰花茶", "忌食胀气食物", "少食辛辣刺激"],
            "生活起居": ["保持心情愉快", "多参加户外活动", "培养兴趣爱好"],
            "注意事项": ["避免情绪激动", "学会情绪管理", "规律作息"]
        },
        "心火上炎证": {
            "饮食建议": ["宜食莲子心、苦瓜、绿茶等清心食物", "忌食辛辣温热", "多饮温水"],
            "生活起居": ["保持充足睡眠", "避免精神紧张", "午间适当休息"],
            "注意事项": ["调节情绪", "避免过度思虑", "适度运动"]
        },
        "平和质": {
            "饮食建议": ["均衡饮食，五味调和", "定时定量", "多食新鲜蔬果"],
            "生活起居": ["规律作息", "适度运动", "保持乐观心态"],
            "注意事项": ["预防为主", "定期体检", "养生保健"]
        }
    }
    
    default_advice = {
        "饮食建议": ["饮食清淡", "营养均衡", "定时定量"],
        "生活起居": ["规律作息", "适度运动", "心态平和"],
        "注意事项": ["遵医嘱", "定期复查", "如有不适及时就医"]
    }
    
    return advice_db.get(syndrome, default_advice)


def validate_features(features: dict) -> dict:
    """验证舌象特征"""
    
    errors = []
    warnings = []
    suggestions = []
    
    # 获取特征值
    tongue_color = features.get("tongue_color", "")
    tongue_shape = features.get("tongue_shape", "")
    tongue_coating_color = features.get("tongue_coating_color", "")
    tongue_coating_texture = features.get("tongue_coating_texture", "")
    crack = features.get("crack", "")
    teeth_mark = features.get("teeth_mark", "")
    spots = features.get("spots", "")
    
    # 验证枚举值
    valid_colors = ["淡红", "淡白", "红", "绛", "紫", "青紫"]
    valid_shapes = ["胖大", "瘦薄", "正常"]
    valid_coating_colors = ["薄白", "白厚", "黄", "灰黑", "剥落"]
    valid_coating_textures = ["薄", "厚", "正常"]
    valid_yn = ["是", "否"]
    
    if tongue_color and tongue_color not in valid_colors:
        errors.append({"field": "tongue_color", "message": f"舌色必须为以下值之一: {', '.join(valid_colors)}", "code": "INVALID_ENUM"})
    
    if tongue_shape and tongue_shape not in valid_shapes:
        errors.append({"field": "tongue_shape", "message": f"舌形必须为以下值之一: {', '.join(valid_shapes)}", "code": "INVALID_ENUM"})
    
    if tongue_coating_color and tongue_coating_color not in valid_coating_colors:
        errors.append({"field": "tongue_coating_color", "message": f"苔色必须为以下值之一: {', '.join(valid_coating_colors)}", "code": "INVALID_ENUM"})
    
    if tongue_coating_texture and tongue_coating_texture not in valid_coating_textures:
        errors.append({"field": "tongue_coating_texture", "message": f"苔质必须为以下值之一: {', '.join(valid_coating_textures)}", "code": "INVALID_ENUM"})
    
    # 逻辑一致性检查
    if tongue_color == "红" and tongue_shape == "胖大":
        warnings.append({"field": "tongue_color+tongue_shape", "message": "红舌通常与瘦薄舌相关，与胖大舌组合较少见，建议核实"})
    
    if tongue_color == "淡白" and tongue_shape == "瘦薄":
        warnings.append({"field": "tongue_color+tongue_shape", "message": "淡白瘦薄舌多见于严重气血两虚，请注意综合辨证"})
    
    if tongue_coating_color == "黄" and tongue_coating_texture == "薄":
        pass  # 黄薄苔是正常或轻微热象
    
    if tongue_coating_color == "薄白" and tongue_coating_texture == "厚":
        warnings.append({"field": "tongue_coating", "message": "薄白苔与厚苔组合存在逻辑矛盾，请核实"})
    
    # 生成建议
    if not tongue_coating_color:
        suggestions.append("建议补充舌苔颜色信息")
    
    if not tongue_shape:
        suggestions.append("建议补充舌形信息")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions
    }


def search_acupoints(syndrome: str, symptom: str = None, organ: str = None, limit: int = 5) -> dict:
    """搜索穴位"""
    
    # 获取证型对应的穴位
    base_acupoints = get_acupoints_for_syndrome(syndrome)
    
    all_acupoints = base_acupoints.get("主穴", []) + base_acupoints.get("配穴", [])
    
    # 根据症状筛选
    if symptom:
        symptom_keywords = {
            "失眠": ["神门", "三阴交", "安眠"],
            "头痛": ["百会", "风池", "太阳"],
            "胃痛": ["中脘", "足三里", "内关"],
            "便秘": ["天枢", "大肠俞", "支沟"],
            "咳嗽": ["肺俞", "列缺", "天突"]
        }
        for key, acupoints in symptom_keywords.items():
            if key in symptom:
                for ac in acupoints:
                    if ac not in [a["穴位"] for a in all_acupoints]:
                        all_acupoints.append({"穴位": ac, "经络": "", "功效": "对症治疗"})
    
    # 根据脏腑筛选
    if organ:
        organ_keywords = {
            "心": ["神门", "少府", "通里"],
            "肝": ["太冲", "期门", "肝俞"],
            "脾": ["足三里", "阴陵泉", "脾俞"],
            "胃": ["中脘", "内关", "梁丘"],
            "肺": ["列缺", "尺泽", "肺俞"],
            "肾": ["太溪", "肾俞", "命门"]
        }
        if organ in organ_keywords:
            for ac in organ_keywords[organ]:
                if ac not in [a["穴位"] for a in all_acupoints]:
                    all_acupoints.append({"穴位": ac, "经络": "", "功效": "对应脏腑"})
    
    return {
        "证型": syndrome,
        "穴位总数": len(all_acupoints),
        "穴位列表": all_acupoints[:limit]
    }


# ============================================================
# 服务器启动
# ============================================================

async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
