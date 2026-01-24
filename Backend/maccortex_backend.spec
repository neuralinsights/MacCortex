# -*- mode: python ; coding: utf-8 -*-
# MacCortex Backend PyInstaller Spec
# 用于将 FastAPI 后端打包为独立可执行文件
# 嵌入 MacCortex.app/Contents/Resources/python_backend/

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# 收集子模块
langchain_hiddenimports = collect_submodules('langchain')
langchain_community_hiddenimports = collect_submodules('langchain_community')
langgraph_hiddenimports = collect_submodules('langgraph')

# 核心隐藏导入
hiddenimports = [
    # FastAPI / Uvicorn
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.responses',
    'starlette.websockets',

    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic_settings',

    # LangChain 核心
    'langchain_anthropic',
    'langchain_core',
    'langchain_core.messages',
    'langchain_core.prompts',
    'langchain_core.output_parsers',

    # LangGraph
    'langgraph.graph',
    'langgraph.graph.state',
    'langgraph.checkpoint',
    'langgraph.checkpoint.sqlite',

    # MLX (Apple Silicon ML)
    'mlx',
    'mlx.core',
    'mlx.nn',
    'mlx_lm',
    'mlx_lm.utils',

    # Ollama
    'ollama',

    # 工具库
    'loguru',
    'tenacity',
    'duckduckgo_search',
    'dotenv',
    'aiofiles',
    'httpx',
    'anyio',
    'sniffio',
    'h11',
    'httptools',
    'websockets',
    'rich',

    # Python 标准库（PyInstaller 可能遗漏）
    'multiprocessing',
    'multiprocessing.resource_tracker',
    'multiprocessing.popen_spawn_posix',
    'asyncio',
    'json',
    'sqlite3',
    'email.mime.text',

    # 内部模块
    'api',
    'api.swarm_routes',
    'patterns',
    'patterns.registry',
    'patterns.base',
    'patterns.extract',
    'patterns.format',
    'patterns.search',
    'patterns.summarize',
    'patterns.translate',
    'orchestration',
    'orchestration.graph',
    'orchestration.swarm_graph',
    'orchestration.state',
    'orchestration.model_router',
    'orchestration.hitl',
    'orchestration.cache',
    'orchestration.checkpoints',
    'orchestration.rollback',
    'orchestration.nodes',
    'orchestration.nodes.planner',
    'orchestration.nodes.coder',
    'orchestration.nodes.reviewer',
    'orchestration.nodes.researcher',
    'orchestration.nodes.reflector',
    'orchestration.nodes.tool_runner',
    'orchestration.nodes.stop_condition',
    'middleware',
    'middleware.security_middleware',
    'middleware.rate_limit_middleware',
    'security',
    'security.audit_logger',
    'security.input_validator',
    'security.output_validator',
    'security.prompt_guard',
    'security.rate_limiter',
    'security.security_config',
    'utils',
    'utils.config',
    'utils.cache',
    'utils.watermark',
]

# 合并自动收集的子模块
hiddenimports += langchain_hiddenimports
hiddenimports += langchain_community_hiddenimports
hiddenimports += langgraph_hiddenimports

# 去重
hiddenimports = list(set(hiddenimports))

# 数据文件
datas = [
    ('.env.example', '.'),
]

# 收集 MLX Metal 着色器（关键：mlx_metal 包含 .metallib 文件）
try:
    mlx_datas = collect_data_files('mlx')
    datas += mlx_datas
except Exception:
    pass

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型库
        'tkinter',
        'matplotlib',
        'PIL',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'chromadb',  # 已禁用（Python 3.14 兼容性问题）
        'torch',
        'tensorflow',
        'keras',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='maccortex_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # 不 strip（保持代码签名兼容性）
    upx=False,    # 不使用 UPX（macOS 签名不兼容）
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity='',        # 不在此签名（由 sign.sh 统一处理）
    entitlements_file='',        # 不在此设置（由 sign.sh 统一处理）
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='maccortex_backend',
)
