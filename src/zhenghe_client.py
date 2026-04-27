# -*- coding: utf-8 -*-
"""
舌镜-正和积分客户端

玄镜团队 · 提供舌诊服务与正和积分系统的交互能力
"""

import os
import uuid
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
import httpx


class ZhengheError(Exception):
    """正和系统异常"""
    
    def __init__(self, error: dict):
        self.code = error.get("code", -1)
        self.message = error.get("message", "Unknown error")
        super().__init__(f"[{self.code}] {self.message}")
    
    def __str__(self):
        return f"ZhengheError: [{self.code}] {self.message}"


class ZhengheClient:
    """
    正和系统积分客户端
    
    用于舌镜MCP Server调用正和MCP的积分服务
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        初始化正和客户端
        
        参数：
            api_key: 正和API密钥，默认从环境变量 ZHENGHE_API_KEY 获取
            base_url: 正和MCP服务地址，默认从环境变量 ZHENGHE_MCP_URL 获取
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or os.getenv("ZHENGHE_API_KEY", "")
        self.base_url = base_url or os.getenv(
            "ZHENGHE_MCP_URL", 
            "http://localhost:8000/mcp"
        )
        self.timeout = timeout
    
    def _generate_reference_id(
        self,
        user_id: str,
        session_id: str,
        service_type: str = "tongue"
    ) -> str:
        """
        生成幂等参考号
        
        格式：ref_{service}_{user}_{timestamp}_{hash}
        示例：ref_tongue_acc_123_1714320000_a1b2c3d4
        
        参数：
            user_id: 用户账户ID
            session_id: 会话ID
            service_type: 服务类型标识
        
        返回：
            str: 唯一参考号
        """
        timestamp = int(datetime.now().timestamp())
        raw = f"{user_id}_{session_id}_{timestamp}_{service_type}"
        hash_suffix = hashlib.md5(raw.encode()).hexdigest()[:8]
        return f"ref_tongue_{user_id}_{timestamp}_{hash_suffix}"
    
    async def _call_mcp(self, method: str, params: dict) -> dict:
        """
        调用MCP端点
        
        参数：
            method: MCP方法名
            params: 参数字典
        
        返回：
            dict: 解析后的结果
        
        异常：
            ZhengheError: 调用失败时抛出
        """
        if not self.api_key:
            raise ZhengheError({
                "code": -32000,
                "message": "API key not configured. Set ZHENGHE_API_KEY environment variable."
            })
        
        request_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": method,
                        "params": params
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if "error" in result:
                    raise ZhengheError(result["error"])
                
                return result.get("result", {})
                
            except httpx.TimeoutException:
                raise ZhengheError({
                    "code": -32003,
                    "message": "Request timeout"
                })
            except httpx.HTTPStatusError as e:
                raise ZhengheError({
                    "code": e.response.status_code,
                    "message": f"HTTP error: {e.response.status_code}"
                })
            except Exception as e:
                raise ZhengheError({
                    "code": -32001,
                    "message": f"Request failed: {str(e)}"
                })
    
    async def get_balance(self, account_id: str) -> dict:
        """
        查询账户余额
        
        参数：
            account_id: 账户ID
        
        返回：
            dict: 余额信息
                - balance: 积分余额
                - price: 当前价格
                - value_usdt: USDT价值
        """
        result = await self._call_mcp("tools/call", {
            "name": "get_balance",
            "arguments": {"account_id": account_id}
        })
        
        # 解析结果内容
        content = result.get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "{}")
            try:
                return {"raw": result, "parsed": eval(text)}
            except:
                return {"raw": result}
        return result
    
    async def check_balance(
        self, 
        account_id: str, 
        required_tokens: Optional[Decimal] = None,
        required_usdt: Optional[Decimal] = None
    ) -> dict:
        """
        检查余额是否充足
        
        参数：
            account_id: 账户ID
            required_tokens: 所需积分数量（精确）
            required_usdt: 所需USDT价值（估算）
        
        返回：
            dict: 检查结果
                - sufficient: 是否充足
                - balance: 当前余额
                - required: 所需金额
        """
        balance_info = await self.get_balance(account_id)
        parsed = balance_info.get("parsed", {})
        
        current_balance = Decimal(str(parsed.get("balance", "0")))
        current_price = Decimal(str(parsed.get("price", "1")))
        
        # 估算所需积分
        if required_usdt and required_tokens is None:
            required_tokens = required_usdt / current_price
        
        return {
            "sufficient": required_tokens is None or current_balance >= required_tokens,
            "balance": str(current_balance),
            "balance_usdt": str(current_balance * current_price),
            "required": str(required_tokens) if required_tokens else None,
            "price": str(current_price)
        }
    
    async def consume(
        self,
        consumer_account_id: str,
        provider_agent_id: str,
        pricing_usdt: Decimal,
        reference_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        service_type: str = "tongue_diagnosis",
        referrer_account_id: Optional[str] = None
    ) -> dict:
        """
        消费服务并燃烧积分
        
        参数：
            consumer_account_id: 消费者账户ID
            provider_agent_id: 服务提供者Agent ID（舌镜Agent）
            pricing_usdt: 服务定价（USDT）
            reference_id: 幂等参考号（可选，不提供则自动生成）
            user_id: 用户ID（用于生成reference_id）
            session_id: 会话ID（用于生成reference_id）
            service_type: 服务类型
            referrer_account_id: 推荐人账户ID（可选）
        
        返回：
            dict: 消费结果
                - tx_id: 交易ID
                - burned_tokens: 燃烧的积分数量
                - pricing_usdt: 服务定价
                - status: 状态
        """
        # 自动生成幂等参考号
        if not reference_id:
            if not user_id or not session_id:
                raise ZhengheError({
                    "code": -32002,
                    "message": "reference_id or (user_id + session_id) required"
                })
            reference_id = self._generate_reference_id(
                user_id=user_id,
                session_id=session_id,
                service_type=service_type
            )
        
        params = {
            "consumer_account_id": consumer_account_id,
            "provider_agent_id": provider_agent_id,
            "pricing_usdt": str(pricing_usdt),
            "reference_id": reference_id
        }
        
        if referrer_account_id:
            params["referrer_account_id"] = referrer_account_id
        
        result = await self._call_mcp("tools/call", {
            "name": "consume",
            "arguments": params
        })
        
        # 解析结果内容
        content = result.get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "{}")
            try:
                parsed_result = eval(text)
                return {
                    "raw": result,
                    "tx_id": parsed_result.get("tx_id"),
                    "burned_tokens": parsed_result.get("burned_tokens"),
                    "pricing_usdt": str(pricing_usdt),
                    "reference_id": reference_id,
                    "status": "completed"
                }
            except:
                return {
                    "raw": result,
                    "reference_id": reference_id,
                    "status": "unknown"
                }
        
        return {"raw": result, "status": "unknown"}


# 全局客户端实例（延迟初始化）
_client_instance: Optional[ZhengheClient] = None


def get_zhenghe_client() -> ZhengheClient:
    """获取全局正和客户端实例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = ZhengheClient()
    return _client_instance


def init_zhenghe_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> ZhengheClient:
    """初始化全局正和客户端"""
    global _client_instance
    _client_instance = ZhengheClient(api_key=api_key, base_url=base_url)
    return _client_instance
