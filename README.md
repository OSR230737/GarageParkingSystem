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
   auth.py      Password hashing and JWT authentication
  config.py    Environment configuration
  db.py        SQLAlchemy engine, sessions, and model base
   fees.py      Parking fee calculation
  main.py      FastAPI application entry point
   models.py    User, parking spot, and parking session models
   schemas.py   API request and response schemas
docker-compose.yml
requirements.txt
```

## API workflow

Tables are created automatically when the API starts. Register an attendant and
log in to receive a bearer token:

```bash
curl -X POST http://localhost:8000/auth/register \
   -H 'Content-Type: application/json' \
   -d '{"username":"attendant","email":"attendant@example.com","password":"password123"}'

curl -X POST http://localhost:8000/auth/login \
   -H 'Content-Type: application/json' \
   -d '{"username":"attendant","password":"password123"}'
```

Authenticated endpoints support creating spots, listing available spots,
checking vehicles in and out, and finding an active session by plate:

- `POST /spots`
- `GET /spots?spot_type=ev&is_occupied=false&skip=0&limit=10`
- `GET /spots/ev/available`
- `POST /checkin`
- `POST /checkout/{session_id}`
- `GET /sessions`
- `GET /search?plate=XX`