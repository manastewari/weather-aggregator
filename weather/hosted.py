"""Single-service deployment: serve the built React UI alongside the existing API."""
import os

from fastapi.staticfiles import StaticFiles

from weather.api import create_app


def create_hosted_app():
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if not database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise RuntimeError("Hosted deployment requires a PostgreSQL DATABASE_URL")
    app = create_app(database_url=database_url)

    @app.get("/healthz", include_in_schema=False)
    def health():
        return {"status": "ok"}

    # Mount last: existing API endpoints must take precedence over static files.
    app.mount("/", StaticFiles(directory=os.getenv("STATIC_DIR", "/app/static"), html=True), name="ui")
    return app
