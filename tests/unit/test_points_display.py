from flask import url_for
import server
from server import clubs


def test_display_board_public_access(client):
    """Vérifie que la route /displayBoard est accessible publiquement (200)."""
    response = client.get('/displayBoard')
    assert response.status_code == 200
    assert "Points des clubs" in response.get_data(as_text=True)


def test_display_board_clubs_sorted_by_points(client):
    """Le classement général est trié par points décroissants."""
    response = client.get('/displayBoard')
    content = response.get_data(as_text=True)

    assert content.index('Simply Lift') < content.index('She Lifts')
    assert content.index('She Lifts') < content.index('Iron Temple')


def test_display_board_has_competition_selector(client):
    """Le classement public propose les compétitions dans un sélecteur."""
    response = client.get('/displayBoard')
    content = response.get_data(as_text=True)

    assert 'competition-select' in content
    assert 'Classement général' in content
    assert 'Future Open' in content


def test_display_board_competition_ranking(client):
    """Le classement d'une compétition utilise les places réservées."""
    simply_lift = next(c for c in server.clubs if c['name'] == 'Simply Lift')
    she_lifts = next(c for c in server.clubs if c['name'] == 'She Lifts')
    iron_temple = next(c for c in server.clubs if c['name'] == 'Iron Temple')
    simply_lift['booked'] = {'Future Open': 2}
    she_lifts['booked'] = {'Future Open': 5}
    iron_temple['booked'] = {}

    response = client.get(
        '/displayBoard', query_string={'competition': 'Future Open'}
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Places réservées' in content
    assert content.index('She Lifts') < content.index('Simply Lift')
    assert 'Iron Temple' not in content
    assert 'Inscriptions ouvertes' in content


def test_display_board_competition_without_booking(client):
    """Une compétition sans réservation affiche un état vide."""
    response = client.get(
        '/displayBoard', query_string={'competition': 'Future Open'}
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Aucune place réservée' in content


def test_display_board_unknown_competition_shows_general(client):
    """Une compétition inconnue revient au classement général."""
    response = client.get(
        '/displayBoard', query_string={'competition': 'Inconnue'}
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Points des clubs' in content
    assert 'Classement général' in content


def test_points_alias_access(client):
    """Vérifie que la route alias /points est également accessible."""
    response = client.get('/points')
    assert response.status_code == 200
    assert "Points des clubs" in response.get_data(as_text=True)


def test_display_board_renders_all_clubs_and_points(client):
    """Vérifie que tous les clubs et leurs points sont bien affichés."""
    response = client.get('/displayBoard')
    assert response.status_code == 200
    content = response.get_data(as_text=True)

    for club in clubs:
        assert club['name'] in content
        assert str(club['points']) in content


def test_index_contains_display_board_link(client):
    """Vérifie la présence du lien vers le tableau des points sur l'accueil."""
    response = client.get('/')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    with client.application.test_request_context():
        expected_link = url_for('displayBoard')
    assert expected_link in content


def test_welcome_contains_display_board_link(client):
    """Vérifie le lien vers le tableau des points sur la page sommaire."""
    response = client.post(
        '/showSummary', data={'email': 'john@simplylift.co'}
    )
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    with client.application.test_request_context():
        expected_link = url_for('displayBoard')
    assert expected_link in content
