"""Inbound REST adapter and composition root. No infrastructure is started on import."""
import os
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from weather.adapters.database import DatabaseAdapter
from weather.adapters.open_meteo import OpenMeteoAdapter
from weather.domain import CityNotFound, InvalidCity, ProviderUnavailable
from weather.service import WeatherService


def create_app(database_url=None, geocoding_url=None, weather_url=None):
    @asynccontextmanager
    async def lifespan(app):
        repository = DatabaseAdapter(database_url or os.getenv("DATABASE_URL", "sqlite:///./weather.db"))
        try:
            repository.initialize()
            provider = OpenMeteoAdapter(
                geocoding_url or os.getenv("GEOCODING_URL", "https://geocoding-api.open-meteo.com"),
                weather_url or os.getenv("WEATHER_URL", "https://api.open-meteo.com"),
            )
            app.state.service = WeatherService(provider, repository)
            yield
        finally:
            repository.close()

    app = FastAPI(title="Weather Aggregator", lifespan=lifespan)

    @app.exception_handler(InvalidCity)
    async def invalid_city(request, exc):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(CityNotFound)
    async def city_not_found(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ProviderUnavailable)
    async def provider_unavailable(request, exc):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.post("/weather/fetch", status_code=201)
    def fetch(city: str = Query(..., min_length=1, max_length=100)):
        return asdict(app.state.service.fetch(city))

    @app.get("/weather/{city}/latest")
    def latest(city: str):
        reading = app.state.service.latest(city)
        if reading is None:
            raise HTTPException(404, "No saved readings for this city")
        return asdict(reading)

    @app.get("/weather/{city}")
    def history(city: str):
        return [asdict(reading) for reading in app.state.service.history(city)]

    return app


app = create_app()
