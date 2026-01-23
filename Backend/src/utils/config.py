#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - Configuration
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20

应用配置管理（使用 pydantic-settings）
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    host: str = "localhost"
    port: int = 8000
    reload: bool = True
    log_level: str = "INFO"

    # CORS 配置
    cors_origins: list[str] = ["*"]

    # MLX 配置
    mlx_model: str = "mlx-community/Llama-3.2-1B-Instruct-4bit"
    mlx_max_tokens: int = 2048
    mlx_temperature: float = 0.7

    # Ollama 配置
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3:14b"

    # ChromaDB 配置
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "maccortex"

    # 性能配置
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='allow',  # 允许额外的环境变量（如 langchain_*, anthropic_api_key）
    )


# 全局配置实例
settings = Settings()
