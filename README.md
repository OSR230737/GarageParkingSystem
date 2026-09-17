# ParkSmart

ParkSmart is a parking garage management system for attendants. It tracks
availability across multiple floors, enforces EV spot rules, calculates tiered
parking fees, and makes active vehicles searchable by license plate.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Database:** PostgreSQL 16 running with Docker Compose
- **ORM:** SQLAlchemy
- **Authentication:** JWT with `python-jose` and password hashing with Passlib/bcrypt
- **Frontend:** Vanilla HTML, CSS, and JavaScript

## Features

- User registration and JWT login
- Password hashing with bcrypt
- Multi-floor parking spot management
- Compact, standard, and EV spot types
- EV vehicle validation
- Real-time free and occupied spot counts
- Check-in and checkout workflows
- Tiered fees with part-hour rounding and a daily cap
- EV charging surcharge included in the cap
- Active session pagination and sorting
- Case-insensitive license plate search
- CORS enabled for frontend development

## Prerequisites

- Python 3.11 or newer
- Docker and Docker Compose

## Local Setup

1. Clone the repository and enter the project directory.

2. Create a virtual environment and install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

4. Start PostgreSQL:

   ```bash
   docker compose up -d db
   ```

5. Seed the admin account and default parking spots:

   ```bash
   python seed.py
   ```

   The seed script is safe to run more than once. Existing users and spot
   numbers are skipped.

6. Start the FastAPI server:

   ```bash
   uvicorn app.main:app --reload
   ```

The API is available at http://localhost:8000. Database tables are created
automatically when the API starts.

## Default Seed Account

```text
Username: admin
Password: admin123
Email:    admin@parksmart.com
```

Change this password before using the system outside local development.

## API Documentation

FastAPI generates interactive documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","database":"connected"}
```

## REST API

### Authentication

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | Create a user | No |
| `POST` | `/auth/login` | Return a JWT token | No |
| `GET` | `/auth/me` | Return the authenticated user | Bearer token |

Login response:

```json
{
  "token": "jwt-token",
  "username": "admin"
}
```

Send the token on protected requests:

```text
Authorization: Bearer <token>
```

### Parking Spots

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/spots` | Create a parking spot | Bearer token |
| `GET` | `/spots` | List and filter spots | No |
| `GET` | `/spots/ev/available` | Count free EV spots | No |

`GET /spots` supports these query parameters:

```text
spot_type=compact|standard|ev
is_occupied=true|false
skip=0
limit=10
sort_by=id|spot_number|spot_type|floor_level|is_occupied
```

### Parking Sessions

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/checkin` | Check a vehicle into a spot | Bearer token |
| `POST` | `/checkout/{session_id}` | Check out and calculate the fee | Bearer token |
| `GET` | `/sessions` | List active sessions | Bearer token |
| `GET` | `/search?plate=XX` | Search sessions by plate | Bearer token |

`GET /sessions` supports:

```text
skip=0
limit=10
sort_by=id|plate_number|vehicle_type|checked_in_at|checked_out_at|fee_charged
order=asc|desc
```

## Frontend

The frontend is framework-free and lives in the `frontend/` directory:

- [Landing page](frontend/index.html)
- [Login and registration](frontend/login.html)
- [Attendant dashboard](frontend/app.html)

The frontend currently points to the configured FastAPI API URL in the script
of `login.html` and `app.html`. When deploying elsewhere, update that URL in
both files.

For local browser testing, serve the frontend directory from a static server:

```bash
python -m http.server 5500 --directory frontend
```

Then open http://localhost:5500.

## Project Structure

```text
.
├── app/
│   ├── api/routes/
│   │   ├── auth.py
│   │   ├── health.py
│   │   ├── sessions.py
│   │   └── spots.py
│   ├── auth.py
│   ├── config.py
│   ├── db.py
│   ├── fees.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── frontend/
│   ├── app.html
│   ├── index.html
│   └── login.html
├── seed.py
├── docker-compose.yml
├── requirements.txt
└── tests/
```

## Testing

Run the current unit tests with:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

The tests cover the database dependency and SQLAlchemy model behavior.
