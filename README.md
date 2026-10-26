# GUDLFT — Réservation de compétitions

Application Flask développée dans le cadre du projet OpenClassrooms, permettant aux secrétaires de clubs de réserver des places pour les compétitions de powerlifting avec leurs points.

---

## Sommaire

1. [Le projet](#le-projet)
2. [Installation & Lancement](#installation--lancement)
3. [Comptes pour tester](#comptes-pour-tester)
4. [Tests & Qualité du code](#tests--qualité-du-code)
5. [Tests de charge (Locust)](#tests-de-charge-locust)
6. [Organisation Git](#organisation-git)
7. [Structure des fichiers](#structure-des-fichiers)

---

## Le projet

L'application d'origine comportait plusieurs dysfonctionnements et manques fonctionnels. Le travail a consisté à assainir la base de code, corriger les bugs critiques, ajouter le tableau d'affichage public et compléter l'espace de gestion.

### Règles de réservation
- **1 place = 1 point**.
- **Limite de 12 places** par compétition : un club ne peut pas inscrire plus de 12 athlètes sur une même compétition, et le cumul de tous les clubs ne peut pas dépasser 12 places au total.
- **Solde non négatif** : impossible de réserver plus de places que le solde de points disponible.
- **Dates passées** : les compétitions terminées ne sont plus ouvertes à la réservation.

### Espace Club (`/`)
- Connexion sécurisée par email de secrétaire.
- Tableau de bord avec solde de points, places réservées, prochaines échéances et alertes sur les places libérées.
- Formulaire de réservation contrôlé (nombre entier positif, calcul du quota restant, déduction automatique des points).
- Historique complet des opérations de points (débits de réservation, remboursements, ajustements).

### Classement public (`/displayBoard` ou `/points`)
- Accessible sans être connecté.
- Classement général des clubs triés par points.
- Classement par compétition pour visualiser la répartition des places réservées.

### Espace Administration (`/admin/login`)
- Accès sécurisé par mot de passe en session.
- Gestion des clubs et des compétitions (création, mise à jour, suppression).
- Gestion des points (crédit / débit contrôlé avec motif obligatoire).
- Ouverture / fermeture manuelle des inscriptions d'une compétition.
- Annulation de réservation avec remboursement automatique des points au club.
- Journal d'audit (`audit.json`) traçant les connexions, modifications et réservations.

---

## Installation & Lancement

### Prérequis
- Python 3.10 ou supérieur
- Git

### Installation

```powershell
# Cloner le dépôt
git clone https://github.com/Lamine10x/Python_Testing_2627.git
cd Python_Testing_2627

# Créer et activer l'environnement virtuel
python -m venv env
.\env\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
```

*(Sur Linux/macOS : `source env/bin/activate`)*

### Démarrage local

```powershell
$env:FLASK_APP = "server"
flask run
```

L'application tourne sur **http://127.0.0.1:5000**.

---

## Comptes pour tester

### Clubs (secrétaires)
Pour se connecter sur l'accueil, utilisez simplement l'email d'un club :
- `john@simplylift.co` (Simply Lift — 13 pts)
- `kate@shelifts.co.uk` (She Lifts — 12 pts)
- `admin@irontemple.com` (Iron Temple — 4 pts)

### Administrateur
Rendez-vous sur **http://127.0.0.1:5000/admin/login** :
- **Email** : `admin@gudlft.com`
- **Mot de passe** : `admin1234`

*(Ces identifiants sont configurables dans `admin.json`).*

---

## Tests & Qualité du code

### Lancer la suite de tests

Le projet utilise **pytest** avec une couverture totale du fichier serveur :

```powershell
# Lancer tous les tests
pytest tests/

# Avec rapport de couverture
pytest --cov=server --cov-report=term-missing tests/
```

> **État actuel** : 136 tests passés avec succès, 100 % de couverture sur `server.py`.

### Linting (PEP8 / Flake8)

Le code respecte strictement les normes PEP8 :

```powershell
flake8 --exclude=env
```

Pour générer un rapport visuel :
```powershell
python generate_flake8_report.py
```
Le fichier généré est consultable dans `rapport_flake8.html` (0 erreur).

---

## Tests de charge (Locust)

Des tests de performance ont été exécutés avec Locust pour vérifier la réactivité du serveur :

```powershell
# Avec interface web sur http://localhost:8089
locust -f locustfile.py --host http://127.0.0.1:5000

# Ou directement en ligne de commande avec export HTML
locust -f locustfile.py --headless -u 6 -r 1 -t 30s --host http://127.0.0.1:5000 --html=rapport_locust.html
```

**Résultats constatés (6 utilisateurs / 30s) :**
- 0 requête en échec.
- Temps de réponse moyen : ~2 ms (largement sous le seuil demandé de 2s / 5s).

---

## Organisation Git

Le projet suit un workflow par branches thématiques :
- `main` : branche principale stable.
- `QA` : branche de validation.
- `bug/<nom>` : branches de correctifs ciblés.
- `feature/<nom>` : branches pour les nouveaux modules.

Chaque branche est intégrée avec `--no-ff` pour conserver un historique clair et lisible dans l'arbre Git.

---

## Structure des fichiers

```text
.
├── server.py                 # Application Flask, routes et logique métier
├── clubs.json                # Données des clubs, points et réservations
├── competitions.json         # Données des compétitions et places
├── admin.json                # Identifiants administrateurs
├── audit.json                # Historique du journal d'audit
├── requirements.txt          # Dépendances Python
├── locustfile.py             # Script de test de charge Locust
├── generate_flake8_report.py # Script pour générer le rapport Flake8 HTML
├── static/
│   └── css/
│       └── style.css         # Feuilles de style
├── templates/
│   ├── index.html            # Page d'accueil / connexion club
│   ├── welcome.html          # Espace secrétaire de club
│   ├── booking.html          # Formulaire de réservation
│   ├── display_board.html    # Classement public des points
│   └── admin/                # Espace d'administration
└── tests/
    ├── conftest.py           # Fixtures de test
    └── unit/                 # Tests unitaires
```
