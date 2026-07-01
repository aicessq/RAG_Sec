"""入库 worker。

Phase 2 只建立异步任务入口与占位状态流转；
真实解析/清洗/切分/索引链路在后续 Phase 才实现。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from app.db.session import SessionLocal
from app.models.ingest_task import IngestTask
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.ingest_worker.ingest_document_task")
def ingest_document_task(*, document_id: str, version_id: str, task_id: str, file_path: str) -> dict[str, str]:
    """Phase 2 占位入库任务。

    当前只验证：任务可以被异步投递，并把任务状态更新为 processing。
    真正的解析与入库工作在后续 Phase 补全。
    """
    logger.info(
        "收到 Phase 2 占位入库任务: document_id=%s version_id=%s task_id=%s file_path=%s",
        document_id,
        version_id,
        task_id,
        file_path,
    )

    db = SessionLocal()
    try:
        task = db.get(IngestTask, UUID(task_id))
        if task is not None:
            task.status = "processing"
            task.message = "Phase 2：任务已投递，真实解析/入库链路将在后续 Phase 实现"
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
        return {
            "document_id": document_id,
            "version_id": version_id,
            "task_id": task_id,
            "status": "processing",
        }
    finally:
        db.close()
