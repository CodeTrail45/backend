import pytest
from fastapi.testclient import TestClient
from app import app
from database.security import auth
from database import models

client = TestClient(app)

def test_register_user(client, db_session):
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpass", "email": "test@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "is_active" in data

def test_register_duplicate_user(client, db_session):
    # First registration
    client.post(
        "/register",
        json={"username": "testuser2", "password": "testpass", "email": "test2@example.com"}
    )
    
    # Try to register same user again
    response = client.post(
        "/register",
        json={"username": "testuser2", "password": "testpass", "email": "test2@example.com"}
    )
    assert response.status_code == 400

def test_authenticate_user(client, db_session):
    # Register a user
    client.post(
        "/register",
        json={"username": "testuser3", "password": "testpass", "email": "test3@example.com"}
    )
    
    # Try to authenticate
    response = client.post(
        "/token",
        data={"username": "testuser3", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_authenticate_wrong_password(client, db_session):
    # Register a user
    client.post(
        "/register",
        json={"username": "testuser4", "password": "testpass", "email": "test4@example.com"}
    )
    
    # Try to authenticate with wrong password
    response = client.post(
        "/token",
        data={"username": "testuser4", "password": "wrongpass"}
    )
    assert response.status_code == 401 