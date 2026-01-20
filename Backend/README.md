# MacCortex Python Backend

**Phase 1 - Week 2 Day 8-9**
**创建时间**: 2026-01-20

AI Pattern 执行引擎，为 MacCortex Swift 应用提供 Python 后端支持。

## 功能特性

- ✅ **FastAPI 服务**: 高性能 Python Web API
- ✅ **MLX 集成**: Apple Silicon 优化的 LLM 推理
- ✅ **Ollama 支持**: 本地 LLM 模型运行
- ✅ **Pattern 系统**: 可扩展的 AI 任务抽象
- ⏳ **LangGraph**: 复杂工作流编排（Day 9）
- ⏳ **ChromaDB**: 向量数据库（Day 9）

## 快速开始

### 1. 安装依赖

```bash
cd Backend

# 方式 1: 使用 Poetry（推荐）
poetry install

# 方式 2: 使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 根据需要修改 .env 配置
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
python src/main.py

# 或使用 uvicorn
uvicorn src.main:app --host localhost --port 8000 --reload
```

### 4. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 端点

### 1. 健康检查

```bash
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-20T12:00:00",
  "version": "0.1.0",
  "uptime": 123.45,
  "patterns_loaded": 1
}
```

### 2. 版本信息

```bash
GET /version
```

**响应**:
```json
{
  "python": "3.14.2",
  "backend": "0.1.0",
  "mlx": "0.5.0",
  "ollama": "0.1.6"
}
```

### 3. 列出可用 Pattern

```bash
GET /patterns
```

**响应**:
```json
{
  "total": 1,
  "patterns": [
    {
      "id": "summarize",
      "name": "Summarize",
      "description": "Summarize long text into concise key points",
      "version": "1.0.0"
    }
  ]
}
```

### 4. 执行 Pattern

```bash
POST /execute
Content-Type: application/json

{
  "pattern_id": "summarize",
  "text": "这是一段需要总结的长文本...",
  "parameters": {
    "length": "medium",
    "style": "bullet",
    "language": "zh-CN"
  },
  "request_id": "req-12345"
}
```

**响应**:
```json
{
  "request_id": "req-12345",
  "success": true,
  "output": "• 要点 1\n• 要点 2\n• 要点 3",
  "metadata": {
    "length": "medium",
    "style": "bullet",
    "language": "zh-CN",
    "original_length": 1000,
    "summary_length": 150
  },
  "error": null,
  "duration": 2.35
}
```

## 项目结构

```
Backend/
├── src/
│   ├── main.py                 # FastAPI 应用入口
│   ├── patterns/               # Pattern 实现
│   │   ├── __init__.py
│   │   ├── base.py            # BasePattern 抽象类
│   │   ├── registry.py        # PatternRegistry
│   │   └── summarize.py       # SummarizePattern 实现
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       └── config.py          # 配置管理
├── tests/                      # 单元测试（Day 9）
├── data/                       # 数据目录（自动创建）
├── pyproject.toml             # Poetry 配置
├── requirements.txt           # pip 依赖
├── .env.example               # 环境变量模板
└── README.md                  # 本文件
```

## Pattern 系统

### BasePattern 抽象类

所有 Pattern 继承自 `BasePattern`：

```python
from patterns.base import BasePattern

class MyPattern(BasePattern):
    @property
    def pattern_id(self) -> str:
        return "my_pattern"

    @property
    def name(self) -> str:
        return "My Pattern"

    @property
    def description(self) -> str:
        return "Pattern description"

    async def execute(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # 实现逻辑
        return {
            "output": "结果文本",
            "metadata": {"key": "value"}
        }
```

### 注册 Pattern

在 `patterns/registry.py` 的 `initialize()` 方法中添加：

```python
patterns = [
    SummarizePattern(),
    MyPattern(),  # 添加新 Pattern
]
```

## 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 0.109.0 | Web 框架 |
| **Pydantic** | 2.5.0 | 数据验证 |
| **MLX** | 0.5.0 | Apple Silicon LLM 推理 |
| **Ollama** | 0.1.6 | 本地 LLM 运行时 |
| **LangChain** | 0.1.0 | LLM 工具链 |
| **LangGraph** | 0.0.20 | 工作流编排 |
| **ChromaDB** | 0.4.22 | 向量数据库 |
| **Loguru** | 0.7.2 | 日志框架 |

## 性能优化

### Apple Silicon 优化（MLX）

MLX 是 Apple 专为 Apple Silicon 设计的机器学习框架：

- **Metal 加速**: 直接使用 GPU
- **统一内存**: 高效的内存管理
- **4-bit 量化**: 降低内存占用
- **推理速度**: 230 tok/s（比 Ollama 快 8-10 倍）

### Ollama 本地模型

如果 MLX 不可用，自动回退到 Ollama：

```bash
# 安装 Ollama（macOS）
brew install ollama

# 启动服务
ollama serve

# 拉取模型
ollama pull qwen3:14b
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=src --cov-report=html
```

### 代码格式化

```bash
# Black 格式化
black src/

# Ruff 检查
ruff check src/
```

### 日志级别

在 `.env` 中设置：

```bash
LOG_LEVEL=DEBUG   # 开发环境
LOG_LEVEL=INFO    # 生产环境
```

## 与 Swift 应用集成

Swift 应用通过 `PythonBridge` 模块与后端通信：

```swift
// Swift 代码示例
let bridge = PythonBridge.shared
try await bridge.start()  // 启动 Python 后端

let request = PythonRequest(
    patternID: "summarize",
    text: "长文本...",
    parameters: ["length": "medium"]
)

let response = try await bridge.execute(request: request)
print(response.output)  // 总结结果
```

## 故障排除

### MLX 安装失败

```bash
# 确保使用 Apple Silicon Mac
uname -m  # 应输出 arm64

# 安装 MLX
pip install mlx mlx-lm
```

### Ollama 连接失败

```bash
# 检查 Ollama 服务状态
curl http://localhost:11434/api/tags

# 重启 Ollama
killall ollama && ollama serve
```

### 依赖冲突

```bash
# 使用虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 下一步（Day 9）

- [ ] 实现其他 4 个 Pattern（extract/translate/format/search）
- [ ] 集成 LangGraph 工作流
- [ ] 集成 ChromaDB 向量数据库
- [ ] 编写单元测试
- [ ] 性能压测（< 2s 延迟目标）

## 许可证

MacCortex © 2026
