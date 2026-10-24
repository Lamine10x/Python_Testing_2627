from server import loadClubs, loadCompetitions, clubs, competitions


def test_load_clubs_points_sont_entiers():
    """Vérifie que les points de tous les clubs sont bien chargés en tant qu'entiers."""
    loaded_clubs = loadClubs()
    assert len(loaded_clubs) > 0
    for club in loaded_clubs:
        assert isinstance(club['points'], int), f"Les points du club {club['name']} ne sont pas un entier."


def test_load_competitions_places_sont_entiers():
    """Vérifie que le nombre de places de chaque compétition est chargé en tant qu'entier."""
    loaded_comps = loadCompetitions()
    assert len(loaded_comps) > 0
    for comp in loaded_comps:
        assert isinstance(comp['numberOfPlaces'], int), (
            f"Le nombre de places de {comp['name']} n'est pas un entier."
        )


def test_reservation_maintient_types_entiers(client):
    """Vérifie que le solde de points et de places reste strictement de type entier après réservation."""
    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '1'
    })

    assert response.status_code == 200
    assert isinstance(club['points'], int)
    assert isinstance(competition['numberOfPlaces'], int)
