from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_health():
    """
    Test the /health endpoint to ensure it returns a 200 OK status and the correct message.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_cors_headers():
    """
    Test that CORS headers are present on responses, allowing cross-origin requests.
    We check this by sending an OPTIONS request, which triggers a preflight check.
    """
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    response = client.options("/api/v1/analysis/analyze_flowchart", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

def test_root_endpoint():
    """
    Test the root endpoint to ensure it returns the welcome message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Flowchart Learning & Analysis Tool API"} 