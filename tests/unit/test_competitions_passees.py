import html
from datetime import datetime


def test_reservation_competition_passee_refusee_via_purchase(client):
    """Vérifie qu'on ne peut pas acheter des places pour une compétition passée."""
    from server import clubs, competitions

    club = [c for c in clubs if c['name'] == 'Simply Lift'][0]
    # Spring Festival : 2020-03-27 -> compétition passée
    competition = [c for c in competitions if c['name'] == 'Spring Festival'][0]

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2'
    })

    assert response.status_code == 400
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Vous ne pouvez pas réserver pour une compétition déjà passée." in texte_reponse


def test_reservation_competition_passee_refusee_via_book(client):
    """Vérifie que la route /book redirige avec erreur pour une compétition passée."""
    response = client.get('/book/Spring Festival/Simply Lift')

    assert response.status_code == 400
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Vous ne pouvez pas réserver pour une compétition déjà passée." in texte_reponse


def test_competition_future_accessible(client):
    """Vérifie qu'une compétition future est toujours réservable."""
    from server import competitions

    # On injecte une compétition future pour le test
    competition_future = {
        'name': 'Test Future',
        'date': '2099-01-01 10:00:00',
        'numberOfPlaces': '10'
    }
    competitions.append(competition_future)

    response = client.get('/book/Test Future/Simply Lift')
    assert response.status_code == 200

    # Nettoyage
    competitions.remove(competition_future)
