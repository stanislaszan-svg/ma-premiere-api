# Ma Première API — Gestionnaire de Tâches

![Tests](https://github.com/stanislaszan-svg/ma-premiere-api/actions/workflows/tests.yml/badge.svg)

API REST de gestion de tâches construite avec **FastAPI** et **SQLite**, avec une interface web intégrée.

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

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Interface web |
| `http://localhost:8000/docs` | Documentation Swagger interactive |

## Interface web

L'application inclut un frontend complet servi directement par FastAPI (`/`).

**Fonctionnalités :**
- Tableau de bord avec statistiques (total, terminées, en cours, en retard)
- Barres de progression par priorité et nuage de tags cliquables
- Cartes de tâches avec badges de priorité, tags et date d'échéance
- Formulaire complet : titre, description, priorité, date d'échéance, tags (chips)
- Barre de recherche globale (titre, description, tags) avec debounce
- Filtres : Toutes, Terminées, En retard, Aujourd'hui, À venir
- Actions par carte : terminer, rouvrir, modifier, supprimer
- Raccourcis clavier : `N` = nouvelle tâche, `Esc` = fermer, `Ctrl+Entrée` = enregistrer

## Endpoints

### Tâches

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/tasks` | Lister les tâches — params optionnels : `?done=true\|false`, `?priority=low\|medium\|high`, `?tag=<tag>`, combinables |
| `POST` | `/tasks` | Créer une tâche |
| `GET` | `/tasks/{id}` | Récupérer une tâche |
| `PUT` | `/tasks/{id}` | Remplacer une tâche |
| `PATCH` | `/tasks/{id}` | Modifier partiellement une tâche |
| `DELETE` | `/tasks/{id}` | Supprimer une tâche |

### Actions

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/tasks/{id}/complete` | Marquer une tâche comme terminée |
| `POST` | `/tasks/{id}/reopen` | Rouvrir une tâche terminée |
| `DELETE` | `/tasks/completed` | Supprimer toutes les tâches terminées |

### Filtres par date

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/tasks/today` | Tâches dues aujourd'hui, non terminées |
| `GET` | `/tasks/overdue` | Tâches en retard (due_date dépassée, non terminées) |
| `GET` | `/tasks/upcoming` | Tâches à venir (due_date ≥ aujourd'hui, non terminées) |

### Recherche et tags

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/tasks/search?q=` | Recherche plein texte : titre, description et tags |
| `GET` | `/tasks/tags` | Lister tous les tags distincts, triés alphabétiquement |

### Historique

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/tasks/{id}/history` | Historique des modifications d'une tâche (champ, ancienne valeur, nouvelle valeur, horodatage) |
| `DELETE` | `/tasks/{id}/history` | Effacer l'historique d'une tâche — retourne `{"deleted": N}` |

### Statistiques

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/tasks/stats` | Total, terminées, en cours, détail par priorité, par tag et par date d'échéance |

## Modèle de tâche

```json
{
  "id": 1,
  "title": "Acheter du lait",
  "description": "2 litres",
  "done": false,
  "priority": "high",
  "due_date": "2026-12-31",
  "tags": ["courses", "urgent"],
  "created_at": "2026-06-06 10:00:00"
}
```

- `priority` : `"low"`, `"medium"` (défaut), `"high"`
- `due_date` : format ISO 8601 `YYYY-MM-DD`, optionnel
- `tags` : liste de strings, défaut `[]`

## Exemples curl

**Créer une tâche**
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Acheter du lait", "priority": "high", "due_date": "2026-12-31", "tags": ["courses"]}'
```

**Filtrer par priorité et statut**
```bash
curl "http://localhost:8000/tasks?priority=high&done=false"
```

**Recherche plein texte**
```bash
curl "http://localhost:8000/tasks/search?q=réunion"
```

**Historique des modifications**
```bash
curl http://localhost:8000/tasks/1/history
```

**Statistiques**
```bash
curl http://localhost:8000/tasks/stats
```

## Tests

```bash
pip install pytest httpx
pytest test_api.py -v
```

**Vérification du frontend (nécessite Playwright) :**
```bash
pip install playwright
python -m playwright install chromium
python verify_frontend.py
```
