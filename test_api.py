"""Quick smoke tests — run with: pytest test_api.py"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_and_list():
    r = client.post("/tasks", json={"title": "Buy milk", "description": "2 litres"})
    assert r.status_code == 201
    task = r.json()
    assert task["title"] == "Buy milk"
    assert task["done"] is False

    r = client.get("/tasks")
    assert r.status_code == 200
    assert any(t["id"] == task["id"] for t in r.json())


def test_get_task():
    r = client.post("/tasks", json={"title": "Test get"})
    task_id = r.json()["id"]
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["id"] == task_id


def test_update_task():
    r = client.post("/tasks", json={"title": "Original"})
    task_id = r.json()["id"]
    r = client.put(f"/tasks/{task_id}", json={"title": "Updated", "done": True})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"
    assert r.json()["done"] is True


def test_delete_task():
    r = client.post("/tasks", json={"title": "Delete me"})
    task_id = r.json()["id"]
    r = client.delete(f"/tasks/{task_id}")
    assert r.status_code == 204
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 404


def test_complete_task():
    r = client.post("/tasks", json={"title": "To complete"})
    task_id = r.json()["id"]
    assert r.json()["done"] is False

    r = client.post(f"/tasks/{task_id}/complete")
    assert r.status_code == 200
    assert r.json()["done"] is True

    r = client.post("/tasks/999999/complete")
    assert r.status_code == 404


def test_filter_by_done():
    client.post("/tasks", json={"title": "Pending task"})
    r = client.post("/tasks", json={"title": "Done task"})
    client.put(f"/tasks/{r.json()['id']}", json={"done": True})

    done_tasks = client.get("/tasks?done=true").json()
    pending_tasks = client.get("/tasks?done=false").json()
    all_tasks = client.get("/tasks").json()

    assert all(t["done"] is True for t in done_tasks)
    assert all(t["done"] is False for t in pending_tasks)
    assert len(all_tasks) == len(done_tasks) + len(pending_tasks)


def test_stats():
    r = client.get("/tasks/stats")
    assert r.status_code == 200
    before = r.json()

    client.post("/tasks", json={"title": "Stats pending"})
    r = client.post("/tasks", json={"title": "Stats done"})
    client.post(f"/tasks/{r.json()['id']}/complete")

    stats = client.get("/tasks/stats").json()
    assert stats["total"] == before["total"] + 2
    assert stats["done"] == before["done"] + 1
    assert stats["pending"] == before["pending"] + 1
    assert stats["total"] == stats["done"] + stats["pending"]


def test_patch_task():
    r = client.post("/tasks", json={"title": "Original", "description": "Desc"})
    task_id = r.json()["id"]

    r = client.patch(f"/tasks/{task_id}", json={"title": "Patched"})
    assert r.status_code == 200
    assert r.json()["title"] == "Patched"
    assert r.json()["description"] == "Desc"  # inchangé

    r = client.patch(f"/tasks/{task_id}", json={"done": True})
    assert r.json()["done"] is True
    assert r.json()["title"] == "Patched"  # inchangé

    assert client.patch("/tasks/999999", json={"title": "x"}).status_code == 404
    assert client.patch(f"/tasks/{task_id}", json={}).status_code == 422


def test_delete_completed():
    client.post("/tasks", json={"title": "Pending"})
    r = client.post("/tasks", json={"title": "Done A"})
    client.post(f"/tasks/{r.json()['id']}/complete")
    r = client.post("/tasks", json={"title": "Done B"})
    client.post(f"/tasks/{r.json()['id']}/complete")

    r = client.delete("/tasks/completed")
    assert r.status_code == 200
    assert r.json()["deleted"] >= 2

    assert all(t["done"] is False for t in client.get("/tasks").json())


def test_not_found():
    assert client.get("/tasks/999999").status_code == 404
    assert client.put("/tasks/999999", json={"title": "x"}).status_code == 404
    assert client.delete("/tasks/999999").status_code == 404
