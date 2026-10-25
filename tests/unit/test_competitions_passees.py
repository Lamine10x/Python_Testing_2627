import html


def test_reservation_competition_passee_refusee_via_purchase(client):
    """Vérifie le rejet de réservation pour une compétition passée."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    matched = [c for c in competitions if c['name'] == 'Spring Festival']
    competition = matched[0]

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2'
    })

    assert response.status_code == 400
    msg = "Vous ne pouvez pas réserver pour une compétition déjà passée."
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert msg in texte_reponse


def test_reservation_competition_passee_refusee_via_book(client):
    """Vérifie le rejet de la route /book pour compétition passée."""
    response = client.get('/book/Spring Festival/Simply Lift')

    assert response.status_code == 400
    msg = "Vous ne pouvez pas réserver pour une compétition déjà passée."
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert msg in texte_reponse


def test_competition_future_accessible(client):
    """Vérifie qu'une compétition future est toujours réservable."""
    from server import competitions

    competition_future = {
        'name': 'Test Future',
        'date': '2099-01-01 10:00:00',
        'numberOfPlaces': 10
    }
    competitions.append(competition_future)

    response = client.get('/book/Test Future/Simply Lift')
    assert response.status_code == 200

    competitions.remove(competition_future)
