import html
import json

import pytest

import server


ADMIN_EMAIL = 'admin@gudlft.com'
ADMIN_PASSWORD = 'admin1234'

REAL_SAVE_CLUBS = server.saveClubs
REAL_SAVE_COMPETITIONS = server.saveCompetitions


@pytest.fixture(autouse=True)
def prevent_disk_writes(monkeypatch):
    """Evite d'ecrire dans les fichiers JSON pendant les tests."""
    monkeypatch.setattr(server, 'saveClubs', lambda: None)
    monkeypatch.setattr(server, 'saveCompetitions', lambda: None)


def login_admin(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    return client.post(
        '/admin/login', data={'email': email, 'password': password}
    )


def test_admin_login_page_accessible(client):
    """La page de connexion admin est accessible sans session."""
    response = client.get('/admin/login')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Connexion administrateur' in content
    assert 'form-admin-login' in content


def test_admin_unauthorized_redirects_and_flashes(client):
    """Une route admin non authentifiee redirige avec un message."""
    response = client.get('/admin', follow_redirects=True)
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Accès réservé aux administrateurs.' in content
    assert 'Connexion administrateur' in content


@pytest.mark.parametrize('method,path', [
    ('get', '/admin'),
    ('get', '/admin/clubs'),
    ('get', '/admin/clubs/add'),
    ('get', '/admin/clubs/edit/Simply%20Lift'),
    ('get', '/admin/clubs/Simply%20Lift/points'),
    ('post', '/admin/clubs/delete/Simply%20Lift'),
    ('get', '/admin/competitions'),
    ('get', '/admin/competitions/add'),
    ('get', '/admin/competitions/edit/Future%20Open'),
    ('post', '/admin/competitions/Future%20Open/toggle-registration'),
    ('post', '/admin/competitions/delete/Future%20Open'),
])
def test_admin_routes_require_login(client, method, path):
    """Toutes les routes d'administration sont protegees."""
    response = getattr(client, method)(path)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/login')


def test_admin_login_success(client):
    """Une connexion valide ouvre une session administrateur."""
    response = login_admin(client)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin')

    with client.session_transaction() as sess:
        assert sess['admin_logged_in'] is True
        assert sess['admin_name'] == 'Super Admin'


def test_admin_login_failure(client):
    """Des identifiants invalides affichent une erreur."""
    response = login_admin(client, password='mauvais-mot-de-passe')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Identifiants incorrects.' in content

    with client.session_transaction() as sess:
        assert 'admin_logged_in' not in sess


def test_admin_login_already_logged_in_redirects(client):
    """Un administrateur deja connecte est redirige vers le dashboard."""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_name'] = 'Super Admin'

    response = client.get('/admin/login')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin')


def test_admin_dashboard_displays_data(client):
    """Le dashboard affiche les statistiques et les donnees."""
    login_admin(client)
    response = client.get('/admin')
    assert response.status_code == 200
    content = response.get_data(as_text=True)

    assert 'Super Admin' in content
    assert 'Clubs inscrits' in content
    assert 'Compétitions' in content
    assert 'Points cumulés' in content
    assert 'Simply Lift' in content
    assert 'Future Open' in content


def test_admin_clubs_list(client):
    """La liste des clubs affiche les informations des clubs."""
    login_admin(client)
    response = client.get('/admin/clubs')
    assert response.status_code == 200
    content = response.get_data(as_text=True)

    assert 'clubs-admin-table' in content
    assert 'Simply Lift' in content
    assert 'john@simplylift.co' in content
    assert 'Ajouter un club' in content


def test_admin_competitions_list(client):
    """La liste des competitions affiche les informations utiles."""
    login_admin(client)
    response = client.get('/admin/competitions')
    assert response.status_code == 200
    content = response.get_data(as_text=True)

    assert 'competitions-admin-table' in content
    assert 'Future Open' in content
    assert '2099-06-15 10:00:00' in content
    assert 'Ajouter une compétition' in content
    assert 'Ouvertes' in content


def test_admin_add_club(client):
    """Un club valide est ajoute a la liste."""
    login_admin(client)
    response = client.get('/admin/clubs/add')
    assert response.status_code == 200
    assert 'form-add-club' in response.get_data(as_text=True)

    response = client.post('/admin/clubs/add', data={
        'name': 'Test Club',
        'email': 'test@club.com',
        'points': '7',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/clubs')

    club = next(c for c in server.clubs if c['name'] == 'Test Club')
    assert club['email'] == 'test@club.com'
    assert club['points'] == 7


def test_admin_add_club_invalid_points(client):
    """Des points non numeriques sont refuses."""
    login_admin(client)
    response = client.post('/admin/clubs/add', data={
        'name': 'Test Club',
        'email': 'test@club.com',
        'points': 'abc',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Valeur de points invalide.' in response.get_data(as_text=True)
    assert not any(c['name'] == 'Test Club' for c in server.clubs)


def test_admin_add_club_missing_fields(client):
    """Le nom et l'email sont obligatoires."""
    login_admin(client)
    response = client.post('/admin/clubs/add', data={
        'name': '',
        'email': '',
        'points': '5',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Nom et email requis.' in response.get_data(as_text=True)
    assert len(server.clubs) == 3


def test_admin_edit_club(client):
    """Un club existant peut etre modifie."""
    login_admin(client)
    response = client.get('/admin/clubs/edit/Simply%20Lift')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'form-edit-club' in content
    assert 'Simply Lift' in content

    response = client.post('/admin/clubs/edit/Simply%20Lift', data={
        'name': 'Simply Lift Renamed',
        'email': 'renamed@simplylift.co',
        'points': '42',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/clubs')

    club = next(
        c for c in server.clubs if c['name'] == 'Simply Lift Renamed'
    )
    assert club['email'] == 'renamed@simplylift.co'
    assert club['points'] == 42
    assert isinstance(club['points'], int)


def test_admin_edit_club_invalid_points(client):
    """Une valeur de points invalide ne modifie pas le club."""
    login_admin(client)
    club = next(c for c in server.clubs if c['name'] == 'Simply Lift')
    points_before = club['points']

    response = client.post('/admin/clubs/edit/Simply%20Lift', data={
        'name': 'Simply Lift',
        'email': club['email'],
        'points': 'abc',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Valeur de points invalide.' in response.get_data(as_text=True)
    assert club['points'] == points_before


def test_admin_edit_unknown_club(client):
    """Un club inconnu redirige vers la liste avec un message."""
    login_admin(client)
    response = client.get(
        '/admin/clubs/edit/Unknown%20Club', follow_redirects=True
    )
    assert response.status_code == 200
    assert 'Club introuvable.' in response.get_data(as_text=True)


def test_admin_delete_club(client):
    """Un club peut etre supprime."""
    login_admin(client)
    response = client.post(
        '/admin/clubs/delete/Simply%20Lift', follow_redirects=True
    )
    assert response.status_code == 200
    content = html.unescape(response.get_data(as_text=True))
    assert 'Club \'Simply Lift\' supprimé.' in content
    assert not any(c['name'] == 'Simply Lift' for c in server.clubs)


def test_admin_add_competition(client):
    """Une competition valide est ajoutee a la liste."""
    login_admin(client)
    response = client.get('/admin/competitions/add')
    assert response.status_code == 200
    assert 'form-add-competition' in response.get_data(as_text=True)

    response = client.post('/admin/competitions/add', data={
        'name': 'New Competition',
        'date': '2099-01-01 10:00:00',
        'numberOfPlaces': '30',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/competitions')

    comp = next(
        c for c in server.competitions if c['name'] == 'New Competition'
    )
    assert comp['date'] == '2099-01-01 10:00:00'
    assert comp['numberOfPlaces'] == 30
    assert comp['registration_open'] is True


def test_admin_add_competition_invalid_places(client):
    """Un nombre de places invalide est refuse."""
    login_admin(client)
    response = client.post('/admin/competitions/add', data={
        'name': 'New Competition',
        'date': '2099-01-01 10:00:00',
        'numberOfPlaces': 'abc',
    }, follow_redirects=True)
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Nombre de places invalide.' in content
    assert not any(
        c['name'] == 'New Competition' for c in server.competitions
    )


def test_admin_add_competition_missing_fields(client):
    """Le nom et la date sont obligatoires."""
    login_admin(client)
    response = client.post('/admin/competitions/add', data={
        'name': '',
        'date': '',
        'numberOfPlaces': '10',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Nom et date requis.' in response.get_data(as_text=True)
    assert len(server.competitions) == 3


def test_admin_edit_competition(client):
    """Une competition existante peut etre modifiee."""
    login_admin(client)
    response = client.get('/admin/competitions/edit/Future%20Open')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'form-edit-competition' in content
    assert 'Future Open' in content

    response = client.post(
        '/admin/competitions/edit/Future%20Open',
        data={
            'name': 'Future Open Updated',
            'date': '2099-07-01 12:30:00',
            'numberOfPlaces': '40',
        }
    )
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/competitions')

    comp = next(
        c for c in server.competitions if c['name'] == 'Future Open Updated'
    )
    assert comp['date'] == '2099-07-01 12:30:00'
    assert comp['numberOfPlaces'] == 40
    assert isinstance(comp['numberOfPlaces'], int)
    assert comp['registration_open'] is True


def test_admin_edit_competition_invalid_places(client):
    """Un nombre de places invalide ne modifie pas la competition."""
    login_admin(client)
    comp = next(
        c for c in server.competitions if c['name'] == 'Future Open'
    )
    places_before = comp['numberOfPlaces']

    response = client.post(
        '/admin/competitions/edit/Future%20Open',
        data={
            'name': comp['name'],
            'date': comp['date'],
            'numberOfPlaces': 'abc',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert 'Nombre de places invalide.' in content
    assert comp['numberOfPlaces'] == places_before


def test_admin_edit_unknown_competition(client):
    """Une competition inconnue redirige vers la liste."""
    login_admin(client)
    response = client.get(
        '/admin/competitions/edit/Unknown', follow_redirects=True
    )
    assert response.status_code == 200
    assert 'Compétition introuvable.' in response.get_data(as_text=True)


def test_admin_delete_competition(client):
    """Une competition peut etre supprimee."""
    login_admin(client)
    response = client.post(
        '/admin/competitions/delete/Future%20Open',
        follow_redirects=True,
    )
    assert response.status_code == 200
    content = html.unescape(response.get_data(as_text=True))
    assert 'Compétition \'Future Open\' supprimée.' in content
    assert not any(
        c['name'] == 'Future Open' for c in server.competitions
    )


def test_admin_logout(client):
    """La deconnexion admin vide la session et redirige."""
    login_admin(client)
    response = client.get('/admin/logout', follow_redirects=True)
    assert response.status_code == 200
    assert 'Session admin terminée.' in response.get_data(as_text=True)

    with client.session_transaction() as sess:
        assert 'admin_logged_in' not in sess
        assert 'admin_name' not in sess


def test_load_admins_accepts_utf8_bom(tmp_path, monkeypatch):
    """Le chargement des admins tolere un fichier UTF-8 avec BOM."""
    admin_file = tmp_path / 'admin.json'
    admin_file.write_bytes(
        b'\xef\xbb\xbf[{"email": "a@b.c", "password": "x", "name": "A"}]'
    )
    monkeypatch.chdir(tmp_path)

    admins = server.loadAdmins()

    assert admins[0]['email'] == 'a@b.c'


def test_save_functions_write_json(tmp_path, monkeypatch):
    """Les fonctions de sauvegarde ecrivent bien les donnees JSON."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        server, 'clubs',
        [{
            'name': 'Test',
            'email': 'test@club.com',
            'points': 3,
            'points_history': [{
                'amount': 2,
                'reason': 'Bonus été',
                'balance': 3,
            }],
        }]
    )
    monkeypatch.setattr(
        server, 'competitions',
        [{
            'name': 'Comp',
            'date': '2099-01-01 00:00:00',
            'numberOfPlaces': 5,
            'registration_open': False,
        }]
    )
    monkeypatch.setattr(server, 'saveClubs', REAL_SAVE_CLUBS)
    monkeypatch.setattr(server, 'saveCompetitions', REAL_SAVE_COMPETITIONS)

    server.saveClubs()
    server.saveCompetitions()

    clubs_data = json.loads(
        (tmp_path / 'clubs.json').read_text(encoding='utf-8')
    )
    comps_data = json.loads(
        (tmp_path / 'competitions.json').read_text(encoding='utf-8')
    )
    assert clubs_data['clubs'][0]['points'] == 3
    assert clubs_data['clubs'][0]['points_history'][0]['amount'] == 2
    assert clubs_data['clubs'][0]['points_history'][0]['reason'] == 'Bonus été'
    assert comps_data['competitions'][0]['numberOfPlaces'] == 5
    assert comps_data['competitions'][0]['registration_open'] is False
