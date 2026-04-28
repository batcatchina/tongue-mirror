# -*- coding: utf-8 -*-
"""
舌镜 MCP Server - Vercel HTTP入口
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import os
from decimal import Decimal

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# 舌诊辨证核心逻辑
# ============================================================

# 证型判定规则
DIAGNOSIS_RULES = {
    "湿热内蕴证": {
        "conditions": ["红舌", "黄苔", "腻苔"],
        "weight": 15,
        "脏腑": ["脾胃", "肝胆"],
        "治则": "清热利湿，健脾和胃",
        "主穴": ["中脘", "丰隆", "阴陵泉"],
        "配穴": ["内庭", "足三里"]
    },
    "气血两虚证": {
        "conditions": ["淡白舌", "薄苔", "胖大舌", "齿痕"],
        "weight": 14,
        "脏腑": ["心脾"],
        "治则": "益气养血，健脾宁心",
        "主穴": ["足三里", "三阴交", "膈俞"],
        "配穴": ["脾俞", "心俞"]
    },
    "阴虚火旺证": {
        "conditions": ["红舌", "少苔", "剥落苔", "瘦薄舌"],
        "weight": 13,
        "脏腑": ["肝肾"],
        "治则": "滋阴降火，清热安神",
        "主穴": ["太溪", "三阴交", "神门"],
        "配穴": ["肾俞", "肝俞"]
    },
    "血瘀证": {
        "conditions": ["紫舌", "青紫舌", "瘀斑"],
        "weight": 12,
        "脏腑": ["心肝"],
        "治则": "活血化瘀，通络止痛",
        "主穴": ["膈俞", "血海", "三阴交"],
        "配穴": ["合谷", "太冲"]
    },
    "脾虚湿盛证": {
        "conditions": ["淡白舌", "白厚苔", "腻苔", "齿痕", "胖大舌"],
        "weight": 14,
        "脏腑": ["脾胃"],
        "治则": "健脾益气，化湿利水",
        "主穴": ["脾俞", "阴陵泉", "足三里"],
        "配穴": ["中脘", "丰隆"]
    }
}

# 分区辨证规则 - 舌尖/舌边/舌中/舌根对应脏腑
ZONE_DIAGNOSIS = {
    "舌尖": {
        "脏腑": ["心", "肺"],
        "凹陷": {"证型": "心气不足", "治则": "补心气", "主穴": ["内关", "膻中"], "配穴": ["神门"]},
        "鼓胀": {"证型": "心火亢盛", "治则": "清心火", "主穴": ["少海", "神门"], "配穴": ["通里"]}
    },
    "舌边": {
        "脏腑": ["肝", "胆"],
        "凹陷": {"证型": "肝血不足", "治则": "养肝血", "主穴": ["肝俞", "太冲"], "配穴": ["三阴交"]},
        "鼓胀": {"证型": "肝气郁结", "治则": "疏肝理气", "主穴": ["太冲", "期门"], "配穴": ["阳陵泉"]}
    },
    "舌中": {
        "脏腑": ["脾", "胃"],
        "凹陷": {"证型": "脾气虚弱", "治则": "健脾益气", "主穴": ["脾俞", "胃俞"], "配穴": ["足三里"]},
        "鼓胀": {"证型": "脾胃气滞", "治则": "理气和胃", "主穴": ["中脘", "足三里"], "配穴": ["内关"]}
    },
    "舌根": {
        "脏腑": ["肾", "膀胱"],
        "凹陷": {"证型": "肾气不固", "治则": "补肾固本", "主穴": ["关元", "命门"], "配穴": ["肾俞"]},
        "鼓胀": {"证型": "下焦湿热", "治则": "清利湿热", "主穴": ["委中", "阴陵泉"], "配穴": ["膀胱俞"]}
    }
}

def analyze_tongue(
    tongue_color: str,
    tongue_shape: str,
    tongue_coating_color: str,
    tongue_coating_texture: str,
    patient_age: int,
    patient_gender: str,
    chief_complaint: str,
    shape_distribution: dict = None,  # 凹凸形态 {depression: [], bulge: []}
    distribution_features: list = None,  # 舌色分布特征
    **kwargs
) -> dict:
    """执行舌诊辨证分析"""
    
    # 构建特征列表
    features = []
    
    # 舌色
    color_map = {"淡红": "淡红舌", "淡白": "淡白舌", "红": "红舌", "绛": "绛舌", "紫": "紫舌", "青紫": "青紫舌"}
    features.append(color_map.get(tongue_color, tongue_color))
    
    # 苔色
    coating_map = {"薄白": "薄苔", "白厚": "白厚苔", "黄": "黄苔", "灰黑": "灰黑苔", "剥落": "剥落苔"}
    features.append(coating_map.get(tongue_coating_color, tongue_coating_color))
    
    # 苔质
    texture_map = {"薄": "薄苔", "厚": "厚苔", "正常": "薄苔"}
    features.append(texture_map.get(tongue_coating_texture, tongue_coating_texture))
    
    # 舌形
    shape_map = {"胖大": "胖大舌", "瘦薄": "瘦薄舌", "正常": ""}
    if shape_map.get(tongue_shape):
        features.append(shape_map[tongue_shape])
    
    # 齿痕
    if kwargs.get("tooth_marks") == "是":
        features.append("齿痕")
    
    # 裂纹
    if kwargs.get("cracks") == "是":
        features.append("裂纹")
    
    # 瘀斑
    if kwargs.get("stasis_spots") == "是":
        features.append("瘀斑")
    
    # 证型判定
    syndrome_scores = {}
    for syndrome, rule in DIAGNOSIS_RULES.items():
        score = 0
        matched = []
        for condition in rule["conditions"]:
            if condition in features:
                score += rule["weight"]
                matched.append(condition)
        if score > 0:
            syndrome_scores[syndrome] = {"score": score, "matched": matched}
    
    # 排序取最高分
    sorted_syndromes = sorted(syndrome_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    if sorted_syndromes:
        primary_syndrome = sorted_syndromes[0][0]
        rule = DIAGNOSIS_RULES[primary_syndrome]
    else:
        primary_syndrome = "脾虚湿盛证"  # 默认
        rule = DIAGNOSIS_RULES[primary_syndrome]
    
    # 分区凹凸分析 - 核心功能
    zone_analysis = {}
    zone_acupoints = []  # 分区对应的穴位
    zone_syndromes = []  # 分区对应的证型
    
    # 区域映射
    part_map = {"tip": "舌尖", "middle": "舌中", "sides": "舌边", "root": "舌根"}
    
    if shape_distribution:
        # 处理凹陷
        for part_key in shape_distribution.get("depression", []):
            part_name = part_map.get(part_key, part_key)
            if part_name in ZONE_DIAGNOSIS:
                zone_rule = ZONE_DIAGNOSIS[part_name]
                zone_info = zone_rule.get("凹陷", {})
                zone_analysis[part_name] = {
                    "状态": "凹陷",
                    "脏腑": zone_rule["脏腑"],
                    "辨证": zone_info.get("证型", ""),
                    "治则": zone_info.get("治则", ""),
                    "主穴": zone_info.get("主穴", []),
                    "配穴": zone_info.get("配穴", [])
                }
                zone_acupoints.extend(zone_info.get("主穴", []))
                zone_syndromes.append(zone_info.get("证型", ""))
        
        # 处理鼓胀
        for part_key in shape_distribution.get("bulge", []):
            part_name = part_map.get(part_key, part_key)
            if part_name in ZONE_DIAGNOSIS:
                zone_rule = ZONE_DIAGNOSIS[part_name]
                zone_info = zone_rule.get("鼓胀", {})
                zone_analysis[part_name] = {
                    "状态": "鼓胀",
                    "脏腑": zone_rule["脏腑"],
                    "辨证": zone_info.get("证型", ""),
                    "治则": zone_info.get("治则", ""),
                    "主穴": zone_info.get("主穴", []),
                    "配穴": zone_info.get("配穴", [])
                }
                zone_acupoints.extend(zone_info.get("主穴", []))
                zone_syndromes.append(zone_info.get("证型", ""))
    
    # 根据凹凸分析补充辨证
    if zone_syndromes:
        # 将分区证型加入辨证依据
        primary_syndrome = f"{primary_syndrome}，兼{zone_syndromes[0]}" if len(zone_syndromes) == 1 else f"{primary_syndrome}，兼{zone_syndromes[0]}、{zone_syndromes[1]}"
    
    # 合并穴位方案
    all_main_acupoints = list(set(rule["主穴"] + zone_acupoints))
    
    return {
        "辨证结果": {
            "主要证型": primary_syndrome,
            "证型得分": syndrome_scores.get(sorted_syndromes[0][0] if sorted_syndromes else "脾虚湿盛证", {}).get("score", 10),
            "置信度": 0.85 if zone_analysis else 0.75,
            "病机": f"{primary_syndrome}，{rule['治则']}"
        },
        "分区凹凸分析": zone_analysis,  # 核心功能：显示每个区域的凹凸状态和对应辨证
        "脏腑定位": rule["脏腑"] + list(set([z["脏腑"][0] for z in zone_analysis.values()] if zone_analysis else [])),
        "针灸方案": {
            "治疗原则": rule["治则"],
            "主穴": [{"穴位": x, "功效": ""} for x in all_main_acupoints[:5]],
            "配穴": [{"穴位": x, "功效": ""} for x in rule["配穴"]]
        },
        "辨证依据": [{"特征": f, "权重": 5, "贡献": "主证"} for f in features],
        "调护建议": [
            "饮食清淡，少食辛辣油腻",
            "保持规律作息，避免熬夜",
            "适当运动，促进气血运行"
        ]
    }


def validate_features(features: dict) -> dict:
    """验证舌象特征"""
    valid_colors = ["淡红", "淡白", "红", "绛", "紫", "青紫"]
    valid_shapes = ["胖大", "瘦薄", "正常"]
    valid_coating_colors = ["薄白", "白厚", "黄", "灰黑", "剥落"]
    valid_textures = ["薄", "厚", "正常"]
    
    errors = []
    
    if features.get("tongue_color") not in valid_colors:
        errors.append(f"舌色无效: {features.get('tongue_color')}")
    
    if features.get("tongue_shape") not in valid_shapes:
        errors.append(f"舌形无效: {features.get('tongue_shape')}")
    
    if features.get("tongue_coating_color") not in valid_coating_colors:
        errors.append(f"苔色无效: {features.get('tongue_coating_color')}")
    
    if features.get("tongue_coating_texture") not in valid_textures:
        errors.append(f"苔质无效: {features.get('tongue_coating_texture')}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors if errors else None,
        "message": "特征验证通过" if not errors else "存在无效特征"
    }


# ============================================================
# FastAPI App
# ============================================================

def create_app() -> FastAPI:
    app = FastAPI(
        title="舌镜 MCP Server",
        description="中医舌诊辨证智能体",
        version="2.0.0",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"name": "舌镜 MCP Server", "version": "2.0.0", "status": "running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """MCP JSON-RPC 2.0 端点"""
        try:
            body = await request.json()
            method = body.get("method", "")
            params = body.get("params", {})
            request_id = body.get("id", 1)
            
            if method == "tools/list":
                tools = [
                    {"name": "analyze_tongue", "description": "执行舌诊辨证分析"},
                    {"name": "validate_tongue_features", "description": "验证舌象特征有效性"},
                    {"name": "query_acupoints", "description": "根据证型查询穴位"}
                ]
                return {
                    "jsonrpc": "2.0",
                    "result": {"tools": tools},
                    "id": request_id
                }
            
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                if tool_name == "analyze_tongue":
                    result = analyze_tongue(**arguments)
                    return {
                        "jsonrpc": "2.0",
                        "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]},
                        "id": request_id
                    }
                
                elif tool_name == "validate_tongue_features":
                    result = validate_features(arguments)
                    return {
                        "jsonrpc": "2.0",
                        "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]},
                        "id": request_id
                    }
                
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"工具不存在: {tool_name}"},
                        "id": request_id
                    }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"方法不存在: {method}"},
                    "id": request_id
                }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": 1
            }
    
    return app


# Vercel入口
app = create_app()
handler = app
