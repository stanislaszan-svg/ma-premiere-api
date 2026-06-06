from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import date
import sqlite3
import contextlib

app = FastAPI(title="Task Manager API", version="1.0.0")

DB_PATH = "tasks.db"

Priority = Literal["low", "medium", "high"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with contextlib.closing(get_db()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                done INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # migrations pour les bases existantes
        for migration in [
            "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'",
            "ALTER TABLE tasks ADD COLUMN due_date TEXT",
        ]:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass
        conn.commit()


init_db()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = "medium"
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None
    priority: Optional[Priority] = None
    due_date: Optional[date] = None


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    done: bool
    priority: Priority
    due_date: Optional[date]
    created_at: str


def row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        done=bool(row["done"]),
        priority=row["priority"],
        due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
        created_at=row["created_at"],
    )


@app.get("/tasks", response_model=list[Task])
def list_tasks(done: Optional[bool] = None, priority: Optional[Priority] = None):
    filters, values = [], []
    if done is not None:
        filters.append("done = ?")
        values.append(int(done))
    if priority is not None:
        filters.append("priority = ?")
        values.append(priority)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    with contextlib.closing(get_db()) as conn:
        rows = conn.execute(
            f"SELECT * FROM tasks {where} ORDER BY created_at DESC", values
        ).fetchall()
    return [row_to_task(r) for r in rows]


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(body: TaskCreate):
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
            (body.title, body.description, body.priority, body.due_date.isoformat() if body.due_date else None),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_task(row)


@app.get("/tasks/overdue", response_model=list[Task])
def get_overdue_tasks():
    today = date.today().isoformat()
    with contextlib.closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE due_date < ? AND done = 0 ORDER BY due_date ASC",
            (today,),
        ).fetchall()
    return [row_to_task(r) for r in rows]


@app.get("/tasks/upcoming", response_model=list[Task])
def get_upcoming_tasks():
    today = date.today().isoformat()
    with contextlib.closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE due_date >= ? AND done = 0 ORDER BY due_date ASC",
            (today,),
        ).fetchall()
    return [row_to_task(r) for r in rows]


@app.get("/tasks/stats")
def get_stats():
    with contextlib.closing(get_db()) as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    return {"total": total, "done": done, "pending": total - done}


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with contextlib.closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_task(row)


def _apply_update(task_id: int, body: TaskUpdate) -> Task:
    fields, values = [], []
    if body.title is not None:
        fields.append("title = ?")
        values.append(body.title)
    if body.description is not None:
        fields.append("description = ?")
        values.append(body.description)
    if body.done is not None:
        fields.append("done = ?")
        values.append(int(body.done))
    if body.priority is not None:
        fields.append("priority = ?")
        values.append(body.priority)
    if body.due_date is not None:
        fields.append("due_date = ?")
        values.append(body.due_date.isoformat())
    if not fields:
        raise HTTPException(status_code=422, detail="No fields to update")
    values.append(task_id)
    with contextlib.closing(get_db()) as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_task(row)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, body: TaskUpdate):
    return _apply_update(task_id, body)


@app.patch("/tasks/{task_id}", response_model=Task)
def patch_task(task_id: int, body: TaskUpdate):
    return _apply_update(task_id, body)


@app.post("/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: int):
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.post("/tasks/{task_id}/reopen", response_model=Task)
def reopen_task(task_id: int):
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute("UPDATE tasks SET done = 0 WHERE id = ?", (task_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.delete("/tasks/completed", status_code=200)
def delete_completed_tasks():
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute("DELETE FROM tasks WHERE done = 1")
        conn.commit()
    return {"deleted": cur.rowcount}


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
