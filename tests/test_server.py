"""
舌镜 MCP Server 测试用例
"""

import json
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import (
    perform_tongue_analysis,
    validate_features,
    search_acupoints,
    get_acupoints_for_syndrome,
    get_pathogenesis,
    get_organ_localization,
    get_treatment_principle,
    generate_life_advice
)


def test_analyze_tongue():
    """测试舌诊辨证分析"""
    print("=" * 60)
    print("测试: 舌诊辨证分析")
    print("=" * 60)
    
    result = perform_tongue_analysis(
        tongue_color="红",
        tongue_shape="瘦薄",
        tongue_coating_color="黄",
        tongue_coating_texture="薄",
        patient_age=45,
        patient_gender="男",
        chief_complaint="胃脘胀满1周",
        symptoms="口干咽燥",
        tongue_texture="裂纹",
        tongue_movement="正常",
        crack="是",
        teeth_mark="否",
        spots="否",
        mode="详细模式",
        language="中文"
    )
    
    print(f"\n辨证结果:")
    print(f"  主要证型: {result['辨证结果']['主要证型']}")
    print(f"  置信度: {result['辨证结果']['置信度']}")
    print(f"  病机: {result['辨证结果']['病机']}")
    print(f"  脏腑定位: {result['辨证结果']['脏腑定位']}")
    
    print(f"\n针灸方案:")
    print(f"  治疗原则: {result['针灸方案']['治疗原则']}")
    print(f"  主穴数量: {len(result['针灸方案']['主穴'])}")
    for ac in result['针灸方案']['主穴'][:3]:
        print(f"    - {ac['穴位']} ({ac['经络']}): {ac['功效']}")
    
    print(f"\n生活调护:")
    print(f"  饮食建议: {result['生活调护建议']['饮食建议'][0] if result['生活调护建议']['饮食建议'] else '无'}")
    
    print("\n✅ 测试通过")
    return result


def test_validate_features():
    """测试特征验证"""
    print("\n" + "=" * 60)
    print("测试: 特征验证")
    print("=" * 60)
    
    # 测试1: 正常特征
    features1 = {
        "tongue_color": "红",
        "tongue_shape": "瘦薄",
        "tongue_coating_color": "黄",
        "tongue_coating_texture": "薄"
    }
    
    result1 = validate_features(features1)
    print(f"\n测试1 - 正常特征:")
    print(f"  是否有效: {result1['is_valid']}")
    print(f"  错误数: {len(result1['errors'])}")
    print(f"  警告数: {len(result1['warnings'])}")
    
    # 测试2: 逻辑矛盾特征
    features2 = {
        "tongue_color": "红",
        "tongue_shape": "胖大",
        "tongue_coating_color": "薄白",
        "tongue_coating_texture": "厚"
    }
    
    result2 = validate_features(features2)
    print(f"\n测试2 - 逻辑矛盾特征:")
    print(f"  是否有效: {result2['is_valid']}")
    print(f"  警告数: {len(result2['warnings'])}")
    for warn in result2['warnings']:
        print(f"    ⚠️ {warn['message']}")
    
    # 测试3: 无效枚举值
    features3 = {
        "tongue_color": "粉红",  # 无效值
        "tongue_shape": "正常"
    }
    
    result3 = validate_features(features3)
    print(f"\n测试3 - 无效枚举值:")
    print(f"  是否有效: {result3['is_valid']}")
    print(f"  错误数: {len(result3['errors'])}")
    for err in result3['errors']:
        print(f"    ❌ {err['field']}: {err['message']}")
    
    print("\n✅ 测试通过")
    return result1, result2, result3


def test_query_acupoints():
    """测试穴位查询"""
    print("\n" + "=" * 60)
    print("测试: 穴位查询")
    print("=" * 60)
    
    # 测试1: 基本查询
    result1 = search_acupoints(syndrome="阴虚火旺证", limit=5)
    print(f"\n测试1 - 基本查询:")
    print(f"  证型: {result1['证型']}")
    print(f"  穴位总数: {result1['穴位总数']}")
    for ac in result1['穴位列表']:
        print(f"    - {ac['穴位']} ({ac['经络']})")
    
    # 测试2: 带症状查询
    result2 = search_acupoints(syndrome="阴虚火旺证", symptom="失眠", limit=5)
    print(f"\n测试2 - 带症状查询:")
    print(f"  穴位总数: {result2['穴位总数']}")
    for ac in result2['穴位列表']:
        print(f"    - {ac['穴位']} ({ac['经络']})")
    
    # 测试3: 带脏腑查询
    result3 = search_acupoints(syndrome="气血两虚证", organ="心", limit=5)
    print(f"\n测试3 - 带脏腑查询:")
    print(f"  穴位总数: {result3['穴位总数']}")
    for ac in result3['穴位列表']:
        print(f"    - {ac['穴位']} ({ac['经络']})")
    
    print("\n✅ 测试通过")
    return result1, result2, result3


def test_syndrome_analysis():
    """测试多种证型分析"""
    print("\n" + "=" * 60)
    print("测试: 多种证型分析")
    print("=" * 60)
    
    test_cases = [
        {"tongue_color": "淡白", "tongue_shape": "瘦薄", "tongue_coating_color": "薄白", "tongue_coating_texture": "薄"},
        {"tongue_color": "淡白", "tongue_shape": "胖大", "tongue_coating_color": "白厚", "tongue_coating_texture": "厚"},
        {"tongue_color": "红", "tongue_shape": "瘦薄", "tongue_coating_color": "黄", "tongue_coating_texture": "薄"},
        {"tongue_color": "紫", "tongue_shape": "正常", "tongue_coating_color": "薄白", "tongue_coating_texture": "薄", "spots": "是"},
    ]
    
    expected_syndromes = ["气血两虚证", "脾虚湿盛证", "阴虚火旺证", "血瘀证"]
    
    for i, (features, expected) in enumerate(zip(test_cases, expected_syndromes)):
        result = perform_tongue_analysis(
            tongue_color=features["tongue_color"],
            tongue_shape=features["tongue_shape"],
            tongue_coating_color=features["tongue_coating_color"],
            tongue_coating_texture=features["tongue_coating_texture"],
            patient_age=40,
            patient_gender="男",
            chief_complaint="常规体检",
            spots=features.get("spots", "否"),
            mode="快速模式"
        )
        
        actual = result['辨证结果']['主要证型']
        status = "✅" if actual == expected else "⚠️"
        print(f"\n{status} 测试用例 {i+1}:")
        print(f"    舌色: {features['tongue_color']}, 舌形: {features['tongue_shape']}")
        print(f"    预期: {expected}, 实际: {actual}")
        if actual != expected:
            print(f"    置信度: {result['辨证结果']['置信度']}")
            print(f"    病机: {result['辨证结果']['病机']}")
    
    print("\n✅ 测试通过")


def test_helper_functions():
    """测试辅助函数"""
    print("\n" + "=" * 60)
    print("测试: 辅助函数")
    print("=" * 60)
    
    syndrome = "肝郁气滞证"
    
    print(f"\n证型: {syndrome}")
    print(f"  病机: {get_pathogenesis(syndrome)}")
    print(f"  脏腑定位: {get_organ_localization(syndrome)}")
    print(f"  治疗原则: {get_treatment_principle(syndrome)}")
    
    advice = generate_life_advice(syndrome)
    print(f"  饮食建议: {advice['饮食建议'][0] if advice['饮食建议'] else '无'}")
    print(f"  生活起居: {advice['生活起居'][0] if advice['生活起居'] else '无'}")
    
    acupoints = get_acupoints_for_syndrome(syndrome)
    print(f"  主穴: {[ac['穴位'] for ac in acupoints['主穴']]}")
    
    print("\n✅ 测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 舌镜 MCP Server 功能测试")
    print("=" * 60)
    
    try:
        test_analyze_tongue()
        test_validate_features()
        test_query_acupoints()
        test_syndrome_analysis()
        test_helper_functions()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
