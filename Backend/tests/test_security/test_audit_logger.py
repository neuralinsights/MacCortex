#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 审计日志系统测试
Phase 1.5 - Day 4-5
创建时间: 2026-01-21

测试覆盖：
- PIIRedactor: 15+ 脱敏模式
- AuditLogger: 结构化日志 + GDPR 合规
"""

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from security.audit_logger import PIIRedactor, AuditLogger, get_audit_logger


class TestPIIRedactor:
    """测试 PII 脱敏器"""

    @pytest.fixture
    def redactor(self):
        """创建 PII 脱敏器实例"""
        return PIIRedactor()

    def test_email_redaction(self, redactor):
        """测试邮箱脱敏"""
        text = "联系我：user@example.com 或 admin@test.org"
        result = redactor.redact(text)
        assert "[EMAIL]" in result
        assert "user@example.com" not in result
        assert "admin@test.org" not in result

    def test_phone_us_redaction(self, redactor):
        """测试美国电话号码脱敏"""
        text = "电话：123-456-7890 或 987.654.3210"
        result = redactor.redact(text)
        assert "[PHONE]" in result
        assert "123-456-7890" not in result
        assert "987.654.3210" not in result

    def test_phone_international_redaction(self, redactor):
        """测试国际电话号码脱敏"""
        text = "国际电话：+1-555-123-4567 或 +86 138 1234 5678"
        result = redactor.redact(text)
        assert "[PHONE]" in result
        assert "+1-555-123-4567" not in result

    def test_ssn_redaction(self, redactor):
        """测试美国社会保障号脱敏"""
        text = "SSN: 123-45-6789"
        result = redactor.redact(text)
        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_passport_redaction(self, redactor):
        """测试护照号脱敏"""
        text = "护照：A1234567 或 AB12345678"
        result = redactor.redact(text)
        assert "[PASSPORT]" in result
        assert "A1234567" not in result

    def test_credit_card_redaction(self, redactor):
        """测试信用卡号脱敏"""
        text = "信用卡：4532-1234-5678-9010 或 5425 2334 3010 9903"
        result = redactor.redact(text)
        assert "[CREDIT_CARD]" in result
        assert "4532-1234-5678-9010" not in result
        assert "5425 2334 3010 9903" not in result

    def test_iban_redaction(self, redactor):
        """测试 IBAN 脱敏"""
        text = "IBAN: GB82WEST12345698765432"
        result = redactor.redact(text)
        assert "[IBAN]" in result
        assert "GB82WEST12345698765432" not in result

    def test_ipv4_redaction(self, redactor):
        """测试 IPv4 地址脱敏"""
        text = "服务器 IP：192.168.1.100 或 10.0.0.1"
        result = redactor.redact(text)
        assert "[IP_ADDRESS]" in result
        assert "192.168.1.100" not in result
        assert "10.0.0.1" not in result

    def test_ipv6_redaction(self, redactor):
        """测试 IPv6 地址脱敏"""
        text = "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        result = redactor.redact(text)
        assert "[IP_ADDRESS]" in result
        assert "2001:0db8:85a3:0000:0000:8a2e:0370:7334" not in result

    def test_mac_address_redaction(self, redactor):
        """测试 MAC 地址脱敏"""
        text = "MAC: 00:1A:2B:3C:4D:5E 或 00-1A-2B-3C-4D-5F"
        result = redactor.redact(text)
        assert "[MAC_ADDRESS]" in result
        assert "00:1A:2B:3C:4D:5E" not in result

    def test_api_key_redaction(self, redactor):
        """测试 API 密钥脱敏"""
        text = "api_key=abcdef1234567890abcdef1234567890"
        result = redactor.redact(text)
        assert "[API_KEY]" in result
        assert "abcdef1234567890abcdef1234567890" not in result

    def test_bearer_token_redaction(self, redactor):
        """测试 Bearer Token 脱敏"""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redactor.redact(text)
        assert "Bearer [TOKEN]" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_aws_key_redaction(self, redactor):
        """测试 AWS 密钥脱敏"""
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = redactor.redact(text)
        assert "[AWS_KEY]" in result
        assert "AKIAIOSFODNN7EXAMPLE" not in result

    def test_street_address_redaction(self, redactor):
        """测试街道地址脱敏"""
        text = "地址：123 Main Street 或 456 Park Avenue"
        result = redactor.redact(text)
        assert "[ADDRESS]" in result
        assert "123 Main Street" not in result

    def test_zip_code_redaction(self, redactor):
        """测试邮政编码脱敏"""
        text = "ZIP: 12345 或 12345-6789"
        result = redactor.redact(text)
        assert "[ZIP]" in result
        assert "12345" not in result

    def test_url_with_params_redaction(self, redactor):
        """测试带参数 URL 脱敏"""
        text = "URL: https://example.com/api?token=secret&user=admin"
        result = redactor.redact(text)
        assert "[URL_WITH_PARAMS]" in result
        assert "token=secret" not in result

    def test_text_truncation(self, redactor):
        """测试文本截断"""
        long_text = "a" * 300
        result = redactor.redact(long_text, keep_length=200)
        assert len(result) <= 220  # 200 + ...[TRUNCATED]
        assert "[TRUNCATED]" in result

    def test_redact_dict_simple(self, redactor):
        """测试字典脱敏（简单）"""
        data = {
            "email": "user@example.com",
            "phone": "123-456-7890",
            "name": "John Doe"
        }
        result = redactor.redact_dict(data)
        assert result["email"] == "[EMAIL]"
        assert result["phone"] == "[PHONE]"
        assert result["name"] == "John Doe"  # 非 PII 保持不变

    def test_redact_dict_nested(self, redactor):
        """测试字典脱敏（嵌套）"""
        data = {
            "user": {
                "email": "admin@test.com",
                "profile": {
                    "ssn": "123-45-6789"
                }
            }
        }
        result = redactor.redact_dict(data)
        assert result["user"]["email"] == "[EMAIL]"
        assert result["user"]["profile"]["ssn"] == "[SSN]"

    def test_redact_dict_with_list(self, redactor):
        """测试字典脱敏（包含列表）"""
        data = {
            "emails": ["user1@example.com", "user2@test.org"],
            "count": 2
        }
        result = redactor.redact_dict(data)
        assert result["emails"][0] == "[EMAIL]"
        assert result["emails"][1] == "[EMAIL]"
        assert result["count"] == 2

    def test_mixed_pii_redaction(self, redactor):
        """测试混合 PII 脱敏"""
        text = """
        联系信息：
        邮箱：user@example.com
        电话：+1-555-123-4567
        地址：123 Main Street, 12345
        信用卡：4532-1234-5678-9010
        """
        result = redactor.redact(text)
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "[ADDRESS]" in result
        assert "[ZIP]" in result
        assert "[CREDIT_CARD]" in result
        # 确保所有敏感信息被移除
        assert "user@example.com" not in result
        assert "4532-1234-5678-9010" not in result


class TestAuditLogger:
    """测试审计日志器"""

    @pytest.fixture
    def temp_log_dir(self):
        """创建临时日志目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def logger(self, temp_log_dir):
        """创建审计日志器实例"""
        return AuditLogger(
            log_dir=temp_log_dir,
            text_length=200,
            enable_pii_redaction=True
        )

    def test_logger_initialization(self, logger, temp_log_dir):
        """测试日志器初始化"""
        assert logger.log_dir == Path(temp_log_dir)
        assert logger.text_length == 200
        assert logger.enable_pii_redaction is True
        assert logger.pii_redactor is not None
        assert logger.log_dir.exists()

    def test_ip_hashing(self, logger):
        """测试 IP 哈希（GDPR 合规）"""
        ip = "192.168.1.100"
        hashed = logger._hash_ip(ip)

        # 验证哈希长度
        assert len(hashed) == 16

        # 验证哈希一致性
        assert hashed == logger._hash_ip(ip)

        # 验证不同 IP 产生不同哈希
        assert hashed != logger._hash_ip("10.0.0.1")

        # 验证哈希不可逆（不包含原 IP）
        assert ip not in hashed

    def test_log_file_creation(self, logger):
        """测试日志文件创建"""
        logger.log_event(
            event_type="test_event",
            metadata={"key": "value"}
        )

        # 验证日志文件存在
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        assert log_file.exists()

    def test_log_event_structure(self, logger):
        """测试日志事件结构"""
        logger.log_event(
            event_type="test_event",
            metadata={"action": "test", "value": 123},
            request_id="req-12345",
            client_ip="192.168.1.100"
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            line = f.readline()
            event = json.loads(line)

        # 验证结构
        assert event["event_type"] == "test_event"
        assert event["request_id"] == "req-12345"
        assert "timestamp" in event
        assert "client_ip_hash" in event
        assert event["action"] == "test"
        assert event["value"] == 123

    def test_pii_redaction_in_log(self, logger):
        """测试日志中的 PII 脱敏"""
        logger.log_event(
            event_type="user_action",
            metadata={
                "email": "user@example.com",
                "phone": "123-456-7890",
                "message": "正常消息"
            }
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            line = f.readline()
            event = json.loads(line)

        # 验证 PII 已脱敏
        assert event["email"] == "[EMAIL]"
        assert event["phone"] == "[PHONE]"
        assert event["message"] == "正常消息"

    def test_log_request_start(self, logger):
        """测试请求开始日志"""
        logger.log_request_start(
            request_id="req-001",
            method="POST",
            path="/api/test",
            client_ip="10.0.0.1"
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.readline())

        assert event["event_type"] == "request_start"
        assert event["method"] == "POST"
        assert event["path"] == "/api/test"
        assert event["request_id"] == "req-001"

    def test_log_request_end(self, logger):
        """测试请求结束日志"""
        logger.log_request_end(
            request_id="req-002",
            status_code=200,
            duration_ms=125.5,
            success=True,
            client_ip="10.0.0.2"
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.readline())

        assert event["event_type"] == "request_end"
        assert event["status_code"] == 200
        assert event["duration_ms"] == 125.5
        assert event["success"] is True

    def test_log_pattern_execution(self, logger):
        """测试 Pattern 执行日志"""
        logger.log_pattern_execution(
            request_id="req-003",
            pattern_id="summarize",
            input_length=1024,
            output_length=256,
            duration_ms=250.3,
            success=True,
            security_flags=["injection_detected"],
            client_ip="10.0.0.3"
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.readline())

        assert event["event_type"] == "pattern_execute"
        assert event["pattern_id"] == "summarize"
        assert event["input_length"] == 1024
        assert event["output_length"] == 256
        assert event["duration_ms"] == 250.3
        assert event["security_flags"] == ["injection_detected"]

    def test_log_security_event(self, logger):
        """测试安全事件日志"""
        logger.log_security_event(
            request_id="req-004",
            event_subtype="injection_attempt",
            severity="high",
            details={
                "pattern": "ignore previous instructions",
                "confidence": 0.95
            },
            client_ip="10.0.0.4"
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.readline())

        assert event["event_type"] == "security_event"
        assert event["subtype"] == "injection_attempt"
        assert event["severity"] == "high"
        assert event["pattern"] == "ignore previous instructions"
        assert event["confidence"] == 0.95

    def test_log_rotation(self, logger):
        """测试日志轮转（跨天）"""
        # 记录第一条日志
        logger.log_event("test1", {"day": 1})

        # 模拟日期变更（手动更新内部状态）
        from datetime import timedelta
        logger.current_date = None  # 强制重新获取日志文件

        # 记录第二条日志
        logger.log_event("test2", {"day": 2})

        # 验证日志文件存在
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        assert log_file.exists()

    def test_empty_ip_handling(self, logger):
        """测试空 IP 处理"""
        hashed = logger._hash_ip("")
        assert hashed == "unknown"

        hashed = logger._hash_ip(None)
        assert hashed == "unknown"

    def test_jsonl_format_validity(self, logger):
        """测试 JSONL 格式有效性"""
        # 记录多条日志
        for i in range(5):
            logger.log_event(
                f"event_{i}",
                {"index": i, "data": f"test_{i}"}
            )

        # 读取并验证每行都是有效 JSON
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # 每行都能解析为 JSON
                event = json.loads(line)
                assert "timestamp" in event
                assert "event_type" in event
                assert event["index"] == line_num - 1

    def test_disabled_pii_redaction(self, temp_log_dir):
        """测试禁用 PII 脱敏"""
        logger = AuditLogger(
            log_dir=temp_log_dir,
            enable_pii_redaction=False
        )

        logger.log_event(
            "test_event",
            {"email": "user@example.com"}
        )

        # 读取日志
        today = datetime.now(timezone.utc).date()
        log_file = logger.log_dir / f"audit-{today.isoformat()}.jsonl"
        with open(log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.readline())

        # PII 未脱敏
        assert event["email"] == "user@example.com"


class TestAuditLoggerSingleton:
    """测试审计日志器单例模式"""

    def test_get_audit_logger_singleton(self):
        """测试单例模式"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        # 验证是同一个实例
        assert logger1 is logger2

    def test_singleton_state_persistence(self):
        """测试单例状态持久化"""
        logger1 = get_audit_logger()
        logger1.test_attr = "test_value"

        logger2 = get_audit_logger()
        assert hasattr(logger2, "test_attr")
        assert logger2.test_attr == "test_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
