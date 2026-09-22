# NOTE: Please ignore the watermark in the demo video as the demo video was compressed using  a online tool for uploading

# Weather Aggregator

FastAPI + React, with a framework-independent domain and explicit ports and adapters. Open-Meteo supplies current conditions; PostgreSQL persists each fetch. No API key is needed.

## Run

### Windows Docker setup

Docker Desktop 4.91.0 and WSL 2.7.13 were installed on this machine on September 21, 2026. The required Windows restart is complete. PostgreSQL Testcontainers tests and the Docker Compose application have both been verified successfully.

After restarting Windows:

1. Open Docker Desktop and wait for the engine to start.
2. Reopen VS Code so its terminal picks up Docker's updated PATH.
3. Run `docker info` to confirm the engine is available.
4. Stop any locally running API on port 8000 before starting Compose.

To run the assignment tests against PostgreSQL, use PowerShell from this folder:

```powershell
Remove-Item Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest -v -s
```

Do not set the SQLite override for this run. Testcontainers creates and cleans up its own PostgreSQL container; the Compose application does not need to be running for tests.

### Start the application

With Docker Engine / Docker Desktop running:

```sh
docker compose up --build
```

Open http://localhost:8080 for the UI and http://localhost:8000/docs for interactive API documentation. Data persists in the `weather-data` volume. The Compose credentials are local development credentials, not production secrets.

For local development, install Python 3.12 and Node.js 22:

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
pip install -r requirements.lock
pip install --no-deps -e .
npm ci --prefix frontend
uvicorn weather.api:app --reload
# In another terminal:
npm run dev --prefix frontend
```

Open http://localhost:5173. Vite proxies `/weather` to port 8000. Without `DATABASE_URL`, the API uses a local `weather.db` SQLite file for easy development. Set `DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE` to use PostgreSQL. `GEOCODING_URL` and `WEATHER_URL` can override the upstream origins.

## API

| Request | Result |
| --- | --- |
| `POST /weather/fetch?city=Timisoara` | 201, newly persisted reading |
| `GET /weather/Timisoara` | 200, readings newest first; `[]` if none |
| `GET /weather/Timisoara/latest` | 200, newest reading; 404 if none |

```json
{
  "id": 1,
  "city": "Timișoara",
  "temperature": 22.4,
  "wind_speed": 14.2,
  "description": "Overcast",
  "fetched_at": "2026-01-01T12:00:00+00:00"
}
```

Temperature is °C; wind is km/h. Blank/invalid cities return 422, unresolved cities 404, and upstream timeouts, errors or malformed responses 502. Failed fetches do not create readings. Each successful fetch adds a record, even if the upstream measurement has not changed.

## Tests

After installing dependencies above, start Docker and run **all suites, including React and its production build, with one command**:

```sh
python -m pytest -v
```

No real Open-Meteo requests occur in tests. The first database test starts `postgres:16-alpine` through Testcontainers. The session fixture shares that container across database, component, and Behave tests, then stops it. Missing Docker is a failure, not a silently skipped integration suite. These tests must run serially because they reset the shared database between cases.

| Suite | Separate command | Boundary exercised |
| --- | --- | --- |
| Domain/service | `python -m pytest tests/test_service.py` | Plain objects and mocked ports; no HTTP/framework/DB |
| HTTP adapter | `python -m pytest tests/test_open_meteo.py` | Requests intercepted with responses |
| Pact | `python -m pytest tests/test_contract.py` | Real Pact mock server, generated file, real provider verifier against independent HTTP stub |
| Database | `python -m pytest -m integration` | Real PostgreSQL via Testcontainers |
| Component | `python -m pytest -m component` | Full FastAPI lifespan and HTTP routes → real adapter → real DB; upstream stubbed |
| BDD | `python -m pytest -m bdd` | Four Behave/Gherkin scenarios sharing the session database |
| Standalone BDD | `python -m behave features` | Same infrastructure factory and stubs as component tests |
| React | `npm test --prefix frontend` | React Testing Library + user-event |

For diagnostics without Docker only, explicitly set `TEST_DATABASE_URL` to a **disposable** SQLite database (`sqlite:///./test-local.db`). Tests clear the readings table in this database. This is a convenience mode, not evidence that PostgreSQL/Testcontainers works. CI leaves this unset and requires Docker.

Consumer tests generate `pacts/weather-aggregator-open-meteo.json`. The provider verification test depends on that fixture, so it can also run alone. The stub has its own response definitions, does not read answers from the Pact, and returns different valid weather values to exercise type matchers. Verifying a stub checks our assumptions and verification wiring; it does **not** prove the real external provider conforms. Open-Meteo does not participate in our consumer-driven contract and no broker is required here.

## Architecture and decisions

```text
React → REST adapter (weather/api.py) → WeatherService
                                         │
                       ┌─────────────────┴─────────────────┐
                  WeatherProvider                    ReadingRepository
                       ↑                                   ↑
                OpenMeteoAdapter                     DatabaseAdapter
                 requests → API                   SQLAlchemy → PostgreSQL
```

* `weather/domain.py`: immutable values, errors, normalization and two `Protocol` ports; Python standard library only.
* `weather/service.py`: use cases and an injectable clock. Depends on the domain only. Fetch conditions, timestamp after the upstream call, persist, return the repository's saved record.
* `weather/adapters/open_meteo.py`: geocode using the first result, request `current_weather=true` with `wind_speed_unit=kmh`, validate and translate the response. No forecast/hourly data is consumed. Provider observation time is intentionally unused: the requirement asks for our fetch time.
* `weather/adapters/database.py`: SQLAlchemy Core mapping, transactional insert, filtering and deterministic newest-first ordering (`fetched_at DESC, id DESC`). Latest is a limited database query. No ORM models leak into the domain.
* `weather/api.py`: composition root owns resource lifetime and HTTP error mapping. Synchronous routes run through FastAPI's worker pool because both outgoing HTTP and DB operations are synchronous.

City queries are trimmed, whitespace-normalized and case-folded. Both the original query key and the provider's canonical city key are saved, so `Timisoara` and `Timișoara` find a reading fetched as `Timisoara`. This is not a global alias registry. Ambiguous city names use the first geocoding result as required; a production API should accept location IDs/country and persist coordinates.

The HTTP adapter has a 10-second timeout per call and no automatic retries; the whole fetch may take about 20 seconds. Unknown numeric WMO codes are retained as an explicit unknown description. The lookup covers the [Open-Meteo documented codes](https://open-meteo.com/en/docs#weathervariables).

Schema creation uses `create_all` for this small exercise; production schema changes need migrations. History is unpaginated per the brief. Authentication, rate limits, caching and background refresh are outside the exercise. The same-origin proxy avoids broad CORS configuration. The UI loads optional Google Fonts with system-font fallbacks.


## Verification recorded in this workspace

On September 21, 2026, after installing Docker and restarting Windows, the combined command passed **34 pytest tests in 94.37 seconds with real PostgreSQL Testcontainers**, including the Behave runner (four scenarios), the React runner (four component tests), Pact consumer/provider verification, and the production UI build. `TEST_DATABASE_URL` was unset. The run reported three non-failing warnings: two test-library deprecations and a local pytest cache permission warning. Local output is saved in `test-results/postgres-output.txt` and JUnit results in `test-results/postgres.xml` (ignored by Git).

`docker compose up --build -d` successfully built and started the UI, API, and PostgreSQL services. A manual request through the UI proxy at `http://localhost:8080` fetched live Bengaluru conditions from Open-Meteo, saved the reading, and retrieved it through the latest-reading endpoint. GitHub Actions starts automatically on each push; check the repository Actions tab for the latest result. `npm install` reported zero vulnerabilities after updating Vitest.

For the service TDD cycle, `tests/test_service.py` was created and executed before `weather/service.py`; it first failed because the service module did not exist. Implementing the service made the service and HTTP-adapter batch pass (21 tests). The domain/service boundary remains free of framework, HTTP-client and database imports.
