"""Shared infrastructure for component tests and Behave; one container per run."""
from contextlib import contextmanager
import os

import responses
from responses import matchers
from fastapi.testclient import TestClient
from sqlalchemy import delete
from testcontainers.community.postgres import PostgresContainer

from weather.adapters.database import DatabaseAdapter, readings
from weather.api import create_app

GEO = "https://geocoding-api.open-meteo.com"
WEATHER = "https://api.open-meteo.com"


@contextmanager
def database_url():
    # Explicit opt-in for local diagnostic runs. CI always uses Testcontainers.
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        yield override
    else:
        with PostgresContainer("postgres:16-alpine") as postgres:
            yield postgres.get_connection_url()


def clear_database(url):
    repository = DatabaseAdapter(url)
    try:
        repository.initialize()
        with repository.engine.begin() as connection:
            connection.execute(delete(readings))
    finally:
        repository.close()


def stub_weather(stub, city="timisoara", temperature=22.4, mode="ok"):
    geo_match = matchers.query_param_matcher({"name": city, "count": "1", "language": "en", "format": "json"})
    if mode == "missing":
        stub.get(GEO + "/v1/search", json={"results": []}, match=[geo_match])
        return
    stub.get(GEO + "/v1/search", json={"results": [
        {"name": "Timișoara", "country": "Romania", "latitude": 45.75, "longitude": 21.23}
    ]}, match=[geo_match])
    weather_match = matchers.query_param_matcher({"latitude": "45.75", "longitude": "21.23",
                                               "current_weather": "true", "wind_speed_unit": "kmh"})
    if mode == "failure":
        stub.get(WEATHER + "/v1/forecast", status=503, match=[weather_match])
    else:
        stub.get(WEATHER + "/v1/forecast", json={"current_weather": {
            "temperature": temperature, "windspeed": 14.2, "weathercode": 3,
            "time": "2024-06-01T14:00",
        }}, match=[weather_match])


@contextmanager
def full_application(url):
    clear_database(url)
    with responses.RequestsMock(assert_all_requests_are_fired=True) as stub:
        with TestClient(create_app(url, GEO, WEATHER)) as client:
            yield client, stub
