"""Basic smoke tests for the Saathi backend."""
import requests

BASE_URL = "http://localhost:8001"

def test_reminders_endpoint_reachable():
    """Reminders endpoint should return a list for a given user."""
    response = requests.get(f"{BASE_URL}/reminders/demo")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
