# Ma Première API — Gestionnaire de Tâches

API REST de gestion de tâches construite avec **FastAPI** et **SQLite**.

## Stack

- [FastAPI](https://fastapi.tiangolo.com/) — framework web
- [SQLite](https://www.sqlite.org/) — base de données embarquée
- [Pydantic](https://docs.pydantic.dev/) — validation des données
- [Uvicorn](https://www.uvicorn.org/) — serveur ASGI

## Installation

```bash
pip install -r requirements.txt
```

## Démarrage

```bash
uvicorn main:app --reload
```

L'API est disponible sur `http://localhost:8000`.
La documentation interactive Swagger est accessible sur `http://localhost:8000/docs`.

## Endpoints

| Méthode  | Route           | Description              |
|----------|-----------------|--------------------------|
| `GET`    | `/tasks`        | Lister toutes les tâches (param optionnel : `?done=true\|false`) |
| `GET`    | `/tasks/stats`  | Nombre de tâches total, terminées et en cours |
| `POST`   | `/tasks`        | Créer une tâche          |
| `GET`    | `/tasks/{id}`   | Récupérer une tâche      |
| `PUT`    | `/tasks/{id}`   | Modifier une tâche       |
| `PATCH`  | `/tasks/{id}`   | Modifier partiellement une tâche |
| `POST`   | `/tasks/{id}/complete` | Marquer une tâche comme terminée |
| `POST`   | `/tasks/{id}/reopen`   | Rouvrir une tâche terminée |
| `DELETE` | `/tasks/completed` | Supprimer toutes les tâches terminées |
| `DELETE` | `/tasks/{id}`   | Supprimer une tâche      |

## Exemples

**Créer une tâche**
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Acheter du lait", "description": "2 litres"}'
```

**Marquer comme terminée**
```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"done": true}'
```

**Supprimer une tâche**
```bash
curl -X DELETE http://localhost:8000/tasks/1
```

## Tests

```bash
pip install pytest httpx
pytest test_api.py -v
```
