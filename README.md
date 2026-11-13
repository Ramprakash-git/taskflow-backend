# TaskFlow Backend

A small FastAPI API for the TaskFlow DevOps learning project.

## Endpoints
- `GET /health` — process health check (does not verify database connectivity).\n- `GET /ready` — readiness check (returns 503 if the database is unavailable).
- `GET /api/tasks` — list tasks; optional `status` and `search` query parameters.
- `POST /api/tasks` — create a task.
- `GET /api/tasks/{task_id}` — retrieve a task.
- `PATCH /api/tasks/{task_id}` — update a task.
- `DELETE /api/tasks/{task_id}` — delete a task.
- `GET /docs` — interactive API documentation.

Allowed statuses: `pending`, `in_progress`, `completed`.

## Run locally
Requires Python 3.12+ and a reachable PostgreSQL database.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE'
uvicorn app.main:app --reload
```

## Build the container
```bash
docker build -t taskflow-backend:dev .
docker run --rm -p 8000:8000 -e DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE' taskflow-backend:dev
```

Never commit real credentials. Supply `DATABASE_URL` through a secret-management mechanism in deployment.

## Learning-project note
For simplicity, the app creates its table at startup. A production deployment should use schema migrations (such as Alembic), database readiness checks, and a separate migration step.

\n## Run tests
Install the development dependencies and run the test suite:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

The tests use an isolated in-memory SQLite database. They do not connect to RDS or require production credentials.
