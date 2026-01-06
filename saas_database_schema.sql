-- SaaS Multi-Tenancy Database Schema
-- For PostgreSQL (migrate from SQLite)

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    country_code VARCHAR(5) DEFAULT 'IN',
    
    -- Email verification
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_sent_at TIMESTAMP,
    
    -- Password reset
    reset_token VARCHAR(255),
    reset_token_expires_at TIMESTAMP,
    
    -- OAuth
    oauth_provider VARCHAR(50), -- google, twitter, etc.
    oauth_id VARCHAR(255),
    
    -- Account status
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, deleted
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_verification_token ON users(verification_token);
CREATE INDEX idx_users_reset_token ON users(reset_token);

-- ============================================
-- SUBSCRIPTIONS & BILLING
-- ============================================

CREATE TABLE subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- free, basic, pro, enterprise
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Pricing
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    price_yearly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Limits
    max_products INTEGER NOT NULL,
    max_alerts_per_day INTEGER NOT NULL,
    max_price_checks_per_day INTEGER NOT NULL,
    max_api_calls_per_day INTEGER NOT NULL DEFAULT 0,
    
    -- Features
    email_alerts BOOLEAN DEFAULT TRUE,
    sms_alerts BOOLEAN DEFAULT FALSE,
    whatsapp_alerts BOOLEAN DEFAULT FALSE,
    telegram_alerts BOOLEAN DEFAULT FALSE,
    api_access BOOLEAN DEFAULT FALSE,
    priority_support BOOLEAN DEFAULT FALSE,
    data_export BOOLEAN DEFAULT FALSE,
    historical_data_days INTEGER DEFAULT 30,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default plans
INSERT INTO subscription_plans (name, display_name, price_monthly, price_yearly, max_products, max_alerts_per_day, max_price_checks_per_day, historical_data_days) VALUES
('free', 'Free', 0, 0, 3, 5, 2, 30),
('basic', 'Basic', 199, 1990, 25, 20, 6, 90),
('pro', 'Pro', 499, 4990, 100, 100, 24, 365),
('enterprise', 'Enterprise', 0, 0, 999999, 999999, 999999, 999999);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),
    
    -- Billing details
    billing_cycle VARCHAR(20) NOT NULL, -- monthly, yearly
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Payment gateway
    payment_gateway VARCHAR(50), -- razorpay, stripe, paypal
    gateway_subscription_id VARCHAR(255),
    gateway_customer_id VARCHAR(255),
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, cancelled, expired, past_due
    
    -- Dates
    trial_ends_at TIMESTAMP,
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP,
    
    -- Metadata
    cancellation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_current_period_end ON subscriptions(current_period_end);

CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,
    
    -- Gateway
    payment_gateway VARCHAR(50) NOT NULL,
    gateway_transaction_id VARCHAR(255),
    gateway_payment_id VARCHAR(255),
    
    -- Status
    status VARCHAR(20) NOT NULL, -- pending, completed, failed, refunded
    payment_method VARCHAR(50), -- card, upi, wallet, netbanking
    
    -- Invoice
    invoice_number VARCHAR(50),
    invoice_url TEXT,
    
    -- Metadata
    metadata JSONB,
    failure_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX idx_transactions_subscription_id ON payment_transactions(subscription_id);
CREATE INDEX idx_transactions_status ON payment_transactions(status);

-- ============================================
-- PRODUCTS & TRACKING
-- ============================================

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    
    -- Product details
    image_url TEXT,
    brand VARCHAR(255),
    category VARCHAR(100),
    asin VARCHAR(50), -- Amazon ASIN
    product_id VARCHAR(255), -- Flipkart/other ID
    
    -- Platform
    platform VARCHAR(50) NOT NULL, -- amazon, flipkart
    
    -- Current price
    current_price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'INR',
    in_stock BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    last_scraped_at TIMESTAMP,
    scrape_count INTEGER DEFAULT 0,
    scrape_success_count INTEGER DEFAULT 0,
    scrape_fail_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_platform ON products(platform);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_last_scraped ON products(last_scraped_at);

-- User's tracked products
CREATE TABLE user_products (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Alert settings
    alert_enabled BOOLEAN DEFAULT TRUE,
    target_price DECIMAL(10, 2),
    alert_threshold_percent DECIMAL(5, 2), -- Alert if price drops by X%
    
    -- Notification preferences
    email_notification BOOLEAN DEFAULT TRUE,
    sms_notification BOOLEAN DEFAULT FALSE,
    whatsapp_notification BOOLEAN DEFAULT FALSE,
    telegram_notification BOOLEAN DEFAULT FALSE,
    
    -- User notes
    nickname VARCHAR(255),
    notes TEXT,
    priority INTEGER DEFAULT 0, -- Higher = more important
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_notified_at TIMESTAMP,
    notification_count INTEGER DEFAULT 0,
    
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_user_products_user_id ON user_products(user_id);
CREATE INDEX idx_user_products_product_id ON user_products(product_id);
CREATE INDEX idx_user_products_alert_enabled ON user_products(alert_enabled);

-- ============================================
-- PRICE HISTORY
-- ============================================

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Price data
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    in_stock BOOLEAN DEFAULT TRUE,
    
    -- Additional data
    discount_percent DECIMAL(5, 2),
    original_price DECIMAL(10, 2),
    coupon_available BOOLEAN DEFAULT FALSE,
    
    -- Timestamp
    scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_only DATE NOT NULL,
    time_only TIME NOT NULL
);

-- Partition by date for better performance (PostgreSQL 10+)
-- CREATE TABLE price_history_2026_01 PARTITION OF price_history
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_price_history_product_id ON price_history(product_id);
CREATE INDEX idx_price_history_scraped_at ON price_history(scraped_at);
CREATE INDEX idx_price_history_date_only ON price_history(date_only);

-- ============================================
-- ALERTS & NOTIFICATIONS
-- ============================================

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_product_id INTEGER NOT NULL REFERENCES user_products(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Alert type
    alert_type VARCHAR(50) NOT NULL, -- price_drop, target_met, back_in_stock
    
    -- Price data
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2),
    price_difference DECIMAL(10, 2),
    price_difference_percent DECIMAL(5, 2),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed
    sent_at TIMESTAMP,
    
    -- Notification channels
    email_sent BOOLEAN DEFAULT FALSE,
    sms_sent BOOLEAN DEFAULT FALSE,
    whatsapp_sent BOOLEAN DEFAULT FALSE,
    telegram_sent BOOLEAN DEFAULT FALSE,
    
    -- User interaction
    viewed BOOLEAN DEFAULT FALSE,
    viewed_at TIMESTAMP,
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);

-- ============================================
-- USAGE TRACKING & LIMITS
-- ============================================

CREATE TABLE usage_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Counters
    tracked_products_count INTEGER DEFAULT 0,
    alerts_sent_count INTEGER DEFAULT 0,
    price_checks_count INTEGER DEFAULT 0,
    api_calls_count INTEGER DEFAULT 0,
    
    -- Reset tracking
    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, date)
);

CREATE INDEX idx_usage_stats_user_date ON usage_stats(user_id, date);

-- ============================================
-- API ACCESS
-- ============================================

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL, -- First few chars for display
    
    name VARCHAR(100), -- User-given name
    scopes TEXT[], -- ['read:products', 'write:alerts']
    
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- ============================================
-- AFFILIATE TRACKING
-- ============================================

CREATE TABLE affiliate_clicks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    
    -- Affiliate data
    affiliate_link TEXT NOT NULL,
    platform VARCHAR(50), -- amazon, flipkart
    
    -- User data
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    
    -- Conversion tracking
    converted BOOLEAN DEFAULT FALSE,
    conversion_amount DECIMAL(10, 2),
    commission_amount DECIMAL(10, 2),
    converted_at TIMESTAMP,
    
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_affiliate_clicks_user_id ON affiliate_clicks(user_id);
CREATE INDEX idx_affiliate_clicks_product_id ON affiliate_clicks(product_id);
CREATE INDEX idx_affiliate_clicks_clicked_at ON affiliate_clicks(clicked_at);

-- ============================================
-- AUDIT LOG
-- ============================================

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    action VARCHAR(100) NOT NULL, -- login, logout, create_product, delete_product, etc.
    entity_type VARCHAR(50), -- product, subscription, user, etc.
    entity_id INTEGER,
    
    old_values JSONB,
    new_values JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_products_updated_at BEFORE UPDATE ON user_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR ANALYTICS
-- ============================================

-- Active subscriptions summary
CREATE VIEW active_subscriptions_summary AS
SELECT 
    sp.name as plan_name,
    COUNT(s.id) as subscriber_count,
    SUM(s.amount) as total_revenue,
    AVG(s.amount) as average_revenue
FROM subscriptions s
JOIN subscription_plans sp ON s.plan_id = sp.id
WHERE s.status = 'active'
GROUP BY sp.name;

-- User activity summary
CREATE VIEW user_activity_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT up.id) as tracked_products,
    COUNT(DISTINCT a.id) as alerts_received,
    u.last_login_at,
    s.status as subscription_status,
    sp.name as plan_name
FROM users u
LEFT JOIN user_products up ON u.id = up.user_id
LEFT JOIN alerts a ON u.id = a.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
GROUP BY u.id, u.email, u.last_login_at, s.status, sp.name;

-- Daily price changes
CREATE VIEW daily_price_changes AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.platform,
    ph.date_only as date,
    MIN(ph.price) as min_price,
    MAX(ph.price) as max_price,
    AVG(ph.price) as avg_price,
    COUNT(*) as data_points
FROM products p
JOIN price_history ph ON p.id = ph.product_id
GROUP BY p.id, p.name, p.platform, ph.date_only
ORDER BY ph.date_only DESC;

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Create a test user
-- INSERT INTO users (email, password_hash, full_name, email_verified) VALUES
-- ('test@example.com', 'hashed_password_here', 'Test User', TRUE);

-- ============================================
-- MIGRATION FROM SQLITE
-- ============================================

-- Run this after creating the schema:
-- python migrate_excel_to_db.py  (for migrating your existing data)



