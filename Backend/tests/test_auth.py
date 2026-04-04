import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_signup():
    """Test user signup"""
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "Secure123",
        "role": "patient"
    }
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "user_id" in data

def test_login():
    """Test user login"""
    login_data = {
        "email": "test@example.com",
        "password": "Secure123"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_get_current_user():
    """Test getting current user info"""
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_invalid_login():
    """Test login with invalid credentials"""
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401

def test_duplicate_signup():
    """Test signup with existing email"""
    user_data = {
        "email": "test@example.com",
        "full_name": "Another User",
        "password": "TestPass123",
        "role": "patient"
    }
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 400
