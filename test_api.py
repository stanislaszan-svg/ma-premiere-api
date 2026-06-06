"""Quick smoke tests — run with: pytest test_api.py"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_and_list():
    r = client.post("/tasks", json={"title": "Buy milk", "description": "2 litres"})
    assert r.status_code == 201
    task = r.json()
    assert task["title"] == "Buy milk"
    assert task["done"] is False
    assert task["priority"] == "medium"  # défaut

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

    client.post("/tasks", json={"title": "Stats pending", "priority": "high"})
    r = client.post("/tasks", json={"title": "Stats done", "priority": "high"})
    client.post(f"/tasks/{r.json()['id']}/complete")

    stats = client.get("/tasks/stats").json()
    assert stats["total"] == before["total"] + 2
    assert stats["done"] == before["done"] + 1
    assert stats["pending"] == before["pending"] + 1
    assert stats["total"] == stats["done"] + stats["pending"]

    bp = stats["by_priority"]
    assert set(bp.keys()) == {"high", "medium", "low"}
    for p in bp.values():
        assert p["total"] == p["done"] + p["pending"]
    assert bp["high"]["total"] >= 2

    client.post("/tasks", json={"title": "Tagged stats", "tags": ["work", "urgent"]})
    stats = client.get("/tasks/stats").json()
    bt = stats["by_tag"]
    assert "work" in bt and "urgent" in bt
    for v in bt.values():
        assert v["total"] == v["done"] + v["pending"]
    assert list(bt.keys()) == sorted(bt.keys())

    client.post("/tasks", json={"title": "Due today stats", "due_date": date.today().isoformat()})
    client.post("/tasks", json={"title": "Due future stats", "due_date": "2099-01-01"})
    client.post("/tasks", json={"title": "Due past stats", "due_date": "2020-01-01"})
    stats = client.get("/tasks/stats").json()
    bdd = stats["by_due_date"]
    ds = stats["due_date_summary"]
    assert isinstance(bdd, dict)
    assert list(bdd.keys()) == sorted(bdd.keys())
    for v in bdd.values():
        assert v["total"] == v["done"] + v["pending"]
    assert all(k in ds for k in ("overdue", "today", "upcoming", "no_date"))
    assert ds["overdue"] >= 1
    assert ds["today"] >= 1
    assert ds["upcoming"] >= 1


def test_filter_by_priority():
    client.post("/tasks", json={"title": "High 1", "priority": "high"})
    client.post("/tasks", json={"title": "High 2", "priority": "high"})
    client.post("/tasks", json={"title": "Low 1", "priority": "low"})

    highs = client.get("/tasks?priority=high").json()
    lows = client.get("/tasks?priority=low").json()
    mediums = client.get("/tasks?priority=medium").json()

    assert all(t["priority"] == "high" for t in highs)
    assert all(t["priority"] == "low" for t in lows)
    assert all(t["priority"] == "medium" for t in mediums)

    # combinaison done + priority
    task_id = highs[0]["id"]
    client.post(f"/tasks/{task_id}/complete")
    r = client.get("/tasks?priority=high&done=true").json()
    assert all(t["priority"] == "high" and t["done"] is True for t in r)

    assert client.get("/tasks?priority=critical").status_code == 422


def test_today():
    today = date.today().isoformat()

    today_id = client.post("/tasks", json={"title": "Today task", "due_date": today}).json()["id"]
    future_id = client.post("/tasks", json={"title": "Future task", "due_date": "2099-12-31"}).json()["id"]
    past_id = client.post("/tasks", json={"title": "Past task", "due_date": "2020-01-01"}).json()["id"]
    done_id = client.post("/tasks", json={"title": "Today done", "due_date": today}).json()["id"]
    client.post(f"/tasks/{done_id}/complete")

    today_ids = {t["id"] for t in client.get("/tasks/today").json()}
    assert today_id in today_ids
    assert future_id not in today_ids
    assert past_id not in today_ids
    assert done_id not in today_ids


def test_upcoming():
    future_id = client.post("/tasks", json={"title": "Upcoming", "due_date": "2099-12-31"}).json()["id"]
    past_id = client.post("/tasks", json={"title": "Overdue", "due_date": "2020-01-01"}).json()["id"]
    no_date_id = client.post("/tasks", json={"title": "No date"}).json()["id"]
    done_id = client.post("/tasks", json={"title": "Upcoming but done", "due_date": "2099-01-01"}).json()["id"]
    client.post(f"/tasks/{done_id}/complete")

    upcoming_ids = {t["id"] for t in client.get("/tasks/upcoming").json()}
    assert future_id in upcoming_ids
    assert past_id not in upcoming_ids
    assert no_date_id not in upcoming_ids
    assert done_id not in upcoming_ids
    assert all(t["done"] is False for t in client.get("/tasks/upcoming").json())


def test_overdue():
    client.post("/tasks", json={"title": "Overdue", "due_date": "2020-01-01"})
    client.post("/tasks", json={"title": "Future", "due_date": "2099-12-31"})
    client.post("/tasks", json={"title": "No date"})
    r = client.post("/tasks", json={"title": "Overdue but done", "due_date": "2020-01-01"})
    client.post(f"/tasks/{r.json()['id']}/complete")

    overdue = client.get("/tasks/overdue").json()
    assert all(t["done"] is False for t in overdue)
    assert all(t["due_date"] is not None and t["due_date"] < "2026-06-06" for t in overdue)
    assert not any(t["title"] == "Future" for t in overdue)
    assert not any(t["title"] == "No date" for t in overdue)
    assert not any(t["title"] == "Overdue but done" for t in overdue)


def test_search():
    client.post("/tasks", json={"title": "Acheter du lait"})
    client.post("/tasks", json={"title": "Acheter du pain"})
    client.post("/tasks", json={"title": "Faire du sport"})

    r = client.get("/tasks/search?q=Acheter")
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()]
    assert "Acheter du lait" in titles
    assert "Acheter du pain" in titles
    assert "Faire du sport" not in titles

    assert len(client.get("/tasks/search?q=sport").json()) >= 1
    assert client.get("/tasks/search?q=xyzimpossible").json() == []

    # recherche dans la description
    client.post("/tasks", json={"title": "Tâche X", "description": "contient le mot lait"})
    results = client.get("/tasks/search?q=lait").json()
    titles = [t["title"] for t in results]
    assert "Acheter du lait" in titles
    assert "Tâche X" in titles  # trouvé via description

    # recherche dans les tags
    r = client.post("/tasks", json={"title": "Tâche Y", "tags": ["courses", "urgent"]})
    tag_id = r.json()["id"]
    results = client.get("/tasks/search?q=courses").json()
    assert any(t["id"] == tag_id for t in results)  # trouvé via tag
    assert not any(t["title"] == "Faire du sport" for t in results)

    r = client.get("/tasks/search")
    assert r.status_code == 422  # q est obligatoire


def test_list_tags():
    client.post("/tasks", json={"title": "T1", "tags": ["work", "urgent"]})
    client.post("/tasks", json={"title": "T2", "tags": ["home", "work"]})
    client.post("/tasks", json={"title": "T3", "tags": []})

    tags = client.get("/tasks/tags").json()
    assert isinstance(tags, list)
    assert "work" in tags
    assert "urgent" in tags
    assert "home" in tags
    assert tags == sorted(tags)        # triés alphabétiquement
    assert len(tags) == len(set(tags)) # pas de doublons


def test_filter_by_tag():
    a = client.post("/tasks", json={"title": "Work task", "tags": ["work", "urgent"]}).json()["id"]
    b = client.post("/tasks", json={"title": "Home task", "tags": ["home"]}).json()["id"]
    c = client.post("/tasks", json={"title": "Both", "tags": ["work", "home"]}).json()["id"]
    d = client.post("/tasks", json={"title": "No tag"}).json()["id"]

    work_ids = {t["id"] for t in client.get("/tasks?tag=work").json()}
    assert a in work_ids and c in work_ids
    assert b not in work_ids and d not in work_ids

    home_ids = {t["id"] for t in client.get("/tasks?tag=home").json()}
    assert b in home_ids and c in home_ids
    assert a not in home_ids

    # pas de faux positif sur un sous-mot
    assert d not in {t["id"] for t in client.get("/tasks?tag=ork").json()}


def test_tags():
    r = client.post("/tasks", json={"title": "Tagged", "tags": ["work", "urgent"]})
    assert r.status_code == 201
    assert r.json()["tags"] == ["work", "urgent"]

    r = client.post("/tasks", json={"title": "No tags"})
    assert r.json()["tags"] == []

    task_id = r.json()["id"]
    r = client.patch(f"/tasks/{task_id}", json={"tags": ["home", "shopping"]})
    assert r.json()["tags"] == ["home", "shopping"]

    r = client.patch(f"/tasks/{task_id}", json={"tags": []})
    assert r.json()["tags"] == []


def test_due_date():
    r = client.post("/tasks", json={"title": "With date", "due_date": "2026-12-31"})
    assert r.status_code == 201
    assert r.json()["due_date"] == "2026-12-31"

    r = client.post("/tasks", json={"title": "No date"})
    assert r.json()["due_date"] is None

    task_id = r.json()["id"]
    r = client.patch(f"/tasks/{task_id}", json={"due_date": "2026-06-30"})
    assert r.json()["due_date"] == "2026-06-30"

    r = client.post("/tasks", json={"title": "Bad date", "due_date": "not-a-date"})
    assert r.status_code == 422


def test_priority():
    r = client.post("/tasks", json={"title": "Urgent", "priority": "high"})
    assert r.status_code == 201
    assert r.json()["priority"] == "high"

    r = client.post("/tasks", json={"title": "Low prio", "priority": "low"})
    assert r.json()["priority"] == "low"

    task_id = r.json()["id"]
    r = client.patch(f"/tasks/{task_id}", json={"priority": "high"})
    assert r.json()["priority"] == "high"

    r = client.post("/tasks", json={"title": "Bad prio", "priority": "critical"})
    assert r.status_code == 422


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


def test_reopen_task():
    r = client.post("/tasks", json={"title": "To reopen"})
    task_id = r.json()["id"]
    client.post(f"/tasks/{task_id}/complete")

    r = client.post(f"/tasks/{task_id}/reopen")
    assert r.status_code == 200
    assert r.json()["done"] is False

    assert client.post("/tasks/999999/reopen").status_code == 404


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


def test_history():
    r = client.post("/tasks", json={"title": "History task", "priority": "low", "tags": ["a"]})
    task_id = r.json()["id"]

    # aucune entrée au départ
    assert client.get(f"/tasks/{task_id}/history").json() == []

    # PATCH : title + priority + tags changent → 3 entrées
    client.patch(f"/tasks/{task_id}", json={"title": "History task v2", "priority": "high", "tags": ["a", "b"]})
    entries = client.get(f"/tasks/{task_id}/history").json()
    fields = {e["field"] for e in entries}
    assert fields == {"title", "priority", "tags"}
    title_entry = next(e for e in entries if e["field"] == "title")
    assert title_entry["old_value"] == "History task"
    assert title_entry["new_value"] == "History task v2"

    # complete → 1 entrée supplémentaire (done)
    client.post(f"/tasks/{task_id}/complete")
    entries = client.get(f"/tasks/{task_id}/history").json()
    assert any(e["field"] == "done" and e["old_value"] == "0" and e["new_value"] == "1" for e in entries)

    # reopen → 1 entrée supplémentaire (done)
    client.post(f"/tasks/{task_id}/reopen")
    entries = client.get(f"/tasks/{task_id}/history").json()
    done_entries = [e for e in entries if e["field"] == "done"]
    assert len(done_entries) == 2

    # triés du plus récent au plus ancien
    timestamps = [e["changed_at"] for e in entries]
    assert timestamps == sorted(timestamps, reverse=True)

    # 404 sur tâche inexistante
    assert client.get("/tasks/999999/history").status_code == 404

    # PATCH sans changement réel → 0 nouvelles entrées
    count_before = len(entries)
    client.patch(f"/tasks/{task_id}", json={"title": "History task v2"})  # même valeur
    assert len(client.get(f"/tasks/{task_id}/history").json()) == count_before


def test_not_found():
    assert client.get("/tasks/999999").status_code == 404
    assert client.put("/tasks/999999", json={"title": "x"}).status_code == 404
    assert client.delete("/tasks/999999").status_code == 404
