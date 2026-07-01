"""FastAPI 应用入口。

设计说明（教学向）
==================

1. 为什么应用入口要尽量“薄”？
   规格 §3.2 要求“API 层不得写业务主逻辑”。main.py 只负责：
   - 创建 FastAPI 实例；
   - 配置日志；
   - 注册路由；
   - 注册全局异常处理（Phase 0 仅做最小兜底，统一错误响应在后续 Phase 完善）。
   真正的业务逻辑放在 services 层。

2. 为什么 /health 直接挂在根路径，而不是 /api/v1/health？
   规格 §17.1 明确为 `GET /health`（无前缀），常被容器编排直接探活，
   因此单独挂载在根路径。其余业务接口后续挂在 /api/v1 前缀下。

3. 启动方式：
   - 本地开发：uvicorn app.main:app --reload
   - Docker：容器内执行 uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import get_settings
from app.logging_config import setup_logging

# 在创建应用前完成日志初始化，保证后续 logger 输出格式一致
settings = get_settings()
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="网络安全领域 RAG 知识库系统（Phase 0：项目初始化骨架）",
    version="0.1.0",
)

# 业务路由统一挂在 /api/v1 前缀下（后续 Phase 的接口都遵循此前缀）
app.include_router(api_router, prefix="/api/v1")


# ---- 根路径健康检查 ----
# 规格 §17.1 要求 GET /health 返回 {"status":"ok"}，挂在根路径
@app.get("/health")
def health_root() -> dict[str, str]:
    """根路径存活探针，与规格 §17.1 完全一致。"""
    return {"status": "ok"}


# ---- 全局异常兜底 ----
# Phase 0 仅做最小统一兜底：未捕获的异常返回 internal_error，
# 避免把内部堆栈透出给用户（规格 §2.14 / §3.3）。
# 完整的统一错误响应体系在后续 Phase 落地。
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未处理的异常: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "服务器内部错误，请稍后重试",
                "details": {},
            }
        },
    )
