# My Reasoning

## Why I chose this stack

I chose FastAPI because the project is mostly a small set of clear HTTP workflows: register, log in, create or list spots, check a car in, check it out, and search by plate. FastAPI gives me request validation, dependency injection, automatic OpenAPI documentation, and Swagger UI without a large framework getting in the way. That was useful for an assessment because I could test the API contract quickly at `/docs`.

I used PostgreSQL because parking data is relational. Users own the check-in actions, sessions belong to spots, and the same spot cannot be occupied by multiple active vehicles. PostgreSQL is a good fit for those foreign keys, uniqueness constraints, filtering, sorting, and future reporting needs. I already know PostgreSQL from other projects, so the unfamiliar part was mainly connecting it cleanly to FastAPI rather than learning the database itself.

I put PostgreSQL in Docker so the database setup is repeatable and does not depend on a local PostgreSQL installation. The `docker-compose.yml` gives the app a known database name, user, password, port, volume, and health check. It also means I can reset or move the database setup without asking everyone working on the project to configure PostgreSQL manually.

## How I designed the fee calculation

I kept the fee calculation in one function in `app/fees.py` instead of putting it in a route. The function receives the check-in time, check-out time, spot type, and vehicle type, then does the pricing calculation in one place.

The calculation works in this order:

1. Calculate the elapsed time.
2. Round partial hours up using `ceil`.
3. Charge `$5` for the first hour.
4. Charge `$3` for each additional hour.
5. Add `$2` per hour when both the spot and vehicle are EV.
6. Apply the `$20` cap to the final total.

The cap has to be applied after the EV surcharge. Otherwise an EV could pay the base cap and then accidentally get charged extra on top of it. Keeping the function separate also makes it easier to test directly and keeps the checkout route focused on changing session and spot state.

## Why EV validation is in the API

The frontend filters the spot dropdown when the attendant selects an EV vehicle, but that is only a usability feature. It cannot be the actual protection because anyone can bypass browser JavaScript and call the API directly.

The check-in endpoint validates that an EV vehicle is using an EV spot and rejects the request with a 400 response when it is not. The API also checks whether the spot is already occupied. These rules belong at the server boundary because every client, including Swagger, a future mobile app, or a direct HTTP script, must follow the same parking rules.

## Schema decisions

I used separate SQLAlchemy models for `User`, `ParkingSpot`, and `ParkingSession`.

- `User` has unique username and email values, plus a hashed password rather than the original password.
- `ParkingSpot` stores a unique spot number, floor, type, and occupancy state.
- `ParkingSession` stores the vehicle, timestamps, charged fee, assigned spot, and attendant who checked it in.
- `spot_id` and `checked_in_by` are foreign keys so sessions cannot point at arbitrary records.
- `checked_out_at` and `fee_charged` are nullable because they do not exist while a session is active.
- `ParkingSession.spot` is a relationship so route code can access the actual spot object when calculating a fee or returning spot details.

I kept the schema fairly simple for the assessment. Spot and vehicle types are validated in the API rather than introducing database enum types, which keeps the setup easier to change. The tradeoff is that the allowed values are application rules and would need stronger database constraints in a larger production system.

## Mistakes I hit

I initially used the wrong `DATABASE_URL` format. SQLAlchemy needs the driver included for this setup, so the working value uses `postgresql+psycopg://...` rather than a generic PostgreSQL URL. The connection only became reliable after matching the URL to the installed Psycopg driver.

I also had the fee cap in the wrong order while working through the EV examples. The surcharge must be part of the capped total, so the final `min(total, 20)` happens after the surcharge is added. This was a good example of why the pricing rule belongs in a directly testable function instead of being spread through checkout code.

I forgot CORS middleware initially. The API worked from server-side tests, but a browser frontend on another origin could not call it. I added `CORSMiddleware` to the FastAPI app and allowed all origins for this development setup.

My first plate search used an exact match. That did not match the attendant workflow very well, so I changed it to a case-insensitive partial search with SQLAlchemy `ilike`. A search for part of a plate can now find the relevant session without requiring the attendant to type the entire value exactly.

There were also a few practical compatibility issues. Python 3.14 exposed an incompatibility between the original Passlib/bcrypt combination, and the SQLAlchemy version had trouble with some newer union annotations. Pinning a compatible bcrypt version and simplifying the nullable mapped annotations got the application running, although Passlib still emits a non-fatal bcrypt version warning in this environment.

## How I tested it

I started with the `/docs` Swagger UI because it exposed the API contract immediately and made it easy to try requests without building a frontend first. I checked registration, login, bearer authentication, spot creation, check-in, checkout, availability, session listing, and plate search there and through direct HTTP requests.

I also ran focused model tests with an in-memory SQLite database. Those tests cover the database dependency, model mappings, defaults, unique fields, foreign keys, and the `ParkingSession.spot` relationship. For the real integration path, I started PostgreSQL with Docker, verified `SELECT 1` through the SQLAlchemy engine, initialized the tables, and ran the API against that database.

After the API was stable, I tested the full frontend flow: login, registration, dashboard loading, spot availability, check-in, session display, search, pagination, checkout, fee display, and the refresh of stats and spot state. Testing Swagger first helped separate backend problems from browser and frontend problems.

## What I would improve

I would improve environment variable management first. The JWT secret is currently in code and the development database credentials are simple defaults. I would move secrets and environment-specific settings into validated configuration, use different values outside development, and avoid documenting default credentials as if they were production-ready.

I would add proper migrations with Alembic instead of relying on `Base.metadata.create_all` at startup. `create_all` is fine for this assessment, but it does not describe schema changes over time or support controlled upgrades and rollbacks.

I would add rate limiting around login and other sensitive endpoints. Password hashing protects stored credentials, but unrestricted login attempts still create an avoidable attack surface.

I would also containerize the frontend or serve it through a small web server in Docker. Right now the static pages can be served with Python's built-in HTTP server, which is convenient locally but not a complete deployment setup. A frontend container would make the development and deployment environment more consistent and would make the API origin configuration explicit.

Finally, I would add more integration tests to the repository itself. The manual end-to-end checks caught useful issues, but those checks should become automated tests so later changes cannot quietly break the browser-facing API contract.
