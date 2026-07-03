"""Phase 5 vector store 测试。"""

from __future__ import annotations

from types import SimpleNamespace

from app.services.vector_store import QdrantVectorStore, VectorPoint


class FakeQdrantClient:
    """最小可用的 Qdrant 测试替身。"""

    def __init__(self) -> None:
        self.exists = False
        self.created = []
        self.upserted = []
        self.points_by_id: dict[str, object] = {}

    def collection_exists(self, collection_name: str) -> bool:
        return self.exists

    def create_collection(self, *, collection_name: str, vectors_config: object) -> None:
        self.created.append((collection_name, vectors_config))
        self.exists = True

    def upsert(self, *, collection_name: str, points: list[object], wait: bool) -> object:
        self.upserted.append((collection_name, points, wait))
        for point in points:
            self.points_by_id[str(point.id)] = point
        return {"status": "ok"}

    def retrieve(self, *, collection_name: str, ids: list[str], with_payload: bool, with_vectors: bool) -> list[object]:
        del collection_name, with_payload, with_vectors
        return [self.points_by_id[item_id] for item_id in ids if item_id in self.points_by_id]


def test_vector_store_creates_collection_and_upserts_child_chunk() -> None:
    client = FakeQdrantClient()
    store = QdrantVectorStore(
        client,
        collection_name="cybersec_chunks",
        vector_size=4,
        distance_metric="Cosine",
    )

    store.ensure_collection()
    count = store.upsert_chunks(
        [
            VectorPoint(
                chunk_id="chunk-1",
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={
                    "chunk_id": "chunk-1",
                    "chunk_type": "child",
                    "doc_title": "网络安全法",
                    "is_active": True,
                },
            )
        ]
    )

    assert client.created
    assert count == 1
    assert client.upserted
    written_point = client.upserted[0][1][0]
    assert written_point.payload["chunk_id"] == "chunk-1"
    assert written_point.payload["chunk_type"] == "child"
    assert written_point.payload["is_active"] is True


def test_vector_store_can_retrieve_by_chunk_id() -> None:
    client = FakeQdrantClient()
    store = QdrantVectorStore(
        client,
        collection_name="cybersec_chunks",
        vector_size=4,
        distance_metric="Cosine",
    )
    point = SimpleNamespace(
        id="chunk-2",
        payload={"chunk_id": "chunk-2", "doc_title": "等保标准", "is_active": True},
        vector=[0.9, 0.1, 0.2, 0.3],
    )
    client.points_by_id["chunk-2"] = point

    results = store.get_chunks_by_ids(["chunk-2"])

    assert len(results) == 1
    assert results[0].payload["chunk_id"] == "chunk-2"
