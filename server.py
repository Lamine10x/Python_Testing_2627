import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, flash, url_for, session
)


def loadClubs():
    with open('clubs.json', encoding='utf-8-sig') as c:
        listOfClubs = json.load(c)['clubs']
        for club in listOfClubs:
            club['points'] = int(club['points'])
        return listOfClubs


def loadCompetitions():
    with open('competitions.json', encoding='utf-8-sig') as comps:
        listOfCompetitions = json.load(comps)['competitions']
        for comp in listOfCompetitions:
            comp['numberOfPlaces'] = int(comp['numberOfPlaces'])
            comp['registration_open'] = bool(
                comp.get('registration_open', True)
            )
        return listOfCompetitions


def loadAdmins():
    with open('admin.json', encoding='utf-8-sig') as f:
        return json.load(f)


def saveClubs():
    with open('clubs.json', 'w', encoding='utf-8') as f:
        json.dump({'clubs': clubs}, f, indent=4, ensure_ascii=False)


def saveCompetitions():
    with open('competitions.json', 'w', encoding='utf-8') as f:
        json.dump(
            {'competitions': competitions}, f, indent=4, ensure_ascii=False
        )


def recordPointsChange(club, amount, reason):
    """Ajoute une operation a l'historique des points d'un club."""
    history = club.setdefault('points_history', [])
    history.insert(0, {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'admin': session.get('admin_name', 'Administrateur'),
        'amount': amount,
        'reason': reason,
        'balance': int(club['points']),
    })
    del history[50:]


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Accès réservé aux administrateurs.')
            return redirect(url_for('adminLogin'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/showSummary', methods=['POST'])
def showSummary():
    email = request.form.get('email', '').strip()
    matching_clubs = [club for club in clubs if club['email'] == email]
    if not matching_clubs:
        flash("Désolé, cette adresse e-mail n'a pas été trouvée.")
        return render_template('index.html'), 401
    club = matching_clubs[0]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template(
        'welcome.html', club=club, competitions=competitions, now=now
    )


@app.route('/book/<competition>/<club>')
def book(competition, club):
    matching_clubs = [c for c in clubs if c['name'] == club]
    matching_competitions = [
        c for c in competitions if c['name'] == competition
    ]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not matching_clubs:
        flash("Club introuvable.")
        return render_template('index.html'), 404

    foundClub = matching_clubs[0]

    if not matching_competitions:
        flash("Compétition introuvable.")
        return render_template(
            'welcome.html', club=foundClub, competitions=competitions, now=now
        ), 404

    foundCompetition = matching_competitions[0]

    comp_date = datetime.strptime(
        foundCompetition['date'], '%Y-%m-%d %H:%M:%S'
    )
    if comp_date < datetime.now():
        flash("Vous ne pouvez pas réserver pour une compétition déjà passée.")
        return render_template(
            'welcome.html', club=foundClub, competitions=competitions, now=now
        ), 400

    if not foundCompetition.get('registration_open', True):
        flash("Les inscriptions sont fermées pour cette compétition.")
        return render_template(
            'welcome.html', club=foundClub, competitions=competitions, now=now
        ), 403

    return render_template(
        'booking.html', club=foundClub, competition=foundCompetition
    )


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    comp_name = request.form.get('competition')
    club_name = request.form.get('club')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    matching_clubs = [c for c in clubs if c['name'] == club_name]
    if not matching_clubs:
        flash("Club introuvable.")
        return render_template('index.html'), 404

    club = matching_clubs[0]

    matching_competitions = [c for c in competitions if c['name'] == comp_name]
    if not matching_competitions:
        flash("Compétition introuvable.")
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 404

    competition = matching_competitions[0]

    competition_date = datetime.strptime(
        competition['date'], '%Y-%m-%d %H:%M:%S'
    )
    if competition_date < datetime.now():
        flash("Vous ne pouvez pas réserver pour une compétition déjà passée.")
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 400

    if not competition.get('registration_open', True):
        flash("Les inscriptions sont fermées pour cette compétition.")
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 403

    try:
        placesRequired = int(request.form['places'])
    except (ValueError, TypeError, KeyError):
        flash("Veuillez saisir un nombre valide de places.")
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 400

    if placesRequired <= 0:
        flash("Veuillez saisir un nombre de places supérieur à 0.")
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 400

    # Suivi des places déjà réservées par ce club pour cette compétition
    booked = club.setdefault('booked', {})
    already_booked = booked.get(competition['name'], 0)

    if already_booked + placesRequired > 12:
        flash(
            "Vous ne pouvez pas réserver plus de 12 places au total "
            "pour une compétition."
        )
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 400

    if placesRequired > int(competition['numberOfPlaces']):
        flash(
            "Il n'y a pas assez de places disponibles dans cette compétition."
        )
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 400

    if placesRequired > int(club['points']):
        flash(
            "Vous n'avez pas assez de points pour réserver "
            "ce nombre de places."
        )
        return render_template(
            'welcome.html', club=club, competitions=competitions, now=now
        ), 400

    places_int = int(competition['numberOfPlaces']) - placesRequired
    competition['numberOfPlaces'] = places_int
    club['points'] = int(club['points']) - placesRequired
    booked[competition['name']] = already_booked + placesRequired
    saveClubs()
    saveCompetitions()
    flash('Great-booking complete!')
    return render_template(
        'welcome.html', club=club, competitions=competitions, now=now
    )


@app.route('/displayBoard')
@app.route('/points')
def displayBoard():
    selected_name = request.args.get('competition', '').strip()
    selected_competition = next(
        (c for c in competitions if c['name'] == selected_name), None
    )

    if selected_competition:
        competition_ranking = []
        for club in clubs:
            booked_places = int(
                club.get('booked', {}).get(selected_name, 0)
            )
            if booked_places > 0:
                competition_ranking.append({
                    **club,
                    'booked_places': booked_places,
                })
        competition_ranking.sort(
            key=lambda c: (
                -c['booked_places'], -int(c['points']), c['name']
            )
        )
        return render_template(
            'display_board.html',
            clubs=[],
            competitions=competitions,
            selected_competition=selected_competition,
            competition_ranking=competition_ranking,
        )

    sorted_clubs = sorted(
        clubs, key=lambda c: (-int(c['points']), c['name'])
    )
    return render_template(
        'display_board.html',
        clubs=sorted_clubs,
        competitions=competitions,
        selected_competition=None,
        competition_ranking=[],
    )


@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté avec succès.")
    return redirect(url_for('index'))


# ── ADMIN ─────────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():
    if session.get('admin_logged_in'):
        return redirect(url_for('adminDashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        admins = loadAdmins()
        match = next(
            (a for a in admins if a['email'] == email
             and a['password'] == password), None
        )
        if match:
            session['admin_logged_in'] = True
            session['admin_name'] = match['name']
            return redirect(url_for('adminDashboard'))
        flash("Identifiants incorrects.")
    return render_template('admin/login.html')


@app.route('/admin/logout')
def adminLogout():
    session.pop('admin_logged_in', None)
    session.pop('admin_name', None)
    flash("Session admin terminée.")
    return redirect(url_for('adminLogin'))


@app.route('/admin')
@admin_required
def adminDashboard():
    return render_template(
        'admin/dashboard.html',
        clubs=clubs,
        competitions=competitions,
        admin_name=session.get('admin_name')
    )


@app.route('/admin/clubs')
@admin_required
def adminClubs():
    return render_template(
        'admin/clubs.html',
        clubs=clubs,
        admin_name=session.get('admin_name')
    )


@app.route('/admin/clubs/edit/<club_name>', methods=['GET', 'POST'])
@admin_required
def adminEditClub(club_name):
    club = next((c for c in clubs if c['name'] == club_name), None)
    if not club:
        flash("Club introuvable.")
        return redirect(url_for('adminClubs'))
    if request.method == 'POST':
        try:
            new_points = int(request.form.get('points', 0))
        except ValueError:
            flash("Valeur de points invalide.")
            return redirect(url_for('adminEditClub', club_name=club_name))
        old_points = int(club['points'])
        club['name'] = request.form.get('name', club['name']).strip()
        club['email'] = request.form.get('email', club['email']).strip()
        club['points'] = new_points
        if new_points != old_points:
            recordPointsChange(
                club, new_points - old_points, 'Modification via la fiche club'
            )
        saveClubs()
        flash(f"Club '{club['name']}' mis à jour.")
        return redirect(url_for('adminClubs'))
    return render_template(
        'admin/edit_club.html',
        club=club,
        admin_name=session.get('admin_name')
    )


@app.route('/admin/clubs/<club_name>/points', methods=['GET', 'POST'])
@admin_required
def adminClubPoints(club_name):
    club = next((c for c in clubs if c['name'] == club_name), None)
    if not club:
        flash("Club introuvable.")
        return redirect(url_for('adminClubs'))

    if request.method == 'POST':
        operation = request.form.get('operation', 'credit')
        if operation not in ('credit', 'debit'):
            flash("Opération invalide.")
            return redirect(
                url_for('adminClubPoints', club_name=club_name)
            )

        try:
            amount = int(request.form.get('amount', '0'))
        except (TypeError, ValueError):
            flash("Montant invalide : saisissez un nombre entier.")
            return redirect(
                url_for('adminClubPoints', club_name=club_name)
            )

        if amount <= 0:
            flash("Le montant doit être un entier supérieur à 0.")
            return redirect(
                url_for('adminClubPoints', club_name=club_name)
            )

        delta = amount if operation == 'credit' else -amount
        new_points = int(club['points']) + delta
        if new_points < 0:
            flash(
                "Le solde du club ne peut pas devenir négatif. "
                f"Solde actuel : {club['points']} points."
            )
            return redirect(
                url_for('adminClubPoints', club_name=club_name)
            )

        reason = request.form.get('reason', '').strip()
        if not reason:
            reason = 'Ajustement manuel'

        club['points'] = new_points
        recordPointsChange(club, delta, reason)
        saveClubs()

        action = 'crédité(s)' if delta > 0 else 'débité(s)'
        flash(
            f"{amount} point(s) {action} au club '{club['name']}'. "
            f"Nouveau solde : {new_points} points."
        )
        return redirect(url_for('adminClubPoints', club_name=club_name))

    history = club.get('points_history', [])[:20]
    return render_template(
        'admin/club_points.html',
        club=club,
        history=history,
        admin_name=session.get('admin_name')
    )


@app.route('/admin/clubs/add', methods=['GET', 'POST'])
@admin_required
def adminAddClub():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        try:
            points = int(request.form.get('points', 0))
        except ValueError:
            flash("Valeur de points invalide.")
            return redirect(url_for('adminAddClub'))
        if not name or not email:
            flash("Nom et email requis.")
            return redirect(url_for('adminAddClub'))
        clubs.append({
            'name': name,
            'email': email,
            'points': points,
            'points_history': [],
            'booked': {},
        })
        saveClubs()
        flash(f"Club '{name}' ajouté.")
        return redirect(url_for('adminClubs'))
    return render_template(
        'admin/add_club.html',
        admin_name=session.get('admin_name')
    )


@app.route('/admin/clubs/delete/<club_name>', methods=['POST'])
@admin_required
def adminDeleteClub(club_name):
    global clubs
    clubs = [c for c in clubs if c['name'] != club_name]
    saveClubs()
    flash(f"Club '{club_name}' supprimé.")
    return redirect(url_for('adminClubs'))


@app.route('/admin/competitions')
@admin_required
def adminCompetitions():
    return render_template(
        'admin/competitions.html',
        competitions=competitions,
        admin_name=session.get('admin_name')
    )


@app.route('/admin/competitions/edit/<comp_name>', methods=['GET', 'POST'])
@admin_required
def adminEditCompetition(comp_name):
    comp = next((c for c in competitions if c['name'] == comp_name), None)
    if not comp:
        flash("Compétition introuvable.")
        return redirect(url_for('adminCompetitions'))
    if request.method == 'POST':
        try:
            places = int(request.form.get('numberOfPlaces', 0))
        except ValueError:
            flash("Nombre de places invalide.")
            return redirect(
                url_for('adminEditCompetition', comp_name=comp_name)
            )
        comp['name'] = request.form.get('name', comp['name']).strip()
        comp['date'] = request.form.get('date', comp['date']).strip()
        comp['numberOfPlaces'] = places
        comp['registration_open'] = (
            request.form.get('registration_open') != 'off'
        )
        saveCompetitions()
        flash(f"Compétition '{comp['name']}' mise à jour.")
        return redirect(url_for('adminCompetitions'))
    return render_template(
        'admin/edit_competition.html',
        comp=comp,
        admin_name=session.get('admin_name')
    )


@app.route(
    '/admin/competitions/<comp_name>/toggle-registration',
    methods=['POST']
)
@admin_required
def adminToggleCompetitionRegistration(comp_name):
    comp = next((c for c in competitions if c['name'] == comp_name), None)
    if not comp:
        flash("Compétition introuvable.")
        return redirect(url_for('adminCompetitions'))

    comp['registration_open'] = not comp.get('registration_open', True)
    saveCompetitions()
    state = 'ouvertes' if comp['registration_open'] else 'fermées'
    flash(f"Inscriptions {state} pour la compétition '{comp_name}'.")
    return redirect(url_for('adminCompetitions'))


@app.route('/admin/competitions/add', methods=['GET', 'POST'])
@admin_required
def adminAddCompetition():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        date = request.form.get('date', '').strip()
        try:
            places = int(request.form.get('numberOfPlaces', 0))
        except ValueError:
            flash("Nombre de places invalide.")
            return redirect(url_for('adminAddCompetition'))
        if not name or not date:
            flash("Nom et date requis.")
            return redirect(url_for('adminAddCompetition'))
        competitions.append(
            {
                'name': name,
                'date': date,
                'numberOfPlaces': places,
                'registration_open': (
                    request.form.get('registration_open') != 'off'
                ),
            }
        )
        saveCompetitions()
        flash(f"Compétition '{name}' ajoutée.")
        return redirect(url_for('adminCompetitions'))
    return render_template(
        'admin/add_competition.html',
        admin_name=session.get('admin_name')
    )


@app.route('/admin/competitions/delete/<comp_name>', methods=['POST'])
@admin_required
def adminDeleteCompetition(comp_name):
    global competitions
    competitions = [c for c in competitions if c['name'] != comp_name]
    saveCompetitions()
    flash(f"Compétition '{comp_name}' supprimée.")
    return redirect(url_for('adminCompetitions'))
