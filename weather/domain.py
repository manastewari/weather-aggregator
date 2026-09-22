from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class CityNotFound(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


class InvalidCity(ValueError):
    pass


def city_key(city: str) -> str:
    normalized = " ".join(city.split()).casefold()
    if not normalized or len(normalized) > 100 or any(ord(c) < 32 for c in city):
        raise InvalidCity("City must contain 1–100 characters without control characters")
    return normalized


@dataclass(frozen=True)
class Conditions:
    city: str
    temperature: float
    wind_speed: float
    description: str


@dataclass(frozen=True)
class Reading:
    city: str
    temperature: float
    wind_speed: float
    description: str
    fetched_at: datetime
    id: int | None = None


class WeatherProvider(Protocol):
    def current(self, city: str) -> Conditions: ...


class ReadingRepository(Protocol):
    def save(self, reading: Reading, query_city: str) -> Reading: ...
    def by_city(self, city: str) -> list[Reading]: ...
    def latest(self, city: str) -> Reading | None: ...
