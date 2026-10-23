def test_deduction_points_apres_reservation(client):
    """Vérifie que les points du club et les places sont bien déduits après une réservation."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

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
