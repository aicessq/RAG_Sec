"""Hash 工具（file_hash / chunk_hash）。

Phase 2 只实现文件级哈希：基于原始 bytes 计算 SHA-256，
用于 document_version.file_hash。
"""

from __future__ import annotations

import hashlib


def calculate_file_hash(file_bytes: bytes) -> str:
    """基于原始文件 bytes 计算 SHA-256。"""
    return hashlib.sha256(file_bytes).hexdigest()
