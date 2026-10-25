from server import loadClubs, loadCompetitions, clubs, competitions


def test_load_clubs_points_sont_entiers():
    """Vérifie que les points des clubs sont chargés en entiers."""
    loaded_clubs = loadClubs()
    assert len(loaded_clubs) > 0
    for club in loaded_clubs:
        assert isinstance(club['points'], int), (
            f"Les points du club {club['name']} ne sont pas un entier."
        )


def test_load_competitions_places_sont_entiers():
    """Vérifie que les places des compétitions sont chargées en entiers."""
    loaded_comps = loadCompetitions()
    assert len(loaded_comps) > 0
    for comp in loaded_comps:
        assert isinstance(comp['numberOfPlaces'], int), (
            f"Le nombre de places de {comp['name']} n'est pas un entier."
        )


def test_load_competitions_inscriptions_sont_booleennes():
    """Vérifie que l'état des inscriptions est chargé en booléen."""
    loaded_comps = loadCompetitions()
    for comp in loaded_comps:
        assert isinstance(comp['registration_open'], bool), (
            f"L'état des inscriptions de {comp['name']} n'est pas un booléen."
        )


def test_reservation_maintient_types_entiers(client):
    """Vérifie le maintien du type entier après réservation."""
    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    competition = [c for c in competitions if c['name'] == 'Future Open'][0]

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert isinstance(club['points'], int)
    assert isinstance(competition['numberOfPlaces'], int)
