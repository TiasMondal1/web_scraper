"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============================================
# User Schemas
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    email_verified: bool
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============================================
# Subscription Schemas
# ============================================

class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    price_monthly: Decimal
    price_yearly: Decimal
    currency: str
    max_products: int
    max_alerts_per_day: int
    max_price_checks_per_day: int
    email_alerts: bool
    sms_alerts: bool
    api_access: bool
    historical_data_days: int
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: int
    plan: SubscriptionPlanResponse
    status: str
    billing_cycle: str
    amount: Decimal
    current_period_start: datetime
    current_period_end: datetime
    
    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    plan_id: int
    billing_cycle: str  # monthly, yearly


# ============================================
# Product Schemas
# ============================================

class ProductBase(BaseModel):
    url: str


class ProductCreate(ProductBase):
    target_price: Optional[Decimal] = None
    alert_enabled: bool = True


class ProductResponse(BaseModel):
    id: int
    name: str
    url: str
    platform: str
    current_price: Optional[Decimal]
    image_url: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    in_stock: bool
    last_scraped_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProductResponse(BaseModel):
    id: int
    product: ProductResponse
    target_price: Optional[Decimal]
    alert_enabled: bool
    email_notification: bool
    added_at: datetime
    last_notified_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UpdateProductSettings(BaseModel):
    target_price: Optional[Decimal] = None
    alert_enabled: Optional[bool] = None
    email_notification: Optional[bool] = None
    nickname: Optional[str] = None


# ============================================
# Price History Schemas
# ============================================

class PriceHistoryResponse(BaseModel):
    price: Decimal
    scraped_at: datetime
    in_stock: bool
    discount_percent: Optional[Decimal]
    
    class Config:
        from_attributes = True


class PriceHistoryChartResponse(BaseModel):
    product_id: int
    product_name: str
    data_points: List[PriceHistoryResponse]
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal


# ============================================
# Alert Schemas
# ============================================

class AlertResponse(BaseModel):
    id: int
    product_id: int
    alert_type: str
    old_price: Optional[Decimal]
    new_price: Optional[Decimal]
    price_difference: Optional[Decimal]
    price_difference_percent: Optional[Decimal]
    status: str
    viewed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Usage Stats Schemas
# ============================================

class UsageStatsResponse(BaseModel):
    tracked_products: int
    tracked_products_limit: int
    alerts_sent_today: int
    alerts_limit_per_day: int
    price_checks_today: int
    price_checks_limit_per_day: int
    api_calls_today: int
    api_calls_limit_per_day: int


# ============================================
# Dashboard Schemas
# ============================================

class DashboardStatsResponse(BaseModel):
    total_products: int
    active_alerts: int
    price_drops_today: int
    savings_this_month: Decimal
    subscription_plan: str
    subscription_expires: datetime


# ============================================
# Payment Schemas
# ============================================

class CreatePaymentRequest(BaseModel):
    plan_id: int
    billing_cycle: str  # monthly, yearly


class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: int


# ============================================
# Error Responses
# ============================================

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    detail: List[dict]

