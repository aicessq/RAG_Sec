"""pytest 公共夹具。

设计说明（教学向）
==================

1. conftest.py 是 pytest 的“全局夹具文件”，其中的 fixture 对所有测试可见，
   无需 import 即可使用。
2. 这里提供 `client`：基于 FastAPI TestClient 的测试客户端，
   可以在不启动真实 HTTP 服务的情况下直接调用路由。
3. TestClient 不依赖外部基础设施（PG/Redis/Qdrant），因此 /health 这类
   纯进程内接口的单元测试可以稳定通过。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 把 backend 目录加入 sys.path，使得 `import app.main` 在从项目根运行 pytest 时可用
BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture()
def client() -> TestClient:
    """返回 FastAPI 测试客户端。"""
    # 延迟 import，确保 sys.path 已被调整
    from app.main import app

    return TestClient(app)
