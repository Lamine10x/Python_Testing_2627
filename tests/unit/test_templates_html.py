def test_index_template_attributes(client):
    """Vérifie la conformité et l'accessibilité du formulaire de la page d'accueil."""
    response = client.get('/')
    assert response.status_code == 200
    html_content = response.get_data(as_text=True)

    # Vérification des attributs d'accessibilité et de validation
    assert 'id="email"' in html_content
    assert 'required' in html_content
    assert 'id=""' not in html_content
    assert 'action="/showSummary"' in html_content


def test_booking_template_attributes(client):
    """Vérifie la conformité, l'accessibilité et les contraintes HTML5 de booking.html."""
    response = client.get('/book/Future Open/Simply Lift')
    assert response.status_code == 200
    html_content = response.get_data(as_text=True)

    # Vérification des contraintes HTML5 et de l'accessibilité
    assert 'id="places"' in html_content
    assert 'min="1"' in html_content
    assert 'max="12"' in html_content
    assert 'required' in html_content
    assert 'id=""' not in html_content
    assert 'action="/purchasePlaces"' in html_content


def test_welcome_template_clean_html(client):
    """Vérifie l'absence de balise invalide </br> dans welcome.html."""
    response = client.post('/showSummary', data={'email': 'john@simplylift.co'})
    assert response.status_code == 200
    html_content = response.get_data(as_text=True)

    assert '</br>' not in html_content
    assert '<br />' in html_content
