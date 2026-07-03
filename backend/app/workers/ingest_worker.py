"""入库 worker。

Phase 5 在 Phase 4 基础上，把 chunk 落库链路升级为“自动建索引链路”：
- 解析
- 清洗
- 结构化切分
- chunk 落库 PostgreSQL
- 仅对 child chunk 建立 embedding / Qdrant / FTS 索引

本阶段仍不实现：
- 检索查询接口
- RRF 融合
- 查询改写
- answer generation
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
from app.services.index_service import IndexService
from app.services.parser_service import ParseError, parse_document
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.ingest_worker.ingest_document_task")
def ingest_document_task(*, document_id: str, version_id: str, task_id: str, file_path: str) -> dict[str, str | int]:
    """Phase 5 解析、清洗、切分、落库与建索引入口任务。"""
    logger.info(
        "收到 Phase 5 入库任务: document_id=%s version_id=%s task_id=%s file_path=%s",
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
            task.message = "Phase 5：开始执行文档解析、清洗、结构化切分、chunk 落库与索引建立"
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

        if document is None or version is None:
            raise ValueError("document 或 version 不存在，无法执行 Phase 5 入库任务")

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
        persisted_chunks: list[Chunk] = []
        for record in chunk_records:
            chunk = Chunk(**record)
            db.add(chunk)
            persisted_chunks.append(chunk)
        db.flush()

        index_service = IndexService.from_db(db, allow_embedding_fallback=True)
        index_result = index_service.build_chunk_indexes(persisted_chunks, version=version)
        db.commit()

        if task is not None:
            task.status = "completed"
            task.progress = 100
            task.message = (
                "Phase 5：解析、清洗、切分、chunk 落库与 child chunk 索引已完成，"
                "当前已具备索引能力，查询链路将在后续 Phase 实现"
            )
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
            "indexed_chunk_count": index_result.indexed_chunk_count,
        }
    except (ParseError, OSError, ValueError, RuntimeError) as exc:
        db.rollback()
        logger.exception("Phase 5 解析/切分/索引失败: %s", exc)
        task = db.get(IngestTask, UUID(task_id))
        if task is not None:
            task.status = "failed"
            task.error_message = str(exc)
            task.message = "Phase 5：文档解析、清洗、切分、chunk 落库或索引建立失败"
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
            "indexed_chunk_count": 0,
        }
    finally:
        db.close()


@celery_app.task(name="app.workers.ingest_worker.replace_document_task")
def replace_document_task(*, document_id: str, version_id: str, task_id: str, file_path: str) -> dict[str, str | int]:
    """Phase 9 replace 增量更新入口任务。"""
    logger.info(
        "收到 Phase 9 replace 任务: document_id=%s version_id=%s task_id=%s file_path=%s",
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
            task.error_message = None
            task.message = "Phase 9：开始执行 replace 增量更新"
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

        from app.services.update_service import apply_incremental_update

        result = apply_incremental_update(
            db=db,
            document_id=document_id,
            version_id=version_id,
            file_path=file_path,
        )
        if task is not None:
            task.status = "completed"
            task.progress = 100
            task.message = "Phase 9：replace 增量更新已完成"
            task.finished_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
        return {
            "document_id": document_id,
            "version_id": version_id,
            "task_id": task_id,
            "status": "completed",
            "added": int(result["added"]),
            "removed": int(result["removed"]),
            "unchanged": int(result["unchanged"]),
            "indexed_chunk_count": int(result["indexed_chunk_count"]),
        }
    except (ParseError, OSError, ValueError, RuntimeError) as exc:
        db.rollback()
        logger.exception("Phase 9 replace 增量更新失败: %s", exc)
        task = db.get(IngestTask, UUID(task_id))
        if task is not None:
            task.status = "failed"
            task.error_message = str(exc)
            task.message = "Phase 9：replace 增量更新失败"
            task.updated_at = datetime.now(timezone.utc)
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
        return {
            "document_id": document_id,
            "version_id": version_id,
            "task_id": task_id,
            "status": "failed",
            "added": 0,
            "removed": 0,
            "unchanged": 0,
            "indexed_chunk_count": 0,
        }
    finally:
        db.close()
