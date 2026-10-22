import os
import sys
import pytest

# Ajout du dossier racine au sys.path pour importer server.py sans encombre
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
