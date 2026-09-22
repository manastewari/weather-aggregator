from datetime import timezone

from sqlalchemy import (Column, DateTime, Float, Integer, MetaData, String, Table,
                        Index, create_engine, insert, or_, select)

from weather.domain import Reading, city_key

metadata = MetaData()
readings = Table(
    "weather_readings", metadata,
    Column("id", Integer, primary_key=True),
    Column("city", String(100), nullable=False),
    Column("city_key", String(100), nullable=False),
    Column("query_key", String(100), nullable=False),
    Column("temperature", Float, nullable=False),
    Column("wind_speed", Float, nullable=False),
    Column("description", String(200), nullable=False),
    Column("fetched_at", DateTime(timezone=True), nullable=False),
)
Index("ix_readings_city_time", readings.c.city_key, readings.c.fetched_at, readings.c.id)
Index("ix_readings_query_time", readings.c.query_key, readings.c.fetched_at, readings.c.id)


class DatabaseAdapter:
    def __init__(self, url):
        self.engine = create_engine(url, pool_pre_ping=True)

    def initialize(self):
        metadata.create_all(self.engine)

    def close(self):
        self.engine.dispose()

    @staticmethod
    def _reading(row):
        timestamp = row["fetched_at"]
        if timestamp.tzinfo is None:  # SQLite development mode loses timezone metadata.
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return Reading(row["city"], row["temperature"], row["wind_speed"],
                       row["description"], timestamp, row["id"])

    def save(self, reading: Reading, query_city: str) -> Reading:
        with self.engine.begin() as connection:
            row = connection.execute(insert(readings).values(
                city=reading.city, city_key=city_key(reading.city), query_key=city_key(query_city),
                temperature=reading.temperature, wind_speed=reading.wind_speed,
                description=reading.description, fetched_at=reading.fetched_at,
            ).returning(readings)).mappings().one()
            return self._reading(row)

    def _query(self, city):
        key = city_key(city)
        return select(readings).where(or_(readings.c.city_key == key, readings.c.query_key == key)).order_by(
            readings.c.fetched_at.desc(), readings.c.id.desc())

    def by_city(self, city: str) -> list[Reading]:
        with self.engine.connect() as connection:
            return [self._reading(row) for row in connection.execute(self._query(city)).mappings()]

    def latest(self, city: str) -> Reading | None:
        with self.engine.connect() as connection:
            row = connection.execute(self._query(city).limit(1)).mappings().first()
            return self._reading(row) if row else None
