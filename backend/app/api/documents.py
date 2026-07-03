"""文档替换与删除接口。

Phase 9 开始补齐：
- `/documents/{document_id}/replace`
- `DELETE /documents/{document_id}`
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.document import DocumentDeleteResponse, DocumentReplaceResponse
from app.services.storage_service import StorageError
from app.services.update_service import (
    DocumentNotFoundError,
    FileUnchangedError,
    UpdateServiceError,
    process_replace,
    soft_delete_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{document_id}/replace", response_model=DocumentReplaceResponse)
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
    version_status: str = Form(default="active"),
    change_summary: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentReplaceResponse:
    """为已有 document 创建新版本。"""
    try:
        result = await process_replace(
            db=db,
            document_id=document_id,
            upload_file=file,
            version_status=version_status,
            change_summary=change_summary,
        )
        return DocumentReplaceResponse(
            document_id=str(result.document_id),
            version_id=str(result.version_id),
            task_id=str(result.task_id),
            status=result.status,
        )
    except FileUnchangedError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "file_unchanged",
                    "message": str(exc),
                    "details": {"document_id": document_id},
                }
            },
        ) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "not_found",
                    "message": str(exc),
                    "details": {"document_id": document_id},
                }
            },
        ) from exc
    except (UpdateServiceError, StorageError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "invalid_request",
                    "message": str(exc),
                    "details": {},
                }
            },
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "replace 失败，请稍后重试",
                    "details": {"reason": str(exc)},
                }
            },
        ) from exc


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentDeleteResponse:
    """软删除 document，并同步关闭检索可见性。"""
    try:
        result = soft_delete_document(db=db, document_id=document_id)
        return DocumentDeleteResponse(
            document_id=str(result.document_id),
            status=result.status,
            deactivated_chunk_count=result.deactivated_chunk_count,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "not_found",
                    "message": str(exc),
                    "details": {"document_id": document_id},
                }
            },
        ) from exc
    except UpdateServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "invalid_request",
                    "message": str(exc),
                    "details": {},
                }
            },
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "删除失败，请稍后重试",
                    "details": {"reason": str(exc)},
                }
            },
        ) from exc
