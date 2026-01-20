#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置文件
用于设置测试环境

Copyright (c) 2026 Yu Geng. All rights reserved.
"""

import sys
import os

# 添加 src 目录到 Python 路径
src_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, os.path.abspath(src_path))
