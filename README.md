# Garage Parking System

Minimal FastAPI and PostgreSQL foundation for the parking garage assessment.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose

## Run locally

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start PostgreSQL:

   ```bash
   cp .env.example .env
   docker compose up -d db
   ```

3. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Check the API and database connection:

   ```bash
   curl http://localhost:8000/health
   ```

Expected response:

```json
{"status":"ok","database":"connected"}
```

The interactive API documentation is available at http://localhost:8000/docs.

## Structure

```text
app/
  api/routes/  HTTP route handlers
  config.py    Environment configuration
  db.py        SQLAlchemy engine, sessions, and model base
  main.py      FastAPI application entry point
docker-compose.yml
requirements.txt
```# GarageParkingSystem