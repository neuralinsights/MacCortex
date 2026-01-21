# MacCortex Backend API 参考文档

> **版本**: v0.2.0 (Phase 2 Week 4)
> **更新时间**: 2026-01-21
> **Base URL**: `http://localhost:8000`
> **协议**: HTTP/1.1, JSON

---

## 目录

1. [API 概览](#api-概览)
2. [认证与安全](#认证与安全)
3. [核心端点](#核心端点)
4. [Pattern 参数详解](#pattern-参数详解)
5. [错误代码](#错误代码)
6. [速率限制](#速率限制)
7. [使用示例](#使用示例)

---

## API 概览

### 架构

```
┌─────────────────┐
│  MacCortex.app  │  (SwiftUI Frontend)
│    (Port N/A)   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI Backend│  (Python 3.11+)
│  (Port 8000)    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────┐  ┌──────┐
│ MLX  │  │Ollama│  (本地 LLM)
└──────┘  └──────┘
```

### 特性

- ✅ **RESTful API**: 标准 HTTP 方法（POST）
- ✅ **JSON 格式**: 请求和响应均为 JSON
- ✅ **本地运行**: 无外部依赖，零网络延迟
- ✅ **安全防护**: Prompt Injection 检测、输入验证、审计日志
- ✅ **CORS 支持**: 允许跨域请求（开发模式）
- ✅ **OpenAPI 文档**: 自动生成 Swagger UI (`/docs`)

### 支持的 HTTP 方法

| 方法 | 端点 | 用途 |
|------|------|------|
| `GET` | `/` | 健康检查 |
| `GET` | `/health` | 详细状态信息 |
| `GET` | `/docs` | Swagger UI 文档 |
| `POST` | `/execute` | 执行 Pattern（核心端点） |

---

## 认证与安全

### Phase 2: 无认证（本地模式）

当前版本（Phase 2）运行在本地环境，**无需认证**。Backend 仅监听 `localhost:8000`，不接受外部网络请求。

**安全措施**:
- ✅ **输入验证**: 参数白名单检查（见 `input_validator.py`）
- ✅ **Prompt Injection 防护**: 检测 20+ 恶意模式
- ✅ **速率限制**: 60 req/min（防滥用）
- ✅ **审计日志**: 所有请求记录（PII 脱敏）
- ✅ **输出验证**: 防止系统提示泄露

### Phase 3: API Key 认证（远程模式）

未来版本将支持：
- 🔜 **Bearer Token**: `Authorization: Bearer <api_key>`
- 🔜 **OAuth 2.0**: 企业版集成
- 🔜 **TLS 加密**: HTTPS 强制

---

## 核心端点

### POST /execute

**功能**: 执行指定的 AI Pattern（核心 API）

**请求格式**:
```http
POST /execute HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "pattern_id": "summarize",      // 必需，Pattern 类型
  "text": "输入文本...",          // 必需，待处理文本
  "parameters": {                 // 可选，Pattern 参数
    "length": "short",
    "style": "bullet"
  },
  "request_id": "uuid-1234"      // 可选，请求追踪 ID
}
```

**参数说明**:

| 字段 | 类型 | 必需 | 约束 | 说明 |
|------|------|------|------|------|
| `pattern_id` | `string` | ✅ | 白名单 | Pattern 类型（见下文） |
| `text` | `string` | ✅ | ≤ 50,000 字符 | 待处理文本 |
| `parameters` | `object` | ❌ | 白名单 | Pattern 参数（见 Pattern 详解） |
| `request_id` | `string` | ❌ | ≤ 100 字符 | 自定义请求 ID（用于日志追踪） |

**支持的 Pattern ID**:
- `summarize` - 文本总结
- `extract` - 信息提取
- `translate` - 文本翻译
- `format` - 格式转换
- `search` - 网络搜索

**响应格式**（成功）:
```json
{
  "success": true,
  "pattern_id": "summarize",
  "output": "总结后的文本...",
  "metadata": {
    "input_length": 1024,
    "output_length": 150,
    "duration_ms": 1638,
    "model": "mlx-community/Llama-3.2-1B-Instruct-4bit",
    "timestamp": "2026-01-21T12:00:00.000Z"
  }
}
```

**响应格式**（失败）:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数 'length' 的值 'invalid' 无效。允许值: ['short', 'medium', 'long']",
    "details": {
      "field": "length",
      "allowed_values": ["short", "medium", "long"]
    }
  }
}
```

**状态码**:

| 状态码 | 含义 | 场景 |
|--------|------|------|
| `200 OK` | 成功 | Pattern 执行成功 |
| `400 Bad Request` | 参数错误 | 无效 pattern_id、参数超出白名单 |
| `422 Unprocessable Entity` | 验证失败 | 文本超长、类型错误 |
| `429 Too Many Requests` | 速率限制 | 超过 60 req/min |
| `500 Internal Server Error` | 服务器错误 | LLM 模型错误、未知异常 |

---

### GET /

**功能**: 健康检查（简单）

**响应示例**:
```json
{
  "status": "ok",
  "version": "0.2.0",
  "timestamp": "2026-01-21T12:00:00.000Z"
}
```

---

### GET /health

**功能**: 详细健康状态（包含模型加载情况）

**响应示例**:
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "backend": {
    "uptime_seconds": 3600,
    "memory_mb": 26.56,
    "cpu_percent": 0.0
  },
  "models": {
    "mlx": {
      "loaded": true,
      "model_name": "mlx-community/Llama-3.2-1B-Instruct-4bit",
      "device": "apple_silicon"
    },
    "ollama": {
      "available": false,
      "models": []
    }
  },
  "patterns": ["summarize", "extract", "translate", "format", "search"]
}
```

---

## Pattern 参数详解

### 1. Summarize（文本总结）

**参数**:

| 参数 | 类型 | 默认值 | 允许值 | 说明 |
|------|------|--------|--------|------|
| `length` | `string` | `medium` | `short`, `medium`, `long` | 总结长度 |
| `style` | `string` | `paragraph` | `bullet`, `paragraph`, `headline` | 输出风格 |
| `language` | `string` | `zh-CN` | 见语言代码表 | 输出语言 |

**请求示例**:
```json
{
  "pattern_id": "summarize",
  "text": "MacCortex is a next-generation macOS personal AI infrastructure...",
  "parameters": {
    "length": "short",
    "style": "bullet",
    "language": "zh-CN"
  }
}
```

**输出示例**:
```
- MacCortex 是下一代 macOS AI 基础设施
- 集成 MLX 和 Ollama 双 LLM
- 提供 5 个 AI 模式：总结、提取、翻译、格式转换、搜索
```

---

### 2. Extract（信息提取）

**参数**:

| 参数 | 类型 | 默认值 | 允许值 | 说明 |
|------|------|--------|--------|------|
| `entity_types` | `array[string]` | `["person", "organization", "location"]` | `person`, `organization`, `location`, `date`, `email`, `phone` | 实体类型 |
| `extract_keywords` | `boolean` | `false` | `true`, `false` | 是否提取关键词 |
| `extract_contacts` | `boolean` | `false` | `true`, `false` | 是否提取联系方式 |
| `extract_dates` | `boolean` | `false` | `true`, `false` | 是否提取日期 |
| `language` | `string` | `zh-CN` | 见语言代码表 | 输入语言 |

**请求示例**:
```json
{
  "pattern_id": "extract",
  "text": "联系人：Alice Smith (alice@example.com)，Apple Inc. 工程师，位于 San Francisco。项目启动日期：2026-01-21。",
  "parameters": {
    "entity_types": ["person", "organization", "location", "date", "email"],
    "extract_contacts": true
  }
}
```

**输出示例**:
```json
{
  "entities": {
    "person": ["Alice Smith"],
    "organization": ["Apple Inc."],
    "location": ["San Francisco"],
    "date": ["2026-01-21"],
    "email": ["alice@example.com"]
  },
  "contacts": {
    "Alice Smith": {
      "email": "alice@example.com",
      "organization": "Apple Inc."
    }
  }
}
```

---

### 3. Translate（文本翻译）

**参数**:

| 参数 | 类型 | 默认值 | 允许值 | 说明 |
|------|------|--------|--------|------|
| `target_language` | `string` | `en-US` | 见语言代码表 | 目标语言（必需） |
| `source_language` | `string` | `auto` | `auto` + 语言代码 | 源语言（auto 自动检测） |
| `style` | `string` | `casual` | `formal`, `casual`, `technical` | 翻译风格 |

**请求示例**:
```json
{
  "pattern_id": "translate",
  "text": "MacCortex 是一个本地化的 AI 工具。",
  "parameters": {
    "target_language": "en-US",
    "source_language": "zh-CN",
    "style": "formal"
  }
}
```

**输出示例**:
```
MacCortex is a localized AI tool.
```

**已知限制**（Phase 2）:
- 当前模型（Llama-3.2-1B）翻译质量有限
- 长文本（> 200 字）可能出现不完整翻译
- Phase 3 将升级到 aya-23（23B）

---

### 4. Format（格式转换）

**参数**:

| 参数 | 类型 | 默认值 | 允许值 | 说明 |
|------|------|--------|--------|------|
| `from_format` | `string` | - | `json`, `yaml`, `csv`, `markdown`, `xml` | 源格式（必需） |
| `to_format` | `string` | - | `json`, `yaml`, `csv`, `markdown`, `xml` | 目标格式（必需） |
| `prettify` | `boolean` | `true` | `true`, `false` | 是否格式化输出 |

**请求示例**:
```json
{
  "pattern_id": "format",
  "text": "{\"name\":\"Alice\",\"age\":30}",
  "parameters": {
    "from_format": "json",
    "to_format": "yaml",
    "prettify": true
  }
}
```

**输出示例**:
```yaml
name: Alice
age: 30
```

---

### 5. Search（网络搜索）

**参数**:

| 参数 | 类型 | 默认值 | 允许值 | 说明 |
|------|------|--------|--------|------|
| `search_type` | `string` | `web` | `web`, `semantic`, `hybrid` | 搜索类型 |
| `engine` | `string` | `duckduckgo` | `duckduckgo` | 搜索引擎 |
| `num_results` | `integer` | `5` | `1-10` | 结果数量 |
| `language` | `string` | `zh-CN` | 见语言代码表 | 搜索语言 |

**请求示例**:
```json
{
  "pattern_id": "search",
  "text": "macOS 15 Sequoia 新特性",
  "parameters": {
    "search_type": "web",
    "engine": "duckduckgo",
    "num_results": 5,
    "language": "zh-CN"
  }
}
```

**输出示例**:
```json
{
  "query": "macOS 15 Sequoia 新特性",
  "results": [
    {
      "title": "macOS 15 Sequoia - Apple (中国大陆)",
      "url": "https://www.apple.com.cn/macos/sequoia/",
      "snippet": "macOS 15 Sequoia 带来窗口平铺、Safari 更新、密码应用..."
    }
  ],
  "summary": "macOS 15 Sequoia 主要新特性包括：窗口平铺、Safari 15 更新、密码应用、Apple Intelligence 集成..."
}
```

**注意**:
- DuckDuckGo 有速率限制（< 1s 间隔会触发）
- 实现了 5 分钟缓存机制
- 触发速率限制时自动降级到 Mock 搜索

---

## 错误代码

### 客户端错误（4xx）

| 错误代码 | HTTP 状态 | 含义 | 解决方法 |
|----------|-----------|------|----------|
| `INVALID_PATTERN_ID` | 400 | pattern_id 不在白名单 | 检查 pattern_id 拼写 |
| `VALIDATION_ERROR` | 400 | 参数值不在白名单 | 检查参数允许值 |
| `MISSING_REQUIRED_FIELD` | 422 | 缺少必需字段 | 添加 text 或 pattern_id |
| `TEXT_TOO_LONG` | 422 | 文本超过 50,000 字符 | 缩短输入或分批处理 |
| `RATE_LIMIT_EXCEEDED` | 429 | 超过 60 req/min | 等待 60 秒后重试 |

### 服务器错误（5xx）

| 错误代码 | HTTP 状态 | 含义 | 解决方法 |
|----------|-----------|------|----------|
| `MODEL_NOT_LOADED` | 500 | MLX 模型未加载 | 检查日志，重启 Backend |
| `PROMPT_INJECTION_DETECTED` | 500 | 检测到恶意输入 | 修改输入文本 |
| `LLM_GENERATION_ERROR` | 500 | LLM 推理失败 | 查看日志，可能需要重启 |
| `INTERNAL_ERROR` | 500 | 未知错误 | 提交 Bug 报告 |

### 错误响应示例

```json
{
  "success": false,
  "error": {
    "code": "TEXT_TOO_LONG",
    "message": "输入超过最大长度 (50,000 字符)",
    "details": {
      "input_length": 60000,
      "max_length": 50000
    }
  }
}
```

---

## 速率限制

### Phase 2: 基础速率限制

- **每 IP 限制**: 60 请求/分钟
- **全局并发**: 10 个并发请求
- **响应头**:
  ```
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 45
  X-RateLimit-Reset: 1705824000
  ```

### 超出限制时的响应

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "超过速率限制 (60 req/min)，请稍后重试",
    "retry_after_seconds": 60
  }
}
```

---

## 使用示例

### cURL 示例

**总结文本**:
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "summarize",
    "text": "MacCortex is a next-generation macOS personal AI infrastructure...",
    "parameters": {
      "length": "short",
      "style": "bullet"
    }
  }'
```

**搜索网络**:
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "search",
    "text": "Apple Intelligence 新特性",
    "parameters": {
      "num_results": 3,
      "language": "zh-CN"
    }
  }'
```

---

### Python 示例

```python
import requests
import json

# 1. 健康检查
response = requests.get("http://localhost:8000/health")
print(response.json())

# 2. 执行 Pattern
def execute_pattern(pattern_id, text, parameters=None):
    payload = {
        "pattern_id": pattern_id,
        "text": text,
        "parameters": parameters or {}
    }

    response = requests.post(
        "http://localhost:8000/execute",
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            return result["output"]
        else:
            raise Exception(f"Pattern 执行失败: {result['error']}")
    else:
        raise Exception(f"HTTP 错误 {response.status_code}")

# 使用示例
output = execute_pattern(
    pattern_id="summarize",
    text="MacCortex is...",
    parameters={"length": "short", "style": "bullet"}
)
print(output)
```

---

### Swift 示例（macOS）

```swift
import Foundation

struct PatternRequest: Codable {
    let pattern_id: String
    let text: String
    let parameters: [String: AnyCodable]
}

struct PatternResponse: Codable {
    let success: Bool
    let output: String?
    let metadata: Metadata?
    let error: ErrorDetail?

    struct Metadata: Codable {
        let duration_ms: Int
        let model: String
    }

    struct ErrorDetail: Codable {
        let code: String
        let message: String
    }
}

func executePattern(patternId: String, text: String, parameters: [String: Any] = [:]) async throws -> String {
    let url = URL(string: "http://localhost:8000/execute")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let payload = PatternRequest(
        pattern_id: patternId,
        text: text,
        parameters: parameters.mapValues { AnyCodable($0) }
    )

    request.httpBody = try JSONEncoder().encode(payload)

    let (data, response) = try await URLSession.shared.data(for: request)

    guard let httpResponse = response as? HTTPURLResponse,
          httpResponse.statusCode == 200 else {
        throw NSError(domain: "MacCortex", code: -1, userInfo: nil)
    }

    let result = try JSONDecoder().decode(PatternResponse.self, from: data)

    if result.success, let output = result.output {
        return output
    } else if let error = result.error {
        throw NSError(domain: "MacCortex", code: -1, userInfo: [
            NSLocalizedDescriptionKey: error.message
        ])
    }

    throw NSError(domain: "MacCortex", code: -1)
}

// 使用示例
Task {
    do {
        let summary = try await executePattern(
            patternId: "summarize",
            text: "MacCortex is...",
            parameters: ["length": "short", "style": "bullet"]
        )
        print(summary)
    } catch {
        print("错误: \(error)")
    }
}
```

---

## 附录

### 支持的语言代码

| 语言 | ISO 639-1 (短) | ISO 639-1 + ISO 3166-1 (全) |
|------|----------------|----------------------------|
| 中文（简体） | `zh` | `zh-CN` |
| 中文（繁体） | `zh` | `zh-TW` |
| 英语 | `en` | `en-US` |
| 日语 | `ja` | `ja-JP` |
| 韩语 | `ko` | `ko-KR` |
| 西班牙语 | `es` | `es-ES` |
| 法语 | `fr` | `fr-FR` |
| 德语 | `de` | `de-DE` |
| 俄语 | `ru` | `ru-RU` |
| 阿拉伯语 | `ar` | `ar-AR` |

**注意**: 两种格式均支持，推荐使用完整格式（如 `zh-CN`）。

---

### 相关文档

- [用户指南 (USER_GUIDE.md)](./USER_GUIDE.md) - 完整使用手册
- [常见问题 (FAQ.md)](./FAQ.md) - 安装、配置、故障排查
- [变更日志 (CHANGELOG.md)](./CHANGELOG.md) - 版本更新历史
- [Swagger UI](http://localhost:8000/docs) - 交互式 API 文档（需启动 Backend）

---

**文档版本**: v0.2.0
**最后更新**: 2026-01-21（Phase 2 Week 4 Day 19）
**维护者**: MacCortex 开发团队
