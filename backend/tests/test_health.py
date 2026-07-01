"""健康检查接口测试。

对应验收项：GET /health 返回 200 且 body 为 {"status": "ok"}。
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """/health 应返回 200 且 body 为 {"status":"ok"}。"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_shape(client: TestClient) -> None:
    """/health/ready 应返回 200，且包含三个组件状态字段。

    注意：本测试只校验“结构正确”，不要求组件真的连上，
    因为 CI/本地可能没有运行 PG/Redis/Qdrant。
    组件真实连通性由带 integration 标记的集成测试覆盖。
    """
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    components = body["components"]
    # 三个基础设施组件必须都出现在结果中
    assert set(components.keys()) == {"postgres", "redis", "qdrant"}
    for name, info in components.items():
        assert "connected" in info
        assert isinstance(info["connected"], bool)
