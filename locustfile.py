"""Scenario de test de performance GUDLFT.

Lancement avec 6 utilisateurs virtuels :

    locust -f locustfile.py --headless -u 6 -r 1 -t 30s \
        --host http://127.0.0.1:5000

Interface web Locust (http://localhost:8089) :

    locust -f locustfile.py --host http://127.0.0.1:5000
"""

from locust import HttpUser, between, task


class GudlftUser(HttpUser):
    """Utilisateur simule parcourant le portail GUDLFT."""

    wait_time = between(1, 3)

    def on_start(self):
        """Charge la page d'accueil et ouvre une session club."""
        self.client.get('/', name='Accueil')
        self.client.post(
            '/showSummary',
            data={'email': 'john@simplylift.co'},
            name='Connexion club',
        )

    @task(3)
    def display_board(self):
        """Consulte le classement public des clubs."""
        self.client.get('/displayBoard', name='Classement public')

    @task(1)
    def points_alias(self):
        """Consulte l'alias /points du classement."""
        self.client.get('/points', name='Alias /points')

    @task(2)
    def show_summary(self):
        """Se connecte au tableau de bord d'un club."""
        self.client.post(
            '/showSummary',
            data={'email': 'john@simplylift.co'},
            name='Tableau de bord club',
        )

    @task(2)
    def open_booking(self):
        """Ouvre le formulaire de reservation d'une competition future."""
        self.client.get(
            '/book/Future%20Open/Simply%20Lift',
            name='Formulaire de reservation',
        )

    @task(1)
    def admin_login_page(self):
        """Consulte la page de connexion de l'administration."""
        self.client.get('/admin/login', name='Connexion admin')

    @task(1)
    def public_admin_guard(self):
        """Verifie la redirection de la route admin protegee."""
        self.client.get(
            '/admin',
            name='Redirection admin',
            allow_redirects=False,
        )
