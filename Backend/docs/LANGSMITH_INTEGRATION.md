# LangSmith 监控集成指南

**创建时间**: 2026-01-23
**状态**: ✅ 已启用
**用途**: 生产环境可观测性、Token 追踪、性能监控

---

## 📋 目录

- [什么是 LangSmith](#什么是-langsmith)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [验证追踪](#验证追踪)
- [仪表盘使用](#仪表盘使用)
- [高级功能](#高级功能)
- [故障排除](#故障排除)

---

## 什么是 LangSmith

LangSmith 是 LangChain 官方的可观测性平台，提供：

- **完整追踪**：捕获每个 LLM 调用（Planner/Coder/Reviewer/Researcher 等）
- **Token 监控**：实时追踪 Token 消耗与成本
- **性能分析**：延迟、吞吐量、成功率统计
- **调试工具**：完整的调用链路、输入输出日志
- **警报系统**：成本超标、错误率异常自动通知
- **LLM-as-a-Judge**：自动评估输出质量

**行业采用率**：89% 生产环境 LangGraph 应用使用可观测性工具（2026 年数据）

---

## 快速开始

### 1. 注册 LangSmith（5 分钟）

#### 访问官网
```
https://www.langchain.com/langsmith
```

#### 使用 GitHub OAuth 登录
- 点击 "Sign in with GitHub"
- 授权 LangChain 访问您的 GitHub 账户

#### 创建项目
- 项目名称：`MacCortex-Production`
- 描述：MacCortex Swarm Intelligence 生产监控

#### 获取 API Key
1. 点击右上角头像 → **Settings**
2. 选择 **API Keys**
3. 点击 **Create API Key**
4. 复制 API Key（格式：`lsv2_pt_xxx...`）
   - ⚠️ 请妥善保存，离开页面后无法再次查看

---

### 2. 配置环境变量（2 分钟）

#### 编辑 .env 文件

```bash
cd ~/projects/MacCortex/Backend

# 编辑 .env 文件
nano .env  # 或使用 vim、VSCode 等
```

#### 添加 LangSmith 配置

在 .env 文件末尾添加：

```bash
# ==================== LangSmith 监控配置 ====================
# LangSmith 追踪开关（true=启用，false=禁用）
LANGCHAIN_TRACING_V2=true

# LangSmith API Key（从 https://smith.langchain.com/ 获取）
LANGCHAIN_API_KEY=lsv2_pt_your_api_key_here

# LangSmith 项目名称（用于组织追踪数据）
LANGCHAIN_PROJECT=MacCortex-Production

# LangSmith API 端点（通常无需修改）
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

#### 替换 API Key

将 `lsv2_pt_your_api_key_here` 替换为您从 LangSmith 获取的真实 API Key。

---

### 3. 验证追踪（5 分钟）

#### 加载环境变量

```bash
cd ~/projects/MacCortex/Backend
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
```

#### 运行测试任务

```bash
# 运行简单测试（会自动追踪到 LangSmith）
python scripts/benchmark_model_router_simple.py
```

#### 查看追踪数据

1. 访问 https://smith.langchain.com/
2. 选择项目 **MacCortex-Production**
3. 应该能看到最近的追踪记录：
   - Planner 节点调用（Claude Sonnet）
   - Reviewer 节点调用（Ollama）
   - 完整的输入输出日志
   - Token 消耗统计

**预期输出**：
- ✅ 看到 3-4 条追踪记录
- ✅ 每条记录显示模型名称、耗时、Token 数
- ✅ 可以点击查看详细的输入输出

---

## 配置说明

### 环境变量详解

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `LANGCHAIN_TRACING_V2` | ✅ | - | 启用 LangSmith 追踪（`true`/`false`）|
| `LANGCHAIN_API_KEY` | ✅ | - | LangSmith API Key（`lsv2_pt_xxx`）|
| `LANGCHAIN_PROJECT` | 推荐 | `default` | 项目名称（用于组织数据）|
| `LANGCHAIN_ENDPOINT` | 可选 | `https://api.smith.langchain.com` | API 端点（通常无需修改）|

### 最佳实践

#### 开发环境 vs 生产环境

**开发环境** (`.env.development`):
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=MacCortex-Development
```

**生产环境** (`.env.production`):
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=MacCortex-Production
```

#### 免费层限制

LangSmith 免费层提供：
- **5,000 traces/月**
- **14 天数据保留**
- **1 个项目**

如果超出，考虑升级到付费版（$39/月）：
- **50,000 traces/月**
- **90 天数据保留**
- **无限项目**

---

## 仪表盘使用

### 主要功能

#### 1. **Traces（追踪）**

查看所有 LLM 调用：
- 时间线视图
- 调用链路图（Planner → Coder → Reviewer）
- 输入输出日志
- Token 消耗统计

**访问**: https://smith.langchain.com/ → 选择项目 → Traces

#### 2. **Datasets（数据集）**

创建测试数据集，用于回归测试：
- 保存示例任务
- 自动运行测试
- 对比不同版本输出

**用例**: 验证提示词优化后质量是否下降

#### 3. **Evaluations（评估）**

配置 LLM-as-a-Judge 自动评估：
- 输出质量评分
- 毒性检测
- 事实准确性验证

#### 4. **Monitoring（监控）**

实时监控仪表盘：
- Token 消耗趋势
- 延迟分布
- 错误率统计
- 成功率趋势

---

### 创建自定义仪表盘

#### 步骤 1: 配置 Token 消耗图表

1. 访问 https://smith.langchain.com/
2. 选择项目 → **Monitoring** → **Create Chart**
3. 配置：
   - **Metric**: `total_tokens`
   - **Group By**: `node_name`（Planner/Coder/Reviewer）
   - **Time Range**: Last 7 days
   - **Chart Type**: Line Chart

#### 步骤 2: 配置成本警报

1. **Monitoring** → **Alerts** → **Create Alert**
2. 配置：
   - **Condition**: `total_cost > $10`（每日成本超 $10）
   - **Notification**: Email
   - **Frequency**: Daily

#### 步骤 3: 配置延迟警报

1. **Create Alert** → **Latency**
2. 配置：
   - **Condition**: `p95_latency > 30s`（P95 延迟超 30 秒）
   - **Notification**: Slack（如配置 Slack 集成）

---

## 高级功能

### 1. OpenTelemetry 集成

如果您已有 Prometheus/Grafana，可以使用 OpenTelemetry 导出：

```bash
# 安装 OpenTelemetry
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# 配置导出到 Jaeger/Grafana
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

**参考**: https://www.blog.langchain.com/end-to-end-opentelemetry-langsmith/

---

### 2. 自定义标签

为追踪添加自定义元数据：

```python
from langsmith import traceable

@traceable(
    name="custom_task",
    tags=["production", "high-priority"],
    metadata={"user_id": "12345", "version": "1.0"}
)
def run_task():
    # 您的任务代码
    pass
```

---

### 3. LLM-as-a-Judge 评估

配置自动质量评估：

#### 创建评估器

1. **Evaluations** → **Create Evaluator**
2. 选择模板：
   - **Correctness**（正确性）
   - **Toxicity**（毒性检测）
   - **Custom**（自定义评估）

#### 示例：代码质量评估

```python
# 在 LangSmith 中创建自定义评估器
{
  "name": "code_quality",
  "prompt": "评估以下代码的质量（1-10 分），考虑：\n1. 代码规范\n2. 错误处理\n3. 可读性\n\n代码：{output}",
  "model": "claude-sonnet-4",
  "output_parser": "score"
}
```

---

## 故障排除

### 问题 1: 追踪数据未出现在 LangSmith

**症状**: 运行测试后，LangSmith 仪表盘无追踪记录

**可能原因**:
1. `LANGCHAIN_TRACING_V2` 未设置为 `true`
2. `LANGCHAIN_API_KEY` 错误
3. 网络问题（防火墙阻止）

**解决方案**:

```bash
# 1. 验证环境变量
echo $LANGCHAIN_TRACING_V2  # 应输出 "true"
echo $LANGCHAIN_API_KEY     # 应输出 "lsv2_pt_xxx..."

# 2. 重新加载环境变量
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)

# 3. 测试网络连接
curl -H "x-api-key: $LANGCHAIN_API_KEY" https://api.smith.langchain.com/info

# 预期输出：{"version": "..."}
```

---

### 问题 2: API Key 无效

**症状**: `401 Unauthorized` 错误

**解决方案**:
1. 重新生成 API Key（Settings → API Keys → Create）
2. 确认 API Key 格式正确（`lsv2_pt_` 开头）
3. 检查是否有多余空格或换行符

---

### 问题 3: 追踪数据延迟

**症状**: 运行测试后 5-10 分钟才出现数据

**原因**: LangSmith 异步处理追踪数据，通常 1-2 分钟延迟

**解决方案**: 耐心等待，刷新页面

---

### 问题 4: 免费层额度用尽

**症状**: `429 Too Many Requests` 错误

**解决方案**:
1. 升级到付费版（$39/月）
2. 临时禁用追踪（`LANGCHAIN_TRACING_V2=false`）
3. 使用采样（仅追踪 10% 请求）：

```python
import random
from langsmith import Client

client = Client()
if random.random() < 0.1:  # 10% 采样率
    # 启用追踪
    pass
```

---

## 性能影响

LangSmith 追踪对性能的影响：

| 指标 | 影响 |
|------|------|
| **延迟** | < 10ms（异步上报）|
| **内存** | < 5MB |
| **CPU** | < 1% |
| **网络** | ~1-5KB/trace |

**结论**: 性能影响可忽略不计 ✅

---

## 安全注意事项

### 敏感数据过滤

LangSmith 会记录所有输入输出，请注意：

1. **不要在提示词中包含**：
   - 用户密码
   - API Keys
   - 信用卡信息
   - 个人身份信息（PII）

2. **使用数据脱敏**（如需要）：

```python
import re

def sanitize_input(text: str) -> str:
    # 移除邮箱
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    # 移除手机号
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    return text
```

---

## 资源链接

### 官方文档
- [LangSmith 主页](https://www.langchain.com/langsmith)
- [LangSmith 文档](https://docs.langchain.com/oss/python/langchain/observability)
- [OpenTelemetry 集成](https://www.blog.langchain.com/end-to-end-opentelemetry-langsmith/)

### 教程
- [10 分钟快速上手](https://last9.io/blog/langchain-observability/)
- [LLM 可观测性指南](https://activewizards.com/blog/llm-observability-a-guide-to-monitoring-with-langsmith/)

### 社区
- [LangChain Discord](https://discord.gg/langchain)
- [GitHub Discussions](https://github.com/langchain-ai/langchain/discussions)

---

## 总结

LangSmith 集成完成后，您将获得：

✅ **完整追踪**：每个 LLM 调用的详细记录
✅ **Token 监控**：实时成本追踪与预算控制
✅ **性能分析**：延迟、吞吐量、成功率统计
✅ **调试工具**：快速定位问题根因
✅ **质量评估**：LLM-as-a-Judge 自动评分
✅ **警报系统**：成本超标、错误率异常通知

**下一步**:
1. 运行生产任务，观察追踪数据
2. 配置自定义仪表盘
3. 设置成本警报（预算 $50/月）
4. 启用 LLM-as-a-Judge 评估

---

**文档版本**: v1.0
**创建时间**: 2026-01-23
**维护者**: MacCortex 开发团队
**联系方式**: 通过 GitHub Issues 反馈问题
