from pathlib import Path

import pytest
from starlette.exceptions import HTTPException

import src.server as server
from src.server import get_frontend_response


@pytest.fixture
def frontend_dist(tmp_path, monkeypatch):
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html>app</html>")
    (assets_dir / "index.js").write_text("console.log('app')")
    monkeypatch.setattr(server, "FRONTEND_DIST_DIR", dist_dir)
    return dist_dir


def test_get_frontend_response_serves_static_asset(frontend_dist):
    response = get_frontend_response("assets/index.js")

    assert Path(response.path) == frontend_dist / "assets" / "index.js"


def test_get_frontend_response_serves_index_for_root(frontend_dist):
    response = get_frontend_response()

    assert Path(response.path) == frontend_dist / "index.html"


def test_get_frontend_response_falls_back_to_index_for_spa_route(frontend_dist):
    response = get_frontend_response("groups/123")

    assert Path(response.path) == frontend_dist / "index.html"


@pytest.mark.parametrize("path", ["api", "api/missing", "metrics", "socket.io"])
def test_get_frontend_response_does_not_catch_reserved_paths(frontend_dist, path):
    with pytest.raises(HTTPException) as exc_info:
        get_frontend_response(path)

    assert exc_info.value.status_code == 404


def test_get_frontend_response_rejects_path_traversal(frontend_dist):
    with pytest.raises(HTTPException) as exc_info:
        get_frontend_response("../pyproject.toml")

    assert exc_info.value.status_code == 404


def test_get_frontend_response_returns_404_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "FRONTEND_DIST_DIR", tmp_path / "missing")

    with pytest.raises(HTTPException) as exc_info:
        get_frontend_response()

    assert exc_info.value.status_code == 404
    assert "Frontend build not found" in exc_info.value.detail


def test_unhandled_route_error_is_sent_to_posthog(monkeypatch):
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient

    mock_analytics = MagicMock()
    monkeypatch.setattr(server, "analytics", mock_analytics)

    async def boom():
        raise RuntimeError("boom")

    # Register ahead of the SPA catch-all route
    server.fastapi_app.add_api_route("/api/__boom", boom)
    routes = server.fastapi_app.router.routes
    routes.insert(0, routes.pop())
    try:
        client = TestClient(server.fastapi_app, raise_server_exceptions=False)
        response = client.get("/api/__boom")
    finally:
        routes.pop(0)

    assert response.status_code == 500
    mock_analytics.capture_exception.assert_called_once()
    args, kwargs = mock_analytics.capture_exception.call_args
    assert str(args[0]) == "boom"
    assert kwargs["properties"]["path"] == "/api/__boom"
