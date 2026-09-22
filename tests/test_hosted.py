import pytest
from fastapi.testclient import TestClient

from weather.hosted import create_hosted_app

pytestmark = pytest.mark.component


def test_hosted_ui_and_api_share_one_origin(db_url, tmp_path, monkeypatch):
    if db_url.startswith("sqlite:"):
        pytest.skip("Hosted deployment requires PostgreSQL; run without TEST_DATABASE_URL override")
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("STATIC_DIR", str(tmp_path))
    (tmp_path / "index.html").write_text("<h1>Weather journal</h1>", encoding="utf-8")
    with TestClient(create_hosted_app()) as client:
        assert "Weather journal" in client.get("/").text
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/weather/no-such-city").json() == []
        assert client.get("/weather/no-such-city/latest").status_code == 404
        assert client.get("/assets/missing.js").status_code == 404


@pytest.mark.parametrize("url", ["", "sqlite:///weather.db"])
def test_hosted_deployment_requires_persistent_database(monkeypatch, url):
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        create_hosted_app()
