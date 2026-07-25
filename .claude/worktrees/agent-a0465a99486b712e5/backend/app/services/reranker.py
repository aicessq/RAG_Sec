"""本地 Reranker 服务（Qwen3 Reranker 进程内加载）。

Phase 5 先完成：
- 本地模型目录加载
- query + candidates 的统一调用接口
- 返回与输入候选一一对应的分数列表

注意：
- 本阶段只做真实服务封装，不接入查询链路；
- 为便于仓库在无模型权重环境下保持可测试，可显式允许 deterministic fallback；
- 默认仍要求优先加载本地真实模型。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.config import get_settings

try:  # pragma: no cover - 依赖安装与否取决于运行环境
    from sentence_transformers import CrossEncoder
except ImportError:  # pragma: no cover
    CrossEncoder = None  # type: ignore[assignment]


class RerankerModelProtocol(Protocol):
    """统一约束底层 reranker 模型的最小能力。"""

    def predict(self, sentences: list[tuple[str, str]], *, batch_size: int, show_progress_bar: bool) -> object: ...


class RerankerServiceError(RuntimeError):
    """Reranker 服务异常。"""


@dataclass(slots=True)
class RerankResult:
    """单条 rerank 结果。"""

    text: str
    score: float


class DeterministicRerankerModel:
    """测试 / 无模型权重场景下的确定性回退 reranker。"""

    def predict(self, sentences: list[tuple[str, str]], *, batch_size: int, show_progress_bar: bool) -> list[float]:
        del batch_size, show_progress_bar
        return [self._score_pair(query, candidate) for query, candidate in sentences]

    @staticmethod
    def _score_pair(query: str, candidate: str) -> float:
        digest = hashlib.sha256(f"{query}\n{candidate}".encode("utf-8")).digest()
        raw_value = int.from_bytes(digest[:8], byteorder="big", signed=False)
        return raw_value / 2**64


class RerankerService:
    """本地 reranker 服务封装。"""

    def __init__(self, model: RerankerModelProtocol, *, batch_size: int) -> None:
        self.model = model
        self.batch_size = batch_size

    @classmethod
    def from_local_model(
        cls,
        *,
        model_path: str | Path | None = None,
        batch_size: int | None = None,
        allow_fallback: bool = False,
    ) -> "RerankerService":
        """从本地目录加载 reranker 模型。"""
        settings = get_settings()
        resolved_path = Path(model_path or settings.reranker_model_path)
        resolved_batch_size = batch_size or settings.reranker_batch_size

        if CrossEncoder is None:
            if allow_fallback:
                return cls(DeterministicRerankerModel(), batch_size=resolved_batch_size)
            raise RerankerServiceError("sentence-transformers 未安装，无法加载本地 reranker 模型")

        if not resolved_path.exists() or not resolved_path.is_dir():
            if allow_fallback:
                return cls(DeterministicRerankerModel(), batch_size=resolved_batch_size)
            raise RerankerServiceError(f"reranker 模型目录不存在: {resolved_path}")

        try:
            model = CrossEncoder(str(resolved_path), trust_remote_code=True)
        except Exception as exc:  # noqa: BLE001
            if allow_fallback:
                return cls(DeterministicRerankerModel(), batch_size=resolved_batch_size)
            raise RerankerServiceError(f"reranker 模型加载失败: {resolved_path}") from exc

        return cls(model, batch_size=resolved_batch_size)

    def rerank(self, query: str, candidates: list[str]) -> list[RerankResult]:
        """返回与输入候选等长的打分结果。"""
        if not query.strip():
            raise RerankerServiceError("rerank query 不能为空")
        if not candidates:
            return []
        if any(not candidate.strip() for candidate in candidates):
            raise RerankerServiceError("rerank candidates 中存在空文本")

        pairs = [(query, candidate) for candidate in candidates]
        raw_scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        scores = [float(score) for score in raw_scores]  # type: ignore[arg-type]
        return [RerankResult(text=text, score=score) for text, score in zip(candidates, scores, strict=True)]


@lru_cache
def get_reranker_service(*, allow_fallback: bool = False) -> RerankerService:
    """返回 reranker 服务单例。"""
    return RerankerService.from_local_model(allow_fallback=allow_fallback)
