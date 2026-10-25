import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, flash, url_for, session,
    has_request_context,
)


MAX_PLACES_PER_COMPETITION = 12
AUDIT_LOG_FILE = 'audit.json'
MAX_AUDIT_ENTRIES = 500

AUDIT_ACTION_LABELS = {
    'admin_login': 'Connexion admin',
    'admin_logout': 'Déconnexion admin',
    'add_club': 'Ajout de club',
    'update_club': 'Modification de club',
    'delete_club': 'Suppression de club',
    'credit_points': 'Crédit de points',
    'debit_points': 'Débit de points',
    'add_competition': 'Ajout de compétition',
    'update_competition': 'Modification de compétition',
    'delete_competition': 'Suppression de compétition',
    'toggle_registration': 'Changement des inscriptions',
    'book_places': 'Réservation de places',
    'cancel_reservation': 'Annulation de réservation',
}

AUDIT_CATEGORY_LABELS = {
    'auth': 'Authentification',
    'club': 'Clubs',
    'points': 'Points',
    'competition': 'Compétitions',
    'reservation': 'Réservations',
}


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


def loadAuditLog():
    try:
        with open(AUDIT_LOG_FILE, encoding='utf-8-sig') as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    if isinstance(data, list):
        return data
    return data.get('entries', [])


def saveAuditLog():
    with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(
            {'entries': audit_entries}, f, indent=4, ensure_ascii=False
        )


def saveClubs():
    with open('clubs.json', 'w', encoding='utf-8') as f:
        json.dump({'clubs': clubs}, f, indent=4, ensure_ascii=False)


def saveCompetitions():
    with open('competitions.json', 'w', encoding='utf-8') as f:
        json.dump(
            {'competitions': competitions}, f, indent=4, ensure_ascii=False
        )


def getAuditActor(fallback='Système'):
    if has_request_context():
        return (
            session.get('admin_name')
            or session.get('club_name')
            or fallback
        )
    return fallback


def recordAudit(action, category, target='', details=None, actor=None):
    """Ajoute une opération au journal d'audit global."""
    entry = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'actor': actor or getAuditActor(),
        'action': action,
        'category': category,
        'target': target,
        'details': details or {},
    }
    audit_entries.insert(0, entry)
    del audit_entries[MAX_AUDIT_ENTRIES:]
    saveAuditLog()
    return entry


def recordPointsChange(
    club, amount, reason, author=None, entry_type='admin'
):
    """Ajoute une operation a l'historique des points d'un club."""
    history = club.setdefault('points_history', [])
    history.insert(0, {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'admin': author or session.get('admin_name', 'Administrateur'),
        'amount': amount,
        'reason': reason,
        'balance': int(club['points']),
        'type': entry_type,
    })


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()
audit_entries = loadAuditLog()


def findClub(club_name):
    return next((c for c in clubs if c['name'] == club_name), None)


def findCompetition(competition_name):
    return next(
        (c for c in competitions if c['name'] == competition_name), None
    )


def getBookedPlaces(club, competition):
    return int(club.get('booked', {}).get(competition['name'], 0))


def getQuotaRemaining(club, competition):
    return max(
        0, MAX_PLACES_PER_COMPETITION - getBookedPlaces(club, competition)
    )


def getMaxBookable(club, competition):
    return min(
        getQuotaRemaining(club, competition),
        max(0, int(competition['numberOfPlaces'])),
        max(0, int(club['points'])),
    )


def getCompetitionState(club, competition, now=None):
    now = now or datetime.now()
    booked = getBookedPlaces(club, competition)
    quota = getQuotaRemaining(club, competition)
    places = max(0, int(competition['numberOfPlaces']))
    points = max(0, int(club['points']))
    max_bookable = min(quota, places, points)
    is_past = datetime.strptime(
        competition['date'], '%Y-%m-%d %H:%M:%S'
    ) < now
    is_open = bool(competition.get('registration_open', True))

    if is_past:
        status, can_book, status_class = (
            'Terminée', False, 'badge-default'
        )
    elif not is_open:
        status, can_book, status_class = (
            'Inscriptions fermées', False, 'badge-danger'
        )
    elif places <= 0:
        status, can_book, status_class = (
            'Complet', False, 'badge-danger'
        )
    elif quota <= 0:
        status, can_book, status_class = (
            'Quota atteint', False, 'badge-default'
        )
    elif points <= 0:
        status, can_book, status_class = (
            'Points insuffisants', False, 'badge-danger'
        )
    else:
        status, can_book, status_class = (
            'Disponible', True, 'badge-success'
        )

    return {
        'booked': booked,
        'quota_remaining': quota,
        'max_bookable': max_bookable,
        'places_remaining': places,
        'is_past': is_past,
        'is_open': is_open,
        'can_book': can_book,
        'status': status,
        'status_class': status_class,
    }


def getDaysUntil(date_value, now=None):
    now = now or datetime.now()
    try:
        target = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return None
    return max(0, (target.date() - now.date()).days)


def buildRecentReleases(exclude_club=None, limit=5):
    """Construit le flux des places libérées à partir du journal d'audit."""
    now = datetime.now()
    releases = []
    for entry in audit_entries:
        if entry.get('action') != 'cancel_reservation':
            continue
        details = entry.get('details') or {}
        competition = findCompetition(details.get('competition', ''))
        if not competition:
            continue
        try:
            if datetime.strptime(
                competition['date'], '%Y-%m-%d %H:%M:%S'
            ) < now:
                continue
            places = int(details.get('places', 0))
        except (TypeError, ValueError):
            continue
        release_club = details.get('club')
        if exclude_club and release_club == exclude_club:
            continue
        if places <= 0:
            continue
        releases.append({
            'competition': competition,
            'places': places,
            'club': release_club or '',
            'date': entry.get('date', ''),
        })
        if len(releases) >= limit:
            break
    return releases


def getReservationStatus(competition, now=None):
    now = now or datetime.now()
    try:
        is_past = datetime.strptime(
            competition['date'], '%Y-%m-%d %H:%M:%S'
        ) < now
    except (TypeError, ValueError):
        is_past = False
    if is_past:
        status, status_class, status_key = (
            'Terminée', 'badge-default', 'terminee'
        )
    elif not competition.get('registration_open', True):
        status, status_class, status_key = (
            'Inscriptions fermées', 'badge-danger', 'fermee'
        )
    else:
        status, status_class, status_key = (
            'Confirmée', 'badge-success', 'confirmee'
        )
    return {
        'status': status,
        'status_class': status_class,
        'status_key': status_key,
        'is_past': is_past,
    }


def buildAdminReservations(filters=None):
    """Agrège les réservations club/compétition pour l'administration."""
    now = datetime.now()
    filters = filters or {}
    selected_club = filters.get('club', '').strip()
    selected_competition = filters.get('competition', '').strip()
    selected_status = filters.get('statut', '').strip()
    reservations = []

    for club in clubs:
        for comp_name, places in (club.get('booked') or {}).items():
            try:
                booked = int(places)
            except (TypeError, ValueError):
                continue
            if booked <= 0:
                continue
            competition = findCompetition(comp_name)
            if not competition:
                continue
            status_info = getReservationStatus(competition, now)
            if selected_club and club['name'] != selected_club:
                continue
            if (
                selected_competition
                and competition['name'] != selected_competition
            ):
                continue
            if (
                selected_status
                and status_info['status_key'] != selected_status
            ):
                continue
            reservations.append({
                'club': club,
                'competition': competition,
                'booked': booked,
                'points_refundable': booked,
                **status_info,
            })

    reservations.sort(
        key=lambda item: (item['competition']['date'], item['club']['name'])
    )
    stats = {
        'reservations': len(reservations),
        'places': sum(item['booked'] for item in reservations),
        'points': sum(item['points_refundable'] for item in reservations),
        'clubs': len({item['club']['name'] for item in reservations}),
        'competitions': len({
            item['competition']['name'] for item in reservations
        }),
    }

    return {
        'reservations': reservations,
        'reservation_stats': stats,
        'reservation_filters': {
            'club': selected_club,
            'competition': selected_competition,
            'statut': selected_status,
        },
        'club_options': sorted(club['name'] for club in clubs),
        'competition_options': sorted(
            competition['name'] for competition in competitions
        ),
        'status_options': [
            ('confirmee', 'Confirmée'),
            ('fermee', 'Inscriptions fermées'),
            ('terminee', 'Terminée'),
        ],
    }


def formatAuditDetails(entry):
    """Produit un résumé lisible des détails d'une entrée d'audit."""
    details = entry.get('details') or {}
    action = entry.get('action')
    if action == 'cancel_reservation':
        reason = details.get('reason') or 'Sans motif'
        return (
            f"{details.get('places', 0)} place(s) remboursée(s) · {reason}"
        )
    if action == 'book_places':
        return f"{details.get('places', 0)} place(s) réservée(s)"
    if action in ('credit_points', 'debit_points'):
        reason = details.get('reason') or 'Sans motif'
        return f"{details.get('amount', 0)} point(s) · {reason}"
    if action == 'update_club':
        return (
            f"Points {details.get('points_before', '?')} → "
            f"{details.get('points_after', '?')}"
        )
    if action == 'update_competition':
        return (
            f"Places {details.get('places_before', '?')} → "
            f"{details.get('places_after', '?')}"
        )
    if action == 'toggle_registration':
        return (
            'Inscriptions ouvertes'
            if details.get('registration_open')
            else 'Inscriptions fermées'
        )
    if action == 'add_club':
        return details.get('email', '')
    if action == 'add_competition':
        return details.get('date', '')
    if action in ('admin_login', 'admin_logout'):
        return 'Session administrateur'
    return ''


def buildAuditEntries(filters=None):
    """Filtre et enrichit les entrées du journal d'audit global."""
    filters = filters or {}
    selected_category = filters.get('categorie', '').strip()
    selected_action = filters.get('action', '').strip()
    selected_actor = filters.get('acteur', '').strip().lower()
    entries = []

    for entry in audit_entries:
        if (
            selected_category
            and entry.get('category') != selected_category
        ):
            continue
        if selected_action and entry.get('action') != selected_action:
            continue
        actor = entry.get('actor', '')
        if selected_actor and selected_actor not in actor.lower():
            continue
        entries.append({
            **entry,
            'action_label': AUDIT_ACTION_LABELS.get(
                entry.get('action'), entry.get('action', '')
            ),
            'category_label': AUDIT_CATEGORY_LABELS.get(
                entry.get('category'), entry.get('category', '')
            ),
            'details_text': formatAuditDetails(entry),
        })

    return {
        'audit_entries': entries,
        'audit_total': len(audit_entries),
        'audit_filtered_count': len(entries),
        'audit_filters': {
            'categorie': selected_category,
            'action': selected_action,
            'acteur': filters.get('acteur', '').strip(),
        },
        'audit_action_options': [
            {'value': key, 'label': label}
            for key, label in sorted(
                AUDIT_ACTION_LABELS.items(), key=lambda item: item[1]
            )
        ],
        'audit_category_options': [
            {'value': key, 'label': label}
            for key, label in sorted(
                AUDIT_CATEGORY_LABELS.items(), key=lambda item: item[1]
            )
        ],
        'audit_actors': sorted({
            entry.get('actor', '') for entry in audit_entries
            if entry.get('actor')
        }),
    }


def renderAdminCancellation(
    club, competition, status=200, form_places='', form_reason=''
):
    return render_template(
        'admin/cancel_reservation.html',
        club=club,
        competition=competition,
        booked=getBookedPlaces(club, competition),
        status_info=getReservationStatus(competition),
        form_places=form_places,
        form_reason=form_reason,
        admin_name=session.get('admin_name'),
    ), status


def buildClubDashboard(club, filters=None):
    now = datetime.now()
    filters = filters or {}
    selected_status = filters.get('statut', '').strip()
    selected_competition = filters.get('competition', '').strip()
    cards = []
    reservations = []

    for competition in competitions:
        state = getCompetitionState(club, competition, now)
        cards.append({'competition': competition, **state})

        if state['booked'] <= 0:
            continue

        if state['is_past']:
            status, status_class, status_key = (
                'Terminée', 'badge-default', 'terminee'
            )
        elif not state['is_open']:
            status, status_class, status_key = (
                'Inscriptions fermées', 'badge-danger', 'fermee'
            )
        else:
            status, status_class, status_key = (
                'Confirmée', 'badge-success', 'confirmee'
            )

        reservations.append({
            'competition': competition,
            'booked': state['booked'],
            'points_spent': state['booked'],
            'quota_remaining': state['quota_remaining'],
            'max_bookable': state['max_bookable'],
            'can_book': state['can_book'],
            'status': status,
            'status_class': status_class,
            'status_key': status_key,
        })

    cards.sort(key=lambda c: (c['is_past'], c['competition']['date']))
    reservations.sort(key=lambda r: r['competition']['date'])

    upcoming = []
    for card in [c for c in cards if not c['is_past']][:3]:
        upcoming.append({
            'competition': card['competition'],
            'places_remaining': card['places_remaining'],
            'days_until': getDaysUntil(card['competition']['date'], now),
            'status': card['status'],
            'status_class': card['status_class'],
        })

    reservation_total = len(reservations)
    filtered_reservations = [
        reservation for reservation in reservations
        if (
            not selected_status
            or reservation['status_key'] == selected_status
        )
        and (
            not selected_competition
            or reservation['competition']['name'] == selected_competition
        )
    ]

    stats = {
        'points': int(club['points']),
        'competitions': len(competitions),
        'open_competitions': sum(
            1 for card in cards if card['is_open'] and not card['is_past']
        ),
        'booked_places': sum(card['booked'] for card in cards),
        'points_spent': sum(card['booked'] for card in cards),
        'next_deadline': upcoming[0] if upcoming else None,
    }

    return {
        'competition_cards': cards,
        'reservations': filtered_reservations,
        'reservation_total': reservation_total,
        'reservation_filters': {
            'statut': selected_status,
            'competition': selected_competition,
        },
        'points_history': club.get('points_history', []),
        'stats': stats,
        'upcoming': upcoming,
        'recent_releases': buildRecentReleases(exclude_club=club['name']),
        'now': now.strftime('%Y-%m-%d %H:%M:%S'),
    }


def renderClubDashboard(club, status=200, filters=None):
    return render_template(
        'welcome.html', club=club, **buildClubDashboard(club, filters)
    ), status


def getBookingContext(club, competition):
    return {
        'already_booked': getBookedPlaces(club, competition),
        'quota_remaining': getQuotaRemaining(club, competition),
        'max_bookable': getMaxBookable(club, competition),
    }


def renderBooking(club, competition, status=200, form_places=''):
    return render_template(
        'booking.html',
        club=club,
        competition=competition,
        form_places=form_places,
        **getBookingContext(club, competition),
    ), status


@app.template_filter('datefr')
def formatDateFr(value):
    if not value:
        return ''
    for date_format in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.strftime('%d/%m/%Y %H:%M')
        except (TypeError, ValueError):
            continue
    return value


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
    club = next((c for c in clubs if c['email'] == email), None)
    if not club:
        flash(
            "Désolé, cette adresse e-mail n'a pas été trouvée.", 'error'
        )
        return render_template('index.html'), 401
    return renderClubDashboard(club)


@app.route('/dashboard/<club_name>')
def clubDashboard(club_name):
    club = findClub(club_name)
    if not club:
        flash("Club introuvable.", 'error')
        return render_template('index.html'), 404
    filters = {
        'statut': request.args.get('statut', '').strip(),
        'competition': request.args.get('competition', '').strip(),
    }
    return renderClubDashboard(club, filters=filters)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = findClub(club)
    if not foundClub:
        flash("Club introuvable.", 'error')
        return render_template('index.html'), 404

    foundCompetition = findCompetition(competition)
    if not foundCompetition:
        flash("Compétition introuvable.", 'error')
        return renderClubDashboard(foundClub, 404)

    comp_date = datetime.strptime(
        foundCompetition['date'], '%Y-%m-%d %H:%M:%S'
    )
    if comp_date < datetime.now():
        flash(
            "Vous ne pouvez pas réserver pour une compétition déjà passée.",
            'error',
        )
        return renderClubDashboard(foundClub, 400)

    if not foundCompetition.get('registration_open', True):
        flash(
            "Les inscriptions sont fermées pour cette compétition.", 'error'
        )
        return renderClubDashboard(foundClub, 403)

    state = getCompetitionState(foundClub, foundCompetition)
    if state['max_bookable'] <= 0:
        if state['places_remaining'] <= 0:
            message = "Cette compétition est complète."
        elif state['quota_remaining'] <= 0:
            message = (
                "Vous avez atteint la limite de "
                f"{MAX_PLACES_PER_COMPETITION} places pour cette compétition."
            )
        else:
            message = (
                "Vous n'avez pas assez de points pour réserver une place."
            )
        flash(message, 'error')
        return renderClubDashboard(foundClub, 400)

    return renderBooking(foundClub, foundCompetition)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    comp_name = request.form.get('competition')
    club_name = request.form.get('club')
    form_places = request.form.get('places', '')

    club = findClub(club_name)
    if not club:
        flash("Club introuvable.", 'error')
        return render_template('index.html'), 404

    competition = findCompetition(comp_name)
    if not competition:
        flash("Compétition introuvable.", 'error')
        return renderClubDashboard(club, 404)

    competition_date = datetime.strptime(
        competition['date'], '%Y-%m-%d %H:%M:%S'
    )
    if competition_date < datetime.now():
        flash(
            "Vous ne pouvez pas réserver pour une compétition déjà passée.",
            'error',
        )
        return renderClubDashboard(club, 400)

    if not competition.get('registration_open', True):
        flash(
            "Les inscriptions sont fermées pour cette compétition.", 'error'
        )
        return renderClubDashboard(club, 403)

    try:
        placesRequired = int(form_places)
    except (ValueError, TypeError):
        flash("Veuillez saisir un nombre valide de places.", 'error')
        return renderBooking(club, competition, 400, form_places)

    if placesRequired <= 0:
        flash("Veuillez saisir un nombre de places supérieur à 0.", 'error')
        return renderBooking(club, competition, 400, form_places)

    already_booked = getBookedPlaces(club, competition)
    quota_remaining = getQuotaRemaining(club, competition)

    if already_booked + placesRequired > MAX_PLACES_PER_COMPETITION:
        flash(
            "Vous ne pouvez pas réserver plus de "
            f"{MAX_PLACES_PER_COMPETITION} places au total "
            "pour une compétition.",
            'error',
        )
        return renderBooking(club, competition, 400, form_places)

    if placesRequired > int(competition['numberOfPlaces']):
        flash(
            "Il n'y a pas assez de places disponibles dans cette compétition.",
            'error',
        )
        return renderBooking(club, competition, 400, form_places)

    if placesRequired > int(club['points']):
        flash(
            "Vous n'avez pas assez de points pour réserver "
            "ce nombre de places.",
            'error',
        )
        return renderBooking(club, competition, 400, form_places)

    booked = club.setdefault('booked', {})
    competition['numberOfPlaces'] = (
        int(competition['numberOfPlaces']) - placesRequired
    )
    club['points'] = int(club['points']) - placesRequired
    booked[competition['name']] = already_booked + placesRequired
    recordPointsChange(
        club,
        -placesRequired,
        f"Réservation — {competition['name']}",
        author=club['name'],
        entry_type='reservation',
    )
    recordAudit(
        'book_places',
        'reservation',
        target=f"{club['name']} — {competition['name']}",
        actor=club['name'],
        details={
            'club': club['name'],
            'competition': competition['name'],
            'places': placesRequired,
            'points_after': int(club['points']),
            'places_remaining': int(competition['numberOfPlaces']),
        },
    )
    saveClubs()
    saveCompetitions()
    quota_after = max(0, quota_remaining - placesRequired)
    flash(
        f"Réservation confirmée : {placesRequired} place(s) pour "
        f"« {competition['name']} ». Nouveau solde : {club['points']} "
        f"point(s), quota restant : {quota_after}/"
        f"{MAX_PLACES_PER_COMPETITION}.",
        'success',
    )
    return redirect(
        url_for(
            'clubDashboard',
            club_name=club['name'],
            _anchor='mes-reservations',
        ),
        code=303,
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
    flash("Vous avez été déconnecté avec succès.", 'success')
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
            recordAudit(
                'admin_login',
                'auth',
                target='Administration',
                actor=match['name'],
            )
            return redirect(url_for('adminDashboard'))
        flash("Identifiants incorrects.")
    return render_template('admin/login.html')


@app.route('/admin/logout')
def adminLogout():
    if session.get('admin_logged_in'):
        recordAudit(
            'admin_logout',
            'auth',
            target='Administration',
            actor=session.get('admin_name'),
        )
    session.pop('admin_logged_in', None)
    session.pop('admin_name', None)
    flash("Session admin terminée.")
    return redirect(url_for('adminLogin'))


@app.route('/admin')
@admin_required
def adminDashboard():
    reservation_data = buildAdminReservations()
    return render_template(
        'admin/dashboard.html',
        clubs=clubs,
        competitions=competitions,
        reservation_stats=reservation_data['reservation_stats'],
        audit_count=len(audit_entries),
        admin_name=session.get('admin_name')
    )


@app.route('/admin/reservations')
@admin_required
def adminReservations():
    filters = {
        'club': request.args.get('club', '').strip(),
        'competition': request.args.get('competition', '').strip(),
        'statut': request.args.get('statut', '').strip(),
    }
    return render_template(
        'admin/reservations.html',
        admin_name=session.get('admin_name'),
        **buildAdminReservations(filters),
    )


@app.route(
    '/admin/reservations/<club_name>/<comp_name>/cancel',
    methods=['GET', 'POST'],
)
@admin_required
def adminCancelReservation(club_name, comp_name):
    club = findClub(club_name)
    if not club:
        flash("Club introuvable.", 'error')
        return redirect(url_for('adminReservations'))
    competition = findCompetition(comp_name)
    if not competition:
        flash("Compétition introuvable.", 'error')
        return redirect(url_for('adminReservations'))
    booked = getBookedPlaces(club, competition)
    if booked <= 0:
        flash("Aucune réservation à annuler pour ce club.", 'error')
        return redirect(url_for('adminReservations'))

    form_places = request.form.get('places', '')
    form_reason = request.form.get('reason', '')
    if request.method == 'POST':
        try:
            places = int(form_places)
        except (TypeError, ValueError):
            flash("Veuillez saisir un nombre valide de places.", 'error')
            return renderAdminCancellation(
                club, competition, 400, form_places, form_reason
            )
        if places <= 0:
            flash("Le nombre de places doit être supérieur à 0.", 'error')
            return renderAdminCancellation(
                club, competition, 400, form_places, form_reason
            )
        if places > booked:
            flash(
                f"Impossible d'annuler {places} place(s) : le club n'en a "
                f"réservé que {booked}.",
                'error',
            )
            return renderAdminCancellation(
                club, competition, 400, form_places, form_reason
            )

        reason = form_reason.strip() or 'Annulation administrateur'
        remaining = booked - places
        club['points'] = int(club['points']) + places
        competition['numberOfPlaces'] = (
            int(competition['numberOfPlaces']) + places
        )
        booked_map = club.setdefault('booked', {})
        if remaining > 0:
            booked_map[competition['name']] = remaining
        else:
            booked_map.pop(competition['name'], None)

        recordPointsChange(
            club,
            places,
            f"Remboursement — {competition['name']} ({reason})",
            entry_type='refund',
        )
        recordAudit(
            'cancel_reservation',
            'reservation',
            target=f"{club['name']} — {competition['name']}",
            details={
                'club': club['name'],
                'competition': competition['name'],
                'places': places,
                'reason': reason,
                'booked_before': booked,
                'booked_after': remaining,
                'points_after': int(club['points']),
            },
        )
        saveClubs()
        saveCompetitions()
        flash(
            f"{places} place(s) annulée(s) et remboursée(s) au club "
            f"'{club['name']}' pour « {competition['name']} ». "
            f"Nouveau solde : {club['points']} point(s).",
            'success',
        )
        return redirect(url_for('adminReservations'))

    return renderAdminCancellation(club, competition)


@app.route('/admin/audit')
@admin_required
def adminAudit():
    filters = {
        'categorie': request.args.get('categorie', '').strip(),
        'action': request.args.get('action', '').strip(),
        'acteur': request.args.get('acteur', '').strip(),
    }
    return render_template(
        'admin/audit.html',
        admin_name=session.get('admin_name'),
        **buildAuditEntries(filters),
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
        old_name = club['name']
        club['name'] = request.form.get('name', club['name']).strip()
        club['email'] = request.form.get('email', club['email']).strip()
        club['points'] = new_points
        if new_points != old_points:
            recordPointsChange(
                club, new_points - old_points, 'Modification via la fiche club'
            )
        recordAudit(
            'update_club',
            'club',
            target=old_name,
            details={
                'new_name': club['name'],
                'email': club['email'],
                'points_before': old_points,
                'points_after': new_points,
            },
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
        recordAudit(
            'credit_points' if delta > 0 else 'debit_points',
            'points',
            target=club['name'],
            details={
                'amount': amount,
                'reason': reason,
                'balance': new_points,
            },
        )
        saveClubs()

        action = 'crédité(s)' if delta > 0 else 'débité(s)'
        flash(
            f"{amount} point(s) {action} au club '{club['name']}'. "
            f"Nouveau solde : {new_points} points."
        )
        return redirect(url_for('adminClubPoints', club_name=club_name))

    history = club.get('points_history', [])
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
        recordAudit(
            'add_club',
            'club',
            target=name,
            details={'email': email, 'points': points},
        )
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
    recordAudit('delete_club', 'club', target=club_name)
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
        old_name = comp['name']
        old_places = int(comp['numberOfPlaces'])
        old_registration_open = comp.get('registration_open', True)
        comp['name'] = request.form.get('name', comp['name']).strip()
        comp['date'] = request.form.get('date', comp['date']).strip()
        comp['numberOfPlaces'] = places
        comp['registration_open'] = (
            request.form.get('registration_open') != 'off'
        )
        recordAudit(
            'update_competition',
            'competition',
            target=old_name,
            details={
                'new_name': comp['name'],
                'date': comp['date'],
                'places_before': old_places,
                'places_after': places,
                'registration_before': old_registration_open,
                'registration_after': comp['registration_open'],
            },
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
    recordAudit(
        'toggle_registration',
        'competition',
        target=comp['name'],
        details={'registration_open': comp['registration_open']},
    )
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
        recordAudit(
            'add_competition',
            'competition',
            target=name,
            details={'date': date, 'places': places},
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
    recordAudit('delete_competition', 'competition', target=comp_name)
    saveCompetitions()
    flash(f"Compétition '{comp_name}' supprimée.")
    return redirect(url_for('adminCompetitions'))
