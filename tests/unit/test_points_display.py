from flask import url_for
from server import clubs


def test_display_board_public_access(client):
    """Vérifie que la route /displayBoard est accessible publiquement (200)."""
    response = client.get('/displayBoard')
    assert response.status_code == 200
    assert "Points des clubs" in response.get_data(as_text=True)


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
