"""API 路由聚合。

设计说明（教学向）
==================

1. 为什么每个业务域一个 router 文件，再在这里聚合？
   - 单一职责：health / upload / documents / query 等各自维护自己的路由；
   - main.py 只需 include 一次聚合 router，启动代码保持干净；
   - 后续 Phase 新增接口时，只需新建对应文件并在本文件中追加一行 include。

2. 当前已聚合：
   - health：健康检查与就绪探针；
   - upload：Phase 2 新文档上传入口。
   后续 documents / query / admin / eval 等路由仍按阶段逐步接入。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import health, upload

api_router = APIRouter()
# 健康检查路由：/health 与 /health/ready 都在 health.router 内
api_router.include_router(health.router)
# Phase 2：启用新文档上传入口
api_router.include_router(upload.router)
