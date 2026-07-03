"""Phase 5 reranker 服务测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.reranker import DeterministicRerankerModel, RerankerService, RerankerServiceError


def test_reranker_service_loads_from_local_directory_with_fallback(tmp_path: Path) -> None:
    model_dir = tmp_path / "reranker-model"
    model_dir.mkdir()

    service = RerankerService.from_local_model(
        model_path=model_dir,
        batch_size=4,
        allow_fallback=True,
    )

    assert isinstance(service.model, DeterministicRerankerModel)
    assert service.batch_size == 4


def test_reranker_service_returns_scores_for_each_candidate() -> None:
    service = RerankerService(DeterministicRerankerModel(), batch_size=4)

    results = service.rerank(
        "什么是纵深防御",
        ["纵深防御是一种分层安全策略", "日志审计可以帮助溯源"],
    )

    assert len(results) == 2
    assert results[0].text == "纵深防御是一种分层安全策略"
    assert all(isinstance(item.score, float) for item in results)


def test_reranker_service_raises_when_model_path_missing_without_fallback(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing-reranker-model"

    with pytest.raises(RerankerServiceError):
        RerankerService.from_local_model(
            model_path=missing_dir,
            batch_size=4,
            allow_fallback=False,
        )
