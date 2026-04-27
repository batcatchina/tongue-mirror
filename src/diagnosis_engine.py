# -*- coding: utf-8 -*-
"""
舌镜诊断引擎（含正和积分支付）

玄镜团队 · 舌诊辨证与积分经济整合
"""

import logging
from decimal import Decimal
from typing import Optional, Any
from zhenghe_client import ZhengheClient, ZhengheError, get_zhenghe_client
from server import perform_tongue_analysis

logger = logging.getLogger(__name__)

# 舌诊服务定价（USDT）
TONGUE_SERVICE_PRICING = {
    "快速模式": Decimal("0.50"),   # 快速舌诊：单次辨证+主穴
    "详细模式": Decimal("1.00"),   # 详细舌诊：完整辨证+选穴+调护
}


class TongueDiagnosisEngine:
    """
    舌诊诊断引擎（含积分支付）
    
    整合舌诊辨证逻辑与正和积分支付
    """
    
    def __init__(
        self,
        zhenghe_client: Optional[ZhengheClient] = None,
        tongue_agent_id: Optional[str] = None,
        payment_enabled: bool = True,
        fallback_to_free: bool = True
    ):
        """
        初始化诊断引擎
        
        参数：
            zhenghe_client: 正和客户端实例
            tongue_agent_id: 舌镜Agent ID（正和系统注册）
            payment_enabled: 是否启用积分支付
            fallback_to_free: 支付失败时是否降级为免费
        """
        self.zh_client = zhenghe_client or get_zhenghe_client()
        self.tongue_agent_id = tongue_agent_id or _get_tongue_agent_id()
        self.payment_enabled = payment_enabled
        self.fallback_to_free = fallback_to_free
    
    def get_pricing(self, mode: str = "详细模式") -> Decimal:
        """获取服务定价"""
        return TONGUE_SERVICE_PRICING.get(mode, Decimal("1.00"))
    
    async def diagnose_with_payment(
        self,
        user_account_id: str,
        session_id: str,
        tongue_params: dict,
        require_payment: Optional[bool] = None,
        referrer_account_id: Optional[str] = None
    ) -> dict:
        """
        带积分支付的舌诊服务
        
        流程：
        1. 确定是否需要支付
        2. 预检查余额（如需支付）
        3. 执行舌诊辨证
        4. 燃烧积分
        5. 返回结果
        
        参数：
            user_account_id: 用户账户ID
            session_id: 会话ID（用于生成幂等reference_id）
            tongue_params: 舌诊参数字典
            require_payment: 是否强制要求支付（None=使用默认配置）
            referrer_account_id: 推荐人账户ID（可选）
        
        返回：
            dict: 诊断+支付结果
        """
        mode = tongue_params.get("mode", "详细模式")
        pricing = self.get_pricing(mode)
        use_payment = require_payment if require_payment is not None else self.payment_enabled
        
        # 生成唯一参考号
        reference_id = self.zh_client._generate_reference_id(
            user_id=user_account_id,
            session_id=session_id,
            service_type=f"tongue_{mode}"
        )
        
        payment_result = None
        payment_error = None
        
        if use_payment and pricing > 0:
            # === 付费模式 ===
            
            # 1. 预检查余额
            try:
                balance_check = await self.zh_client.check_balance(
                    account_id=user_account_id,
                    required_usdt=pricing
                )
                
                if not balance_check.get("sufficient"):
                    return {
                        "success": False,
                        "error": "INSUFFICIENT_BALANCE",
                        "message": f"积分余额不足。当前余额: {balance_check.get('balance_usdt', '0')} USDT",
                        "required": f"{str(pricing)} USDT",
                        "balance_info": balance_check,
                        "payment_required": True
                    }
            except ZhengheError as e:
                logger.warning(f"余额检查失败: {e}")
                if not self.fallback_to_free:
                    return {
                        "success": False,
                        "error": "BALANCE_CHECK_FAILED",
                        "message": f"余额查询失败: {str(e)}",
                        "payment_required": True
                    }
                # 降级为免费模式
                logger.info("支付失败，降级为免费模式")
                use_payment = False
            except Exception as e:
                logger.warning(f"余额检查异常: {e}")
                if not self.fallback_to_free:
                    return {
                        "success": False,
                        "error": "BALANCE_CHECK_FAILED",
                        "message": f"余额查询异常: {str(e)}",
                        "payment_required": True
                    }
                logger.info("支付失败，降级为免费模式")
                use_payment = False
        
        # 2. 执行舌诊（先诊断后扣费，保证服务可用）
        diagnosis_result = self._perform_diagnosis(tongue_params)
        
        # 3. 燃烧积分（如需支付）
        if use_payment and pricing > 0:
            try:
                payment_result = await self.zh_client.consume(
                    consumer_account_id=user_account_id,
                    provider_agent_id=self.tongue_agent_id,
                    pricing_usdt=pricing,
                    reference_id=reference_id,
                    service_type=f"tongue_{mode}",
                    referrer_account_id=referrer_account_id
                )
            except ZhengheError as e:
                payment_error = str(e)
                logger.error(f"积分燃烧失败: {e}")
                
                # 舌诊已完成但支付失败
                return {
                    "success": True,
                    "partial": True,
                    "diagnosis": diagnosis_result,
                    "payment": {
                        "pricing_usdt": str(pricing),
                        "reference_id": reference_id,
                        "status": "failed",
                        "error": payment_error
                    },
                    "message": "舌诊已完成，积分扣费失败，请联系客服处理"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": "PAYMENT_ERROR",
                    "message": f"支付异常: {str(e)}",
                    "payment_required": True
                }
        
        return {
            "success": True,
            "payment_required": use_payment,
            "diagnosis": diagnosis_result,
            "payment": {
                "pricing_usdt": str(pricing),
                "reference_id": reference_id,
                "tx_id": payment_result.get("tx_id") if payment_result else None,
                "burned_tokens": payment_result.get("burned_tokens") if payment_result else None,
                "status": "completed" if payment_result else "free"
            }
        }
    
    async def diagnose_free(
        self,
        tongue_params: dict
    ) -> dict:
        """
        免费舌诊（不涉及积分）
        
        参数：
            tongue_params: 舌诊参数字典
        
        返回：
            dict: 诊断结果
        """
        diagnosis_result = self._perform_diagnosis(tongue_params)
        
        return {
            "success": True,
            "payment_required": False,
            "diagnosis": diagnosis_result,
            "payment": {
                "status": "free",
                "message": "免费模式"
            }
        }
    
    def _perform_diagnosis(self, params: dict) -> dict:
        """
        执行舌诊辨证
        
        参数：
            params: 舌诊参数字典
        
        返回：
            dict: 辨证结果
        """
        return perform_tongue_analysis(
            tongue_color=params.get("tongue_color"),
            tongue_shape=params.get("tongue_shape"),
            tongue_coating_color=params.get("tongue_coating_color"),
            tongue_coating_texture=params.get("tongue_coating_texture"),
            patient_age=params.get("patient_age"),
            patient_gender=params.get("patient_gender"),
            chief_complaint=params.get("chief_complaint"),
            symptoms=params.get("symptoms", ""),
            tongue_texture=params.get("tongue_texture", "正常"),
            tongue_movement=params.get("tongue_movement", "正常"),
            coating_moisture=params.get("coating_moisture"),
            coating_greasy=params.get("coating_greasy"),
            crack=params.get("crack", "否"),
            teeth_mark=params.get("teeth_mark", "否"),
            spots=params.get("spots", "否"),
            mode=params.get("mode", "详细模式"),
            language=params.get("language", "中文")
        )


def _get_tongue_agent_id() -> str:
    """从环境变量获取舌镜Agent ID"""
    import os
    return os.getenv("TONGUE_AGENT_ID", "agent_tongue_default")


# 全局引擎实例（延迟初始化）
_engine_instance: Optional[TongueDiagnosisEngine] = None


def get_diagnosis_engine() -> TongueDiagnosisEngine:
    """获取全局诊断引擎实例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TongueDiagnosisEngine()
    return _engine_instance


def init_diagnosis_engine(
    zhenghe_client: Optional[ZhengheClient] = None,
    tongue_agent_id: Optional[str] = None,
    payment_enabled: bool = True,
    fallback_to_free: bool = True
) -> TongueDiagnosisEngine:
    """初始化全局诊断引擎"""
    global _engine_instance
    _engine_instance = TongueDiagnosisEngine(
        zhenghe_client=zhenghe_client,
        tongue_agent_id=tongue_agent_id,
        payment_enabled=payment_enabled,
        fallback_to_free=fallback_to_free
    )
    return _engine_instance
