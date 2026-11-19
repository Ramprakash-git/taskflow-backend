import os
import json
import boto3

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Task
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.auth import get_current_user


# Global database objects
engine = None
SessionLocal = None


# Retrieve database credentials and construct SQLAlchemy URL
def get_database_url():
    secret_arn = os.getenv("DB_SECRET_ARN")
    region = os.getenv("AWS_DEFAULT_REGION")
    database_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")

    if not all([secret_arn, region, database_name, db_host]):
        raise RuntimeError(
            "DB_SECRET_ARN, AWS_DEFAULT_REGION, DB_NAME "
            "and DB_HOST must be configured"
        )

    client = boto3.client(
        "secretsmanager",
        region_name=region
    )

    response = client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response["SecretString"])

    return URL.create(
        drivername="postgresql+psycopg",
        username=secret["username"],
        password=secret["password"],
        host=db_host,
        port=int(db_port),
        database=database_name
    )


# FastAPI application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, SessionLocal

    # Tests may provide their own SQLite engine.
    owns_engine = engine is None

    if owns_engine:
        database_url = get_database_url()
        engine = create_engine(
            database_url,
            pool_pre_ping=True
        )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )

    # Database schema is managed through migrations.
    # Do not use create_all() here: it does not update existing tables.

    try:
        yield
    finally:
        # Only dispose engines created by the application.
        if owns_engine:
            engine.dispose()
            engine = None
            SessionLocal = None


app = FastAPI(
    title="TaskFlow API",
    version="1.0.0",
    lifespan=lifespan
)


# Database session dependency
def get_db():

    if SessionLocal is None:
        raise RuntimeError("Database session is not initialized")

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# Health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}


# Readiness endpoint
@app.get("/ready")
def readiness():

    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database not initialized"
        )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "ready"}

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )


# List authenticated user's tasks
@app.get("/api/tasks", response_model=list[TaskRead])
def list_tasks(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    statement = (
        select(Task)
        .where(Task.user_sub == current_user["sub"])
        .order_by(Task.id.desc())
    )

    if status:
        statement = statement.where(Task.status == status)

    if search:
        statement = statement.where(
            Task.title.ilike(f"%{search}%")
        )

    return db.scalars(statement).all()


# Create task for authenticated user
@app.post(
    "/api/tasks",
    response_model=TaskRead,
    status_code=201
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    task = Task(
        **payload.model_dump(),
        user_sub=current_user["sub"]
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


# Get individual task belonging to authenticated user
@app.get("/api/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    statement = select(Task).where(
        Task.id == task_id,
        Task.user_sub == current_user["sub"]
    )

    task = db.scalar(statement)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


# Update authenticated user's task
@app.patch("/api/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    statement = select(Task).where(
        Task.id == task_id,
        Task.user_sub == current_user["sub"]
    )

    task = db.scalar(statement)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


# Delete authenticated user's task
@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    statement = select(Task).where(
        Task.id == task_id,
        Task.user_sub == current_user["sub"]
    )

    task = db.scalar(statement)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()