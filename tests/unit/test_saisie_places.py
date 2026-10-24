import html


def test_reservation_places_negatives_refusee(client):
    """Vérifie qu'un nombre négatif de places est refusé et ne permet pas d'ajouter des points/places."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '-5'
    })

    assert response.status_code == 400
    assert int(club['points']) == points_initiaux
    assert int(competition['numberOfPlaces']) == places_initiales

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Veuillez saisir un nombre de places supérieur à 0." in texte_reponse


def test_reservation_zero_place_refusee(client):
    """Vérifie que la saisie de 0 place est rejetée."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '0'
    })

    assert response.status_code == 400
    assert int(club['points']) == points_initiaux
    assert int(competition['numberOfPlaces']) == places_initiales

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Veuillez saisir un nombre de places supérieur à 0." in texte_reponse


def test_reservation_places_non_numeriques_refusee(client):
    """Vérifie qu'une saisie non numérique ou vide est gérée sans crash 500."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': 'abc'
    })

    assert response.status_code == 400
    assert int(club['points']) == points_initiaux
    assert int(competition['numberOfPlaces']) == places_initiales

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Veuillez saisir un nombre valide de places." in texte_reponse
