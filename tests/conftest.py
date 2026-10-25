import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

import server  # noqa: E402
from server import app  # noqa: E402


@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Réinitialisation propre des données avant chaque test
    server.clubs = server.loadClubs()
    server.competitions = server.loadCompetitions()
    with app.test_client() as client:
        yield client
