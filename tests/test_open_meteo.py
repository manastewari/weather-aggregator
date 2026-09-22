import pytest
import requests
import responses

from weather.adapters.open_meteo import OpenMeteoAdapter, WMO
from weather.domain import CityNotFound, ProviderUnavailable

pytestmark = pytest.mark.adapter
GEO = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER = "https://api.open-meteo.com/v1/forecast"


@responses.activate
@pytest.mark.parametrize("code,description", [(0, "Clear sky"), (3, "Overcast"), (61, "Rain: slight"), (123, "Unknown weather code (123)")])
def test_mapping_uses_only_current_weather(code, description):
    responses.get(GEO, json={"results": [{"name": "Paris", "latitude": 48.8, "longitude": 2.3}]})
    responses.get(WEATHER, json={"hourly": {"temperature": [999]}, "current_weather": {
        "temperature": 22.4, "windspeed": 14.2, "weathercode": code,
    }})
    result = OpenMeteoAdapter().current("paris")
    assert result.description == description
    assert result.temperature == 22.4
    assert "current_weather=true" in responses.calls[1].request.url
    assert "wind_speed_unit=kmh" in responses.calls[1].request.url


@responses.activate
@pytest.mark.parametrize("payload", [{}, {"results": []}])
def test_city_not_found(payload):
    responses.get(GEO, json=payload)
    with pytest.raises(CityNotFound):
        OpenMeteoAdapter().current("unknown")
    assert len(responses.calls) == 1


@responses.activate
@pytest.mark.parametrize("payload", [{}, {"current_weather": {}}, {"current_weather": {
    "temperature": "bad", "windspeed": 2, "weathercode": 0}}, {"current_weather": {
    "temperature": 12, "windspeed": -1, "weathercode": 0}}])
def test_malformed_weather_is_provider_failure(payload):
    responses.get(GEO, json={"results": [{"name": "Paris", "latitude": 48.8, "longitude": 2.3}]})
    responses.get(WEATHER, json=payload)
    with pytest.raises(ProviderUnavailable):
        OpenMeteoAdapter().current("paris")


@responses.activate
@pytest.mark.parametrize("failure", [requests.Timeout(), requests.ConnectionError()])
def test_transport_failure(failure):
    responses.get(GEO, body=failure)
    with pytest.raises(ProviderUnavailable):
        OpenMeteoAdapter().current("paris")


def test_all_documented_codes_have_descriptions():
    assert set(WMO) == {0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                        71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}
