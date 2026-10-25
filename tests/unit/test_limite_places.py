import html


def test_reservation_superieure_a_12_places_refusee(client):
    """Vérifie le blocage à plus de 12 places en une seule fois."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    club.setdefault('booked', {})[competition['name']] = 0

    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '13'
    })

    assert response.status_code == 400
    assert int(club['points']) == points_initiaux
    assert int(competition['numberOfPlaces']) == places_initiales

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "12 places" in texte_reponse


def test_reservation_cumulee_superieure_a_12_places_refusee(client):
    """Vérifie le blocage lors du cumul de réservations dépassant 12 places."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    club.setdefault('booked', {})[competition['name']] = 0

    response_1 = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '8'
    }, follow_redirects=True)
    assert response_1.status_code == 200

    points_apres_premiere = int(club['points'])
    places_apres_premiere = int(competition['numberOfPlaces'])

    response_2 = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '6'
    })

    assert response_2.status_code == 400
    assert int(club['points']) == points_apres_premiere
    assert int(competition['numberOfPlaces']) == places_apres_premiere

    texte_reponse = html.unescape(response_2.get_data(as_text=True))
    assert "12 places" in texte_reponse


def test_surreservation_places_competition_refusee(client):
    """Vérifie le blocage si places demandées > stock restant."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    club.setdefault('booked', {})[competition['name']] = 0
    competition['numberOfPlaces'] = 2
    club['points'] = 10

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '4'
    })

    assert response.status_code == 400
    assert int(competition['numberOfPlaces']) == 2
    assert int(club['points']) == 10

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "places disponibles" in texte_reponse
