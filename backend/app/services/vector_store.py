"""Qdrant 向量存储封装。

Phase 5 负责把 child chunk 的向量与 payload 写入 Qdrant。
本模块只提供“索引写入能力”，不提前实现查询接口。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.config import get_settings
from app.dependencies import get_qdrant_client

try:  # pragma: no cover - 依赖安装与否取决于运行环境
    from qdrant_client.http.models import Distance, PointStruct, VectorParams
except ImportError:  # pragma: no cover
    Distance = None  # type: ignore[assignment]
    PointStruct = None  # type: ignore[assignment]
    VectorParams = None  # type: ignore[assignment]


class VectorStoreError(RuntimeError):
    """Vector store 操作异常。"""


class QdrantClientProtocol(Protocol):
    """统一约束当前模块会用到的 Qdrant 客户端能力。"""

    def collection_exists(self, collection_name: str) -> bool: ...

    def create_collection(self, *, collection_name: str, vectors_config: object) -> None: ...

    def upsert(self, *, collection_name: str, points: list[object], wait: bool) -> object: ...

    def retrieve(self, *, collection_name: str, ids: list[str], with_payload: bool, with_vectors: bool) -> list[object]: ...


@dataclass(slots=True)
class VectorPoint:
    """进入 Qdrant 前的统一 point 表达。"""

    chunk_id: str
    vector: list[float]
    payload: dict[str, Any]


class QdrantVectorStore:
    """Qdrant 写入封装。"""

    def __init__(
        self,
        client: QdrantClientProtocol,
        *,
        collection_name: str,
        vector_size: int,
        distance_metric: str,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance_metric = distance_metric

    @classmethod
    def from_settings(cls, *, client: QdrantClientProtocol | None = None) -> "QdrantVectorStore":
        """按全局配置构造 vector store。"""
        settings = get_settings()
        resolved_client = client or get_qdrant_client()
        if resolved_client is None:
            raise VectorStoreError("Qdrant 客户端不可用，无法初始化 vector store")
        return cls(
            resolved_client,
            collection_name=settings.qdrant_collection,
            vector_size=settings.embedding_vector_size,
            distance_metric=settings.qdrant_distance_metric,
        )

    def ensure_collection(self) -> None:
        """确保 Qdrant collection 已按当前配置创建。"""
        if Distance is None or VectorParams is None:
            raise VectorStoreError("qdrant-client 未安装，无法创建 collection")
        if self.client.collection_exists(self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=getattr(Distance, self.distance_metric),
            ),
        )

    def upsert_chunks(self, points: Sequence[VectorPoint]) -> int:
        """把 child chunk 向量写入 Qdrant。"""
        if PointStruct is None:
            raise VectorStoreError("qdrant-client 未安装，无法写入向量")
        if not points:
            return 0

        qdrant_points = [
            PointStruct(
                id=point.chunk_id,
                vector=point.vector,
                payload=dict(point.payload),
            )
            for point in points
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=qdrant_points,
            wait=True,
        )
        return len(qdrant_points)

    def get_chunks_by_ids(self, chunk_ids: Sequence[str | UUID]) -> list[Any]:
        """按 chunk_id 回查已写入 point。"""
        normalized_ids = [str(chunk_id) for chunk_id in chunk_ids]
        if not normalized_ids:
            return []
        return self.client.retrieve(
            collection_name=self.collection_name,
            ids=normalized_ids,
            with_payload=True,
            with_vectors=True,
        )
