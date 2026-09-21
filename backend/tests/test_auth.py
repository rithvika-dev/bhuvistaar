import uuid

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_user_register_and_login(client):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post("/auth/register", json={
        "name": "Test User",
        "email": unique_email,
        "password": "SecurePassword123!"
    })
    assert reg_resp.status_code == 200, f"Register failed: {reg_resp.text}"
    assert "user_id" in reg_resp.json()

    login_resp = client.post("/auth/login", json={
        "email": unique_email,
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    assert "access_token" in login_resp.json()
    assert login_resp.json()["token_type"] == "bearer"

def test_invalid_login(client):
    login_resp = client.post("/auth/login", json={
        "email": "nonexistent_user_999@example.com",
        "password": "WrongPassword"
    })
    assert login_resp.status_code in (400, 401, 404)
