import html

import server


def test_deduction_points_apres_reservation(client):
    """Vérifie la déduction des points et des places après réservation."""
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
    }, follow_redirects=True)

    assert response.status_code == 200
    assert int(club['points']) == points_initiaux - places_a_reserver
    assert int(competition['numberOfPlaces']) == (
        places_initiales - places_a_reserver
    )
    assert "Réservation confirmée" in response.get_data(as_text=True)


def test_reservation_enregistre_places_et_donnees(client, monkeypatch):
    """Une réservation met à jour le suivi et sauvegarde les fichiers."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]
    calls = []
    monkeypatch.setattr(server, 'saveClubs', lambda: calls.append('clubs'))
    monkeypatch.setattr(
        server, 'saveCompetitions', lambda: calls.append('competitions')
    )

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '3',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert club['booked'][competition['name']] == 3
    assert calls == ['clubs', 'competitions']


def test_reservation_points_insuffisants(client):
    """Vérifie le blocage si places demandées > solde de points."""
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
