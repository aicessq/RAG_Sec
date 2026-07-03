"""document 相关 Pydantic schema。"""

from __future__ import annotations

from pydantic import BaseModel


class DocumentReplaceResponse(BaseModel):
    """Phase 9 replace 接口响应。"""

    document_id: str
    version_id: str
    task_id: str
    status: str


class DocumentDeleteResponse(BaseModel):
    """Phase 9 soft delete 接口响应。"""

    document_id: str
    status: str
    deactivated_chunk_count: int
