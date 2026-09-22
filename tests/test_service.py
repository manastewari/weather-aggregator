from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from weather.domain import Conditions, Reading, CityNotFound, ProviderUnavailable, InvalidCity
from weather.service import WeatherService

pytestmark = pytest.mark.unit
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_fetch_stores_conditions_with_fetch_time():
    provider, repository = Mock(), Mock()
    provider.current.return_value = Conditions("Timișoara", 22.4, 14.2, "Overcast")
    repository.save.side_effect = lambda reading, query: Reading(**{**reading.__dict__, "id": 7})
    service = WeatherService(provider, repository, lambda: NOW)
    result = service.fetch("  TIMISOARA  ")
    provider.current.assert_called_once_with("timisoara")
    repository.save.assert_called_once_with(Reading("Timișoara", 22.4, 14.2, "Overcast", NOW), "timisoara")
    assert result.id == 7


@pytest.mark.parametrize("error", [CityNotFound("Unknown city"), ProviderUnavailable("Unavailable")])
def test_provider_error_does_not_store(error):
    provider, repository = Mock(), Mock()
    provider.current.side_effect = error
    with pytest.raises(type(error)):
        WeatherService(provider, repository).fetch("Paris")
    repository.save.assert_not_called()


@pytest.mark.parametrize("city", ["", "  ", "a" * 101, "Paris\n"])
def test_invalid_city_never_calls_ports(city):
    provider, repository = Mock(), Mock()
    with pytest.raises(InvalidCity):
        WeatherService(provider, repository).fetch(city)
    provider.current.assert_not_called()
    repository.save.assert_not_called()


def test_queries_normalize_and_delegate_to_repository():
    provider, repository = Mock(), Mock()
    service = WeatherService(provider, repository)
    repository.by_city.return_value = []
    repository.latest.return_value = None
    assert service.history(" PARIS ") == []
    assert service.latest(" PARIS ") is None
    repository.by_city.assert_called_once_with("paris")
    repository.latest.assert_called_once_with("paris")
    provider.current.assert_not_called()
