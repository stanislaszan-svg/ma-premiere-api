from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import contextlib

app = FastAPI(title="Task Manager API", version="1.0.0")

DB_PATH = "tasks.db"


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
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


init_db()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    done: bool
    created_at: str


def row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        done=bool(row["done"]),
        created_at=row["created_at"],
    )


@app.get("/tasks", response_model=list[Task])
def list_tasks(done: Optional[bool] = None):
    with contextlib.closing(get_db()) as conn:
        if done is None:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE done = ? ORDER BY created_at DESC", (int(done),)
            ).fetchall()
    return [row_to_task(r) for r in rows]


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(body: TaskCreate):
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            (body.title, body.description),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_task(row)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with contextlib.closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_task(row)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, body: TaskUpdate):
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


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with contextlib.closing(get_db()) as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
