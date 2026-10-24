import json
from flask import Flask,render_template,request,redirect,flash,url_for


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
    return render_template('welcome.html', club=club, competitions=competitions)



@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])

    # Suivi des places déjà réservées par ce club pour cette compétition
    booked = club.setdefault('booked', {})
    already_booked = booked.get(competition['name'], 0)

    if already_booked + placesRequired > 12:
        flash("Vous ne pouvez pas réserver plus de 12 places au total pour une compétition.")
        return render_template('welcome.html', club=club, competitions=competitions), 400

    if placesRequired > int(competition['numberOfPlaces']):
        flash("Il n'y a pas assez de places disponibles dans cette compétition.")
        return render_template('welcome.html', club=club, competitions=competitions), 400

    if placesRequired > int(club['points']):
        flash("Vous n'avez pas assez de points pour réserver ce nombre de places.")
        return render_template('welcome.html', club=club, competitions=competitions), 400

    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    club['points'] = int(club['points']) - placesRequired
    booked[competition['name']] = already_booked + placesRequired
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))