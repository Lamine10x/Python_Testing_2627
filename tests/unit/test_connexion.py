import html


def test_connexion_reussie(client):
    """Test de connexion réussie avec un e-mail valide."""
    response = client.post('/showSummary', data={'email': 'john@simplylift.co'})
    assert response.status_code == 200
    assert "Welcome, john@simplylift.co" in response.get_data(as_text=True)


def test_connexion_email_inconnu(client):
    """Test qu'un e-mail inconnu ne fait pas crasher l'app et affiche une erreur."""
    response = client.post('/showSummary', data={'email': 'inconnu@club.com'})
    assert response.status_code == 401
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Désolé, cette adresse e-mail n'a pas été trouvée." in texte_reponse


def test_connexion_email_vide(client):
    """Test qu'un champ e-mail vide renvoie une erreur."""
    response = client.post('/showSummary', data={'email': ''})
    assert response.status_code == 401
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Désolé, cette adresse e-mail n'a pas été trouvée." in texte_reponse
