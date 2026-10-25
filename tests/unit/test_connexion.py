import html


def test_connexion_reussie(client):
    """Test de connexion réussie avec un e-mail valide."""
    response = client.post(
        '/showSummary', data={'email': 'john@simplylift.co'}
    )
    assert response.status_code == 200
    contenu = response.get_data(as_text=True)
    assert "Simply Lift" in contenu
    assert "john@simplylift.co" in contenu
    assert "Tableau de bord" in contenu


def test_connexion_email_inconnu(client):
    """Test qu'un e-mail inconnu affiche une erreur propre (401)."""
    response = client.post(
        '/showSummary', data={'email': 'inconnu@club.com'}
    )
    assert response.status_code == 401
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Désolé, cette adresse e-mail n'a pas été trouvée." in texte_reponse


def test_connexion_email_vide(client):
    """Test qu'un champ e-mail vide renvoie une erreur."""
    response = client.post('/showSummary', data={'email': ''})
    assert response.status_code == 401
    texte_reponse = html.unescape(response.get_data(as_text=True))
    assert "Désolé, cette adresse e-mail n'a pas été trouvée." in texte_reponse
