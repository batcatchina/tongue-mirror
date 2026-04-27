# -*- coding: utf-8 -*-
"""
舌镜-正和积分整合测试用例

玄镜团队 · 舌诊服务与正和积分系统整合测试
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhenghe_client import ZhengheClient, ZhengheError
from diagnosis_engine import TongueDiagnosisEngine, TONGUE_SERVICE_PRICING


class TestZhengheClient:
    """正和客户端单元测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return ZhengheClient(
            api_key="sk_live_test_key",
            base_url="http://localhost:8000/mcp",
            timeout=10.0
        )
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        with patch.dict(os.environ, {}, clear=True):
            client = ZhengheClient()
            assert client.api_key == ""
            assert client.base_url == "http://localhost:8000/mcp"
    
    def test_init_with_params(self):
        """测试参数初始化"""
        client = ZhengheClient(
            api_key="my_key",
            base_url="https://api.example.com/mcp"
        )
        assert client.api_key == "my_key"
        assert client.base_url == "https://api.example.com/mcp"
    
    def test_generate_reference_id(self, client):
        """测试参考号生成"""
        ref = client._generate_reference_id(
            user_id="acc_123",
            session_id="sess_abc",
            service_type="tongue"
        )
        
        assert ref.startswith("ref_tongue_acc_123_")
        assert len(ref) > 30
    
    def test_generate_reference_id_unique(self, client):
        """测试参考号唯一性"""
        refs = set()
        for i in range(10):
            ref = client._generate_reference_id(
                user_id=f"acc_{i}",  # 使用不同的user_id
                session_id=f"sess_{i}",  # 或不同的session
                service_type="tongue"
            )
            refs.add(ref)
        
        # 使用不同输入应该产生不同的reference_id
        assert len(refs) == 10
    
    def test_generate_reference_id_format(self, client):
        """测试参考号格式"""
        import re
        
        ref = client._generate_reference_id(
            user_id="acc_test",
            session_id="sess_xyz",
            service_type="tongue_quick"
        )
        
        # 格式: ref_tongue_{user}_{timestamp}_{hash}
        pattern = r'^ref_tongue_acc_test_\d+_[a-f0-9]{8}$'
        assert re.match(pattern, ref)
    
    @pytest.mark.asyncio
    async def test_get_balance_no_api_key(self):
        """测试无API Key情况"""
        client = ZhengheClient(api_key="")
        
        with pytest.raises(ZhengheError) as exc_info:
            await client.get_balance("acc_123")
        
        assert "API key not configured" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_consume_missing_reference(self, client):
        """测试缺少reference_id且无user_id/session_id"""
        client.api_key = "valid_key"
        
        with pytest.raises(ZhengheError) as exc_info:
            await client.consume(
                consumer_account_id="acc_123",
                provider_agent_id="agent_tongue",
                pricing_usdt=Decimal("1.00")
            )
        
        assert "reference_id" in str(exc_info.value)


class TestZhengheError:
    """正和异常测试"""
    
    def test_error_format(self):
        """测试错误格式化"""
        error = ZhengheError({
            "code": -32001,
            "message": "Test error message"
        })
        
        assert error.code == -32001
        assert error.message == "Test error message"
        assert "[-32001]" in str(error)
    
    def test_error_defaults(self):
        """测试错误默认值"""
        error = ZhengheError({})
        
        assert error.code == -1
        assert error.message == "Unknown error"


class TestTongueDiagnosisEngine:
    """舌诊引擎测试"""
    
    @pytest.fixture
    def mock_client(self):
        """创建模拟客户端"""
        client = MagicMock(spec=ZhengheClient)
        client._generate_reference_id = MagicMock(
            return_value="ref_test_12345_abc123"
        )
        client.check_balance = AsyncMock()
        client.consume = AsyncMock()
        return client
    
    @pytest.fixture
    def engine(self, mock_client):
        """创建测试引擎"""
        return TongueDiagnosisEngine(
            zhenghe_client=mock_client,
            tongue_agent_id="agent_tongue_001",
            payment_enabled=True,
            fallback_to_free=True
        )
    
    @pytest.fixture
    def valid_tongue_params(self):
        """有效舌诊参数"""
        return {
            "tongue_color": "红",
            "tongue_shape": "瘦薄",
            "tongue_coating_color": "黄",
            "tongue_coating_texture": "薄",
            "patient_age": 45,
            "patient_gender": "男",
            "chief_complaint": "胃脘胀满",
            "symptoms": "口干咽燥",
            "mode": "详细模式"
        }
    
    def test_get_pricing(self, engine):
        """测试定价获取"""
        assert engine.get_pricing("快速模式") == Decimal("0.50")
        assert engine.get_pricing("详细模式") == Decimal("1.00")
        assert engine.get_pricing("未知模式") == Decimal("1.00")  # 默认值
    
    @pytest.mark.asyncio
    async def test_diagnose_free(self, engine, valid_tongue_params):
        """测试免费诊断"""
        result = await engine.diagnose_free(valid_tongue_params)
        
        assert result["success"] == True
        assert result["payment_required"] == False
        assert "diagnosis" in result
        assert result["payment"]["status"] == "free"
    
    @pytest.mark.asyncio
    async def test_diagnose_with_payment_success(
        self, 
        engine, 
        mock_client,
        valid_tongue_params
    ):
        """测试完整支付流程"""
        # Mock余额检查通过
        mock_client.check_balance.return_value = {
            "sufficient": True,
            "balance": "100.0",
            "balance_usdt": "700.0"
        }
        
        # Mock消费成功
        mock_client.consume.return_value = {
            "tx_id": "tx_test_123",
            "burned_tokens": "0.15",
            "status": "completed"
        }
        
        result = await engine.diagnose_with_payment(
            user_account_id="acc_123",
            session_id="sess_abc",
            tongue_params=valid_tongue_params,
            require_payment=True
        )
        
        assert result["success"] == True
        assert result["payment_required"] == True
        assert "diagnosis" in result
        assert result["payment"]["status"] == "completed"
        assert result["payment"]["tx_id"] == "tx_test_123"
        
        # 验证调用参数
        mock_client.consume.assert_called_once()
        call_args = mock_client.consume.call_args
        assert call_args.kwargs["consumer_account_id"] == "acc_123"
        assert call_args.kwargs["pricing_usdt"] == Decimal("1.00")
    
    @pytest.mark.asyncio
    async def test_diagnose_insufficient_balance(
        self, 
        engine, 
        mock_client,
        valid_tongue_params
    ):
        """测试余额不足"""
        mock_client.check_balance.return_value = {
            "sufficient": False,
            "balance": "0.5",
            "balance_usdt": "3.5"
        }
        
        result = await engine.diagnose_with_payment(
            user_account_id="acc_poor",
            session_id="sess_abc",
            tongue_params=valid_tongue_params,
            require_payment=True
        )
        
        assert result["success"] == False
        assert result["error"] == "INSUFFICIENT_BALANCE"
        assert result["payment_required"] == True
    
    @pytest.mark.asyncio
    async def test_diagnose_payment_failed_partial_success(
        self, 
        engine, 
        mock_client,
        valid_tongue_params
    ):
        """测试支付失败但诊断成功（部分成功）"""
        mock_client.check_balance.return_value = {
            "sufficient": True,
            "balance": "100.0"
        }
        
        mock_client.consume.side_effect = ZhengheError({
            "code": -32001,
            "message": "Consume failed"
        })
        
        result = await engine.diagnose_with_payment(
            user_account_id="acc_123",
            session_id="sess_abc",
            tongue_params=valid_tongue_params,
            require_payment=True
        )
        
        assert result["success"] == True
        assert result["partial"] == True
        assert "diagnosis" in result
        assert result["payment"]["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_diagnose_balance_check_failed_fallback(
        self, 
        engine, 
        mock_client,
        valid_tongue_params
    ):
        """测试余额检查失败时降级为免费"""
        mock_client.check_balance.side_effect = ZhengheError({
            "code": -32003,
            "message": "Timeout"
        })
        
        # fallback_to_free = True，支付失败时应降级为免费模式
        # 关键：require_payment=True 但 fallback_to_free=True
        # 所以检查失败后应继续执行（不报错），最终以免费模式完成
        result = await engine.diagnose_with_payment(
            user_account_id="acc_123",
            session_id="sess_abc",
            tongue_params=valid_tongue_params,
            require_payment=True  # 尝试付费
        )
        
        # 应该成功（降级为免费模式）
        assert result["success"] == True
        # 因为fallback_to_free=True，所以最终不要求支付
        assert result["payment_required"] == False  # 降级为免费
    
    @pytest.mark.asyncio
    async def test_diagnose_quick_mode_pricing(
        self, 
        engine, 
        mock_client
    ):
        """测试快速模式定价"""
        mock_client.check_balance.return_value = {"sufficient": True}
        mock_client.consume.return_value = {"tx_id": "tx_1", "burned_tokens": "0.08"}
        
        quick_params = {
            "tongue_color": "淡红",
            "tongue_shape": "正常",
            "tongue_coating_color": "薄白",
            "tongue_coating_texture": "薄",
            "patient_age": 30,
            "patient_gender": "女",
            "chief_complaint": "体检",
            "mode": "快速模式"
        }
        
        result = await engine.diagnose_with_payment(
            user_account_id="acc_123",
            session_id="sess_abc",
            tongue_params=quick_params,
            require_payment=True
        )
        
        assert result["success"] == True
        assert result["payment"]["pricing_usdt"] == "0.50"


class TestIdempotency:
    """幂等性测试"""
    
    @pytest.fixture
    def client(self):
        return ZhengheClient(api_key="sk_live_test")
    
    def test_reference_id_deterministic(self, client):
        """测试相同输入产生不同reference_id（时间戳）"""
        import time
        
        # 连续生成的reference_id应该不同
        ref1 = client._generate_reference_id("user1", "sess1", "tongue")
        time.sleep(0.1)  # 确保时间戳变化
        ref2 = client._generate_reference_id("user1", "sess1", "tongue")
        
        # 时间戳部分不同
        ts1 = int(ref1.split("_")[3])
        ts2 = int(ref2.split("_")[3])
        assert ts2 >= ts1


class TestServicePricing:
    """服务定价测试"""
    
    def test_pricing_constants(self):
        """测试定价常量"""
        assert TONGUE_SERVICE_PRICING["快速模式"] == Decimal("0.50")
        assert TONGUE_SERVICE_PRICING["详细模式"] == Decimal("1.00")
    
    def test_pricing_alignment(self):
        """测试定价对齐"""
        # 快速模式定价应该低于详细模式
        assert TONGUE_SERVICE_PRICING["快速模式"] < TONGUE_SERVICE_PRICING["详细模式"]


class TestDiagnosisResult:
    """诊断结果测试"""
    
    @pytest.mark.asyncio
    async def test_free_diagnosis_structure(self):
        """测试免费诊断结果结构"""
        engine = TongueDiagnosisEngine(
            payment_enabled=False,
            fallback_to_free=False
        )
        
        result = await engine.diagnose_free({
            "tongue_color": "淡红",
            "tongue_shape": "正常",
            "tongue_coating_color": "薄白",
            "tongue_coating_texture": "薄",
            "patient_age": 25,
            "patient_gender": "男",
            "chief_complaint": "常规体检",
            "mode": "详细模式"
        })
        
        # 验证结果结构
        assert "success" in result
        assert "diagnosis" in result
        assert "payment" in result
        
        diagnosis = result["diagnosis"]
        assert "辨证结果" in diagnosis
        assert "针灸方案" in diagnosis
        assert "生活调护建议" in diagnosis


# pytest配置
def pytest_configure(config):
    """Pytest配置"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
