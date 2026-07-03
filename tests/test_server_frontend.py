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
