import html


def test_deduction_points_apres_reservation(client):
    """Verifie que les points du club et les places sont bien deduits apres une reservation."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])
    places_a_reserver = 2

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': str(places_a_reserver)
    })

    assert response.status_code == 200
    assert int(club['points']) == points_initiaux - places_a_reserver
    assert int(competition['numberOfPlaces']) == places_initiales - places_a_reserver
    assert b"Great-booking complete!" in response.data


def test_reservation_points_insuffisants(client):
    """Verifie qu'un club ne peut pas reserver plus de places qu'il n'a de points."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Iron Temple'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])
    places_demandees = points_initiaux + 5

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': str(places_demandees)
    })

    assert response.status_code == 400
    assert int(club['points']) == points_initiaux
    assert int(competition['numberOfPlaces']) == places_initiales

    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "points" in texte_reponse
