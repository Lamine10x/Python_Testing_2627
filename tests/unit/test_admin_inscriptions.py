import pytest

import server


ADMIN_EMAIL = 'admin@gudlft.com'
ADMIN_PASSWORD = 'admin1234'


@pytest.fixture(autouse=True)
def prevent_disk_writes(monkeypatch):
    """Evite d'ecrire dans les fichiers JSON pendant les tests."""
    monkeypatch.setattr(server, 'saveCompetitions', lambda: None)
    monkeypatch.setattr(server, 'saveClubs', lambda: None)


def login_admin(client):
    return client.post(
        '/admin/login',
        data={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD},
    )


def get_competition(name):
    return next(c for c in server.competitions if c['name'] == name)


def get_club(name):
    return next(c for c in server.clubs if c['name'] == name)


def test_admin_toggle_registration_closes_then_reopens(client):
    """Le bouton admin alterne entre inscriptions ouvertes et fermees."""
    login_admin(client)
    comp = get_competition('Future Open')
    assert comp['registration_open'] is True

    response = client.post(
        '/admin/competitions/Future%20Open/toggle-registration',
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert comp['registration_open'] is False
    content = response.get_data(as_text=True)
    assert 'Inscriptions fermées' in content
    assert 'Ouvrir' in content

    response = client.post(
        '/admin/competitions/Future%20Open/toggle-registration',
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert comp['registration_open'] is True
    content = response.get_data(as_text=True)
    assert 'Inscriptions ouvertes pour' in content
    assert 'Fermer' in content


def test_admin_toggle_unknown_competition(client):
    """Une competition inconnue redirige vers la liste."""
    login_admin(client)
    response = client.post(
        '/admin/competitions/Unknown/toggle-registration',
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert 'Compétition introuvable.' in response.get_data(as_text=True)


def test_closed_competition_blocks_booking_page(client):
    """Une competition fermee ne permet pas d'ouvrir la page de reservation."""
    comp = get_competition('Future Open')
    comp['registration_open'] = False

    response = client.get('/book/Future%20Open/Simply%20Lift')

    assert response.status_code == 403
    assert 'Les inscriptions sont fermées' in response.get_data(as_text=True)


def test_closed_competition_blocks_purchase(client):
    """Une competition fermee ne permet pas de reserver des places."""
    comp = get_competition('Future Open')
    comp['registration_open'] = False
    club = get_club('Simply Lift')
    points_before = club['points']
    places_before = comp['numberOfPlaces']

    response = client.post('/purchasePlaces', data={
        'competition': 'Future Open',
        'club': 'Simply Lift',
        'places': '2',
    })

    assert response.status_code == 403
    assert 'Les inscriptions sont fermées' in response.get_data(as_text=True)
    assert club['points'] == points_before
    assert comp['numberOfPlaces'] == places_before


def test_open_competition_allows_booking_page(client):
    """Une competition ouverte reste reservable."""
    response = client.get('/book/Future%20Open/Simply%20Lift')

    assert response.status_code == 200
    assert 'Réserver' in response.get_data(as_text=True)


def test_welcome_shows_closed_registration(client):
    """Le tableau de bord club signale les inscriptions fermees."""
    comp = get_competition('Future Open')
    comp['registration_open'] = False

    response = client.post(
        '/showSummary', data={'email': 'john@simplylift.co'}
    )

    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Inscriptions fermées' in content
    assert '/book/Future%20Open/Simply%20Lift' not in content


def test_admin_add_competition_defaults_to_open(client):
    """Une competition ajoutee sans choix explicite est ouverte."""
    login_admin(client)
    client.post('/admin/competitions/add', data={
        'name': 'Open By Default',
        'date': '2099-01-01 10:00:00',
        'numberOfPlaces': '30',
    })

    comp = get_competition('Open By Default')
    assert comp['registration_open'] is True


def test_admin_add_competition_can_be_closed(client):
    """Une competition peut etre ajoutee avec les inscriptions fermees."""
    login_admin(client)
    client.post('/admin/competitions/add', data={
        'name': 'Closed Competition',
        'date': '2099-01-01 10:00:00',
        'numberOfPlaces': '30',
        'registration_open': 'off',
    })

    comp = get_competition('Closed Competition')
    assert comp['registration_open'] is False


def test_admin_edit_competition_can_close_registration(client):
    """La fiche de modification permet de fermer les inscriptions."""
    login_admin(client)
    comp = get_competition('Future Open')

    response = client.post(
        '/admin/competitions/edit/Future%20Open',
        data={
            'name': comp['name'],
            'date': comp['date'],
            'numberOfPlaces': str(comp['numberOfPlaces']),
            'registration_open': 'off',
        },
    )

    assert response.status_code == 302
    assert comp['registration_open'] is False
