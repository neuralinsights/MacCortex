# MacCortex HITL 严格测试报告

> **测试时间**: 2026-01-22 13:40 UTC
> **测试范围**: Human-in-the-Loop 功能严格验证
> **测试数量**: 16 个
> **通过率**: 14/16 (87.5%)

---

## 执行摘要

针对用户质疑"有没有严格测试过？"，执行了额外的 16 个严格测试，覆盖：
- ✅ 边缘情况（无效输入、大小写、别名）
- ✅ 风险评估（高/中/低风险、敏感路径、危险代码）
- ✅ 消息格式化
- ✅ modify 操作
- ⚠️ 连续中断场景
- ⚠️ checkpointer 缺失场景

**发现的问题**: 2 个失败测试暴露了 HITL 实现的真实问题。

---

## 测试结果详情

### ✅ 通过的测试 (14/16)

#### 1. 边缘情况测试 (3/3)

| 测试用例 | 状态 | 验证内容 |
|----------|------|----------|
| `test_parse_invalid_user_decision` | ✅ PASSED | 无效输入（如 "xyz"）抛出 ValueError |
| `test_parse_user_decision_case_insensitive` | ✅ PASSED | APPROVE/Approve/approve 均识别为 "approve" |
| `test_parse_user_decision_aliases` | ✅ PASSED | yes/y/ok → approve; no/n/skip → deny |

**关键验证**:
```python
# 测试无效输入
with pytest.raises(ValueError) as exc_info:
    HITLHelper.parse_user_decision("xyz", "tool_execution")

assert "无效的决策" in str(exc_info.value)  # ✅ 通过

# 测试别名
decision = HITLHelper.parse_user_decision("y", "tool_execution")
assert decision["action"] == "approve"  # ✅ 通过
```

---

#### 2. 风险评估测试 (7/7)

| 测试用例 | 状态 | 验证内容 |
|----------|------|----------|
| `test_high_risk_tools` | ✅ PASSED | delete_file/execute_shell/send_email → high |
| `test_medium_risk_tools` | ✅ PASSED | write_file/move_file → medium |
| `test_low_risk_tools` | ✅ PASSED | read_file/search_web → low |
| `test_sensitive_path_escalation` | ✅ PASSED | write /etc/passwd → high（升级） |
| `test_code_risk_dangerous_keywords` | ✅ PASSED | exec/eval/DROP TABLE → high |
| `test_code_risk_long_code` | ✅ PASSED | >1000 字符 → medium |
| `test_code_risk_safe_code` | ✅ PASSED | 普通函数 → low |

**关键验证**:
```python
# 敏感路径升级风险
risk = RiskAssessor.assess_tool_risk(
    "write_file",  # 通常是 medium
    {"path": "/etc/passwd"}  # 敏感路径
)
assert risk == "high"  # ✅ 通过（升级为 high）

# 危险代码检测
code = "exec('malicious code')"
risk = RiskAssessor.assess_code_risk(code, "python")
assert risk == "high"  # ✅ 通过
```

---

#### 3. 消息格式化测试 (3/3)

| 测试用例 | 状态 | 验证内容 |
|----------|------|----------|
| `test_format_tool_execution_interrupt` | ✅ PASSED | 包含工具名、参数、风险标记（🟡） |
| `test_format_code_generation_interrupt` | ✅ PASSED | 包含语言、代码预览、风险标记（🟢） |
| `test_format_review_intervention_interrupt` | ✅ PASSED | 包含迭代次数、反馈 |

**关键验证**:
```python
message = HITLHelper.format_interrupt_message(prompt_data)

assert "tool_execution" in message  # ✅ 通过
assert "MEDIUM" in message  # ✅ 通过
assert "write_file" in message  # ✅ 通过
assert "🟡" in message  # ✅ 通过（medium 风险标记）
```

---

#### 4. modify 操作测试 (1/1)

| 测试用例 | 状态 | 验证内容 |
|----------|------|----------|
| `test_modify_tool_args` | ✅ PASSED | 修改参数后工具正确执行 |

**关键验证**:
```python
# 原始参数：创建 original.txt
# 修改参数：创建 modified.txt

user_decision = {
    "action": "modify",
    "modified_data": {
        "tool_args": {
            "path": f"{tmp_path}/modified.txt",  # 修改路径
            "content": "Modified Content"  # 修改内容
        }
    }
}

final_state = await graph.ainvoke(Command(resume=user_decision), thread)

assert (tmp_path / "modified.txt").exists()  # ✅ 通过
assert not (tmp_path / "original.txt").exists()  # ✅ 通过
```

---

### ❌ 失败的测试 (2/16)

#### 失败 1: 连续中断场景（批准 → 拒绝）

**测试**: `test_approve_then_deny`
**状态**: ❌ FAILED
**失败原因**: Reflector 评估逻辑问题

**测试场景**:
```python
# 两个工具任务
# 第一个：批准 → 文件应该创建
# 第二个：拒绝 → 文件应该不创建

# 第一次审批
await graph.ainvoke(Command(resume={"action": "approve", ...}))

# 第二次审批
final_state = await graph.ainvoke(Command(resume={"action": "deny", ...}))

# 验证
assert final_state["subtask_results"][0]["passed"] is True  # ✅ 通过
assert final_state["subtask_results"][1]["passed"] is False  # ❌ 失败
```

**实际结果**:
```python
AssertionError: assert False is True
# subtask_results[1]["passed"] = True（预期是 False）
```

**根因分析**:
- ToolRunner 正确标记了第二个任务为失败（用户拒绝）
- 但 Reflector 可能覆盖了这个状态
- 需要检查 Reflector 是否修改了 subtask_results

**影响**: 🟡 **中等**
- HITL 核心逻辑正确（工具未执行）
- 但最终状态报告不准确（显示成功实际失败）

---

#### 失败 2: checkpointer 缺失场景 🔴

**测试**: `test_hitl_requires_checkpointer`
**状态**: ❌ FAILED
**失败原因**: 预期抛出异常，实际静默失败

**测试场景**:
```python
# 创建 graph WITHOUT checkpointer
graph = create_full_swarm_graph(
    workspace_path=tmp_path,
    checkpointer=None,  # ← 没有 checkpointer
    tool_runner={"require_approval": True}  # ← 启用 HITL
)

# 预期：应该抛出明确错误
with pytest.raises(Exception) as exc_info:
    await graph.ainvoke(state)

assert "checkpointer" in str(exc_info.value).lower()  # ❌ 失败
```

**实际结果**:
```
Failed: DID NOT RAISE <class 'Exception'>
```

**手动验证结果**:
```bash
$ python /tmp/test_no_checkpointer.py

Status: executing（卡在执行中，不是 completed）
File exists: False（好消息：文件未创建）
IndexError: list index out of range（错误，但不清晰）
```

**根因分析**:
- `interrupt()` 在没有 checkpointer 时**不会抛出明确错误**
- 工作流卡在 "executing" 状态
- 后续访问 subtask_results 时抛出 IndexError（不清晰）
- 文件未创建（好消息），但错误提示不友好（坏消息）

**影响**: 🔴 **严重**
- 用户配置错误时没有清晰的错误提示
- 调试困难（IndexError 不说明根本原因）
- 应该在 Graph 创建时就检查 checkpointer

**建议修复**:
```python
# src/orchestration/swarm_graph.py

def create_full_swarm_graph(
    workspace_path: Path,
    checkpointer=None,
    tool_runner: dict = None,
    ...
):
    # ← 添加验证
    if tool_runner and tool_runner.get("require_approval") and not checkpointer:
        raise ValueError(
            "HITL requires checkpointer. "
            "Set require_approval=False or provide a checkpointer (e.g., InMemorySaver())"
        )

    # 继续创建 graph...
```

---

## 当前测试覆盖度总结

### 已覆盖 ✅

| 测试类别 | 测试数量 | 通过率 | 状态 |
|----------|----------|--------|------|
| **基础 HITL 流程** | 5/5 | 100% | ✅ 优秀 |
| **边缘情况** | 3/3 | 100% | ✅ 优秀 |
| **风险评估** | 7/7 | 100% | ✅ 优秀 |
| **消息格式化** | 3/3 | 100% | ✅ 优秀 |
| **modify 操作** | 1/1 | 100% | ✅ 优秀 |
| **连续中断** | 0/1 | 0% | ❌ 需修复 |
| **checkpointer 验证** | 0/1 | 0% | ❌ 需修复 |

**总计**: 19/21 (90.5%)

---

### 未覆盖 ❌

| 测试场景 | 优先级 | 风险等级 |
|----------|--------|----------|
| **跨进程恢复** | P0 | 🔴 高 |
| **检查点持久化（MemorySaver）** | P0 | 🔴 高 |
| **真实 LLM 调用** | P1 | 🟡 中 |
| **CLI 工具端到端测试** | P1 | 🟡 中 |
| **网络中断恢复** | P2 | 🟡 中 |
| **并发中断** | P2 | 🟡 中 |
| **工具执行超时后的中断状态** | P2 | 🟡 中 |
| **性能测试（100+ 中断）** | P3 | 🟢 低 |

---

## 关键问题与建议

### 问题 1: checkpointer 缺失未验证 🔴

**当前行为**:
- 没有 checkpointer 时，`interrupt()` 静默失败
- 工作流卡在 "executing" 状态
- 错误信息不清晰（IndexError）

**建议修复**:
```python
# src/orchestration/swarm_graph.py 添加验证
if tool_runner and tool_runner.get("require_approval") and not checkpointer:
    raise ValueError(
        "HITL requires checkpointer. Set require_approval=False or provide checkpointer."
    )
```

**优先级**: 🔴 P0（立即修复）

---

### 问题 2: Reflector 覆盖 subtask_results 🟡

**当前行为**:
- ToolRunner 正确标记任务失败（用户拒绝）
- Reflector 可能覆盖了这个状态
- 最终报告显示任务成功（不准确）

**建议修复**:
- 检查 Reflector 逻辑，确保不覆盖已有的 subtask_results
- 或者在 ToolRunner 中添加 "immutable" 标记

**优先级**: 🟡 P1（下一次迭代修复）

---

### 问题 3: CLI 工具未端到端测试 ⚠️

**当前状态**:
- `run_swarm_hitl.py` 创建完成
- 但因缺少 API key，从未实际运行
- 交互逻辑、用户输入解析未验证

**建议**:
- 使用 Mock LLM 运行一次完整的交互流程
- 或者配置 API key 进行真实测试

**优先级**: 🟡 P1（Week 5 验收前完成）

---

### 问题 4: 缺少跨进程恢复测试 🔴

**当前状态**:
- 所有测试都在单一进程内完成
- 没有测试：关闭程序 → 重启 → 恢复中断

**建议**:
- 使用 `MemorySaver` 替代 `InMemorySaver`
- 测试持久化检查点的恢复

**优先级**: 🔴 P0（Week 5 验收前必须完成）

---

## 测试通过率总结

| 测试套件 | 测试数量 | 通过率 | 状态 |
|----------|----------|--------|------|
| **基础测试（test_hitl.py）** | 5/5 | 100% | ✅ 优秀 |
| **严格测试（test_hitl_strict.py）** | 14/16 | 87.5% | ⚠️ 良好（需修复 2 个） |
| **总计** | 19/21 | **90.5%** | ⚠️ 良好（但有关键问题） |

---

## 结论

### ✅ 已验证的功能
- HITL 核心流程（approve/deny/abort）
- 风险评估系统（准确率 100%）
- 边缘情况处理（无效输入、大小写、别名）
- modify 操作
- 消息格式化

### ⚠️ 存在的问题
1. 🔴 **checkpointer 缺失未验证**（P0，立即修复）
2. 🟡 **Reflector 覆盖 subtask_results**（P1，下一次迭代）
3. ⚠️ **CLI 工具未端到端测试**（P1，Week 5 前完成）
4. 🔴 **缺少跨进程恢复测试**（P0，Week 5 前完成）

### 用户的质疑是否合理？
**是的**，用户的质疑非常合理。虽然基础测试通过率 100%，但：
- CLI 工具未实际运行
- checkpointer 缺失场景未验证
- 缺少跨进程恢复测试
- 缺少真实 LLM 调用测试

**当前测试严格度评分**: 6/10
- 单元测试：8/10 ✅
- 集成测试：7/10 ✅
- 端到端测试：3/10 ❌
- 边缘情况：8/10 ✅
- 真实场景：2/10 ❌

---

## 下一步行动

### 立即修复（P0）
1. **添加 checkpointer 验证**
   ```python
   # 在 create_full_swarm_graph() 中添加：
   if tool_runner.get("require_approval") and not checkpointer:
       raise ValueError("HITL requires checkpointer")
   ```

2. **跨进程恢复测试**
   - 使用 `MemorySaver` 持久化检查点
   - 测试：执行 → 中断 → 关闭 → 重启 → 恢复

### Week 5 验收前完成（P1）
3. **CLI 工具端到端测试**
   - 配置 API key 或使用 Mock LLM
   - 运行完整交互流程

4. **修复 Reflector 覆盖问题**
   - 检查 Reflector 逻辑
   - 确保 subtask_results 不被覆盖

---

**报告时间**: 2026-01-22 13:40 UTC
**报告作者**: Claude Code (Sonnet 4.5)
**测试工具**: pytest 9.0.2
**测试环境**: macOS Darwin 25.2.0, Python 3.14.2
