# GUDLFT — Plateforme de réservation de compétitions

Application Flask de démonstration pour la gestion des réservations de places
de compétitions par les clubs de powerlifting.

Le projet couvre les correctifs de la Phase 1, le tableau public des points
(Phase 2), un espace club enrichi (réservations, quota, historique complet,
filtres et accessibilité) et une interface d'administration complète, y
compris la gestion des réservations, l'annulation avec remboursement, la
gestion des points, l'ouverture ou la fermeture des inscriptions et le
journal d'audit global.

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
- [Conventions Git et workflow](#conventions-git-et-workflow)
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
- Affichage de tous les clubs et de leurs points, triés par points décroissants.
- Classement avec mise en avant des trois premiers clubs.
- Sélecteur de compétition sur le classement public :
  - classement général des points des clubs ;
  - classement par compétition basé sur les places réservées ;
  - affichage de la date, des places restantes et de l'état des inscriptions ;
  - état vide lorsqu'aucune place n'a encore été réservée.
- Exemple de classement par compétition :
  `/displayBoard?competition=Future%20Open`.
- Liens vers le classement depuis la page d'accueil et le tableau de bord club.
- Les réservations sont enregistrées dans le champ `booked` de chaque club,
  ce qui permet de conserver le classement par compétition après redémarrage.

### Espace club — réservations et points

- Tableau de bord club avec six indicateurs : points disponibles, places
  réservées, points consommés, prochaine échéance, inscriptions ouvertes et
  compétitions totales.
- Bloc « Prochaines échéances » avec les trois prochaines compétitions, leur
  date, les places restantes et le nombre de jours restants.
- Bloc « Places libérées récemment » alimenté par le journal d'audit : le club
  voit immédiatement les places rendues par les autres clubs, sans attendre la
  mise à jour du classement.
- Section « Mes réservations » :
  - compétitions déjà réservées par le club ;
  - nombre de places réservées ;
  - points engagés ;
  - quota restant sur les 12 places autorisées ;
  - statut de la réservation : confirmée, terminée ou inscriptions fermées ;
  - filtres serveur par statut et par compétition, avec réinitialisation ;
  - barre de progression accessible pour visualiser le quota consommé.
- Affichage du quota restant et du nombre de places déjà réservées sur
  chaque carte de compétition.
- Calcul du maximum réservable à partir de trois contraintes :
  - quota restant du club pour la compétition ;
  - places encore disponibles dans la compétition ;
  - solde de points du club.
- Formulaire de réservation enrichi :
  - rappel des places disponibles, du solde de points, des places déjà
    réservées et du maximum réservable ;
  - attribut `max` aligné sur le maximum réellement réservable ;
  - récapitulatif dynamique du coût, du solde après réservation et du quota
    après réservation ;
  - conservation de la saisie lorsqu'une erreur de validation est détectée.
- Redirection Post/Redirect/Get (HTTP 303) après une réservation réussie,
  avec message de confirmation et retour sur la section « Mes réservations ».
- Historique des points côté club :
  - affichage de l'historique complet, sans limite aux dix derniers mouvements ;
  - distinction entre réservation, remboursement et ajustement administrateur ;
  - date, motif, variation et solde après opération ;
  - enregistrement automatique du débit de points lors d'une réservation.
- Accessibilité renforcée :
  - lien d'évitement vers le contenu principal ;
  - navigation et formulaires libellés en ARIA ;
  - tableaux avec légendes, en-têtes `scope="col"` et barres de progression
    accessibles ;
  - messages flash annoncés via `role="status"` et `aria-live` ;
  - styles de focus visibles au clavier ;
  - icônes décoratives masquées aux lecteurs d'écran.
- Messages flash différenciés : succès, erreur et information.
- Route `GET /dashboard/<club>` utilisée comme cible de la redirection après
  réservation et pour appliquer les filtres.
- Chaque réservation est tracée dans le journal d'audit global `audit.json`.


### Interface d'administration

- Connexion et déconnexion administrateur protégées par session.
- Tableau de bord avec six indicateurs :
  - nombre de clubs ;
  - nombre de compétitions ;
  - total des points ;
  - réservations actives ;
  - places réservées ;
  - nombre d'entrées d'audit.
- Gestion des réservations :
  - vue consolidée par club et compétition ;
  - filtres par club, compétition et statut ;
  - indicateurs des places réservées et des points remboursables ;
  - formulaire d'annulation partielle ou totale ;
  - remboursement automatique de 1 point par place annulée ;
  - remise immédiate des places dans la compétition ;
  - mise à jour de la réservation du club et de son historique de points ;
  - message de confirmation avec le nouveau solde.
- Journal d'audit global :
  - conservation des 500 dernières opérations dans `audit.json` ;
  - traçabilité des connexions et déconnexions administrateur ;
  - traçabilité des ajouts, modifications et suppressions de clubs ;
  - traçabilité des crédits et débits de points ;
  - traçabilité des ajouts, modifications et suppressions de compétitions ;
  - traçabilité de l'ouverture et de la fermeture des inscriptions ;
  - traçabilité des réservations et des annulations/remboursements ;
  - filtres par catégorie, action et acteur ;
  - affichage de l'acteur, de la cible, de la date et d'un résumé lisible.
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
  - historique complet et horodaté des mouvements avec l'administrateur, le
    type, le motif et le solde après opération.
- Ouverture et fermeture des inscriptions par compétition :
  - bouton d'action direct depuis la liste des compétitions ;
  - case à cocher dans les formulaires d'ajout et de modification ;
  - blocage des réservations lorsque les inscriptions sont fermées ;
  - affichage de l'état sur le tableau de bord club.
- Templates dédiés dans `templates/admin/`.
- Routes principales : `/admin/reservations`, `/admin/audit` et
  `/admin/reservations/<club>/<competition>/cancel`.
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
135 tests passent
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

## Conventions Git et workflow

### Nommage des branches

- Branche principale : `main`.
- Branches de travail : `<type>/nom-descriptif`, par exemple
  `bug/correction-reservation`, `feature/tableau-public` ou
  `docs/documentation-pdf`.
- Types utilisés : `bug/`, `feature/`, `improvement/` et `docs/`.
- Une branche porte un seul correctif ou une seule fonctionnalité.
- Les branches mergées sont conservées pour garder la traçabilité.

### Workflow de livraison

1. Créer la branche depuis `main` avant de commencer :

   ```powershell
   git switch main
   git pull origin main
   git switch -c feature/nom-de-la-fonctionnalite
   ```

2. Développer, tester et commiter sur la branche.

3. Pousser la branche et, si nécessaire, ouvrir une pull request :

   ```powershell
   git push -u origin feature/nom-de-la-fonctionnalite
   ```

4. Intégrer dans `main` avec un commit de merge explicite :

   ```powershell
   git switch main
   git merge --no-ff feature/nom-de-la-fonctionnalite `
     -m "Merge : nom de la fonctionnalite"
   git push origin main
   ```

5. Après validation, aligner `QA` sur `main` :

   ```powershell
   git branch -f QA main
   git push --force-with-lease origin QA
   ```

Le merge `--no-ff` est obligatoire même lorsque Git pourrait faire un
fast-forward : l'historique doit garder une trace visible de la branche.

### État des branches

Au moment de cette mise à jour, toutes les branches de travail sont mergées
dans `main` :

| Branche | Commit | État |
| --- | --- | --- |
| `main` | dernier commit | Branche de livraison |
| `QA` | = `main` | Miroir de `main` pour la revue finale |
| `feature/espace-club-reservations-historique` | `1302182` | Mergée |
| `docs/retrait-reference-pdf-supprime` | — | Mergée |
| `docs/pdf-documentation-fonctionnalites-bugs` | — | Mergée |
| `feature/gestion-points-et-inscriptions` | `06cd9b0` | Mergée |
| `feature/classement-public-par-competition` | `8e5f975` | Mergée |
| `feature/tableau-de-bord-admin` | `88aa5ca` | Mergée |
| `feature/tableau-public-points-clubs` | `9c4b08a` | Mergée |
| `bug/...` | — | Toutes mergées |

Historique récent :

```text
*   Merge : retrait reference PDF supprime
|\
| * Docs : retrait reference PDF supprime
|/
*   Merge : espace club reservations et historique
|\
| * Feature : mes reservations quota et historique des points
|/
*   Merge : documentation PDF fonctionnalites et bugs
|\
| * Docs : ajout du PDF de documentation
* |   Merge : classement public par competition
|\ \
| |/
| * Feature : classement public par competition
* |   Merge : gestion des points et des inscriptions
|\ \
| |/
| * Feature : gestion des points et des inscriptions
|/
* Fix : chargement de admin.json avec BOM UTF-8
```

Vérification :

```powershell
git branch --no-merged main
git branch -r --no-merged main
```

Les deux commandes ne doivent retourner aucune branche.

## Structure du projet

```text
.
├── server.py                 # Application Flask et routes
├── clubs.json                # Clubs et points
├── competitions.json         # Compétitions et places
├── admin.json                # Comptes administrateur
├── audit.json                # Journal d'audit global
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
