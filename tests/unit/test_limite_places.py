import html


def test_reservation_superieure_a_12_places_refusee(client):
    """Vérifie qu'un club ne peut pas réserver plus de 12 places en une seule fois."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    # Réinitialise le suivi des réservations pour le test
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
    assert "Vous ne pouvez pas réserver plus de 12 places au total pour une compétition." in texte_reponse


def test_reservation_cumulee_superieure_a_12_places_refusee(client):
    """Vérifie qu'un club ne peut pas dépasser 12 places en cumulant plusieurs réservations."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    # Réinitialise le suivi des réservations pour le test
    club.setdefault('booked', {})[competition['name']] = 0

    # Première réservation de 8 places (valide car <= 12)
    response_1 = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '8'
    })
    assert response_1.status_code == 200

    # Deuxième réservation de 6 places (8 + 6 = 14 > 12 -> doit être refusée)
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
    assert "Vous ne pouvez pas réserver plus de 12 places au total pour une compétition." in texte_reponse


def test_surreservation_places_competition_refusee(client):
    """Vérifie qu'un club ne peut pas réserver plus de places que le stock restant de la compétition."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    # Réinitialise le suivi des réservations
    club.setdefault('booked', {})[competition['name']] = 0

    # On simule une compétition avec seulement 2 places disponibles
    competition['numberOfPlaces'] = 2
    club['points'] = 10  # Le club a assez de points

    # On tente de réserver 4 places (<= 12 et <= points du club, mais > 2 places disponibles)
    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '4'
    })

    assert response.status_code == 400
    assert int(competition['numberOfPlaces']) == 2
    assert int(club['points']) == 10

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Il n'y a pas assez de places disponibles dans cette compétition." in texte_reponse
