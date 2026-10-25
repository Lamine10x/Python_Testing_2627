import pytest

import server


ADMIN_EMAIL = 'admin@gudlft.com'
ADMIN_PASSWORD = 'admin1234'


@pytest.fixture(autouse=True)
def prevent_disk_writes(monkeypatch):
    """Evite d'ecrire dans clubs.json pendant les tests."""
    monkeypatch.setattr(server, 'saveClubs', lambda: None)


def login_admin(client):
    return client.post(
        '/admin/login',
        data={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD},
    )


def get_club(name):
    return next(c for c in server.clubs if c['name'] == name)


def test_admin_points_page_displays_club_and_history(client):
    """La page de gestion des points affiche le solde et l'historique."""
    login_admin(client)
    response = client.get('/admin/clubs/Simply%20Lift/points')

    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Ajuster les points' in content
    assert 'Simply Lift' in content
    assert 'Solde actuel' in content
    assert 'Historique des ajustements' in content
    assert 'Aucun ajustement enregistré pour ce club.' in content


def test_admin_credit_points(client):
    """Un credit augmente le solde et ajoute une entree d'historique."""
    login_admin(client)
    club = get_club('Simply Lift')
    points_before = club['points']

    response = client.post(
        '/admin/clubs/Simply%20Lift/points',
        data={
            'operation': 'credit',
            'amount': '5',
            'reason': 'Bonus partenaire',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert club['points'] == points_before + 5
    assert club['points_history'][0]['amount'] == 5
    assert club['points_history'][0]['balance'] == club['points']
    assert club['points_history'][0]['reason'] == 'Bonus partenaire'
    assert club['points_history'][0]['admin'] == 'Super Admin'

    content = response.get_data(as_text=True)
    assert '5 point(s) crédité(s)' in content
    assert 'Bonus partenaire' in content


def test_admin_debit_points(client):
    """Un debit diminue le solde et ajoute une entree negative."""
    login_admin(client)
    club = get_club('Simply Lift')
    points_before = club['points']

    response = client.post(
        '/admin/clubs/Simply%20Lift/points',
        data={
            'operation': 'debit',
            'amount': '3',
            'reason': 'Régularisation',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert club['points'] == points_before - 3
    assert club['points_history'][0]['amount'] == -3
    assert club['points_history'][0]['balance'] == club['points']
    assert '3 point(s) débité(s)' in response.get_data(as_text=True)


def test_admin_debit_cannot_make_balance_negative(client):
    """Un debit superieur au solde est refuse."""
    login_admin(client)
    club = get_club('Iron Temple')
    club['points'] = 2

    response = client.post(
        '/admin/clubs/Iron%20Temple/points',
        data={'operation': 'debit', 'amount': '3'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert club['points'] == 2
    assert club.get('points_history', []) == []
    assert 'ne peut pas devenir négatif' in response.get_data(as_text=True)


def test_admin_points_invalid_amount(client):
    """Un montant non numerique est refuse."""
    login_admin(client)
    club = get_club('Simply Lift')
    points_before = club['points']

    response = client.post(
        '/admin/clubs/Simply%20Lift/points',
        data={'operation': 'credit', 'amount': 'abc'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert club['points'] == points_before
    assert 'Montant invalide' in response.get_data(as_text=True)


def test_admin_points_amount_must_be_positive(client):
    """Un montant nul ou negatif est refuse."""
    login_admin(client)
    club = get_club('Simply Lift')
    points_before = club['points']

    response = client.post(
        '/admin/clubs/Simply%20Lift/points',
        data={'operation': 'credit', 'amount': '0'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert club['points'] == points_before
    assert 'supérieur à 0' in response.get_data(as_text=True)


def test_admin_points_default_reason(client):
    """Un motif vide est remplace par un libelle par defaut."""
    login_admin(client)
    club = get_club('Simply Lift')

    client.post(
        '/admin/clubs/Simply%20Lift/points',
        data={'operation': 'credit', 'amount': '2', 'reason': ''},
    )

    assert club['points_history'][0]['reason'] == 'Ajustement manuel'


def test_admin_points_invalid_operation(client):
    """Une operation inconnue est refusee."""
    login_admin(client)
    club = get_club('Simply Lift')
    points_before = club['points']

    response = client.post(
        '/admin/clubs/Simply%20Lift/points',
        data={'operation': 'annuler', 'amount': '5'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert club['points'] == points_before
    assert 'Opération invalide.' in response.get_data(as_text=True)


def test_admin_points_unknown_club(client):
    """Un club inconnu redirige vers la liste avec un message."""
    login_admin(client)
    response = client.get(
        '/admin/clubs/Unknown%20Club/points', follow_redirects=True
    )

    assert response.status_code == 200
    assert 'Club introuvable.' in response.get_data(as_text=True)
