# 🧪 API Testing Guide - Quick Start

## 🚀 Start the Server

```bash
cd /Users/tiasmondal166/card_scraper
python -m uvicorn app.main:app --reload
```

**Open in browser:** http://localhost:8000/docs

---

## 📝 Test Flow (Copy & Paste)

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

**Save the `access_token` from response!**

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 3. Get Current User Info

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. View Subscription Plans

```bash
curl -X GET "http://localhost:8000/api/subscriptions/plans"
```

### 5. Get Current Subscription

```bash
curl -X GET "http://localhost:8000/api/subscriptions/current" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Track a Product

```bash
curl -X POST "http://localhost:8000/api/products/track" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.amazon.in/dp/B08WRF18SC",
    "target_price": 25000,
    "alert_enabled": true
  }'
```

### 7. Get My Products

```bash
curl -X GET "http://localhost:8000/api/products/my" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Dashboard Stats

```bash
curl -X GET "http://localhost:8000/api/dashboard/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 9. Get Usage Stats

```bash
curl -X GET "http://localhost:8000/api/subscriptions/usage" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🌐 Interactive Testing (Recommended!)

**Much Easier:** Visit http://localhost:8000/docs

1. Click **"Authorize"** button (top right)
2. Enter: `Bearer YOUR_ACCESS_TOKEN` (replace with your token)
3. Click **"Authorize"**
4. Now test all endpoints by clicking "Try it out"!

---

## ✅ What to Test

### Authentication
- [x] Register new user
- [x] Login with credentials
- [x] Get current user info
- [x] Refresh token

### Products
- [x] Track a product
- [x] List my products
- [x] View price history
- [x] Update product settings
- [x] Stop tracking

### Subscriptions
- [x] View available plans
- [x] Check current subscription
- [x] View usage stats
- [x] Cancel subscription

### Dashboard
- [x] Dashboard statistics
- [x] Recent alerts
- [x] Monthly savings
- [x] Top deals

---

## 🎯 All Available Endpoints

```
Health & Info:
GET    /health                              - Health check

Authentication:
POST   /api/auth/register                  - Register
POST   /api/auth/login                     - Login
POST   /api/auth/refresh                   - Refresh token
GET    /api/auth/me                        - Current user
POST   /api/auth/logout                    - Logout
POST   /api/auth/verify-email/{token}      - Verify email

Products:
POST   /api/products/track                 - Track product
GET    /api/products/my                    - My products
GET    /api/products/{id}                  - Product details
PATCH  /api/products/{id}                  - Update settings
DELETE /api/products/{id}                  - Stop tracking
GET    /api/products/{id}/history          - Price history

Subscriptions:
GET    /api/subscriptions/plans            - Available plans
GET    /api/subscriptions/current          - Current subscription
POST   /api/subscriptions/cancel           - Cancel subscription
GET    /api/subscriptions/usage            - Usage statistics

Dashboard:
GET    /api/dashboard/stats                - Dashboard stats
GET    /api/dashboard/alerts               - Recent alerts
POST   /api/dashboard/alerts/{id}/mark-viewed  - Mark alert viewed
GET    /api/dashboard/savings/monthly      - Monthly savings
GET    /api/dashboard/top-deals            - Top deals
```

---

## 🔍 Check Logs

Terminal shows:
- ✅ All requests
- ✅ Database queries (if DEBUG=True)
- ❌ Errors and stack traces

---

## 🐛 Troubleshooting

### "401 Unauthorized"
→ Token expired or invalid. Login again to get new token.

### "403 Forbidden: Product limit reached"
→ You're on Free plan (3 products max). Upgrade to track more.

### "Failed to scrape product"
→ Product URL may be invalid or site structure changed.

### "No active subscription found"
→ Database not initialized. Restart server to auto-create free subscription.

---

## 💡 Pro Tips

1. **Use the interactive docs** at /docs - Much easier than curl!
2. **Save your token** - You'll need it for every authenticated request
3. **Check the terminal** - Logs show what's happening
4. **Try invalid data** - See how validation works
5. **Test limits** - Try adding 4 products on free plan

---

## 🎉 You're Ready!

Your SaaS backend is fully functional. Start testing!

**Next:** Add Razorpay payments and deploy to production 🚀

