"""A real Pact mock server exercises the consumer; the verifier replays it to an independent stub."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse

from pact import Pact, Verifier, match
import pytest

from weather.adapters.open_meteo import OpenMeteoAdapter

pytestmark = pytest.mark.contract
PACT_DIR = Path(__file__).resolve().parents[1] / "pacts"


@pytest.fixture(scope="module")
def generated_pact():
    pact = Pact("weather-aggregator", "open-meteo").with_specification("V4")
    (pact.upon_receiving("resolve a city")
     .with_request("GET", "/v1/search")
     .with_query_parameter("name", "timisoara")
     .with_query_parameter("count", "1")
     .with_query_parameter("language", "en")
     .with_query_parameter("format", "json")
     .will_respond_with(200)
     .with_body({"results": [{"name": match.str("Timișoara"),
                               "latitude": match.float(45.75), "longitude": match.float(21.23)}]}))
    (pact.upon_receiving("fetch current conditions")
     .with_request("GET", "/v1/forecast")
     .with_query_parameter("latitude", "45.75")
     .with_query_parameter("longitude", "21.23")
     .with_query_parameter("current_weather", "true")
     .with_query_parameter("wind_speed_unit", "kmh")
     .will_respond_with(200)
     .with_body({"current_weather": {"temperature": match.float(22.4), "windspeed": match.float(14.2),
                                     "weathercode": match.int(3)}}))
    with pact.serve() as server:
        result = OpenMeteoAdapter(str(server.url), str(server.url)).current("timisoara")
        assert result.city == "Timișoara"
        assert result.temperature == 22.4
        assert result.wind_speed == 14.2
        assert result.description == "Overcast"
    PACT_DIR.mkdir(exist_ok=True)
    pact.write_file(PACT_DIR, overwrite=True)
    return PACT_DIR / "weather-aggregator-open-meteo.json"


def test_consumer_contract(generated_pact):
    assert generated_pact.is_file()


class ProviderStub(BaseHTTPRequestHandler):
    """Independent provider fixture, deliberately not loaded from the Pact file."""
    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)
        if url.path == "/v1/search" and params == {
            "name": ["timisoara"], "count": ["1"], "language": ["en"], "format": ["json"]
        }:
            body = {"results": [{"name": "Timișoara", "latitude": 45.75, "longitude": 21.23, "country": "Romania"}]}
        elif url.path == "/v1/forecast" and params == {
            "latitude": ["45.75"], "longitude": ["21.23"], "current_weather": ["true"], "wind_speed_unit": ["kmh"]
        }:
            body = {"current_weather": {"temperature": 19.2, "windspeed": 8.5, "weathercode": 61, "time": "2026-01-01T12:00"}}
        else:
            self.send_error(400)
            return
        encoded = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args):
        pass


def test_provider_verification_against_stub(generated_pact):
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderStub)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        (Verifier("open-meteo", host="127.0.0.1")
         .add_transport(url=f"http://127.0.0.1:{server.server_port}")
         .add_source(generated_pact)
         .verify())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
