"""Phase 6 retriever 测试。"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.fusion import RetrievalHit
from app.services.metadata_filter import MetadataFilter
from app.services.retriever import HybridRetriever


@dataclass(slots=True)
class FakeEmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        assert text == "网络安全法 第一条"
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def search(self, query_vector, *, top_k: int, filters: MetadataFilter):
        assert query_vector == [0.1, 0.2, 0.3]
        assert top_k == 30
        assert filters.doc_type == ["law"]
        return [
            RetrievalHit(
                chunk_id="chunk-1",
                score=0.9,
                source="vector",
                chunk_text="第一条 为了规范网络安全工作，制定本法。",
                document_id="doc-1",
                version_id="ver-1",
                doc_title="网络安全法样例",
                doc_type="law",
            )
        ]


class FakeKeywordStore:
    def search(self, query: str, *, top_k: int, filters: MetadataFilter):
        assert query == "网络安全法 第一条"
        assert top_k == 30
        assert filters.doc_type == ["law"]
        return [
            RetrievalHit(
                chunk_id="chunk-1",
                score=0.7,
                source="keyword",
                chunk_text="第一条 为了规范网络安全工作，制定本法。",
                document_id="doc-1",
                version_id="ver-1",
                doc_title="网络安全法样例",
                doc_type="law",
            ),
            RetrievalHit(
                chunk_id="chunk-2",
                score=0.5,
                source="keyword",
                chunk_text="第二条 国家支持网络安全技术创新。",
                document_id="doc-1",
                version_id="ver-1",
                doc_title="网络安全法样例",
                doc_type="law",
            ),
        ]


def test_hybrid_retriever_returns_top_k_fused_chunks() -> None:
    retriever = HybridRetriever(
        embedding_service=FakeEmbeddingService(),
        vector_store=FakeVectorStore(),
        keyword_store=FakeKeywordStore(),
    )

    response = retriever.retrieve(
        query="网络安全法 第一条",
        top_k=1,
        filters=MetadataFilter.from_input({"doc_type": ["law"]}),
        debug=True,
    )

    assert response.query == "网络安全法 第一条"
    assert response.top_k == 1
    assert len(response.final_results) == 1
    assert response.final_results[0].chunk_id == "chunk-1"
    assert response.debug.vector_results
    assert response.debug.keyword_results
    assert response.debug.fused_results


def test_hybrid_retriever_rejects_empty_query() -> None:
    retriever = HybridRetriever(
        embedding_service=FakeEmbeddingService(),
        vector_store=FakeVectorStore(),
        keyword_store=FakeKeywordStore(),
    )

    try:
        retriever.retrieve(query="   ")
    except ValueError as exc:
        assert "query 不能为空" in str(exc)
    else:  # pragma: no cover - 测试必须抛错
        raise AssertionError("空 query 应抛出 ValueError")
