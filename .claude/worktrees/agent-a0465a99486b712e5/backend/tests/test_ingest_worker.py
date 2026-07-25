"""Phase 4 入库 worker 测试。"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.ingest_task import IngestTask
from app.workers.ingest_worker import ingest_document_task

pytestmark = pytest.mark.integration


def create_ingest_task_records(
    db_session,
    *,
    file_path: Path,
    title: str,
    doc_type: str,
    mime_type: str,
    file_hash: str = "hash",
) -> tuple[Document, DocumentVersion, IngestTask]:
    """创建 worker 测试所需的 document/version/task 记录。"""
    document_id = uuid.uuid4()
    version_id = uuid.uuid4()
    task_id = uuid.uuid4()

    document = Document(
        id=document_id,
        title=title,
        doc_type=doc_type,
        source_filename=file_path.name,
        storage_path=str(file_path),
        status="active",
        security_domain=["compliance"],
        tags=[],
        current_version_id=None,
    )
    version = DocumentVersion(
        id=version_id,
        document_id=document_id,
        version_no=1,
        file_hash=file_hash,
        file_size=file_path.stat().st_size,
        mime_type=mime_type,
        storage_path=str(file_path),
        version_status="active",
    )
    task = IngestTask(
        id=task_id,
        document_id=document_id,
        version_id=version_id,
        task_type="ingest",
        status="queued",
        progress=0,
        message="等待处理",
    )

    db_session.add(document)
    db_session.add(version)
    db_session.add(task)
    db_session.flush()
    document.current_version_id = version_id
    db_session.commit()
    return document, version, task


def test_ingest_worker_persists_chunks_for_law_text(db_session) -> None:
    sample_path = Path(__file__).parent / "fixtures" / "law_sample.txt"
    document, version, task = create_ingest_task_records(
        db_session,
        file_path=sample_path,
        title="网络安全法样例",
        doc_type="law",
        mime_type="text/plain",
    )

    result = ingest_document_task(
        document_id=str(document.id),
        version_id=str(version.id),
        task_id=str(task.id),
        file_path=str(sample_path),
    )

    db_session.expire_all()
    refreshed_task = db_session.get(IngestTask, task.id)
    persisted_chunks = db_session.query(Chunk).filter(Chunk.version_id == version.id).order_by(Chunk.chunk_index).all()

    assert result["status"] == "completed"
    assert result["chunk_count"] >= 2
    assert refreshed_task is not None
    assert refreshed_task.status == "completed"
    assert "切分与 chunk 落库已完成" in (refreshed_task.message or "")
    assert persisted_chunks
    assert any(chunk.chunk_type == "parent" for chunk in persisted_chunks)
    assert any(chunk.chunk_type == "child" for chunk in persisted_chunks)
    assert all(chunk.chunk_hash for chunk in persisted_chunks)
    assert any(chunk.article_no for chunk in persisted_chunks if chunk.chunk_type == "child")


def test_ingest_worker_marks_failed_when_chunking_cannot_produce_output(db_session, monkeypatch) -> None:
    sample_path = Path(__file__).parent / "fixtures" / "plain_note.txt"
    document, version, task = create_ingest_task_records(
        db_session,
        file_path=sample_path,
        title="普通说明",
        doc_type="other",
        mime_type="text/plain",
    )

    monkeypatch.setattr("app.workers.ingest_worker.generate_chunks", lambda **kwargs: [])

    result = ingest_document_task(
        document_id=str(document.id),
        version_id=str(version.id),
        task_id=str(task.id),
        file_path=str(sample_path),
    )

    db_session.expire_all()
    refreshed_task = db_session.get(IngestTask, task.id)

    assert result["status"] == "failed"
    assert refreshed_task is not None
    assert refreshed_task.status == "failed"
    assert refreshed_task.error_message
    assert "失败" in (refreshed_task.message or "")
