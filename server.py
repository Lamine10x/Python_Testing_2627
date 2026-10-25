import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, flash, url_for, session
)


def loadClubs():
    with open('clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
        for club in listOfClubs:
            club['points'] = int(club['points'])
        return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
        listOfCompetitions = json.load(comps)['competitions']
        for comp in listOfCompetitions:
            comp['numberOfPlaces'] = int(comp['numberOfPlaces'])
        return listOfCompetitions


def loadAdmins():
    with open('admin.json', encoding='utf-8-sig') as f:
        return json.load(f)


def saveClubs():
    with open('clubs.json', 'w') as f:
        json.dump({'clubs': clubs}, f, indent=4)


def saveCompetitions():
    with open('competitions.json', 'w') as f:
        json.dump({'competitions': competitions}, f, indent=4)


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
    flash('Great-booking complete!')
    return render_template(
        'welcome.html', club=club, competitions=competitions, now=now
    )


@app.route('/displayBoard')
@app.route('/points')
def displayBoard():
    return render_template('display_board.html', clubs=clubs)


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
        club['name'] = request.form.get('name', club['name']).strip()
        club['email'] = request.form.get('email', club['email']).strip()
        club['points'] = new_points
        saveClubs()
        flash(f"Club '{club['name']}' mis à jour.")
        return redirect(url_for('adminClubs'))
    return render_template(
        'admin/edit_club.html',
        club=club,
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
        clubs.append({'name': name, 'email': email, 'points': points})
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
        saveCompetitions()
        flash(f"Compétition '{comp['name']}' mise à jour.")
        return redirect(url_for('adminCompetitions'))
    return render_template(
        'admin/edit_competition.html',
        comp=comp,
        admin_name=session.get('admin_name')
    )


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
            {'name': name, 'date': date, 'numberOfPlaces': places}
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
