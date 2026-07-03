"""混合检索服务（向量 + 关键词 + RRF）。

Phase 6 负责第一次把“已索引 child chunk”升级为“可查询并返回的检索结果”。
本模块只做基础检索链路，不提前实现 answer generation。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.fusion import FusedRetrievalHit, RetrievalHit, reciprocal_rank_fusion
from app.services.keyword_store import KeywordStore
from app.services.metadata_filter import MetadataFilter
from app.services.vector_store import QdrantVectorStore


@dataclass(slots=True)
class RetrievalDebugInfo:
    """调试接口输出的检索明细。"""

    vector_results: list[RetrievalHit] = field(default_factory=list)
    keyword_results: list[RetrievalHit] = field(default_factory=list)
    fused_results: list[FusedRetrievalHit] = field(default_factory=list)


@dataclass(slots=True)
class RetrievalResponse:
    """混合检索服务输出。"""

    query: str
    top_k: int
    final_results: list[FusedRetrievalHit]
    debug: RetrievalDebugInfo


class HybridRetriever:
    """Phase 6 混合检索服务。"""

    def __init__(
        self,
        *,
        embedding_service: EmbeddingService,
        vector_store: QdrantVectorStore,
        keyword_store: KeywordStore,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.keyword_store = keyword_store

    @classmethod
    def from_db(
        cls,
        db: Session,
        *,
        embedding_service: EmbeddingService | None = None,
        vector_store: QdrantVectorStore | None = None,
        allow_embedding_fallback: bool = False,
    ) -> "HybridRetriever":
        """按当前数据库会话构造检索服务。"""
        return cls(
            embedding_service=embedding_service or get_embedding_service(allow_fallback=allow_embedding_fallback),
            vector_store=vector_store or QdrantVectorStore.from_settings(),
            keyword_store=KeywordStore.from_db(db),
        )

    def retrieve(
        self,
        *,
        query: str,
        top_k: int = 5,
        filters: MetadataFilter | None = None,
        debug: bool = False,
    ) -> RetrievalResponse:
        """执行向量检索 + 关键词检索 + RRF 融合。"""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query 不能为空")

        effective_filters = filters or MetadataFilter()
        query_vector = self.embedding_service.embed_text(normalized_query)
        vector_results = self.vector_store.search(query_vector, top_k=30, filters=effective_filters)
        keyword_results = self.keyword_store.search(normalized_query, top_k=30, filters=effective_filters)
        fused_results = reciprocal_rank_fusion(vector_results, keyword_results)
        final_results = fused_results[:top_k]
        debug_info = RetrievalDebugInfo(
            vector_results=vector_results if debug else [],
            keyword_results=keyword_results if debug else [],
            fused_results=fused_results if debug else [],
        )
        return RetrievalResponse(
            query=normalized_query,
            top_k=top_k,
            final_results=final_results,
            debug=debug_info,
        )
