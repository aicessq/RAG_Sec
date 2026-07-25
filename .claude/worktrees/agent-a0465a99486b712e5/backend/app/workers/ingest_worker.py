"""入库 worker。

Phase 4 在 Phase 3 解析/清洗基础上，新增：
- 结构化切分
- parent-child chunk 生成
- chunk 落库 PostgreSQL

本阶段仍不实现 embedding / vector store / keyword index / query 逻辑。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from app.db.session import SessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.ingest_task import IngestTask
from app.services.chunk_service import build_chunk_records, generate_chunks
from app.services.cleaner_service import clean_parsed_document
from app.services.parser_service import ParseError, parse_document
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.ingest_worker.ingest_document_task")
def ingest_document_task(*, document_id: str, version_id: str, task_id: str, file_path: str) -> dict[str, str | int]:
    """Phase 4 解析、清洗、切分与 chunk 落库入口任务。"""
    logger.info(
        "收到 Phase 4 入库任务: document_id=%s version_id=%s task_id=%s file_path=%s",
        document_id,
        version_id,
        task_id,
        file_path,
    )

    db = SessionLocal()
    try:
        task = db.get(IngestTask, UUID(task_id))
        document = db.get(Document, UUID(document_id))
        version = db.get(DocumentVersion, UUID(version_id))

        if task is not None:
            task.status = "processing"
            task.error_message = None
            task.message = "Phase 4：开始执行文档解析、清洗、结构化切分与 chunk 落库"
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

        if document is None or version is None:
            raise ValueError("document 或 version 不存在，无法执行 Phase 4 入库任务")

        parsed_document = parse_document(file_path, title=document.title)
        cleaned_document = clean_parsed_document(parsed_document)
        chunk_drafts = generate_chunks(
            document=cleaned_document,
            doc_type=document.doc_type,
            document_id=document_id,
            version_id=version_id,
            file_hash=version.file_hash,
            doc_title=document.title,
        )
        if not chunk_drafts:
            raise ValueError("切分结果为空，无法写入 chunk")

        existing_chunks = db.query(Chunk).filter(Chunk.version_id == UUID(version_id)).all()
        for chunk in existing_chunks:
            db.delete(chunk)
        db.flush()

        chunk_records = build_chunk_records(
            drafts=chunk_drafts,
            document_id=document.id,
            version_id=version.id,
            doc_type=document.doc_type,
            doc_title=document.title,
            security_domain=document.security_domain,
        )
        for record in chunk_records:
            db.add(Chunk(**record))
        db.commit()

        if task is not None:
            task.status = "completed"
            task.progress = 60
            task.message = "Phase 4：解析、清洗、切分与 chunk 落库已完成，索引阶段将在后续 Phase 实现"
            task.finished_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

        return {
            "document_id": document_id,
            "version_id": version_id,
            "task_id": task_id,
            "status": "completed",
            "page_count": len(cleaned_document.pages),
            "chunk_count": len(chunk_records),
        }
    except (ParseError, OSError, ValueError) as exc:
        logger.exception("Phase 4 解析/切分失败: %s", exc)
        task = db.get(IngestTask, UUID(task_id))
        if task is not None:
            task.status = "failed"
            task.error_message = str(exc)
            task.message = "Phase 4：文档解析、清洗、切分或 chunk 落库失败"
            task.updated_at = datetime.now(timezone.utc)
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
        return {
            "document_id": document_id,
            "version_id": version_id,
            "task_id": task_id,
            "status": "failed",
            "page_count": 0,
            "chunk_count": 0,
        }
    finally:
        db.close()
