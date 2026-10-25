import json

import server


REAL_SAVE_AUDIT = server.saveAuditLog


def login(client, email='john@simplylift.co'):
    return client.post('/showSummary', data={'email': email})


def get_club(name):
    return next(c for c in server.clubs if c['name'] == name)


def get_competition(name):
    return next(c for c in server.competitions if c['name'] == name)


def test_tableau_de_bord_affiche_mes_reservations(client):
    """Le tableau de bord affiche les places déjà réservées et le quota."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 3}
    club['points'] = 10

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Mes réservations' in content
    assert 'Future Open' in content
    assert '3/12' in content
    assert '9/12' in content
    assert 'Confirmée' in content
    assert 'Quota restant' in content


def test_page_reservation_affiche_quota_et_maximum(client):
    """Le formulaire de réservation tient compte du quota déjà consommé."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 10}
    club['points'] = 13

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'max="2"' in content
    assert 'Déjà réservées' in content
    assert '10/12' in content
    assert 'Maximum réservable' in content
    assert 'Récapitulatif' in content
    assert 'summary-balance' in content


def test_reservation_reussie_redirige_et_affiche_confirmation(client):
    """Après réservation, le navigateur est redirigé vers le dashboard."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    points_initiaux = int(club['points'])
    places_initiales = int(competition['numberOfPlaces'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2',
    })

    assert response.status_code == 303
    assert '/dashboard/' in response.headers['Location']
    assert response.headers['Location'].endswith('#mes-reservations')

    page = client.get(response.headers['Location'])
    content = page.get_data(as_text=True)

    assert page.status_code == 200
    assert 'Réservation confirmée' in content
    assert '2 place(s)' in content
    assert 'Historique des points' in content
    assert 'Réservation — Future Open' in content
    assert int(club['points']) == points_initiaux - 2
    assert int(competition['numberOfPlaces']) == places_initiales - 2
    assert club['booked'][competition['name']] == 2


def test_reservation_ajoute_une_ligne_dans_historique_points(client):
    """Une réservation crée un mouvement de points de type reservation."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')

    client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2',
    })

    assert len(club['points_history']) == 1
    entry = club['points_history'][0]
    assert entry['type'] == 'reservation'
    assert entry['amount'] == -2
    assert entry['reason'] == 'Réservation — Future Open'
    assert entry['admin'] == club['name']
    assert entry['balance'] == int(club['points'])


def test_tableau_de_bord_affiche_historique_admin(client):
    """Les anciens mouvements et les ajustements admin restent visibles."""
    club = get_club('Simply Lift')
    club['points_history'] = [
        {
            'date': '2026-01-02 10:00:00',
            'admin': 'Super Admin',
            'amount': 5,
            'reason': 'Bonus de début d’année',
            'balance': 18,
            'type': 'admin',
        },
        {
            'date': '2025-12-01 09:30:00',
            'admin': 'Super Admin',
            'amount': -1,
            'reason': 'Correction',
            'balance': 13,
        },
    ]

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Historique des points' in content
    assert 'Ajustement' in content
    assert 'Bonus de début d’année' in content
    assert '+5' in content
    assert 'Correction' in content
    assert '-1' in content


def test_tableau_de_bord_historique_vide(client):
    """Un club sans mouvement affiche un état vide lisible."""
    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Aucun mouvement de points enregistré.' in content


def test_reservation_quota_atteint_refusee(client):
    """Une réservation directe est bloquée quand le quota de 12 est atteint."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 12}

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'limite de 12 places' in content
    assert 'Quota atteint' in content


def test_reservation_points_insuffisants_refusee(client):
    """Une réservation directe est bloquée quand le club n'a plus de points."""
    club = get_club('Simply Lift')
    club['points'] = 0

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "pas assez de points" in content
    assert 'Points insuffisants' in content


def test_erreur_reservation_reste_sur_le_formulaire(client):
    """Une erreur de quota conserve la saisie et affiche l'erreur."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    points_initiaux = int(club['points'])

    response = client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '13',
    })
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'plus de 12 places' in content
    assert 'id="booking-form"' in content
    assert 'value="13"' in content
    assert 'flash-error' in content
    assert int(club['points']) == points_initiaux
    assert club.get('booked', {}).get(competition['name'], 0) == 0


def test_dashboard_get_accessible_par_url(client):
    """La route GET du tableau de bord sert de cible à la redirection PRG."""
    response = client.get('/dashboard/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Tableau de bord' in content
    assert 'Simply Lift' in content


def test_dashboard_club_inconnu(client):
    """Un club inconnu renvoie une 404 sur la route du dashboard."""
    response = client.get('/dashboard/ClubInexistant')
    content = response.get_data(as_text=True)

    assert response.status_code == 404
    assert 'Club introuvable.' in content


def test_competition_complete_refusee(client):
    """Une compétition sans place restante est signalée comme complète."""
    get_club('Simply Lift')
    competition = get_competition('Future Open')
    competition['numberOfPlaces'] = 0

    response = client.get('/book/Future Open/Simply Lift')
    content = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'Cette compétition est complète.' in content
    assert 'Complet' in content


def test_reservations_terminees_et_fermees_affichees(client):
    """Les réservations passées ou fermées gardent leur statut."""
    club = get_club('Simply Lift')
    past = get_competition('Spring Festival')
    future = get_competition('Future Open')
    club['booked'] = {
        past['name']: 2,
        future['name']: 1,
    }
    future['registration_open'] = False
    club['points'] = 10

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Terminée' in content
    assert 'Inscriptions fermées' in content


def test_filtre_datefr_geres_les_valeurs_invalides():
    """Le filtre de date renvoie une valeur lisible en cas de donnée vide."""
    assert server.formatDateFr('') == ''
    assert server.formatDateFr(None) == ''
    assert server.formatDateFr('pas-une-date') == 'pas-une-date'


def test_filtre_reservations_par_statut_et_competition(client):
    """Le tableau de bord peut filtrer les réservations par statut et nom."""
    club = get_club('Simply Lift')
    past = get_competition('Spring Festival')
    future = get_competition('Future Open')
    club['booked'] = {
        past['name']: 2,
        future['name']: 1,
    }
    club['points'] = 10

    termine = server.buildClubDashboard(club, {'statut': 'terminee'})
    assert [r['competition']['name'] for r in termine['reservations']] == [
        past['name']
    ]

    confirme = server.buildClubDashboard(club, {
        'statut': 'confirmee',
        'competition': future['name'],
    })
    assert [r['competition']['name'] for r in confirme['reservations']] == [
        future['name']
    ]

    aucun = server.buildClubDashboard(club, {
        'statut': 'confirmee',
        'competition': past['name'],
    })
    assert aucun['reservations'] == []
    assert aucun['reservation_total'] == 2


def test_dashboard_affiche_formulaire_de_filtre_et_etat_vide(client):
    """Le filtre est accessible et signale l'absence de résultat."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 1}

    response = client.get(
        '/dashboard/Simply Lift?statut=terminee&competition=Future%20Open'
    )
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Filtrer mes réservations' in content
    assert (
        'Aucune réservation ne correspond aux filtres sélectionnés.'
        in content
    )
    assert 'value="terminee" selected' in content
    assert 'value="Future Open" selected' in content


def test_historique_complet_affiche_plus_de_dix_mouvements(client):
    """L'historique n'est plus limité aux dix derniers mouvements."""
    club = get_club('Simply Lift')
    club['points_history'] = [
        {
            'date': f'2026-01-{index:02d} 10:00:00',
            'admin': 'Super Admin',
            'amount': 1,
            'reason': f'Mouvement {index}',
            'balance': index,
            'type': 'admin',
        }
        for index in range(1, 16)
    ]

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Mouvement 1' in content
    assert 'Mouvement 15' in content
    assert '15 mouvement(s)' in content


def test_dashboard_visuel_affiche_points_consommes_echeances_et_liberations(
    client
):
    """Les indicateurs et les flux récents sont visibles sur le dashboard."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 3}
    club['points'] = 7
    server.audit_entries = [{
        'date': '2026-01-02 10:00:00',
        'actor': 'Super Admin',
        'action': 'cancel_reservation',
        'category': 'reservation',
        'target': 'Iron Temple — Future Open',
        'details': {
            'club': 'Iron Temple',
            'competition': competition['name'],
            'places': 2,
        },
    }]

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Points consommés' in content
    assert 'Prochaines échéances' in content
    assert 'Places libérées récemment' in content
    assert 'Libérées par Iron Temple' in content
    assert '2 place(s)' in content
    assert 'J-' in content


def test_reservation_ecrit_une_entree_dans_le_journal_audit(client):
    """Une réservation est tracée dans le journal global."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')

    client.post('/purchasePlaces', data={
        'club': club['name'],
        'competition': competition['name'],
        'places': '2',
    })

    assert len(server.audit_entries) == 1
    entry = server.audit_entries[0]
    assert entry['action'] == 'book_places'
    assert entry['category'] == 'reservation'
    assert entry['actor'] == club['name']
    assert entry['details']['places'] == 2
    assert entry['details']['competition'] == competition['name']


def test_dashboard_espace_club_accessibilite_clavier_et_aria(client):
    """Les repères ARIA, le lien d'évitement et les libellés sont présents."""
    club = get_club('Simply Lift')
    competition = get_competition('Future Open')
    club['booked'] = {competition['name']: 1}
    club['points_history'] = [{
        'date': '2026-01-02 10:00:00',
        'admin': 'Super Admin',
        'amount': 1,
        'reason': 'Bonus',
        'balance': 14,
        'type': 'admin',
    }]

    response = login(client)
    content = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'class="skip-link"' in content
    assert 'aria-label="Navigation principale"' in content
    assert 'aria-label="Indicateurs du club"' in content
    assert 'aria-label="Filtrer mes réservations"' in content
    assert '<caption class="sr-only">' in content
    assert 'scope="col"' in content
    assert 'aria-label="0 places réservées sur 12' in content

    booking = client.get('/book/Future Open/Simply Lift')
    booking_content = booking.get_data(as_text=True)
    assert booking.status_code == 200
    assert 'role="status"' in booking_content
    assert 'aria-live="polite"' in booking_content


def test_load_audit_log_absent_et_format_liste(tmp_path, monkeypatch):
    """Le journal d'audit accepte un fichier absent ou une liste directe."""
    audit_file = tmp_path / 'audit.json'
    monkeypatch.setattr(server, 'AUDIT_LOG_FILE', str(audit_file))
    assert server.loadAuditLog() == []

    audit_file.write_text(
        json.dumps([{'action': 'test'}]), encoding='utf-8'
    )
    assert server.loadAuditLog() == [{'action': 'test'}]


def test_save_audit_log_ecrit_les_entrees(tmp_path, monkeypatch):
    """La sauvegarde du journal écrit les entrées au format attendu."""
    audit_file = tmp_path / 'audit.json'
    monkeypatch.setattr(server, 'AUDIT_LOG_FILE', str(audit_file))
    monkeypatch.setattr(server, 'saveAuditLog', REAL_SAVE_AUDIT)
    server.audit_entries = [{'action': 'test'}]

    server.saveAuditLog()

    data = json.loads(audit_file.read_text(encoding='utf-8'))
    assert data == {'entries': [{'action': 'test'}]}


def test_get_audit_actor_utilise_la_session_ou_le_fallback():
    """L'acteur vient de la session admin, club, ou du fallback."""
    assert server.getAuditActor() == 'Système'

    with server.app.test_request_context('/'):
        from flask import session
        assert server.getAuditActor() == 'Système'
        session['club_name'] = 'Simply Lift'
        assert server.getAuditActor() == 'Simply Lift'
        session['admin_name'] = 'Super Admin'
        assert server.getAuditActor() == 'Super Admin'


def test_get_days_until_et_flux_liberations_ignorent_les_donnees_invalides():
    """Les dates invalides et entrées inexploitables sont ignorées."""
    past = get_competition('Spring Festival')
    future = get_competition('Future Open')

    assert server.getDaysUntil('pas-une-date') is None
    assert server.getDaysUntil(None) is None
    assert server.getDaysUntil(future['date']) >= 0

    server.audit_entries = [
        {'action': 'book_places', 'details': {}},
        {
            'action': 'cancel_reservation',
            'details': {'competition': 'Inconnue', 'places': 2},
        },
        {
            'action': 'cancel_reservation',
            'details': {'competition': past['name'], 'places': 2},
        },
        {
            'action': 'cancel_reservation',
            'details': {'competition': future['name'], 'places': 'abc'},
        },
        {
            'action': 'cancel_reservation',
            'details': {
                'competition': future['name'],
                'places': 2,
                'club': 'Simply Lift',
            },
        },
        {
            'action': 'cancel_reservation',
            'details': {
                'competition': future['name'],
                'places': 0,
                'club': 'Iron Temple',
            },
        },
        {
            'action': 'cancel_reservation',
            'date': '2026-01-02 10:00:00',
            'details': {
                'competition': future['name'],
                'places': 2,
                'club': 'Iron Temple',
            },
        },
        {
            'action': 'cancel_reservation',
            'details': {
                'competition': future['name'],
                'places': 1,
                'club': 'She Lifts',
            },
        },
    ]

    releases = server.buildRecentReleases(
        exclude_club='Simply Lift', limit=1
    )

    assert len(releases) == 1
    assert releases[0]['club'] == 'Iron Temple'
    assert releases[0]['places'] == 2
