"""
Test authentication endpoints
"""
import pytest


def test_register_user(client, test_plans):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client, test_user, test_plans):
    """Test registration with existing email"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user, test_plans):
    """Test successful login"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/api/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


def test_get_current_user_unauthorized(client):
    """Test getting user info without auth"""
    response = client.get("/api/auth/me")
    
    assert response.status_code == 401
