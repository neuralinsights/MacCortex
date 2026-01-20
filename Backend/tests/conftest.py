#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - Pytest 配置
Phase 1.5 - Day 4-5

自动添加 src/ 到 Python 路径
"""

import sys
from pathlib import Path

# 添加 Backend/src 到 Python 路径
backend_root = Path(__file__).parent.parent
src_path = backend_root / "src"
src_path_str = str(src_path.absolute())

if src_path_str not in sys.path:
    sys.path.insert(0, src_path_str)
