from datetime import datetime, timezone
from typing import Callable

from weather.domain import Reading, ReadingRepository, WeatherProvider, city_key


class WeatherService:
    def __init__(self, provider: WeatherProvider, repository: ReadingRepository,
                 clock: Callable[[], datetime] | None = None):
        self.provider = provider
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch(self, city: str) -> Reading:
        key = city_key(city)
        current = self.provider.current(key)
        reading = Reading(current.city, current.temperature, current.wind_speed,
                          current.description, self.clock())
        return self.repository.save(reading, key)

    def history(self, city: str) -> list[Reading]:
        return self.repository.by_city(city_key(city))

    def latest(self, city: str) -> Reading | None:
        return self.repository.latest(city_key(city))
