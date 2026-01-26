#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - Pytest 配置
Phase 1.5 - Day 4-5

自动添加项目路径到 Python 路径
"""

import sys
from pathlib import Path

# 添加 Backend 根目录到 Python 路径（支持 from src.xxx 导入）
backend_root = Path(__file__).parent.parent
backend_root_str = str(backend_root.absolute())

if backend_root_str not in sys.path:
    sys.path.insert(0, backend_root_str)

# 同时添加 src/ 目录（支持 from xxx 导入，如 from orchestration.xxx）
src_path = backend_root / "src"
src_path_str = str(src_path.absolute())

if src_path_str not in sys.path:
    sys.path.insert(0, src_path_str)
