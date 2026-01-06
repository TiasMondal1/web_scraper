# 🚀 Quick Start: Turn Your Price Tracker into SaaS

## Overview

This guide gets you from current state to a functioning SaaS product in **6-8 weeks**.

---

## Week 1-2: Database & Authentication

### Step 1: Migrate to PostgreSQL

**Why?** SQLite doesn't scale for SaaS. PostgreSQL is production-ready.

```bash
# Install PostgreSQL locally
# macOS:
brew install postgresql
brew services start postgresql

# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
createdb price_tracker_saas

# Install Python driver
pip install psycopg2-binary
```

**Migrate schema:**
```bash
psql price_tracker_saas < saas_database_schema.sql
```

### Step 2: Implement Authentication

**Install dependencies:**
```bash
pip install flask-login flask-bcrypt pyjwt python-jose email-validator
```

**Create `auth.py`:**
```python
from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
from datetime import datetime, timedelta
import jwt
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# Database connection
def get_db():
    return psycopg2.connect(
        dbname="price_tracker_saas",
        user="your_user",
        password="your_password",
        host="localhost"
    )

class User(UserMixin):
    def __init__(self, id, email, full_name):
        self.id = id
        self.email = email
        self.full_name = full_name

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, email, full_name FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    # Validate
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Hash password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Verification token
    verification_token = secrets.token_urlsafe(32)
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Create user
        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, verification_token, verification_sent_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (email, password_hash, full_name, verification_token, datetime.now()))
        
        user_id = cur.fetchone()[0]
        
        # Create free subscription
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_id, billing_cycle, amount, current_period_start, current_period_end)
            SELECT %s, id, 'monthly', 0, %s, %s + INTERVAL '1 year'
            FROM subscription_plans WHERE name = 'free'
        """, (user_id, datetime.now(), datetime.now()))
        
        conn.commit()
        
        # TODO: Send verification email
        # send_verification_email(email, verification_token)
        
        return jsonify({
            'message': 'Registration successful. Please verify your email.',
            'user_id': user_id
        }), 201
        
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, email, password_hash, full_name FROM users WHERE email = %s", (email,))
    user_data = cur.fetchone()
    conn.close()
    
    if not user_data or not bcrypt.check_password_hash(user_data[2], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    user = User(user_data[0], user_data[1], user_data[3])
    login_user(user)
    
    # Update last login
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_login_at = %s, login_count = login_count + 1 WHERE id = %s",
                (datetime.now(), user.id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Login successful',
        'user': {'id': user.id, 'email': user.email, 'name': user.full_name}
    })

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.full_name
    })

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Week 3-4: Payment Integration

### Razorpay Setup

**Sign up:** https://razorpay.com/
**Docs:** https://razorpay.com/docs/

**Install SDK:**
```bash
pip install razorpay
```

**Create `payments.py`:**
```python
import razorpay
from flask import Flask, request, jsonify
from flask_login import login_required, current_user
import hmac
import hashlib

app = Flask(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(
    "YOUR_KEY_ID",  # From Razorpay dashboard
    "YOUR_KEY_SECRET"
))

@app.route('/api/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    data = request.json
    plan_name = data.get('plan')  # 'basic', 'pro'
    
    # Get plan details from database
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, price_monthly FROM subscription_plans WHERE name = %s", (plan_name,))
    plan = cur.fetchone()
    
    if not plan:
        return jsonify({'error': 'Invalid plan'}), 400
    
    plan_id, amount = plan
    
    try:
        # Create Razorpay order
        order = razorpay_client.order.create({
            'amount': int(amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1
        })
        
        return jsonify({
            'order_id': order['id'],
            'amount': amount,
            'key_id': "YOUR_KEY_ID"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    data = request.json
    
    # Verify signature
    generated_signature = hmac.new(
        bytes("YOUR_KEY_SECRET", 'utf-8'),
        bytes(f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}", 'utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if generated_signature != data['razorpay_signature']:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Payment verified, activate subscription
    conn = get_db()
    cur = conn.cursor()
    
    # Deactivate old subscriptions
    cur.execute("UPDATE subscriptions SET status = 'cancelled' WHERE user_id = %s AND status = 'active'",
                (current_user.id,))
    
    # Create new subscription
    cur.execute("""
        INSERT INTO subscriptions (user_id, plan_id, billing_cycle, amount, status, gateway_subscription_id, current_period_start, current_period_end)
        VALUES (%s, %s, 'monthly', %s, 'active', %s, NOW(), NOW() + INTERVAL '1 month')
    """, (current_user.id, data['plan_id'], data['amount'], data['razorpay_payment_id']))
    
    # Record transaction
    cur.execute("""
        INSERT INTO payment_transactions (user_id, amount, currency, total_amount, payment_gateway, gateway_payment_id, status, payment_method)
        VALUES (%s, %s, 'INR', %s, 'razorpay', %s, 'completed', 'online')
    """, (current_user.id, data['amount'], data['amount'], data['razorpay_payment_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Subscription activated'})

# Frontend payment button example (HTML + JavaScript)
"""
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
<button onclick="payWithRazorpay()">Subscribe Now</button>

<script>
async function payWithRazorpay() {
    // Create order
    const response = await fetch('/api/create-subscription', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ plan: 'basic' })
    });
    const order = await response.json();
    
    // Open Razorpay checkout
    const options = {
        key: order.key_id,
        amount: order.amount * 100,
        currency: 'INR',
        order_id: order.order_id,
        name: 'Price Tracker Pro',
        description: 'Basic Plan Subscription',
        handler: async function (response) {
            // Verify payment
            await fetch('/api/verify-payment', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(response)
            });
            alert('Payment successful!');
        }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
}
</script>
"""
```

---

## Week 5: User Dashboard & Product Management

**Create user-specific product tracking:**

```python
@app.route('/api/products/track', methods=['POST'])
@login_required
def track_product():
    data = request.json
    url = data.get('url')
    
    # Check user's plan limits
    conn = get_db()
    cur = conn.cursor()
    
    # Get current tracked count
    cur.execute("SELECT COUNT(*) FROM user_products WHERE user_id = %s AND is_active = TRUE",
                (current_user.id,))
    current_count = cur.fetchone()[0]
    
    # Get plan limit
    cur.execute("""
        SELECT sp.max_products
        FROM subscriptions s
        JOIN subscription_plans sp ON s.plan_id = sp.id
        WHERE s.user_id = %s AND s.status = 'active'
    """, (current_user.id,))
    
    limit = cur.fetchone()
    if not limit or current_count >= limit[0]:
        return jsonify({'error': 'Product limit reached. Upgrade your plan.'}), 403
    
    # Scrape product info
    product_data = scrape_product_info(url)  # Your existing scraper
    
    # Add to products table if not exists
    cur.execute("""
        INSERT INTO products (name, url, platform, current_price, image_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
    """, (product_data['name'], url, product_data['platform'], 
          product_data['price'], product_data['image']))
    
    product_id = cur.fetchone()[0]
    
    # Link to user
    cur.execute("""
        INSERT INTO user_products (user_id, product_id, target_price)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, product_id) DO NOTHING
    """, (current_user.id, product_id, data.get('target_price')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product tracked successfully', 'product_id': product_id})

@app.route('/api/products/my', methods=['GET'])
@login_required
def get_my_products():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.id, p.name, p.url, p.current_price, p.image_url, 
               up.target_price, up.alert_enabled, up.added_at
        FROM user_products up
        JOIN products p ON up.product_id = p.id
        WHERE up.user_id = %s AND up.is_active = TRUE
        ORDER BY up.added_at DESC
    """, (current_user.id,))
    
    products = []
    for row in cur.fetchall():
        products.append({
            'id': row[0],
            'name': row[1],
            'url': row[2],
            'current_price': float(row[3]) if row[3] else None,
            'image_url': row[4],
            'target_price': float(row[5]) if row[5] else None,
            'alert_enabled': row[6],
            'added_at': row[7].isoformat()
        })
    
    conn.close()
    return jsonify({'products': products})
```

---

## Week 6: Email Notifications

**Install:**
```bash
pip install sendgrid
# OR
pip install boto3  # For AWS SES
```

**Email service (`emails.py`):**
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = 'your-key'

def send_price_alert(user_email, product_name, old_price, new_price, product_url):
    message = Mail(
        from_email='alerts@yourpricetracker.com',
        to_emails=user_email,
        subject=f'Price Drop Alert: {product_name}',
        html_content=f"""
        <h2>Great News! Price Dropped</h2>
        <p>The product you're tracking has dropped in price:</p>
        <h3>{product_name}</h3>
        <p>Old Price: ₹{old_price}</p>
        <p>New Price: ₹{new_price} (Save ₹{old_price - new_price}!)</p>
        <a href="{product_url}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            View Product
        </a>
        """
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
```

---

## Week 7-8: Deploy to Production

### Option A: Railway (Easiest)

**1. Install Railway CLI:**
```bash
npm i -g @railway/cli
```

**2. Login & Initialize:**
```bash
railway login
railway init
```

**3. Add PostgreSQL:**
```bash
railway add --database postgres
```

**4. Deploy:**
```bash
railway up
```

**Cost:** ~$20-50/month

### Option B: DigitalOcean App Platform

**1. Create `app.yaml`:**
```yaml
name: price-tracker-pro
services:
  - name: web
    github:
      repo: yourusername/price-tracker
      branch: main
    build_command: pip install -r requirements.txt
    run_command: gunicorn app:app
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
    http_port: 8080

databases:
  - name: db
    engine: PG
    production: true
```

**2. Deploy via UI:** https://cloud.digitalocean.com/apps

**Cost:** ~$25-100/month

### Environment Variables

Create `.env` file:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
SENDGRID_API_KEY=SG.xxx
FLASK_ENV=production
```

---

## Week 8: Launch Prep

### 1. Create Landing Page

**Simple structure:**
- Hero: "Never Miss a Price Drop Again"
- Features: Product tracking, Price alerts, Historical charts
- Pricing table (Free, Basic, Pro)
- CTA: "Start Tracking Free"
- Social proof: "Join 1000+ smart shoppers"

**Tools:**
- Build with Tailwind CSS
- Use Stripe pricing table widget
- Add testimonials (collect from beta users)

### 2. Analytics Setup

```bash
pip install mixpanel google-analytics
```

Track events:
- User registration
- Product added
- Subscription purchased
- Alert sent/clicked

### 3. Product Hunt Submission

**Prepare:**
- 2-min demo video
- Screenshots (5-6 high quality)
- Tagline: "Track prices, get alerts, save money on Flipkart & Amazon India"
- First comment: Detailed product description
- Maker's comment: Your story

**Schedule:** Tuesday-Thursday, 12:01 AM PT

---

## Pricing Recommendation

| Plan | Price | Products | Target Market |
|------|-------|----------|---------------|
| Free | ₹0 | 3 | Trial users |
| Basic | ₹199/mo | 25 | Regular shoppers |
| Pro | ₹499/mo | 100 | Power users |
| Enterprise | Custom | Unlimited | Businesses |

**Annual:** 20% off (₹1,990 and ₹4,990/year)

---

## Launch Day Checklist

- [ ] Database backed up
- [ ] SSL certificate installed
- [ ] Error monitoring active (Sentry)
- [ ] Payment flow tested end-to-end
- [ ] Email delivery tested
- [ ] Load testing done (handle 100 concurrent users)
- [ ] Social media posts scheduled
- [ ] Product Hunt submission ready
- [ ] Support email set up
- [ ] Terms & privacy policy live
- [ ] Blog post written
- [ ] Demo video uploaded to YouTube
- [ ] Press kit ready (screenshots, logo)

---

## Post-Launch (Month 1)

### Week 1: Bugs & Feedback
- Fix critical bugs within 24h
- Respond to all user feedback
- Monitor server performance

### Week 2: Optimize Conversion
- A/B test pricing page
- Improve onboarding flow
- Add product tour

### Week 3: Content Marketing
- Publish blog posts (2-3/week)
- Share on social media
- Engage in communities

### Week 4: Feature Iteration
- Implement top requested features
- Improve UI/UX based on feedback
- Add integrations (Telegram, WhatsApp)

---

## Success Metrics (First 90 Days)

**Conservative Goals:**
- Day 30: 50 registered users, 5 paying ($1,000 MRR)
- Day 60: 200 users, 20 paying ($4,000 MRR)
- Day 90: 500 users, 50 paying ($10,000 MRR)

**Optimistic Goals:**
- Day 30: 200 users, 20 paying ($4,000 MRR)
- Day 60: 800 users, 80 paying ($16,000 MRR)
- Day 90: 2000 users, 200 paying ($40,000 MRR)

---

## Need Help?

**Technical Issues:**
- Stack Overflow
- r/flask, r/python subreddit
- IndieHackers community

**Business/Marketing:**
- IndieHackers.com
- r/SaaS
- r/startups
- Twitter #buildinpublic

**Hire Freelancers:**
- Upwork (developers, designers)
- Fiverr (logo, marketing materials)
- Toptal (senior developers)

---

## Budget Breakdown (First 3 Months)

| Item | Cost (₹) |
|------|----------|
| Domain (.com) | 800/year |
| Hosting (Railway/DO) | 2,000/mo x 3 = 6,000 |
| SendGrid (email) | Free up to 100/day |
| Razorpay | 2% per transaction |
| Design/Logo | 5,000 one-time |
| Marketing | 10,000/mo x 3 = 30,000 |
| SSL | Free (Let's Encrypt) |
| Monitoring (Sentry) | Free tier |
| **Total** | **~₹45,000** |

---

## Let's Go! 🚀

You have everything you need. The hardest part is starting. Set a launch date **8 weeks from today** and work backwards.

Remember: **Done is better than perfect.** Launch, learn, iterate.

Good luck! 💪



