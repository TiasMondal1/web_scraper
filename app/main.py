"""
Main FastAPI Application
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.config import settings
from app.database import get_db, init_db
from app.models import User, SubscriptionPlan, Subscription
from app.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    RefreshTokenRequest, ErrorResponse
)
from app.auth import (
    get_password_hash, authenticate_user, create_user_tokens,
    get_current_user, generate_verification_token, decode_token
)
from app.routers import products, subscriptions, dashboard, payments, admin, exports

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SaaS Price Tracking Application - Track prices, get alerts, save money!",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Include routers
app.include_router(products.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(exports.router)

# Add custom middleware
from app.middleware import RateLimitMiddleware, LoggingMiddleware, SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Startup Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and create default subscription plans"""
    init_db()
    
    # Create default subscription plans if they don't exist
    db = next(get_db())
    try:
        if db.query(SubscriptionPlan).count() == 0:
            plans = [
                SubscriptionPlan(
                    name="free",
                    display_name="Free",
                    description="Perfect for trying out",
                    price_monthly=0,
                    price_yearly=0,
                    max_products=3,
                    max_alerts_per_day=5,
                    max_price_checks_per_day=2,
                    historical_data_days=30
                ),
                SubscriptionPlan(
                    name="basic",
                    display_name="Basic",
                    description="For regular shoppers",
                    price_monthly=199,
                    price_yearly=1990,
                    max_products=25,
                    max_alerts_per_day=20,
                    max_price_checks_per_day=6,
                    historical_data_days=90
                ),
                SubscriptionPlan(
                    name="pro",
                    display_name="Pro",
                    description="For power users",
                    price_monthly=499,
                    price_yearly=4990,
                    max_products=100,
                    max_alerts_per_day=100,
                    max_price_checks_per_day=24,
                    max_api_calls_per_day=100,
                    api_access=True,
                    data_export=True,
                    historical_data_days=365
                ),
                SubscriptionPlan(
                    name="enterprise",
                    display_name="Enterprise",
                    description="For businesses",
                    price_monthly=0,  # Custom pricing
                    price_yearly=0,
                    max_products=999999,
                    max_alerts_per_day=999999,
                    max_price_checks_per_day=999999,
                    max_api_calls_per_day=999999,
                    api_access=True,
                    data_export=True,
                    priority_support=True,
                    historical_data_days=999999
                )
            ]
            db.add_all(plans)
            db.commit()
            print("✅ Default subscription plans created")
    finally:
        db.close()


# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# ============================================
# Authentication Endpoints
# ============================================

@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    - Creates user account
    - Generates verification token
    - Creates free subscription
    - Returns access and refresh tokens
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    verification_token = generate_verification_token()
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        verification_token=verification_token,
        verification_sent_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.flush()  # Get user ID before committing
    
    # Create free subscription
    free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "free").first()
    subscription = Subscription(
        user_id=new_user.id,
        plan_id=free_plan.id,
        billing_cycle="monthly",
        amount=0,
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=365)  # Free is 1 year
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(new_user)
    
    # Send verification and welcome emails
    try:
        from app.utils.email import send_verification_email, send_welcome_email
        send_verification_email(new_user.email, verification_token)
        send_welcome_email(new_user.email, new_user.full_name or new_user.email)
    except Exception as e:
        # Log error but don't fail registration
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send welcome email: {str(e)}")
    
    # Create tokens
    tokens = create_user_tokens(new_user.id)
    
    return tokens


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user
    - Validates credentials
    - Updates last login time
    - Returns access and refresh tokens
    """
    user = authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    db.commit()
    
    # Create tokens
    tokens = create_user_tokens(user.id)
    
    return tokens


@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    payload = decode_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )
    
    # Create new tokens
    tokens = create_user_tokens(user.id)
    
    return tokens


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    Requires: Bearer token in Authorization header
    """
    return current_user


@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should discard tokens)
    """
    return {"message": "Logged out successfully"}


@app.post("/api/auth/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email with verification token
    """
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    user.email_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.DEBUG)

