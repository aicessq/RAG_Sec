"""API 路由聚合。

设计说明（教学向）
==================

1. 为什么每个业务域一个 router 文件，再在这里聚合？
   - 单一职责：health / upload / documents / query 等各自维护自己的路由；
   - main.py 只需 include 一次聚合 router，启动代码保持干净；
   - 后续 Phase 新增接口时，只需新建对应文件并在本文件中追加一行 include。

2. Phase 0 只聚合 health；其余路由文件目前是 TODO 占位，不 include，
   避免引入未实现的路由导致启动报错或超范围。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import health

api_router = APIRouter()
# 健康检查路由：/health 与 /health/ready 都在 health.router 内
api_router.include_router(health.router)
