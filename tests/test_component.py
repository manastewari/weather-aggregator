from datetime import datetime, timezone

import pytest

from tests.support import stub_weather

pytestmark = pytest.mark.component


def test_full_fetch_history_and_latest(full_app):
    client, stub = full_app
    stub_weather(stub)
    before = datetime.now(timezone.utc)
    first = client.post("/weather/fetch", params={"city": "Timisoara"})
    second = client.post("/weather/fetch", params={"city": "TIMISOARA"})
    assert first.status_code == second.status_code == 201
    reading = first.json()
    assert reading["city"] == "Timișoara"
    assert reading["temperature"] == 22.4
    assert reading["wind_speed"] == 14.2
    assert reading["description"] == "Overcast"
    assert before <= datetime.fromisoformat(reading["fetched_at"]) <= datetime.now(timezone.utc)
    assert client.get("/weather/timisoara").json() == [second.json(), reading]
    assert client.get("/weather/Timișoara/latest").json() == second.json()


@pytest.mark.parametrize("mode,status", [("missing", 404), ("failure", 502)])
def test_failure_does_not_persist(full_app, mode, status):
    client, stub = full_app
    stub_weather(stub, mode=mode)
    result = client.post("/weather/fetch", params={"city": "timisoara"})
    assert result.status_code == status
    assert "detail" in result.json()
    assert client.get("/weather/timisoara").json() == []
    assert client.get("/weather/timisoara/latest").status_code == 404


@pytest.mark.parametrize("city", ["", "   ", "a" * 101])
def test_invalid_city_is_rejected(full_app, city):
    client, _ = full_app
    assert client.post("/weather/fetch", params={"city": city}).status_code == 422


def test_empty_history_and_missing_latest(full_app):
    client, _ = full_app
    assert client.get("/weather/paris").json() == []
    assert client.get("/weather/paris/latest").status_code == 404
    assert client.post("/weather/fetch").status_code == 422
