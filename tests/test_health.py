import requests
import pytest


MINIO_URL = "http://localhost:9000/minio/health/live"

def test_minio_container_reachable():
    try:
        response = requests.get(MINIO_URL, timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to cinema_minio. Check Docker networking.")
