def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint_when_database_is_available(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_create_and_get_task(client):
    create_response = client.post(
        "/api/tasks",
        json={
            "title": "Prepare CI pipeline",
            "description": "Add backend tests",
            "status": "pending",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Prepare CI pipeline"
    assert created["status"] == "pending"
    assert isinstance(created["id"], int)

    get_response = client.get(f"/api/tasks/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == created


def test_list_tasks_with_status_and_search_filters(client):
    client.post("/api/tasks", json={"title": "Write deployment guide"})
    client.post(
        "/api/tasks",
        json={"title": "Review networking", "status": "in_progress"},
    )

    response = client.get("/api/tasks", params={"status": "in_progress"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Review networking"

    search_response = client.get("/api/tasks", params={"search": "deployment"})
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1
    assert search_response.json()[0]["title"] == "Write deployment guide"


def test_update_task(client):
    created = client.post(
        "/api/tasks",
        json={"title": "Original title"},
    ).json()

    response = client.patch(
        f"/api/tasks/{created['id']}",
        json={"title": "Updated title", "status": "completed"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    assert response.json()["status"] == "completed"


def test_delete_task(client):
    created = client.post(
        "/api/tasks",
        json={"title": "Temporary task"},
    ).json()

    response = client.delete(f"/api/tasks/{created['id']}")
    assert response.status_code == 204

    get_response = client.get(f"/api/tasks/{created['id']}")
    assert get_response.status_code == 404


def test_missing_task_returns_404(client):
    response = client.get("/api/tasks/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_invalid_task_status_is_rejected(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Invalid status", "status": "blocked"},
    )
    assert response.status_code == 422
