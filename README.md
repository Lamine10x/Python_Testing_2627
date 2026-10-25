# GUDLFT — Plateforme de réservation de compétitions

Application Flask de démonstration pour la gestion des réservations de places
de compétitions par les clubs de powerlifting.

Le projet couvre les correctifs de la Phase 1, le tableau public des points
(Phase 2) et une interface d'administration complète, y compris la gestion
des points des clubs et l'ouverture ou la fermeture des inscriptions aux
compétitions.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Installation](#installation)
- [Lancement](#lancement)
- [Comptes de test](#comptes-de-test)
- [Tests unitaires](#tests-unitaires)
- [Rapport Flake8](#rapport-flake8)
- [Tests de performance](#tests-de-performance)
- [Ressources](#ressources)
- [Conventions Git](#conventions-git)
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
- Gestion des points des clubs :
  - crédit ou débit d'un montant entier positif ;
  - motif facultatif ;
  - contrôle du solde pour interdire un solde négatif ;
  - historique horodaté des ajustements avec l'administrateur, le motif et
    le solde après opération.
- Ouverture et fermeture des inscriptions par compétition :
  - bouton d'action direct depuis la liste des compétitions ;
  - case à cocher dans les formulaires d'ajout et de modification ;
  - blocage des réservations lorsque les inscriptions sont fermées ;
  - affichage de l'état sur le tableau de bord club.
- Templates dédiés dans `templates/admin/`.
- Identifiants stockés dans `admin.json`.
- Les ajustements de points sont conservés dans le champ `points_history`
  de chaque club ; l'état des inscriptions est stocké dans le champ
  `registration_open` de chaque compétition.
- Accès rapide : dans `Admin > Clubs`, le bouton `Points` ouvre la gestion
  des points ; dans `Admin > Compétitions`, le bouton `Fermer` ou `Ouvrir`
  change l'état des inscriptions.

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
88 tests passent
Couverture de server.py : 100 %
```

## Rapport Flake8

Commande utilisée :

```powershell
flake8 server.py tests/ locustfile.py generate_flake8_report.py --count --statistics --show-source
```

Générer le rapport HTML :

```powershell
python generate_flake8_report.py
```

Puis ouvrir `rapport_flake8.html` dans le navigateur.

Résultat :

```text
Version Flake8 : 7.4.1
Fichiers analysés : server.py, tests/, locustfile.py,
                    generate_flake8_report.py
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

Lancer un test sans interface graphique et générer le rapport HTML :

```powershell
locust -f locustfile.py --headless -u 6 -r 1 -t 30s `
  --host http://127.0.0.1:5000 --html=rapport_locust.html
```

Le scénario simule la consultation de l'accueil, la connexion d'un club,
le classement public, le formulaire de réservation et les routes admin.

Le rapport HTML est disponible dans `rapport_locust.html`.

### Dernier test de performance

Test réalisé avec 6 utilisateurs pendant 30 secondes :

```text
Requêtes        : 97
Échecs          : 0
Temps moyen     : 2 ms
95e percentile  : 4 ms
Temps maximum   : 7 ms
```

Les seuils du cahier des charges sont respectés :

- liste des compétitions : moins de 5 secondes ;
- mise à jour des points : moins de 2 secondes.

## Ressources

- Dépôt GitHub : <https://github.com/Lamine10x/Python_Testing_2627>
- Documentation Flask : <https://flask.palletsprojects.com/>
- Documentation pytest : <https://docs.pytest.org/>
- Documentation Flake8 : <https://flake8.pycqa.org/>
- Documentation Locust : <https://docs.locust.io/>

## Conventions Git

- Branche principale : `main`.
- Branches de travail : `<type>/nom-descriptif`, par exemple
  `bug/correction-reservation` ou `feature/tableau-public`.
- Types utilisés : `bug/`, `feature/` et `improvement/`.
- Une branche porte un seul correctif ou une seule fonctionnalité.
- La branche `QA` sert à la revue finale et n'est pas fusionnée dans `main`.

## Structure du projet

```text
.
├── server.py                 # Application Flask et routes
├── clubs.json                # Clubs et points
├── competitions.json         # Compétitions et places
├── admin.json                # Comptes administrateur
├── locustfile.py             # Scénario de test de performance
├── generate_flake8_report.py # Générateur du rapport Flake8 HTML
├── rapport_flake8.html       # Rapport Flake8 généré
├── rapport_locust.html       # Rapport de performance Locust
├── requirements.txt          # Dépendances Python
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
