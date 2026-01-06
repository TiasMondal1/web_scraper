"""
Product tracking endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import User, Product, UserProduct, Subscription, SubscriptionPlan, PriceHistory
from app.schemas import (
    ProductCreate, ProductResponse, UserProductResponse,
    UpdateProductSettings, PriceHistoryChartResponse, PriceHistoryResponse
)
from app.auth import get_current_user
from app.utils.scraper import scrape_product_info
from app.utils.limits import check_product_limit

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("/track", response_model=UserProductResponse, status_code=status.HTTP_201_CREATED)
async def track_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a product to track
    - Checks user's product limit based on subscription
    - Scrapes product information
    - Creates product if doesn't exist
    - Links product to user
    """
    # Check if user has reached product limit
    active_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active subscription found"
        )
    
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == active_subscription.plan_id
    ).first()
    
    # Count current tracked products
    current_count = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.is_active == True
    ).count()
    
    if current_count >= plan.max_products:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Product limit reached ({plan.max_products}). Upgrade your plan to track more products."
        )
    
    # Check if product already exists
    product = db.query(Product).filter(Product.url == product_data.url).first()
    
    if not product:
        # Scrape product information
        try:
            product_info = await scrape_product_info(product_data.url)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to scrape product: {str(e)}"
            )
        
        # Create new product
        product = Product(
            name=product_info['name'],
            url=product_data.url,
            platform=product_info['platform'],
            current_price=product_info.get('price'),
            image_url=product_info.get('image_url'),
            brand=product_info.get('brand'),
            category=product_info.get('category'),
            in_stock=product_info.get('in_stock', True),
            last_scraped_at=datetime.utcnow(),
            scrape_count=1,
            scrape_success_count=1
        )
        
        db.add(product)
        db.flush()
        
        # Add initial price history
        if product_info.get('price'):
            price_history = PriceHistory(
                product_id=product.id,
                price=product_info['price'],
                in_stock=product_info.get('in_stock', True),
                scraped_at=datetime.utcnow()
            )
            db.add(price_history)
    
    # Check if user already tracking this product
    existing_user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product.id
    ).first()
    
    if existing_user_product:
        if existing_user_product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already tracking this product"
            )
        else:
            # Reactivate
            existing_user_product.is_active = True
            existing_user_product.target_price = product_data.target_price
            existing_user_product.alert_enabled = product_data.alert_enabled
            db.commit()
            db.refresh(existing_user_product)
            return existing_user_product
    
    # Create user-product link
    user_product = UserProduct(
        user_id=current_user.id,
        product_id=product.id,
        target_price=product_data.target_price,
        alert_enabled=product_data.alert_enabled,
        email_notification=True
    )
    
    db.add(user_product)
    db.commit()
    db.refresh(user_product)
    
    return user_product


@router.get("/my", response_model=List[UserProductResponse])
async def get_my_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all products tracked by current user
    """
    user_products = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.is_active == True
    ).order_by(UserProduct.added_at.desc()).all()
    
    return user_products


@router.get("/{product_id}", response_model=UserProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific product details
    """
    user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product_id,
        UserProduct.is_active == True
    ).first()
    
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return user_product


@router.patch("/{product_id}", response_model=UserProductResponse)
async def update_product_settings(
    product_id: int,
    settings: UpdateProductSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update product tracking settings
    """
    user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product_id,
        UserProduct.is_active == True
    ).first()
    
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update settings
    if settings.target_price is not None:
        user_product.target_price = settings.target_price
    if settings.alert_enabled is not None:
        user_product.alert_enabled = settings.alert_enabled
    if settings.email_notification is not None:
        user_product.email_notification = settings.email_notification
    if settings.nickname is not None:
        user_product.nickname = settings.nickname
    
    db.commit()
    db.refresh(user_product)
    
    return user_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_tracking_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop tracking a product (soft delete)
    """
    user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product_id,
        UserProduct.is_active == True
    ).first()
    
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    user_product.is_active = False
    db.commit()
    
    return None


@router.get("/{product_id}/history", response_model=PriceHistoryChartResponse)
async def get_price_history(
    product_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get price history for a product
    - Returns chart data
    - Limited by subscription plan's historical_data_days
    """
    # Check if user is tracking this product
    user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product_id,
        UserProduct.is_active == True
    ).first()
    
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get user's subscription plan limits
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()
    
    # Limit days based on plan
    max_days = min(days, plan.historical_data_days)
    
    # Get price history
    cutoff_date = datetime.utcnow() - timedelta(days=max_days)
    price_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        PriceHistory.scraped_at >= cutoff_date
    ).order_by(PriceHistory.scraped_at.asc()).all()
    
    if not price_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No price history found"
        )
    
    # Calculate statistics
    prices = [float(ph.price) for ph in price_history]
    
    product = user_product.product
    
    return PriceHistoryChartResponse(
        product_id=product.id,
        product_name=product.name,
        data_points=price_history,
        min_price=min(prices),
        max_price=max(prices),
        avg_price=sum(prices) / len(prices)
    )

