# 📚 Price Tracker Pro - Complete API Documentation

**Base URL**: `https://your-domain.com`  
**Version**: 1.0.0  
**Authentication**: Bearer Token (JWT)

## Table of Contents

1. [Authentication](#authentication)
2. [Products](#products)
3. [Subscriptions](#subscriptions)
4. [Payments](#payments)
5. [Dashboard](#dashboard)
6. [Admin](#admin)
7. [Error Codes](#error-codes)
8. [Rate Limits](#rate-limits)

---

## Authentication

### Register User

Create a new user account.

```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "phone": "+919876543210"
}
```

**Response (201):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### Login

Authenticate and get access tokens.

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### Refresh Token

Get a new access token using refresh token.

```http
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### Get Current User

Get authenticated user's information.

```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "email_verified": true,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-01-20T15:45:00Z"
}
```

---

### Logout

Logout user (client discards tokens).

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Products

### Track Product

Add a product to track.

```http
POST /api/products/track
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "url": "https://www.amazon.in/product/dp/B08L5WYFP2",
  "target_price": 25000,
  "alert_enabled": true
}
```

**Response (200):**
```json
{
  "user_product_id": 123,
  "product": {
    "id": 456,
    "name": "Samsung Galaxy S21 FE 5G",
    "platform": "amazon",
    "current_price": 27999,
    "image_url": "https://...",
    "in_stock": true
  },
  "target_price": 25000,
  "alert_enabled": true,
  "added_at": "2024-01-20T16:00:00Z"
}
```

---

### Get My Products

Get all products tracked by the user.

```http
GET /api/products/my
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 50)

**Response (200):**
```json
[
  {
    "id": 123,
    "product": {
      "id": 456,
      "name": "Samsung Galaxy S21 FE 5G",
      "url": "https://...",
      "platform": "amazon",
      "current_price": 27999,
      "image_url": "https://...",
      "in_stock": true,
      "last_scraped_at": "2024-01-20T15:30:00Z"
    },
    "target_price": 25000,
    "alert_enabled": true,
    "email_notification": true,
    "added_at": "2024-01-15T10:00:00Z",
    "last_notified_at": null
  }
]
```

---

### Get Product Details

Get details of a specific tracked product.

```http
GET /api/products/{product_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 123,
  "product": {
    "id": 456,
    "name": "Samsung Galaxy S21 FE 5G",
    "url": "https://...",
    "platform": "amazon",
    "current_price": 27999,
    "brand": "Samsung",
    "category": "Electronics",
    "in_stock": true
  },
  "target_price": 25000,
  "alert_enabled": true
}
```

---

### Update Product Settings

Update tracking settings for a product.

```http
PATCH /api/products/{product_id}
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "target_price": 24000,
  "alert_enabled": false,
  "email_notification": true
}
```

**Response (200):**
```json
{
  "message": "Product settings updated",
  "product_id": 123
}
```

---

### Stop Tracking Product

Remove product from tracking.

```http
DELETE /api/products/{product_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Product removed from tracking",
  "product_id": 123
}
```

---

### Get Price History

Get historical price data for a product.

```http
GET /api/products/{product_id}/history
Authorization: Bearer <token>
```

**Query Parameters:**
- `days` (optional): Number of days of history (default: 30)

**Response (200):**
```json
{
  "product_id": 456,
  "product_name": "Samsung Galaxy S21 FE 5G",
  "data_points": [
    {
      "price": 27999,
      "scraped_at": "2024-01-20T15:30:00Z",
      "in_stock": true,
      "discount_percent": 10
    }
  ],
  "min_price": 25999,
  "max_price": 32999,
  "avg_price": 28500
}
```

---

## Subscriptions

### Get Subscription Plans

Get all available subscription plans (public endpoint).

```http
GET /api/subscriptions/plans
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "free",
    "display_name": "Free",
    "description": "Perfect for trying out",
    "price_monthly": 0,
    "price_yearly": 0,
    "currency": "INR",
    "max_products": 3,
    "max_alerts_per_day": 5,
    "max_price_checks_per_day": 2,
    "email_alerts": true,
    "sms_alerts": false,
    "api_access": false,
    "historical_data_days": 30
  },
  {
    "id": 2,
    "name": "basic",
    "display_name": "Basic",
    "description": "For regular shoppers",
    "price_monthly": 199,
    "price_yearly": 1990,
    "max_products": 25,
    "max_alerts_per_day": 20,
    "max_price_checks_per_day": 6,
    "historical_data_days": 90
  }
]
```

---

### Get Current Subscription

Get user's active subscription.

```http
GET /api/subscriptions/current
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 789,
  "plan": {
    "id": 2,
    "name": "basic",
    "display_name": "Basic",
    "price_monthly": 199
  },
  "status": "active",
  "billing_cycle": "monthly",
  "amount": 199,
  "current_period_start": "2024-01-15T00:00:00Z",
  "current_period_end": "2024-02-15T00:00:00Z"
}
```

---

### Cancel Subscription

Cancel current subscription (remains active until period end).

```http
POST /api/subscriptions/cancel
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Subscription cancelled",
  "active_until": "2024-02-15T00:00:00Z"
}
```

---

### Get Usage Statistics

Get current usage stats against plan limits.

```http
GET /api/subscriptions/usage
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "tracked_products": 5,
  "tracked_products_limit": 25,
  "alerts_sent_today": 3,
  "alerts_limit_per_day": 20,
  "price_checks_today": 2,
  "price_checks_limit_per_day": 6,
  "api_calls_today": 0,
  "api_calls_limit_per_day": 0
}
```

---

## Payments

### Create Payment Order

Create Razorpay order for subscription payment.

```http
POST /api/payments/create-order
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "plan_id": 2,
  "billing_cycle": "monthly"
}
```

**Response (200):**
```json
{
  "order_id": "order_Razorpay123456",
  "amount": 199,
  "currency": "INR",
  "key_id": "rzp_test_123",
  "plan_name": "Basic",
  "user_email": "user@example.com",
  "user_name": "John Doe"
}
```

**Next Steps:**
1. Use this data to initialize Razorpay checkout on frontend
2. User completes payment
3. Call `/verify-payment` with Razorpay response

---

### Verify Payment

Verify payment and activate subscription.

```http
POST /api/payments/verify-payment
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "razorpay_order_id": "order_Razorpay123456",
  "razorpay_payment_id": "pay_Razorpay789012",
  "razorpay_signature": "signature_hash",
  "plan_id": 2
}
```

**Response (200):**
```json
{
  "message": "Payment verified and subscription activated",
  "subscription_id": 789,
  "plan": "Basic",
  "valid_until": "2024-02-15T00:00:00Z"
}
```

---

### Get Invoices

Get user's payment history/invoices.

```http
GET /api/payments/invoices
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "invoices": [
    {
      "id": 101,
      "amount": 199,
      "currency": "INR",
      "status": "completed",
      "payment_method": "upi",
      "date": "2024-01-15T10:30:00Z",
      "invoice_url": null
    }
  ]
}
```

---

## Dashboard

### Get Dashboard Stats

Get overview statistics for user dashboard.

```http
GET /api/dashboard/stats
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "total_products": 8,
  "active_alerts": 2,
  "price_drops_today": 3,
  "savings_this_month": 2500,
  "subscription_plan": "Basic",
  "subscription_expires": "2024-02-15T00:00:00Z"
}
```

---

### Get Recent Alerts

Get recent price drop alerts.

```http
GET /api/dashboard/alerts?limit=10
Authorization: Bearer <token>
```

**Response (200):**
```json
[
  {
    "id": 501,
    "product_id": 456,
    "alert_type": "price_drop",
    "old_price": 27999,
    "new_price": 25999,
    "price_difference": 2000,
    "price_difference_percent": 7.14,
    "status": "sent",
    "viewed": false,
    "created_at": "2024-01-20T10:30:00Z"
  }
]
```

---

### Mark Alert as Viewed

Mark an alert as viewed.

```http
POST /api/dashboard/alerts/{alert_id}/mark-viewed
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Alert marked as viewed"
}
```

---

### Get Monthly Savings

Get savings breakdown by month.

```http
GET /api/dashboard/savings/monthly?months=6
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "monthly_savings": [
    {
      "month": "January 2024",
      "savings": 5000,
      "alerts_count": 12
    }
  ]
}
```

---

### Get Top Deals

Get best price drop deals.

```http
GET /api/dashboard/top-deals?limit=5
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "top_deals": [
    {
      "product_name": "Samsung Galaxy S21 FE 5G",
      "old_price": 32999,
      "new_price": 25999,
      "savings": 7000,
      "discount_percent": 21.21,
      "date": "2024-01-18T10:00:00Z",
      "product_url": "https://..."
    }
  ]
}
```

---

## Admin

**Note:** All admin endpoints require admin privileges.

### Get Admin Dashboard Stats

Get overall platform statistics.

```http
GET /api/admin/dashboard/stats
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "users": {
    "total": 1250,
    "verified": 980,
    "new_this_week": 45
  },
  "subscriptions": {
    "active": 320,
    "mrr": 52800
  },
  "revenue": {
    "this_month": 63600,
    "total": 158000
  },
  "products": {
    "total": 5600,
    "active_tracking": 4200
  },
  "alerts": {
    "today": 156
  }
}
```

---

### List Users

Get paginated list of users.

```http
GET /api/admin/users?skip=0&limit=50&status=active&search=john
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `skip`: Pagination offset
- `limit`: Records per page
- `status`: Filter by status (active, suspended, deleted)
- `search`: Search by email or name

**Response (200):**
```json
{
  "total": 1250,
  "users": [
    {
      "id": 1,
      "email": "john@example.com",
      "full_name": "John Doe",
      "email_verified": true,
      "status": "active",
      "plan": "Basic",
      "products_tracked": 8,
      "created_at": "2024-01-10T00:00:00Z",
      "last_login_at": "2024-01-20T15:30:00Z"
    }
  ],
  "page": 1,
  "pages": 25
}
```

---

### Get User Details

Get detailed user information.

```http
GET /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "john@example.com",
    "full_name": "John Doe",
    "status": "active",
    "login_count": 45
  },
  "subscription": {
    "plan": "Basic",
    "status": "active",
    "billing_cycle": "monthly",
    "amount": 199
  },
  "stats": {
    "products_tracked": 8,
    "total_alerts": 24,
    "total_payments": 3
  },
  "recent_alerts": [],
  "payment_history": []
}
```

---

### Update User Status

Update user status (suspend, activate, delete).

```http
PATCH /api/admin/users/{user_id}/status
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "new_status": "suspended"
}
```

**Response (200):**
```json
{
  "message": "User status updated to suspended",
  "user_id": 1,
  "new_status": "suspended"
}
```

---

## Error Codes

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Common Errors

**Authentication Failed:**
```json
{
  "detail": "Incorrect email or password"
}
```

**Token Expired:**
```json
{
  "detail": "Token has expired"
}
```

**Rate Limit Exceeded:**
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

---

## Rate Limits

### Default Limits

- **Anonymous**: 30 requests/minute
- **Authenticated**: 60 requests/minute
- **Premium**: 120 requests/minute

### Rate Limit Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
```

When rate limit is exceeded:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## Webhooks

### Razorpay Webhook

Endpoint for Razorpay payment webhooks.

```http
POST /api/payments/webhook
X-Razorpay-Signature: <signature>
```

**Events Handled:**
- `payment.captured`
- `payment.failed`
- `subscription.charged`
- `subscription.cancelled`

---

## SDK & Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    "https://api.your-domain.com/api/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Track product
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "https://api.your-domain.com/api/products/track",
    headers=headers,
    json={
        "url": "https://www.amazon.in/product",
        "target_price": 25000
    }
)
```

### JavaScript

```javascript
// Login
const response = await fetch('https://api.your-domain.com/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const {access_token} = await response.json();

// Track product
await fetch('https://api.your-domain.com/api/products/track', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://www.amazon.in/product',
    target_price: 25000
  })
});
```

---

## Interactive Documentation

For interactive API testing, visit:
- **Swagger UI**: https://your-domain.com/docs
- **ReDoc**: https://your-domain.com/redoc

---

## Support

- **Email**: support@your-domain.com
- **Documentation**: https://docs.your-domain.com
- **Status Page**: https://status.your-domain.com

**API Version**: 1.0.0  
**Last Updated**: January 2026
