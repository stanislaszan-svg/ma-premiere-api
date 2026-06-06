"""Peuple la base avec 53 tâches de démonstration."""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

def api(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(BASE + path, data=data, method=method,
           headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

tasks = [
    # ── Travail ────────────────────────────────────────────────────────────
    {"title": "Préparer la réunion de lancement", "description": "Slides, agenda et invitations à envoyer", "priority": "high", "due_date": "2026-06-10", "tags": ["travail", "réunion"]},
    {"title": "Rédiger le rapport mensuel", "description": "Inclure KPIs, chiffres de vente et commentaires", "priority": "high", "due_date": "2026-06-15", "tags": ["travail", "rapport"]},
    {"title": "Revoir les pull requests en attente", "priority": "medium", "due_date": "2026-06-07", "tags": ["travail", "dev", "code"]},
    {"title": "Mettre à jour la documentation technique", "description": "Documenter les nouvelles routes API", "priority": "medium", "due_date": "2026-06-20", "tags": ["travail", "dev", "docs"]},
    {"title": "Planifier le sprint suivant", "priority": "high", "due_date": "2026-06-08", "tags": ["travail", "agile"]},
    {"title": "Former le nouveau stagiaire", "description": "Présenter les outils, processus et base de code", "priority": "medium", "due_date": "2026-06-12", "tags": ["travail", "formation"]},
    {"title": "Audit de sécurité de l'application", "priority": "high", "due_date": "2026-06-30", "tags": ["travail", "dev", "securite"]},
    {"title": "Négocier le contrat fournisseur", "description": "Comparer 3 offres et préparer une contre-proposition", "priority": "high", "due_date": "2026-06-18", "tags": ["travail", "finance"]},
    {"title": "Déployer la version 2.0 en production", "priority": "high", "due_date": "2026-07-01", "tags": ["travail", "dev", "deploiement"]},
    {"title": "Analyser les retours utilisateurs", "description": "Consolider les feedbacks du mois de mai", "priority": "medium", "tags": ["travail", "produit"]},

    # ── Personnel ──────────────────────────────────────────────────────────
    {"title": "Réserver les vacances d'été", "description": "Comparer Grèce, Portugal et Croatie", "priority": "medium", "due_date": "2026-06-25", "tags": ["personnel", "voyage"]},
    {"title": "Renouveler le passeport", "priority": "high", "due_date": "2026-07-15", "tags": ["personnel", "administratif"]},
    {"title": "Faire la déclaration d'impôts", "priority": "high", "due_date": "2026-06-30", "tags": ["personnel", "finance", "administratif"]},
    {"title": "Classer les papiers administratifs", "priority": "low", "tags": ["personnel", "administratif"]},
    {"title": "Trier et donner les vieux vêtements", "priority": "low", "tags": ["personnel", "maison"]},
    {"title": "Réparer la fuite du robinet", "priority": "medium", "due_date": "2026-06-09", "tags": ["personnel", "maison"]},
    {"title": "Acheter un cadeau anniversaire pour Marie", "priority": "high", "due_date": "2026-06-14", "tags": ["personnel", "shopping"]},
    {"title": "Appeler les parents", "priority": "medium", "due_date": "2026-06-08", "tags": ["personnel", "famille"]},
    {"title": "Organiser le déménagement", "description": "Comparer les devis de 3 sociétés de déménagement", "priority": "high", "due_date": "2026-08-01", "tags": ["personnel", "maison"]},
    {"title": "Mettre à jour le testament", "priority": "low", "tags": ["personnel", "administratif", "finance"]},

    # ── Santé ──────────────────────────────────────────────────────────────
    {"title": "Rendez-vous chez le dentiste", "priority": "medium", "due_date": "2026-06-20", "tags": ["sante"]},
    {"title": "Bilan de santé annuel", "priority": "medium", "due_date": "2026-07-10", "tags": ["sante", "medecin"]},
    {"title": "Commander les lentilles de contact", "priority": "medium", "due_date": "2026-06-10", "tags": ["sante", "shopping"]},
    {"title": "S'inscrire à la salle de sport", "priority": "low", "tags": ["sante", "sport"]},
    {"title": "Courir 3 fois par semaine", "description": "Objectif : 5 km en moins de 30 min", "priority": "medium", "tags": ["sante", "sport"]},
    {"title": "Prendre les vitamines chaque matin", "priority": "low", "tags": ["sante"]},
    {"title": "Consulter un nutritionniste", "priority": "low", "due_date": "2026-07-30", "tags": ["sante"]},

    # ── Courses & Achats ───────────────────────────────────────────────────
    {"title": "Faire les courses de la semaine", "description": "Légumes, fruits, pain, laitage", "priority": "medium", "due_date": "2026-06-07", "tags": ["courses", "maison"]},
    {"title": "Acheter un nouveau laptop", "description": "Budget max 1500€, comparer Dell XPS et MacBook", "priority": "high", "due_date": "2026-06-30", "tags": ["shopping", "travail"]},
    {"title": "Commander les fournitures de bureau", "priority": "low", "tags": ["shopping", "travail"]},
    {"title": "Acheter un vélo électrique", "priority": "medium", "due_date": "2026-07-15", "tags": ["shopping", "transport"]},
    {"title": "Renouveler l'abonnement logiciel", "priority": "high", "due_date": "2026-06-11", "tags": ["shopping", "travail", "finance"]},

    # ── Apprentissage ──────────────────────────────────────────────────────
    {"title": "Terminer le cours FastAPI sur Udemy", "description": "Modules 7 à 12 restants", "priority": "medium", "due_date": "2026-06-28", "tags": ["apprentissage", "dev"]},
    {"title": "Lire Clean Code de Robert Martin", "priority": "low", "tags": ["apprentissage", "dev"]},
    {"title": "Pratiquer l'espagnol 20 min par jour", "priority": "medium", "tags": ["apprentissage", "langue"]},
    {"title": "Suivre le MOOC machine learning", "priority": "medium", "due_date": "2026-07-31", "tags": ["apprentissage", "dev", "ia"]},
    {"title": "Regarder les conférences PyCon 2026", "priority": "low", "tags": ["apprentissage", "dev"]},

    # ── Finance ────────────────────────────────────────────────────────────
    {"title": "Payer la facture d'électricité", "priority": "high", "due_date": "2026-06-09", "tags": ["finance", "maison"]},
    {"title": "Virer sur le compte épargne", "description": "Objectif mensuel : 500€", "priority": "medium", "due_date": "2026-06-30", "tags": ["finance"]},
    {"title": "Revoir le budget mensuel", "priority": "medium", "due_date": "2026-06-30", "tags": ["finance"]},
    {"title": "Contacter la banque pour renégocier le prêt", "priority": "medium", "due_date": "2026-07-15", "tags": ["finance", "administratif"]},

    # ── Projets personnels ─────────────────────────────────────────────────
    {"title": "Lancer le blog technique", "description": "Configurer Hugo, rédiger le premier article", "priority": "medium", "due_date": "2026-07-01", "tags": ["projet", "dev", "ecriture"]},
    {"title": "Apprendre à faire du pain au levain", "priority": "low", "tags": ["projet", "cuisine"]},
    {"title": "Monter le portfolio en ligne", "description": "Mettre en avant les 5 meilleurs projets", "priority": "high", "due_date": "2026-06-30", "tags": ["projet", "dev", "travail"]},
    {"title": "Contribuer à un projet open source", "priority": "low", "tags": ["projet", "dev"]},
    {"title": "Écrire une nouvelle courte", "priority": "low", "tags": ["projet", "ecriture"]},

    # ── En retard ──────────────────────────────────────────────────────────
    {"title": "Envoyer le contrat signé", "priority": "high", "due_date": "2026-05-30", "tags": ["travail", "administratif"]},
    {"title": "Rappeler le client Dupont", "description": "Relance suite à la démo du 20 mai", "priority": "high", "due_date": "2026-05-28", "tags": ["travail", "client"]},
    {"title": "Rembourser Pierre", "description": "45€ pour le dîner du 15 mai", "priority": "medium", "due_date": "2026-06-01", "tags": ["personnel", "finance"]},
    {"title": "Renouveler l'assurance voiture", "priority": "high", "due_date": "2026-06-03", "tags": ["personnel", "finance", "administratif"]},

    # ── Aujourd'hui ────────────────────────────────────────────────────────
    {"title": "Standup quotidien", "priority": "high", "due_date": "2026-06-06", "tags": ["travail", "reunion"]},
    {"title": "Relire les emails de la nuit", "priority": "medium", "due_date": "2026-06-06", "tags": ["travail"]},
    {"title": "Préparer le dîner pour ce soir", "description": "Invités à 20h — menu 3 plats", "priority": "medium", "due_date": "2026-06-06", "tags": ["personnel", "cuisine"]},
]

COMPLETE = {
    "Rappeler le client Dupont", "Standup quotidien",
    "Revoir les pull requests en attente", "Faire les courses de la semaine",
    "Prendre les vitamines chaque matin", "Appeler les parents",
    "Payer la facture d'électricité", "Rédiger le rapport mensuel",
    "Commander les lentilles de contact", "Trier et donner les vieux vêtements",
}

PATCHES = {
    "Déployer la version 2.0 en production": {"priority": "high", "due_date": "2026-06-25", "description": "Avancé d'une semaine — approbation reçue"},
    "Acheter un nouveau laptop":             {"description": "Budget revu à 1800€ — approbation DG obtenue"},
    "Monter le portfolio en ligne":          {"description": "Inclure projets API, CV interactif et page contact"},
}

created = []
for t in tasks:
    created.append(api("POST", "/tasks", t))

for task in created:
    if task["title"] in COMPLETE:
        api("POST", f'/tasks/{task["id"]}/complete')

for task in created:
    if task["title"] in PATCHES:
        api("PATCH", f'/tasks/{task["id"]}', PATCHES[task["title"]])

stats = api("GET", "/tasks/stats")
ds    = stats["due_date_summary"]
print(f"Taches creees    : {len(created)}")
print(f"Terminees        : {len(COMPLETE)}")
print(f"Modifiees        : {len(PATCHES)}")
print(f"Total en base    : {stats['total']}")
print(f"Done             : {stats['done']}")
print(f"Pending          : {stats['pending']}")
print(f"Overdue          : {ds['overdue']}")
print(f"Today            : {ds['today']}")
print(f"Upcoming         : {ds['upcoming']}")
print(f"Tags distincts   : {len(stats['by_tag'])}")
