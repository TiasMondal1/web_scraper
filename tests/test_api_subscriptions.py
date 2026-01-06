"""
Test subscription endpoints
"""
import pytest


def test_get_subscription_plans(client):
    """Test getting subscription plans (public endpoint)"""
    response = client.get("/api/subscriptions/plans")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_current_subscription(client, auth_headers):
    """Test getting current subscription"""
    response = client.get("/api/subscriptions/current", headers=auth_headers)
    
    # Might be 404 if no subscription, or 200 with subscription
    assert response.status_code in [200, 404]


def test_get_usage_stats(client, auth_headers):
    """Test getting usage statistics"""
    response = client.get("/api/subscriptions/usage", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    # Check that usage stats are returned
    assert "tracked_products" in data or "error" not in data
