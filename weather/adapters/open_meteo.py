"""Outbound HTTP adapter. Only current_weather is consumed."""
import math

import requests

from weather.domain import CityNotFound, Conditions, ProviderUnavailable


WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Drizzle: light", 53: "Drizzle: moderate", 55: "Drizzle: dense",
    56: "Freezing drizzle: light", 57: "Freezing drizzle: dense",
    61: "Rain: slight", 63: "Rain: moderate", 65: "Rain: heavy",
    66: "Freezing rain: light", 67: "Freezing rain: heavy",
    71: "Snow fall: slight", 73: "Snow fall: moderate", 75: "Snow fall: heavy",
    77: "Snow grains", 80: "Rain showers: slight", 81: "Rain showers: moderate",
    82: "Rain showers: violent", 85: "Snow showers: slight", 86: "Snow showers: heavy",
    95: "Thunderstorm: slight or moderate", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Expected a finite number")
    return float(value)


class OpenMeteoAdapter:
    def __init__(self, geocoding_url="https://geocoding-api.open-meteo.com",
                 weather_url="https://api.open-meteo.com", timeout=10):
        self.geocoding_url = geocoding_url.rstrip("/")
        self.weather_url = weather_url.rstrip("/")
        self.timeout = timeout

    def _get(self, url, params):
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def current(self, city: str) -> Conditions:
        try:
            geo = self._get(self.geocoding_url + "/v1/search", {
                "name": city, "count": 1, "language": "en", "format": "json",
            })
            results = geo.get("results", [])
            if not isinstance(results, list):
                raise ValueError("Invalid geocoding results")
            if not results:
                raise CityNotFound(f"City not found: {city}")
            location = results[0]
            name = location["name"]
            if not isinstance(name, str) or not name.strip() or len(name) > 100:
                raise ValueError("Invalid city name")
            latitude, longitude = number(location["latitude"]), number(location["longitude"])
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError("Invalid coordinates")
            payload = self._get(self.weather_url + "/v1/forecast", {
                "latitude": latitude, "longitude": longitude,
                "current_weather": "true", "wind_speed_unit": "kmh",
            })
            current = payload["current_weather"]
            temperature, wind = number(current["temperature"]), number(current["windspeed"])
            code = current["weathercode"]
            if wind < 0 or type(code) is not int:
                raise ValueError("Invalid current weather")
            return Conditions(name, temperature, wind, WMO.get(code, f"Unknown weather code ({code})"))
        except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
            raise ProviderUnavailable("Weather provider unavailable or returned invalid data") from exc
