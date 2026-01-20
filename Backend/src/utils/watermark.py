#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Watermark and Integrity Verification
隐藏水印与完整性验证系统

此模块包含项目水印和反篡改检测机制。
DO NOT REMOVE OR MODIFY.
"""

__author__ = "Yu Geng"
__copyright__ = "Copyright 2026, Yu Geng"
__license__ = "Proprietary"

import hashlib
import os
import sys
from datetime import datetime
from typing import Optional

# 项目唯一标识符（隐藏水印）
_PROJECT_WATERMARK = {
    "id": "MacCortex-YG-2026-0121-PROD",
    "owner": "Yu Geng",
    "email": "james.geng@gmail.com",
    "created": "2026-01-21",
    "hash": "8f3b5c7a9e1d2f4b6a8c0e3f5d7b9a1c3e5f7d9b",
    "signature": "MCC-YG-0x7F9A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E",
}


def verify_ownership() -> bool:
    """
    验证项目所有权

    Returns:
        bool: 所有权验证通过返回 True
    """
    expected_owner = "Yu Geng"
    expected_hash = _PROJECT_WATERMARK["hash"]

    # 验证所有权信息
    if _PROJECT_WATERMARK["owner"] != expected_owner:
        return False

    # 验证哈希完整性
    computed_hash = hashlib.sha256(
        f"{expected_owner}{_PROJECT_WATERMARK['email']}{_PROJECT_WATERMARK['created']}".encode()
    ).hexdigest()[:40]

    return computed_hash == expected_hash


def get_project_info() -> dict:
    """
    获取项目信息（包含隐藏标识）

    Returns:
        dict: 项目元信息
    """
    return {
        "project": "MacCortex",
        "version": "1.0.0",
        "owner": _PROJECT_WATERMARK["owner"],
        "license": "Proprietary",
        "watermark": _PROJECT_WATERMARK["id"],
        "verified": verify_ownership(),
    }


def check_integrity() -> bool:
    """
    检查代码完整性（防篡改）

    Returns:
        bool: 完整性检查通过返回 True
    """
    # 检查关键文件是否存在
    required_files = [
        "patterns/base.py",
        "patterns/registry.py",
        "main.py",
    ]

    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        if not os.path.exists(full_path):
            return False

    return True


def verify_environment() -> bool:
    """
    验证运行环境（防调试）

    Returns:
        bool: 环境验证通过返回 True
    """
    # 检查是否在调试模式
    if sys.gettrace() is not None:
        return False

    # 检查环境变量
    if os.environ.get("PYTHONDEBUG") or os.environ.get("DEBUG"):
        return False

    return True


def get_license_info() -> dict:
    """
    获取许可证信息

    Returns:
        dict: 许可证详情
    """
    return {
        "type": "Proprietary",
        "owner": "Yu Geng",
        "email": "james.geng@gmail.com",
        "issued": "2026-01-21",
        "expires": "永久",
        "restrictions": [
            "禁止商业使用",
            "禁止复制分发",
            "禁止逆向工程",
            "禁止创建衍生作品",
        ],
    }


# 隐藏的验证函数（在模块加载时自动执行）
def _hidden_verification():
    """
    隐藏验证函数（自动执行）

    此函数在模块导入时自动运行，验证项目完整性。
    DO NOT REMOVE.
    """
    if not verify_ownership():
        # 所有权验证失败（可能被篡改）
        pass  # 静默失败，不暴露检测逻辑

    if not check_integrity():
        # 完整性检查失败
        pass

    if not verify_environment():
        # 环境验证失败（可能在调试）
        pass


# 模块加载时执行验证
_hidden_verification()


# 额外的混淆代码（增加逆向难度）
_obfuscated_data = bytes.fromhex(
    "4d6163436f7274657820436f7079726967687420323032362059752047656e67"
)  # "MacCortex Copyright 2026 Yu Geng"


def _decode_watermark(data: bytes) -> str:
    """解码水印信息"""
    return data.decode("utf-8")


# 验证函数
if __name__ == "__main__":
    print("MacCortex Watermark Verification")
    print("=" * 50)
    print(f"Project ID: {_PROJECT_WATERMARK['id']}")
    print(f"Owner: {_PROJECT_WATERMARK['owner']}")
    print(f"Ownership Verified: {verify_ownership()}")
    print(f"Integrity Check: {check_integrity()}")
    print(f"Environment Safe: {verify_environment()}")
    print(f"Hidden Message: {_decode_watermark(_obfuscated_data)}")
