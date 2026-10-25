import html


def test_book_club_inconnu(client):
    """Vérifie qu'un club inconnu renvoie une erreur 404 propre."""
    response = client.get('/book/Future Open/ClubInexistant')

    assert response.status_code == 404
    texte = html.unescape(response.get_data(as_text=True))
    assert "Club introuvable." in texte


def test_book_competition_inconnue(client):
    """Vérifie qu'une compétition inconnue renvoie une erreur 404 propre."""
    response = client.get('/book/CompetitionInexistante/Simply Lift')

    assert response.status_code == 404
    texte = html.unescape(response.get_data(as_text=True))
    assert "Compétition introuvable." in texte


def test_purchase_club_inconnu(client):
    """Vérifie qu'un club inconnu dans le formulaire renvoie une 404."""
    response = client.post('/purchasePlaces', data={
        'club': 'ClubInexistant',
        'competition': 'Future Open',
        'places': '1'
    })

    assert response.status_code == 404
    texte = html.unescape(response.get_data(as_text=True))
    assert "Club introuvable." in texte


def test_purchase_competition_inconnue(client):
    """Vérifie qu'une compétition inconnue dans le formulaire renvoie 404."""
    response = client.post('/purchasePlaces', data={
        'club': 'Simply Lift',
        'competition': 'CompetitionInexistante',
        'places': '1'
    })

    assert response.status_code == 404
    texte = html.unescape(response.get_data(as_text=True))
    assert "Compétition introuvable." in texte


def test_purchase_champs_manquants(client):
    """Vérifie qu'une requête sans champs renvoie une erreur 404 propre."""
    response = client.post('/purchasePlaces', data={})

    assert response.status_code == 404
    texte = html.unescape(response.get_data(as_text=True))
    assert "Club introuvable." in texte
