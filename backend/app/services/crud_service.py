"""Phase 1 最小 CRUD 辅助层。

本模块只提供数据库模型的基础创建与主键查询能力，
用于支撑 Phase 1 的持久化验证与后续 Phase 的最小复用。
"""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.eval_dataset import EvalDataset
from app.models.eval_run import EvalRun
from app.models.ingest_task import IngestTask

T = TypeVar("T")


def create_document(
    db: Session,
    *,
    title: str,
    doc_type: str,
    source_filename: str,
    storage_path: str,
    status: str = "active",
    security_domain: list[str] | None = None,
    tags: list[str] | None = None,
    current_version_id: uuid.UUID | None = None,
) -> Document:
    """创建逻辑文档记录。"""
    document = Document(
        title=title,
        doc_type=doc_type,
        source_filename=source_filename,
        storage_path=storage_path,
        status=status,
        security_domain=security_domain or [],
        tags=tags or [],
        current_version_id=current_version_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def create_document_version(
    db: Session,
    *,
    document_id: uuid.UUID,
    version_no: int,
    file_hash: str,
    file_size: int,
    mime_type: str,
    storage_path: str,
    version_status: str = "active",
    **extra: Any,
) -> DocumentVersion:
    """创建文档版本记录。"""
    version = DocumentVersion(
        document_id=document_id,
        version_no=version_no,
        file_hash=file_hash,
        file_size=file_size,
        mime_type=mime_type,
        storage_path=storage_path,
        version_status=version_status,
        **extra,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def create_chunk(
    db: Session,
    *,
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    chunk_index: int,
    chunk_type: str,
    text: str,
    normalized_text: str,
    chunk_hash: str,
    doc_type: str,
    doc_title: str,
    **extra: Any,
) -> Chunk:
    """创建 chunk 记录。"""
    chunk = Chunk(
        document_id=document_id,
        version_id=version_id,
        chunk_index=chunk_index,
        chunk_type=chunk_type,
        text=text,
        normalized_text=normalized_text,
        chunk_hash=chunk_hash,
        doc_type=doc_type,
        doc_title=doc_title,
        **extra,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def create_ingest_task(
    db: Session,
    *,
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    task_type: str,
    status: str,
    progress: int = 0,
    **extra: Any,
) -> IngestTask:
    """创建入库任务记录。"""
    ingest_task = IngestTask(
        document_id=document_id,
        version_id=version_id,
        task_type=task_type,
        status=status,
        progress=progress,
        **extra,
    )
    db.add(ingest_task)
    db.commit()
    db.refresh(ingest_task)
    return ingest_task


def create_eval_dataset(
    db: Session,
    *,
    name: str,
    description: str | None = None,
    source_path: str | None = None,
    status: str = "active",
) -> EvalDataset:
    """创建评测数据集记录。"""
    dataset = EvalDataset(
        name=name,
        description=description,
        source_path=source_path,
        status=status,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def create_eval_run(
    db: Session,
    *,
    dataset_id: uuid.UUID,
    status: str,
    total_count: int = 0,
    completed_count: int = 0,
    **extra: Any,
) -> EvalRun:
    """创建评测运行记录。"""
    run = EvalRun(
        dataset_id=dataset_id,
        status=status,
        total_count=total_count,
        completed_count=completed_count,
        **extra,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_by_id(db: Session, model: type[T], object_id: uuid.UUID) -> T | None:
    """按主键查询单个 ORM 对象。"""
    return db.get(model, object_id)
