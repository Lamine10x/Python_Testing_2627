import pytest

import server


ADMIN_EMAIL = 'admin@gudlft.com'
ADMIN_PASSWORD = 'admin1234'


def login_admin(client):
    return client.post(
        '/admin/login',
        data={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD},
    )


def get_club(name):
    return next(c for c in server.clubs if c['name'] == name)


def get_competition(name):
    return next(c for c in server.competitions if c['name'] == name)


def prepare_reservations():
    simply = get_club('Simply Lift')
    iron = get_club('Iron Temple')
    future = get_competition('Future Open')
    simply['booked'] = {future['name']: 3}
    iron['booked'] = {future['name']: 1}
    return simply, iron, future


def test_admin_reservations_liste_et_indicateurs(client):
    """La liste admin agrège les réservations de tous les clubs."""
    prepare_reservations()
    login_admin(client)

    response = client.get('/admin/reservations')
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'admin-reservations-table' in content
    assert 'Réservations actives' in content
    assert 'Places réservées' in content
    assert 'Points remboursables' in content
    assert 'Simply Lift' in content
    assert 'Iron Temple' in content
    assert 'Future Open' in content
    assert 'Annuler / rembourser' in content


def test_admin_reservations_filtres(client):
    """Les filtres admin limitent les lignes par club et compétition."""
    simply, iron, future = prepare_reservations()
    login_admin(client)

    data = server.buildAdminReservations({'club': simply['name']})
    assert [item['club']['name'] for item in data['reservations']] == [
        simply['name']
    ]

    data = server.buildAdminReservations({
        'competition': future['name'],
        'statut': 'confirmee',
    })
    assert len(data['reservations']) == 2

    data = server.buildAdminReservations({'statut': 'terminee'})
    assert data['reservations'] == []

    data = server.buildAdminReservations({
        'competition': 'Spring Festival',
    })
    assert data['reservations'] == []

    response = client.get(
        '/admin/reservations?club=Simply%20Lift&statut=confirmee'
    )
    content = response.get_data(as_text=True)
    assert 'value="Simply Lift" selected' in content
    assert 'value="confirmee" selected' in content


def test_admin_dashboard_affiche_reservations_et_audit(client):
    """Le tableau de bord admin expose les nouveaux indicateurs et liens."""
    prepare_reservations()
    login_admin(client)

    response = client.get('/admin')
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Réservations actives' in content
    assert 'Places réservées' in content
    assert "Entrées d'audit" in content
    assert 'Gérer les réservations' in content
    assert "Journal d'audit" in content


def test_admin_annulation_formulaire(client):
    """Le formulaire d'annulation rappelle le quota et le remboursement."""
    simply, _, future = prepare_reservations()
    simply['points'] = 10
    login_admin(client)

    response = client.get(
        '/admin/reservations/Simply%20Lift/Future%20Open/cancel'
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Annulation et remboursement' in content
    assert 'Places réservées' in content
    assert 'Remboursement max.' in content
    assert 'max="3"' in content
    assert 'Confirmer' in content
    assert future['name'] in content


def test_admin_annulation_partielle_rembourse_et_trace(client):
    """Une annulation partielle crédite les points et libère les places."""
    simply, _, future = prepare_reservations()
    simply['points'] = 10
    future['numberOfPlaces'] = 5
    login_admin(client)

    response = client.post(
        '/admin/reservations/Simply%20Lift/Future%20Open/cancel',
        data={'places': '2', 'reason': 'Blessure'},
        follow_redirects=True,
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '2 place(s) annulée(s)' in content
    assert 'Nouveau solde : 12 point(s)' in content
    assert simply['points'] == 12
    assert future['numberOfPlaces'] == 7
    assert simply['booked'][future['name']] == 1
    entry = simply['points_history'][0]
    assert entry['type'] == 'refund'
    assert entry['amount'] == 2
    assert 'Blessure' in entry['reason']
    assert entry['balance'] == 12

    audit = server.audit_entries[0]
    assert audit['action'] == 'cancel_reservation'
    assert audit['category'] == 'reservation'
    assert audit['details']['places'] == 2
    assert audit['details']['booked_after'] == 1
    assert audit['details']['reason'] == 'Blessure'


def test_admin_annulation_totale_supprime_la_reservation(client):
    """Une annulation totale retire la réservation du club."""
    simply, _, future = prepare_reservations()
    simply['points'] = 10
    future['numberOfPlaces'] = 5
    login_admin(client)

    response = client.post(
        '/admin/reservations/Simply%20Lift/Future%20Open/cancel',
        data={'places': '3'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert future['name'] not in simply['booked']
    assert simply['points'] == 13
    assert future['numberOfPlaces'] == 8
    assert simply['points_history'][0]['type'] == 'refund'


@pytest.mark.parametrize(
    'places, message',
    [
        ('abc', 'nombre valide'),
        ('0', 'supérieur à 0'),
        ('4', 'réservé que 3'),
    ],
)
def test_admin_annulation_invalide(client, places, message):
    """Une annulation invalide ne modifie ni les points ni les places."""
    simply, _, future = prepare_reservations()
    simply['points'] = 10
    future['numberOfPlaces'] = 5
    login_admin(client)

    response = client.post(
        '/admin/reservations/Simply%20Lift/Future%20Open/cancel',
        data={'places': places, 'reason': 'Test'},
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert message in content
    assert simply['points'] == 10
    assert future['numberOfPlaces'] == 5
    assert simply['booked'][future['name']] == 3
    assert len(simply['points_history']) == 0


def test_admin_annulation_club_ou_competition_inconnu(client):
    """Les cibles inconnues sont signalées sans modification."""
    login_admin(client)

    response = client.get(
        '/admin/reservations/Inconnu/Future%20Open/cancel',
        follow_redirects=True,
    )
    assert 'Club introuvable.' in response.get_data(as_text=True)

    response = client.get(
        '/admin/reservations/Simply%20Lift/Inconnue/cancel',
        follow_redirects=True,
    )
    assert 'Compétition introuvable.' in response.get_data(as_text=True)


def test_admin_annulation_sans_reservation(client):
    """Un club sans réservation ne peut pas annuler."""
    login_admin(client)

    response = client.get(
        '/admin/reservations/Simply%20Lift/Future%20Open/cancel',
        follow_redirects=True,
    )
    assert 'Aucune réservation à annuler' in response.get_data(as_text=True)


def test_admin_audit_page_et_filtre(client):
    """Le journal affiche les actions et se filtre par catégorie."""
    simply = get_club('Simply Lift')
    login_admin(client)
    client.post(
        f'/admin/clubs/{simply["name"]}/points',
        data={
            'operation': 'credit',
            'amount': '5',
            'reason': 'Bonus audit',
        },
    )

    response = client.get('/admin/audit')
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'audit-table' in content
    assert 'Connexion admin' in content
    assert 'Crédit de points' in content
    assert 'Super Admin' in content
    assert 'Bonus audit' in content

    data = server.buildAuditEntries({'categorie': 'points'})
    assert data['audit_entries']
    assert all(
        entry['category'] == 'points'
        for entry in data['audit_entries']
    )
    assert any(
        entry['action'] == 'credit_points'
        for entry in data['audit_entries']
    )

    response = client.get('/admin/audit?categorie=points&action=credit_points')
    content = response.get_data(as_text=True)
    assert 'value="points" selected' in content
    assert 'value="credit_points" selected' in content
    assert 'Crédit de points' in content


def test_admin_actions_ecrivent_dans_l_audit(client):
    """Les principales actions admin alimentent le journal global."""
    login_admin(client)
    client.post('/admin/clubs/add', data={
        'name': 'Audit Club',
        'email': 'audit@club.com',
        'points': '4',
    })
    client.post(
        '/admin/competitions/Future%20Open/toggle-registration'
    )
    client.post('/admin/competitions/add', data={
        'name': 'Audit Competition',
        'date': '2099-08-01 10:00:00',
        'numberOfPlaces': '20',
    })
    client.post('/admin/clubs/delete/Audit%20Club')

    actions = {entry['action'] for entry in server.audit_entries}
    assert {
        'admin_login',
        'add_club',
        'toggle_registration',
        'add_competition',
        'delete_club',
    } <= actions


def test_format_audit_details_couvre_les_types_d_action():
    """Chaque type d'action dispose d'un résumé lisible."""
    cases = [
        ('cancel_reservation', {'places': 2, 'reason': 'Blessure'}),
        ('book_places', {'places': 3}),
        ('credit_points', {'amount': 5, 'reason': 'Bonus'}),
        ('debit_points', {'amount': 2, 'reason': 'Correction'}),
        ('update_club', {'points_before': 3, 'points_after': 8}),
        ('update_competition', {'places_before': 5, 'places_after': 9}),
        ('toggle_registration', {'registration_open': True}),
        ('toggle_registration', {'registration_open': False}),
        ('add_club', {'email': 'club@test.com'}),
        ('add_competition', {'date': '2099-01-01 10:00:00'}),
        ('admin_login', {}),
        ('admin_logout', {}),
        ('unknown_action', {}),
    ]
    for action, details in cases:
        text = server.formatAuditDetails({
            'action': action,
            'details': details,
        })
        assert isinstance(text, str)


def test_build_audit_entries_filtre_acteur_et_options(client):
    """Les filtres acteur et les options de formulaire sont exposés."""
    server.audit_entries = [
        {
            'date': '2026-01-02 10:00:00',
            'actor': 'Super Admin',
            'action': 'credit_points',
            'category': 'points',
            'target': 'Simply Lift',
            'details': {'amount': 5, 'reason': 'Bonus'},
        },
        {
            'date': '2026-01-01 09:00:00',
            'actor': 'Simply Lift',
            'action': 'book_places',
            'category': 'reservation',
            'target': 'Simply Lift — Future Open',
            'details': {'places': 2},
        },
    ]

    data = server.buildAuditEntries({'acteur': 'simply'})
    assert len(data['audit_entries']) == 1
    assert data['audit_entries'][0]['actor'] == 'Simply Lift'
    assert data['audit_entries'][0]['action_label'] == 'Réservation de places'
    assert data['audit_entries'][0]['category_label'] == 'Réservations'
    assert data['audit_entries'][0]['details_text'] == (
        '2 place(s) réservée(s)'
    )
    assert data['audit_total'] == 2
    assert data['audit_filtered_count'] == 1
    assert data['audit_action_options']
    assert data['audit_category_options']
    assert data['audit_actors'] == ['Simply Lift', 'Super Admin']

    data = server.buildAuditEntries({'action': 'admin_login'})
    assert data['audit_entries'] == []


def test_build_admin_reservations_ignore_les_donnees_invalides(client):
    """Les réservations mal formées ou orphelines sont ignorées."""
    club = get_club('Simply Lift')
    club['booked'] = {
        'Future Open': 'abc',
        'Compétition absente': 2,
        'Spring Festival': 0,
    }

    data = server.buildAdminReservations()
    assert data['reservations'] == []
    assert data['reservation_stats']['reservations'] == 0


def test_get_reservation_status_date_invalide_et_statuts(client):
    """Le statut couvre les dates invalides, passées et fermées."""
    status = server.getReservationStatus({
        'name': 'Test',
        'date': 'pas-une-date',
        'registration_open': True,
    })
    assert status['status'] == 'Confirmée'

    past = get_competition('Spring Festival')
    assert server.getReservationStatus(past)['status'] == 'Terminée'

    future = get_competition('Future Open')
    future['registration_open'] = False
    assert (
        server.getReservationStatus(future)['status']
        == 'Inscriptions fermées'
    )
