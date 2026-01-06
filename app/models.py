"""
SQLAlchemy Models for SaaS Application
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    country_code = Column(String(5), default="IN")
    
    # Email verification
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), index=True)
    verification_sent_at = Column(DateTime)
    
    # Password reset
    reset_token = Column(String(255), index=True)
    reset_token_expires_at = Column(DateTime)
    
    # OAuth
    oauth_provider = Column(String(50))
    oauth_id = Column(String(255))
    
    # Account status
    status = Column(String(20), default="active")  # active, suspended, deleted
    last_login_at = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    user_products = relationship("UserProduct", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pricing
    price_monthly = Column(Numeric(10, 2), nullable=False, default=0)
    price_yearly = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), default="INR")
    
    # Limits
    max_products = Column(Integer, nullable=False)
    max_alerts_per_day = Column(Integer, nullable=False)
    max_price_checks_per_day = Column(Integer, nullable=False)
    max_api_calls_per_day = Column(Integer, default=0)
    
    # Features
    email_alerts = Column(Boolean, default=True)
    sms_alerts = Column(Boolean, default=False)
    whatsapp_alerts = Column(Boolean, default=False)
    telegram_alerts = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    data_export = Column(Boolean, default=False)
    historical_data_days = Column(Integer, default=30)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    # Billing
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    
    # Payment gateway
    payment_gateway = Column(String(50))
    gateway_subscription_id = Column(String(255))
    gateway_customer_id = Column(String(255))
    
    # Status
    status = Column(String(20), default="active", index=True)  # active, cancelled, expired, past_due
    
    # Dates
    trial_ends_at = Column(DateTime)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False, index=True)
    cancelled_at = Column(DateTime)
    
    # Metadata
    cancellation_reason = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    url = Column(Text, nullable=False, unique=True)
    
    # Product details
    image_url = Column(Text)
    brand = Column(String(255))
    category = Column(String(100), index=True)
    asin = Column(String(50))
    product_id = Column(String(255))
    
    # Platform
    platform = Column(String(50), nullable=False, index=True)  # amazon, flipkart
    
    # Current price
    current_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="INR")
    in_stock = Column(Boolean, default=True)
    
    # Metadata
    last_scraped_at = Column(DateTime, index=True)
    scrape_count = Column(Integer, default=0)
    scrape_success_count = Column(Integer, default=0)
    scrape_fail_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user_products = relationship("UserProduct", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")


class UserProduct(Base):
    __tablename__ = "user_products"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert settings
    alert_enabled = Column(Boolean, default=True, index=True)
    target_price = Column(Numeric(10, 2))
    alert_threshold_percent = Column(Numeric(5, 2))
    
    # Notification preferences
    email_notification = Column(Boolean, default=True)
    sms_notification = Column(Boolean, default=False)
    whatsapp_notification = Column(Boolean, default=False)
    telegram_notification = Column(Boolean, default=False)
    
    # User notes
    nickname = Column(String(255))
    notes = Column(Text)
    priority = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_notified_at = Column(DateTime)
    notification_count = Column(Integer, default=0)
    
    added_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_products")
    product = relationship("Product", back_populates="user_products")


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Price data
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    in_stock = Column(Boolean, default=True)
    
    # Additional data
    discount_percent = Column(Numeric(5, 2))
    original_price = Column(Numeric(10, 2))
    coupon_available = Column(Boolean, default=False)
    
    # Timestamp
    scraped_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_product_id = Column(Integer, ForeignKey("user_products.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Alert type
    alert_type = Column(String(50), nullable=False)  # price_drop, target_met, back_in_stock
    
    # Price data
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    price_difference = Column(Numeric(10, 2))
    price_difference_percent = Column(Numeric(5, 2))
    
    # Status
    status = Column(String(20), default="pending", index=True)  # pending, sent, failed
    sent_at = Column(DateTime)
    
    # Notification channels
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)
    whatsapp_sent = Column(Boolean, default=False)
    telegram_sent = Column(Boolean, default=False)
    
    # User interaction
    viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")


class UsageStats(Base):
    __tablename__ = "usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False, default=func.current_date())
    
    # Counters
    tracked_products_count = Column(Integer, default=0)
    alerts_sent_count = Column(Integer, default=0)
    price_checks_count = Column(Integer, default=0)
    api_calls_count = Column(Integer, default=0)
    
    # Reset tracking
    last_reset = Column(DateTime, default=func.now())


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)
    
    name = Column(String(100))
    scopes = Column(ARRAY(Text))
    
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"))
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    tax_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Gateway
    payment_gateway = Column(String(50), nullable=False)
    gateway_transaction_id = Column(String(255))
    gateway_payment_id = Column(String(255))
    
    # Status
    status = Column(String(20), nullable=False, index=True)  # pending, completed, failed, refunded
    payment_method = Column(String(50))  # card, upi, wallet, netbanking
    
    # Invoice
    invoice_number = Column(String(50))
    invoice_url = Column(Text)
    
    # Metadata
    failure_reason = Column(Text)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

