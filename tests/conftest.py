import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Base

from app import main
from app.auth import get_current_user


@pytest.fixture
def client(monkeypatch):

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user():
        return {
            "sub": "test-user-sub",
            "username": "test-user",
        }

    # Replace the production database with the test database.
    monkeypatch.setattr(main, "engine", test_engine)

    # Create database tables in the temporary test database.
    Base.metadata.create_all(bind=test_engine)

    # Override database and authentication dependencies.
    main.app.dependency_overrides[main.get_db] = override_get_db
    main.app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        with TestClient(main.app) as test_client:
            yield test_client
    finally:
        main.app.dependency_overrides.clear()
        test_engine.dispose()