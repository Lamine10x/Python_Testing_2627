# GUDLFT — Plateforme de réservation de compétitions

Application Flask de démonstration pour la gestion des réservations de places
de compétitions par les clubs de powerlifting.

Le projet couvre les correctifs de la Phase 1, le tableau public des points
(Phase 2) et une interface d'administration complète.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Installation](#installation)
- [Lancement](#lancement)
- [Comptes de test](#comptes-de-test)
- [Tests unitaires](#tests-unitaires)
- [Rapport Flake8](#rapport-flake8)
- [Tests de performance](#tests-de-performance)
- [Structure du projet](#structure-du-projet)

## Fonctionnalités

### Phase 1 — Correctifs

- Gestion propre des emails inconnus lors de la connexion (HTTP 401).
- Gestion des clubs et compétitions inconnus (HTTP 404).
- Blocage des réservations pour une compétition déjà passée.
- Validation des places saisies : nombre positif et entier.
- Limite stricte de 12 places par club et par compétition, réservations
  cumulées incluses.
- Blocage des réservations si les points du club sont insuffisants.
- Blocage de la surréservation par rapport aux places restantes.
- Déduction correcte des points du club après réservation.
- Harmonisation des types numériques lus depuis les fichiers JSON.
- Correction des balises HTML invalides et des formulaires.
- Nettoyage complet de la session à la déconnexion avec message de confirmation.
- Mise en conformité PEP8 et correction des alertes Flake8.

### Phase 2 — Tableau public des points

- Page publique accessible sans connexion :
  - `/displayBoard`
  - alias `/points`
- Affichage de tous les clubs et de leurs points.
- Classement avec mise en avant des trois premiers clubs.
- Liens vers le classement depuis la page d'accueil et le tableau de bord club.

### Interface d'administration

- Connexion et déconnexion administrateur protégées par session.
- Tableau de bord avec statistiques :
  - nombre de clubs ;
  - nombre de compétitions ;
  - total des points.
- Gestion complète des clubs :
  - liste ;
  - ajout ;
  - modification ;
  - suppression.
- Gestion complète des compétitions :
  - liste ;
  - ajout ;
  - modification ;
  - suppression.
- Templates dédiés dans `templates/admin/`.
- Identifiants stockés dans `admin.json`.

## Technologies

- Python 3.x
- Flask 1.1.2
- Jinja2
- pytest et pytest-cov
- Flake8
- Locust
- Fichiers JSON comme base de données légère

## Installation

Depuis PowerShell, à la racine du projet :

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sous cmd.exe, l'activation se fait avec :

```bat
env\Scripts\activate.bat
```

Sous Linux ou macOS :

```bash
source env/bin/activate
```

## Lancement

Toujours depuis la racine du projet, avec l'environnement virtuel activé :

```powershell
$env:FLASK_APP = "server"
$env:FLASK_ENV = "development"
flask run
```

Version en une seule ligne :

```powershell
$env:FLASK_APP="server"; $env:FLASK_ENV="development"; flask run
```

Adresses utiles :

- Application club : <http://127.0.0.1:5000>
- Classement public : <http://127.0.0.1:5000/displayBoard>
- Administration : <http://127.0.0.1:5000/admin/login>

Les variables d'environnement sont valables uniquement pour la session
PowerShell en cours.

## Comptes de test

### Clubs

| Email | Club |
| --- | --- |
| `john@simplylift.co` | Simply Lift |
| `admin@irontemple.com` | Iron Temple |
| `kate@shelifts.co.uk` | She Lifts |

### Administration

| Champ | Valeur |
| --- | --- |
| Email | `admin@gudlft.com` |
| Mot de passe | `admin1234` |
| URL | <http://127.0.0.1:5000/admin/login> |

Les identifiants administrateur peuvent être modifiés dans `admin.json`.
Pensez à changer le mot de passe par défaut avant tout déploiement réel.

## Tests unitaires

Lancer tous les tests :

```powershell
pytest tests/
```

Lancer les tests avec le rapport de couverture :

```powershell
pytest --cov=server tests/
```

Générer un rapport HTML de couverture :

```powershell
pytest --cov=server --cov-report=html tests/
```

Le rapport HTML est disponible dans `htmlcov/index.html`.

### Résultat actuel

```text
66 tests passent
Couverture de server.py : 100 %
```

## Rapport Flake8

Commande utilisée :

```powershell
flake8 server.py tests/ locustfile.py --count --statistics --show-source
```

Résultat :

```text
Version Flake8 : 7.4.1
Fichiers analysés : server.py, tests/, locustfile.py
Nombre d'erreurs : 0
```

Aucune erreur PEP8 / Flake8 n'a été détectée.

## Tests de performance

L'application Flask doit être lancée avant de démarrer Locust.

Lancer Locust avec l'interface web :

```powershell
locust -f locustfile.py --host http://127.0.0.1:5000
```

Puis ouvrir <http://localhost:8089> et renseigner :

- 6 utilisateurs ;
- taux d'apparition : 1 utilisateur/seconde.

Lancer un test sans interface graphique :

```powershell
locust -f locustfile.py --headless -u 6 -r 1 -t 30s --host http://127.0.0.1:5000
```

Le scénario simule la consultation de l'accueil, la connexion d'un club,
le classement public, le formulaire de réservation et les routes admin.

### Dernier test de fumée

```text
6 utilisateurs
24 requêtes
0 échec
```

## Structure du projet

```text
.
├── server.py                 # Application Flask et routes
├── clubs.json                # Clubs et points
├── competitions.json         # Compétitions et places
├── admin.json                # Comptes administrateur
├── locustfile.py             # Scénario de test de performance
├── requirements.txt          # Dépendances Python
├── LANCEMENT.txt             # Aide-mémoire des commandes
├── static/
│   └── css/
│       └── style.css         # Styles de l'application
├── templates/
│   ├── index.html
│   ├── welcome.html
│   ├── booking.html
│   ├── display_board.html
│   └── admin/                # Templates d'administration
└── tests/
    ├── conftest.py
    └── unit/                 # Tests unitaires
```
