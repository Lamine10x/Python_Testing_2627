import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

import server  # noqa: E402
from server import app  # noqa: E402


@pytest.fixture(autouse=True)
def prevent_disk_writes(monkeypatch):
    """Evite d'ecrire dans les fichiers JSON pendant les tests."""
    monkeypatch.setattr(server, 'saveClubs', lambda: None)
    monkeypatch.setattr(server, 'saveCompetitions', lambda: None)
    monkeypatch.setattr(server, 'saveAuditLog', lambda: None)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Réinitialisation propre des données avant chaque test
    server.clubs = server.loadClubs()
    server.competitions = server.loadCompetitions()
    server.audit_entries = []
    with app.test_client() as client:
        yield client
