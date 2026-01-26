#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 审计日志系统
Phase 1.5 - Day 4-5
创建时间: 2026-01-21

结构化 JSON 审计日志 + PII 脱敏（GDPR/CCPA 合规）
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class PIIRedactor:
    """PII（个人可识别信息）脱敏器（GDPR/CCPA 合规）"""

    # 15+ PII 脱敏模式
    PATTERNS = {
        # 联系方式
        "email": (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL]",
        ),
        "phone_us": (
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "[PHONE]",
        ),
        "phone_international": (
            r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
            "[PHONE]",
        ),

        # 身份信息
        "ssn": (
            r"\b\d{3}-\d{2}-\d{4}\b",
            "[SSN]",
        ),
        "passport": (
            r"\b[A-Z]{1,2}\d{6,9}\b",
            "[PASSPORT]",
        ),

        # 金融信息
        "credit_card": (
            r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "[CREDIT_CARD]",
        ),
        "iban": (
            r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",
            "[IBAN]",
        ),

        # 网络信息
        "ipv4": (
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "[IP_ADDRESS]",
        ),
        "ipv6": (
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
            "[IP_ADDRESS]",
        ),
        "mac_address": (
            r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
            "[MAC_ADDRESS]",
        ),

        # 凭证信息
        "api_key": (
            r"(api[-_]?key|apikey|api_token|token)[\s]*[=:][\s]*['\"]?[\w\-]{20,}['\"]?",
            r"\1=[API_KEY]",
        ),
        "bearer_token": (
            r"Bearer\s+[\w\-\.]+",
            "Bearer [TOKEN]",
        ),
        "aws_key": (
            r"AKIA[0-9A-Z]{16}",
            "[AWS_KEY]",
        ),

        # 地址信息
        "street_address": (
            r"\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b",
            "[ADDRESS]",
        ),
        "zip_code": (
            r"\b\d{5}(?:-\d{4})?\b",
            "[ZIP]",
        ),

        # 其他敏感信息
        "url_with_params": (
            r"https?://[^\s]+\?[^\s]+",
            "[URL_WITH_PARAMS]",
        ),
    }

    def __init__(self):
        """初始化 PII 脱敏器"""
        # 编译所有正则表达式
        self._compiled_patterns = {}
        for name, (pattern, replacement) in self.PATTERNS.items():
            self._compiled_patterns[name] = (
                re.compile(pattern, re.IGNORECASE),
                replacement,
            )

    def redact(self, text: str, keep_length: int = 200) -> str:
        """
        脱敏文本中的 PII

        Args:
            text: 原始文本
            keep_length: 保留的最大字符长度（0 = 不限制）

        Returns:
            脱敏后的文本
        """
        if not text:
            return text

        # 截断文本（如果需要）
        if keep_length > 0 and len(text) > keep_length:
            text = text[:keep_length] + "...[TRUNCATED]"

        # 应用所有脱敏模式
        redacted = text
        for pattern, replacement in self._compiled_patterns.values():
            redacted = pattern.sub(replacement, redacted)

        return redacted

    def redact_dict(
        self, data: Dict[str, Any], keep_length: int = 200
    ) -> Dict[str, Any]:
        """
        脱敏字典中的 PII

        Args:
            data: 原始字典
            keep_length: 文本字段保留的最大长度

        Returns:
            脱敏后的字典
        """
        redacted = {}
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = self.redact(value, keep_length)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value, keep_length)
            elif isinstance(value, list):
                redacted[key] = [
                    self.redact(v, keep_length) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                redacted[key] = value
        return redacted


class AuditLogger:
    """审计日志器（结构化 JSON + PII 脱敏）"""

    def __init__(
        self,
        log_dir: Optional[str] = None,
        text_length: int = 200,
        enable_pii_redaction: bool = True,
    ):
        """
        初始化审计日志器

        Args:
            log_dir: 日志目录（默认：Backend/logs/）
            text_length: 记录的文本最大长度（0 = 不限制）
            enable_pii_redaction: 是否启用 PII 脱敏
        """
        # 设置日志目录（优先使用用户可写目录，避免只读文件系统问题）
        if log_dir is None:
            log_dir = os.getenv("AUDIT_LOG_DIR")
            if not log_dir:
                # 使用 macOS 标准日志目录
                home = os.path.expanduser("~")
                log_dir = os.path.join(home, "Library", "Logs", "MacCortex", "audit")
        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # 如果无法创建目录（如只读文件系统），使用临时目录
            import tempfile
            fallback_dir = os.path.join(tempfile.gettempdir(), "MacCortex", "audit")
            logger.warning(f"无法创建日志目录 {log_dir}: {e}, 回退到 {fallback_dir}")
            self.log_dir = Path(fallback_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # 配置参数
        self.text_length = int(os.getenv("AUDIT_LOG_TEXT_LENGTH", str(text_length)))
        self.enable_pii_redaction = enable_pii_redaction

        # PII 脱敏器
        self.pii_redactor = PIIRedactor() if enable_pii_redaction else None

        # 当前日志文件
        self.current_date = None
        self.log_file = None

        logger.info(
            f"✓ AuditLogger 初始化: dir={self.log_dir}, "
            f"text_length={self.text_length}, pii_redaction={enable_pii_redaction}"
        )

    def _get_log_file(self) -> Path:
        """获取当前日期的日志文件路径"""
        today = datetime.now(timezone.utc).date()

        # 检查是否需要轮转日志文件
        if today != self.current_date:
            self.current_date = today
            self.log_file = self.log_dir / f"audit-{today.isoformat()}.jsonl"

        return self.log_file

    def _hash_ip(self, ip: str) -> str:
        """哈希 IP 地址（GDPR 合规）"""
        if not ip:
            return "unknown"
        # 使用 SHA-256 哈希 IP 地址（不可逆）
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def log_event(
        self,
        event_type: str,
        metadata: Dict[str, Any],
        request_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> None:
        """
        记录审计事件（结构化 JSON）

        Args:
            event_type: 事件类型（如 "pattern_execute", "security_violation"）
            metadata: 事件元数据
            request_id: 请求 ID
            client_ip: 客户端 IP 地址
        """
        try:
            # 构建审计事件
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "request_id": request_id or "unknown",
            }

            # 添加哈希后的 IP（GDPR 合规）
            if client_ip:
                event["client_ip_hash"] = self._hash_ip(client_ip)

            # 处理元数据
            if self.pii_redactor and self.enable_pii_redaction:
                # PII 脱敏
                safe_metadata = self.pii_redactor.redact_dict(
                    metadata, keep_length=self.text_length
                )
            else:
                safe_metadata = metadata

            event.update(safe_metadata)

            # 写入日志文件（JSONL 格式）
            log_file = self._get_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    def log_request_start(
        self,
        request_id: str,
        method: str,
        path: str,
        client_ip: Optional[str] = None,
    ) -> None:
        """记录请求开始"""
        self.log_event(
            event_type="request_start",
            metadata={
                "method": method,
                "path": path,
            },
            request_id=request_id,
            client_ip=client_ip,
        )

    def log_request_end(
        self,
        request_id: str,
        status_code: int,
        duration_ms: float,
        success: bool,
        client_ip: Optional[str] = None,
    ) -> None:
        """记录请求结束"""
        self.log_event(
            event_type="request_end",
            metadata={
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "success": success,
            },
            request_id=request_id,
            client_ip=client_ip,
        )

    def log_pattern_execution(
        self,
        request_id: str,
        pattern_id: str,
        input_length: int,
        output_length: int,
        duration_ms: float,
        success: bool,
        security_flags: Optional[List[str]] = None,
        client_ip: Optional[str] = None,
    ) -> None:
        """记录 Pattern 执行"""
        self.log_event(
            event_type="pattern_execute",
            metadata={
                "pattern_id": pattern_id,
                "input_length": input_length,
                "output_length": output_length,
                "duration_ms": round(duration_ms, 2),
                "success": success,
                "security_flags": security_flags or [],
            },
            request_id=request_id,
            client_ip=client_ip,
        )

    def log_security_event(
        self,
        request_id: str,
        event_subtype: str,
        severity: str,
        details: Dict[str, Any],
        client_ip: Optional[str] = None,
    ) -> None:
        """记录安全事件"""
        self.log_event(
            event_type="security_event",
            metadata={
                "subtype": event_subtype,
                "severity": severity,
                **details,
            },
            request_id=request_id,
            client_ip=client_ip,
        )


# 全局单例
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志器（单例模式）"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
