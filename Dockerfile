FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml requirements.lock ./
COPY weather ./weather
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps .
RUN useradd --create-home weather
USER weather
EXPOSE 8000
CMD ["uvicorn", "weather.api:app", "--host", "0.0.0.0", "--port", "8000"]
