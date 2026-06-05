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


def test_not_found():
    assert client.get("/tasks/999999").status_code == 404
    assert client.put("/tasks/999999", json={"title": "x"}).status_code == 404
    assert client.delete("/tasks/999999").status_code == 404
