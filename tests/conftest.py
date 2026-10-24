import os
import sys
import pytest

# Ajout du dossier racine au sys.path pour importer server.py sans encombre
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import server
from server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Réinitialisation propre des données avant chaque test pour garantir l'isolation
    server.clubs = server.loadClubs()
    server.competitions = server.loadCompetitions()
    with app.test_client() as client:
        yield client
