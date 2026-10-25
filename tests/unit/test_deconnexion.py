import html


def test_logout_redirection(client):
    """Vérifie que la route /logout redirige vers l'accueil (HTTP 302)."""
    response = client.get('/logout')
    assert response.status_code == 302
    loc = response.headers['Location']
    assert loc == '/' or loc.endswith('/')


def test_logout_message_flash(client):
    """Vérifie le message flash de confirmation après déconnexion."""
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    texte = html.unescape(response.get_data(as_text=True))
    assert "Vous avez été déconnecté avec succès." in texte


def test_logout_purge_session(client):
    """Vérifie que la session est entièrement vidée lors de la déconnexion."""
    with client.session_transaction() as sess:
        sess['club_email'] = 'john@simplylift.co'
        sess['logged_in'] = True

    response = client.get('/logout')
    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert 'club_email' not in sess
        assert 'logged_in' not in sess
