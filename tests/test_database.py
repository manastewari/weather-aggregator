from datetime import datetime, timedelta, timezone

import pytest

from weather.adapters.database import DatabaseAdapter
from weather.domain import Reading
from tests.support import clear_database

pytestmark = pytest.mark.integration


def test_save_history_latest_and_persistence(db_url):
    clear_database(db_url)
    repository = DatabaseAdapter(db_url)
    now = datetime.now(timezone.utc)
    try:
        old = repository.save(Reading("Timișoara", 20, 4, "Clear sky", now), "timisoara")
        new = repository.save(Reading("Timișoara", 22, 5, "Overcast", now + timedelta(seconds=1)), "timisoara")
        repository.save(Reading("Paris", 12, 8, "Rain: slight", now), "paris")
        assert old.id and new.id != old.id
        assert repository.by_city(" TIMISOARA ") == [new, old]
        assert repository.by_city("Timișoara") == [new, old]
        assert repository.latest("timisoara") == new
        assert repository.by_city("missing") == []
        assert repository.latest("missing") is None
    finally:
        repository.close()
    reopened = DatabaseAdapter(db_url)
    try:
        assert reopened.latest("timisoara") == new
    finally:
        reopened.close()


def test_equal_timestamps_use_id_as_tiebreaker(db_url):
    clear_database(db_url)
    repository = DatabaseAdapter(db_url)
    try:
        reading = Reading("Paris", 22, 1, "Clear sky", datetime.now(timezone.utc))
        first = repository.save(reading, "paris")
        second = repository.save(reading, "paris")
        assert repository.by_city("paris") == [second, first]
        assert repository.latest("paris") == second
    finally:
        repository.close()
