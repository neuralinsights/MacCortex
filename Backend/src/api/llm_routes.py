"""
MacCortex LLM API Routes

提供 LLM 模型信息和使用统计的 RESTful API。

Routes:
- GET /llm/models - 获取可用模型列表
- GET /llm/usage - 获取会话使用统计
- GET /llm/usage/{session_id} - 获取特定会话的使用统计
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/llm", tags=["llm"])


# ============================================================================
# Response Models
# ============================================================================


class ModelPricing(BaseModel):
    """模型定价信息"""
    input_price_per_1m: float = Field(..., description="输入价格 ($/1M tokens)")
    output_price_per_1m: float = Field(..., description="输出价格 ($/1M tokens)")


class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型 ID (如 claude-sonnet-4)")
    display_name: str = Field(..., description="显示名称")
    provider: str = Field(..., description="Provider 名称 (如 anthropic)")
    is_local: bool = Field(..., description="是否为本地模型")
    is_available: bool = Field(..., description="是否可用 (API Key 已配置)")
    pricing: ModelPricing = Field(..., description="定价信息")
    capabilities: List[str] = Field(default_factory=list, description="模型能力标签")


class ModelsResponse(BaseModel):
    """模型列表响应"""
    models: List[ModelInfo] = Field(..., description="可用模型列表")
    default_model: str = Field(..., description="默认模型 ID")
    total_count: int = Field(..., description="模型总数")


class AgentUsage(BaseModel):
    """单个 Agent 的使用统计"""
    input_tokens: int = Field(..., description="输入 Token 数")
    output_tokens: int = Field(..., description="输出 Token 数")
    total_tokens: int = Field(..., description="总 Token 数")
    call_count: int = Field(..., description="调用次数")
    total_cost: str = Field(..., description="总成本 (USD)")


class UsageStats(BaseModel):
    """使用统计"""
    total_tokens: int = Field(..., description="总 Token 数")
    input_tokens: int = Field(..., description="输入 Token 数")
    output_tokens: int = Field(..., description="输出 Token 数")
    total_cost: str = Field(..., description="总成本 (USD)")
    formatted_cost: str = Field(..., description="格式化成本 (如 $0.0234)")
    call_count: int = Field(..., description="调用次数")
    by_agent: Dict[str, AgentUsage] = Field(default_factory=dict, description="按 Agent 分组")
    by_model: Dict[str, AgentUsage] = Field(default_factory=dict, description="按模型分组")
    by_provider: Dict[str, AgentUsage] = Field(default_factory=dict, description="按 Provider 分组")


class UsageResponse(BaseModel):
    """使用统计响应"""
    session_id: Optional[str] = Field(None, description="会话 ID (如果指定)")
    stats: UsageStats = Field(..., description="使用统计")


# ============================================================================
# Singleton Router Instance (lazy initialization)
# ============================================================================

_router_instance = None


def get_router():
    """获取 ModelRouterV2 单例"""
    global _router_instance
    if _router_instance is None:
        from llm import create_default_router
        _router_instance = create_default_router()
    return _router_instance


# ============================================================================
# Helper Functions
# ============================================================================


def _get_model_capabilities(model_info) -> List[str]:
    """根据模型信息推断能力标签"""
    capabilities = []
    if model_info.supports_streaming:
        capabilities.append("streaming")
    if model_info.supports_tools:
        capabilities.append("tools")
    if model_info.is_local:
        capabilities.append("local")
    if model_info.context_window >= 100000:
        capabilities.append("long_context")
    return capabilities


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/models", response_model=ModelsResponse)
async def get_models() -> ModelsResponse:
    """
    获取可用模型列表

    返回所有已注册的 LLM 模型信息，包括：
    - 模型 ID 和显示名称
    - Provider 信息
    - 定价信息
    - 可用性状态
    """
    model_router = get_router()

    models = []
    for model_info in model_router.get_available_models():
        # 检查模型是否可用 (Provider 已注册且 API Key 已配置)
        is_available = model_router.is_model_available(model_info.id)

        models.append(ModelInfo(
            id=model_info.id,
            display_name=model_info.display_name,
            provider=model_info.provider.value,
            is_local=model_info.is_local,
            is_available=is_available,
            pricing=ModelPricing(
                input_price_per_1m=float(model_info.input_price_per_1m),
                output_price_per_1m=float(model_info.output_price_per_1m),
            ),
            capabilities=_get_model_capabilities(model_info),
        ))

    return ModelsResponse(
        models=models,
        default_model=model_router.default_model_id,
        total_count=len(models),
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    session_id: Optional[str] = Query(None, description="会话 ID (可选)")
) -> UsageResponse:
    """
    获取使用统计

    返回 Token 使用量和成本统计：
    - 总体统计
    - 按 Agent 分组 (planner, coder, reviewer 等)
    - 按模型分组
    - 按 Provider 分组

    如果指定 session_id，只返回该会话的统计。
    """
    model_router = get_router()
    stats = model_router.get_usage_stats(session_id=session_id)

    # 转换 by_agent 格式
    by_agent = {}
    for agent_name, agent_stats in stats.get("by_agent", {}).items():
        by_agent[agent_name] = AgentUsage(
            input_tokens=agent_stats.get("input_tokens", 0),
            output_tokens=agent_stats.get("output_tokens", 0),
            total_tokens=agent_stats.get("total_tokens", 0),
            call_count=agent_stats.get("call_count", 0),
            total_cost=agent_stats.get("total_cost", "0.000000"),
        )

    # 转换 by_model 格式
    by_model = {}
    for model_id, model_stats in stats.get("by_model", {}).items():
        by_model[model_id] = AgentUsage(
            input_tokens=model_stats.get("input_tokens", 0),
            output_tokens=model_stats.get("output_tokens", 0),
            total_tokens=model_stats.get("total_tokens", 0),
            call_count=model_stats.get("call_count", 0),
            total_cost=model_stats.get("total_cost", "0.000000"),
        )

    # 转换 by_provider 格式
    by_provider = {}
    for provider_name, provider_stats in stats.get("by_provider", {}).items():
        by_provider[provider_name] = AgentUsage(
            input_tokens=provider_stats.get("input_tokens", 0),
            output_tokens=provider_stats.get("output_tokens", 0),
            total_tokens=provider_stats.get("total_tokens", 0),
            call_count=provider_stats.get("call_count", 0),
            total_cost=provider_stats.get("total_cost", "0.000000"),
        )

    return UsageResponse(
        session_id=session_id,
        stats=UsageStats(
            total_tokens=stats.get("total_tokens", 0),
            input_tokens=stats.get("input_tokens", 0),
            output_tokens=stats.get("output_tokens", 0),
            total_cost=stats.get("total_cost", "0.000000"),
            formatted_cost=stats.get("formatted_cost", "$0.00"),
            call_count=stats.get("call_count", 0),
            by_agent=by_agent,
            by_model=by_model,
            by_provider=by_provider,
        ),
    )


@router.post("/usage/reset")
async def reset_usage(
    session_id: Optional[str] = Query(None, description="会话 ID (可选，不指定则重置全部)")
) -> Dict[str, Any]:
    """
    重置使用统计

    清除 Token 使用记录。
    如果指定 session_id，只重置该会话的统计。
    """
    model_router = get_router()
    model_router.reset_usage(session_id=session_id)

    return {
        "success": True,
        "message": f"Usage stats reset" + (f" for session {session_id}" if session_id else ""),
    }
