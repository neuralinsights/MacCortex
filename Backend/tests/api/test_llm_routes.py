"""
LLM API Routes 测试

测试 /llm/models, /llm/usage 等 API 端点。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from decimal import Decimal

# 在导入模块之前 mock create_default_router
with patch("api.llm_routes.get_router") as mock_get_router:
    mock_router = MagicMock()
    mock_get_router.return_value = mock_router

    from api.llm_routes import router, _get_model_capabilities

from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)


class TestGetModelCapabilities:
    """测试 _get_model_capabilities 辅助函数"""

    def test_streaming_capability(self):
        """测试 streaming 能力标签"""
        model_info = Mock(
            supports_streaming=True,
            supports_tools=False,
            is_local=False,
            context_window=8000
        )
        capabilities = _get_model_capabilities(model_info)
        assert "streaming" in capabilities
        assert "tools" not in capabilities

    def test_tools_capability(self):
        """测试 tools 能力标签"""
        model_info = Mock(
            supports_streaming=False,
            supports_tools=True,
            is_local=False,
            context_window=8000
        )
        capabilities = _get_model_capabilities(model_info)
        assert "tools" in capabilities
        assert "streaming" not in capabilities

    def test_local_capability(self):
        """测试 local 能力标签"""
        model_info = Mock(
            supports_streaming=False,
            supports_tools=False,
            is_local=True,
            context_window=8000
        )
        capabilities = _get_model_capabilities(model_info)
        assert "local" in capabilities

    def test_long_context_capability(self):
        """测试 long_context 能力标签（>=100k）"""
        model_info = Mock(
            supports_streaming=False,
            supports_tools=False,
            is_local=False,
            context_window=200000
        )
        capabilities = _get_model_capabilities(model_info)
        assert "long_context" in capabilities

    def test_no_long_context_below_threshold(self):
        """测试 context_window < 100k 时不添加 long_context"""
        model_info = Mock(
            supports_streaming=False,
            supports_tools=False,
            is_local=False,
            context_window=99999
        )
        capabilities = _get_model_capabilities(model_info)
        assert "long_context" not in capabilities

    def test_all_capabilities(self):
        """测试所有能力都启用的情况"""
        model_info = Mock(
            supports_streaming=True,
            supports_tools=True,
            is_local=True,
            context_window=128000
        )
        capabilities = _get_model_capabilities(model_info)
        assert "streaming" in capabilities
        assert "tools" in capabilities
        assert "local" in capabilities
        assert "long_context" in capabilities
        assert len(capabilities) == 4


class TestLLMModelsEndpoint:
    """测试 GET /llm/models 端点"""

    def test_get_models_empty(self):
        """测试空模型列表"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            mock_router = Mock()
            mock_router.get_available_models.return_value = []
            mock_router.default_model_id = "claude-sonnet-4"
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.get("/llm/models")

            assert response.status_code == 200
            data = response.json()
            assert data["models"] == []
            assert data["total_count"] == 0
            assert data["default_model"] == "claude-sonnet-4"

    def test_get_models_with_data(self):
        """测试有模型数据的情况"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            # Mock ProviderType enum
            mock_provider_type = Mock()
            mock_provider_type.value = "anthropic"

            mock_model = Mock(
                id="claude-sonnet-4",
                display_name="Claude Sonnet 4",
                provider=mock_provider_type,
                is_local=False,
                input_price_per_1m=Decimal("3.00"),
                output_price_per_1m=Decimal("15.00"),
                supports_streaming=True,
                supports_tools=True,
                context_window=200000
            )

            mock_router = Mock()
            mock_router.get_available_models.return_value = [mock_model]
            mock_router.is_model_available.return_value = True
            mock_router.default_model_id = "claude-sonnet-4"
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.get("/llm/models")

            assert response.status_code == 200
            data = response.json()
            assert len(data["models"]) == 1
            assert data["models"][0]["id"] == "claude-sonnet-4"
            assert data["models"][0]["display_name"] == "Claude Sonnet 4"
            assert data["models"][0]["is_available"] is True
            assert data["models"][0]["pricing"]["input_price_per_1m"] == 3.0
            assert "streaming" in data["models"][0]["capabilities"]
            assert "tools" in data["models"][0]["capabilities"]
            assert "long_context" in data["models"][0]["capabilities"]


class TestLLMUsageEndpoint:
    """测试 GET /llm/usage 端点"""

    def test_get_usage_empty(self):
        """测试空使用统计"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            mock_router = Mock()
            mock_router.get_usage_stats.return_value = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": "0.000000",
                "formatted_cost": "$0.00",
                "call_count": 0,
                "by_agent": {},
                "by_model": {},
                "by_provider": {}
            }
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.get("/llm/usage")

            assert response.status_code == 200
            data = response.json()
            assert data["stats"]["total_tokens"] == 0
            assert data["stats"]["total_cost"] == "0.000000"
            assert data["session_id"] is None

    def test_get_usage_with_data(self):
        """测试有使用数据的情况"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            mock_router = Mock()
            mock_router.get_usage_stats.return_value = {
                "total_tokens": 1500,
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_cost": "0.012345",
                "formatted_cost": "$0.0123",
                "call_count": 3,
                "by_agent": {
                    "planner": {
                        "input_tokens": 300,
                        "output_tokens": 150,
                        "total_tokens": 450,
                        "call_count": 1,
                        "total_cost": "0.004115"
                    },
                    "coder": {
                        "input_tokens": 700,
                        "output_tokens": 350,
                        "total_tokens": 1050,
                        "call_count": 2,
                        "total_cost": "0.008230"
                    }
                },
                "by_model": {},
                "by_provider": {}
            }
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.get("/llm/usage")

            assert response.status_code == 200
            data = response.json()
            assert data["stats"]["total_tokens"] == 1500
            assert data["stats"]["input_tokens"] == 1000
            assert data["stats"]["output_tokens"] == 500
            assert data["stats"]["call_count"] == 3
            assert "planner" in data["stats"]["by_agent"]
            assert data["stats"]["by_agent"]["planner"]["total_tokens"] == 450

    def test_get_usage_with_session_id(self):
        """测试带 session_id 的使用统计"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            mock_router = Mock()
            mock_router.get_usage_stats.return_value = {
                "total_tokens": 500,
                "input_tokens": 300,
                "output_tokens": 200,
                "total_cost": "0.005000",
                "formatted_cost": "$0.0050",
                "call_count": 1,
                "by_agent": {},
                "by_model": {},
                "by_provider": {}
            }
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.get("/llm/usage?session_id=test-session-123")

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-123"
            mock_router.get_usage_stats.assert_called_once_with(session_id="test-session-123")


class TestLLMUsageResetEndpoint:
    """测试 POST /llm/usage/reset 端点"""

    def test_reset_usage_all(self):
        """测试重置所有使用统计"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.post("/llm/usage/reset")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "reset" in data["message"].lower()
            mock_router.reset_usage.assert_called_once_with(session_id=None)

    def test_reset_usage_with_session_id(self):
        """测试重置特定会话的使用统计"""
        with patch("api.llm_routes.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router

            client = TestClient(app)
            response = client.post("/llm/usage/reset?session_id=test-session-456")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "test-session-456" in data["message"]
            mock_router.reset_usage.assert_called_once_with(session_id="test-session-456")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
