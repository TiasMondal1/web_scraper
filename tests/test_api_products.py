"""
Test product tracking endpoints
"""
import pytest


def test_track_product(client, auth_headers, test_plans, db):
    """Test adding a product to track"""
    response = client.post(
        "/api/products/track",
        headers=auth_headers,
        json={
            "url": "https://www.amazon.in/test-product/dp/B123456789",
            "target_price": 25000,
            "alert_enabled": True
        }
    )
    
    assert response.status_code in [200, 201]
    # Note: This might fail if actual scraping is attempted
    # In production tests, mock the scraper


def test_get_my_products(client, auth_headers):
    """Test getting user's tracked products"""
    response = client.get("/api/products/my", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_products_unauthorized(client):
    """Test getting products without auth"""
    response = client.get("/api/products/my")
    
    assert response.status_code == 401
