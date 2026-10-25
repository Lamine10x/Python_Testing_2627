import server


def login(client, email='john@simplylift.co'):
    return client.post('/showSummary', data={'email': email})


def get_club(name):
    return next(c for c in server.clubs if c['name'] == name)


def get_competition(name):
    return next(c for c in server.competitions if c['name'] == name)


def test_tableau_de_bord_affiche_mes_reservations(client):
    """Le tableau de bord affiche les places déjà réservées et le quota."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 3}
    club['points'] = 10

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Mes réservations' in content
    assert 'Future Open' in content
    assert '3/12' in content
    assert '9/12' in content
    assert 'Confirmée' in content
    assert 'Quota restant' in content


def test_page_reservation_affiche_quota_et_maximum(client):
    """Le formulaire de réservation tient compte du quota déjà consommé."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 10}
    club['points'] = 13

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'max="2"' in content
    assert 'Déjà réservées' in content
    assert '10/12' in content
    assert 'Maximum réservable' in content
    assert 'Récapitulatif' in content
    assert 'summary-balance' in content


def test_reservation_reussie_redirige_et_affiche_confirmation(client):
    """Après réservation, le navigateur est redirigé vers le dashboard."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2',
    })

    assert response.status_code == 303
    assert '/dashboard/' in response.headers['Location']
    assert response.headers['Location'].endswith('#mes-reservations')

    page = client.get(response.headers['Location'])
    content = page.get_data(as_text=True)

    assert page.status_code == 200
    assert 'Réservation confirmée' in content
    assert '2 place(s)' in content
    assert 'Historique des points' in content
    assert 'Réservation — Future Open' in content
    assert int(club['points']) == points_initiaux - 2
    assert int(competition['numberOfPlaces']) == places_initiales - 2
    assert club['booked'][competition['name']] == 2


def test_reservation_ajoute_une_ligne_dans_historique_points(client):
    """Une réservation crée un mouvement de points de type reservation."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')

    client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2',
    })

    assert len(club['points_history']) == 1
    entry = club['points_history'][0]
    assert entry['type'] == 'reservation'
    assert entry['amount'] == -2
    assert entry['reason'] == 'Réservation — Future Open'
    assert entry['admin'] == club['name']
    assert entry['balance'] == int(club['points'])


def test_tableau_de_bord_affiche_historique_admin(client):
    """Les anciens mouvements et les ajustements admin restent visibles."""
    club = get_club('Simply Lift')
    club['points_history'] = [
        {
            'date': '2026-01-02 10:00:00',
            'admin': 'Super Admin',
            'amount': 5,
            'reason': 'Bonus de début d’année',
            'balance': 18,
            'type': 'admin',
        },
        {
            'date': '2025-12-01 09:30:00',
            'admin': 'Super Admin',
            'amount': -1,
            'reason': 'Correction',
            'balance': 13,
        },
    ]

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Historique des points' in content
    assert 'Ajustement' in content
    assert 'Bonus de début d’année' in content
    assert '+5' in content
    assert 'Correction' in content
    assert '-1' in content


def test_tableau_de_bord_historique_vide(client):
    """Un club sans mouvement affiche un état vide lisible."""
    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Aucun mouvement de points enregistré.' in content


def test_reservation_quota_atteint_refusee(client):
    """Une réservation directe est bloquée quand le quota de 12 est atteint."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 12}

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'limite de 12 places' in content
    assert 'Quota atteint' in content


def test_reservation_points_insuffisants_refusee(client):
    """Une réservation directe est bloquée quand le club n'a plus de points."""
    club = get_club('Simply Lift')
    club['points'] = 0

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "pas assez de points" in content
    assert 'Points insuffisants' in content


def test_erreur_reservation_reste_sur_le_formulaire(client):
    """Une erreur de quota conserve la saisie et affiche l'erreur."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    points_initiaux = int(club['points'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '13',
    })
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'plus de 12 places' in content
    assert 'id="booking-form"' in content
    assert 'value="13"' in content
    assert 'flash-error' in content
    assert int(club['points']) == points_initiaux
    assert club.get('booked', {}).get(competition['name'], 0) == 0


def test_dashboard_get_accessible_par_url(client):
    """La route GET du tableau de bord sert de cible à la redirection PRG."""
    response = client.get('/dashboard/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Tableau de bord' in content
    assert 'Simply Lift' in content


def test_dashboard_club_inconnu(client):
    """Un club inconnu renvoie une 404 sur la route du dashboard."""
    response = client.get('/dashboard/ClubInexistant')
    content = response.get_data(as_text=True)

    assert response.status_code == 404
    assert 'Club introuvable.' in content


def test_competition_complete_refusee(client):
    """Une compétition sans place restante est signalée comme complète."""
    get_club('Simply Lift')
    competition = get_competition('Future Open')
    competition['numberOfPlaces'] = 0

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'Cette compétition est complète.' in content
    assert 'Complet' in content


def test_reservations_terminees_et_fermees_affichees(client):
    """Les réservations passées ou fermées gardent leur statut."""
    club = get_club('Simply Lift')
    past = get_competition('Spring Festival')
    future = get_competition('Future Open')
    club['booked'] = {
        past['name']: 2,
        future['name']: 1,
    }
    future['registration_open'] = False
    club['points'] = 10

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Terminée' in content
    assert 'Inscriptions fermées' in content


def test_filtre_datefr_geres_les_valeurs_invalides():
    """Le filtre de date renvoie une valeur lisible en cas de donnée vide."""
    assert server.formatDateFr('') == ''
    assert server.formatDateFr(None) == ''
    assert server.formatDateFr('pas-une-date') == 'pas-une-date'
