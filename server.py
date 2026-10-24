import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

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
    return render_template('welcome.html', club=club, competitions=competitions, now=now)



@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if foundClub and foundCompetition:
        competition_date = datetime.strptime(foundCompetition['date'], '%Y-%m-%d %H:%M:%S')
        if competition_date < datetime.now():
            flash("Vous ne pouvez pas réserver pour une compétition déjà passée.")
            return render_template('welcome.html', club=foundClub, competitions=competitions, now=now), 400
        return render_template('booking.html', club=foundClub, competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=foundClub, competitions=competitions, now=now)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    competition_date = datetime.strptime(competition['date'], '%Y-%m-%d %H:%M:%S')
    if competition_date < datetime.now():
        flash("Vous ne pouvez pas réserver pour une compétition déjà passée.")
        return render_template('welcome.html', club=club, competitions=competitions, now=now), 400

    try:
        placesRequired = int(request.form['places'])
    except (ValueError, TypeError, KeyError):
        flash("Veuillez saisir un nombre valide de places.")
        return render_template('welcome.html', club=club, competitions=competitions, now=now), 400

    if placesRequired <= 0:
        flash("Veuillez saisir un nombre de places supérieur à 0.")
        return render_template('welcome.html', club=club, competitions=competitions, now=now), 400

    # Suivi des places déjà réservées par ce club pour cette compétition
    booked = club.setdefault('booked', {})
    already_booked = booked.get(competition['name'], 0)

    if already_booked + placesRequired > 12:
        flash("Vous ne pouvez pas réserver plus de 12 places au total pour une compétition.")
        return render_template('welcome.html', club=club, competitions=competitions, now=now), 400

    if placesRequired > int(competition['numberOfPlaces']):
        flash("Il n'y a pas assez de places disponibles dans cette compétition.")
        return render_template('welcome.html', club=club, competitions=competitions, now=now), 400

    if placesRequired > int(club['points']):
        flash("Vous n'avez pas assez de points pour réserver ce nombre de places.")
        return render_template('welcome.html', club=club, competitions=competitions, now=now), 400

    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    club['points'] = int(club['points']) - placesRequired
    booked[competition['name']] = already_booked + placesRequired
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions, now=now)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))