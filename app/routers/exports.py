"""
Data export endpoints - CSV, JSON, PDF
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import csv
import json
from typing import Optional

from app.database import get_db
from app.models import User, UserProduct, Product, PriceHistory, Alert
from app.auth import get_current_user

router = APIRouter(prefix="/api/exports", tags=["exports"])


def generate_csv(headers: list, rows: list) -> str:
    """Generate CSV content from headers and rows"""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()


@router.get("/products/csv")
async def export_products_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export user's tracked products to CSV
    """
    user_products = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.is_active == True
    ).all()
    
    headers = [
        "Product Name", "Platform", "URL", "Current Price", 
        "Target Price", "Alert Enabled", "Added Date", "Last Updated"
    ]
    
    rows = []
    for up in user_products:
        product = db.query(Product).filter(Product.id == up.product_id).first()
        if product:
            rows.append([
                product.name,
                product.platform,
                product.url,
                float(product.current_price) if product.current_price else "N/A",
                float(up.target_price) if up.target_price else "N/A",
                "Yes" if up.alert_enabled else "No",
                up.added_at.strftime("%Y-%m-%d %H:%M:%S"),
                product.last_scraped_at.strftime("%Y-%m-%d %H:%M:%S") if product.last_scraped_at else "N/A"
            ])
    
    csv_content = generate_csv(headers, rows)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=products_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/price-history/csv")
async def export_price_history_csv(
    product_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export price history for a product to CSV
    """
    # Verify user owns this product
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
    
    # Get product
    product = db.query(Product).filter(Product.id == product_id).first()
    
    # Get price history
    since_date = datetime.utcnow() - timedelta(days=days)
    price_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        PriceHistory.scraped_at >= since_date
    ).order_by(PriceHistory.scraped_at.asc()).all()
    
    headers = ["Date", "Price", "In Stock", "Discount %"]
    
    rows = []
    for ph in price_history:
        rows.append([
            ph.scraped_at.strftime("%Y-%m-%d %H:%M:%S"),
            float(ph.price),
            "Yes" if ph.in_stock else "No",
            float(ph.discount_percent) if ph.discount_percent else "0"
        ])
    
    csv_content = generate_csv(headers, rows)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=price_history_{product.name[:30]}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/alerts/csv")
async def export_alerts_csv(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export user's price alerts to CSV
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.created_at >= since_date
    ).order_by(Alert.created_at.desc()).all()
    
    headers = [
        "Date", "Product", "Alert Type", "Old Price", 
        "New Price", "Savings", "Discount %", "Status"
    ]
    
    rows = []
    for alert in alerts:
        product = db.query(Product).filter(Product.id == alert.product_id).first()
        product_name = product.name if product else "Unknown"
        
        rows.append([
            alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            product_name,
            alert.alert_type,
            float(alert.old_price) if alert.old_price else "N/A",
            float(alert.new_price) if alert.new_price else "N/A",
            float(alert.price_difference) if alert.price_difference else "0",
            float(alert.price_difference_percent) if alert.price_difference_percent else "0",
            alert.status
        ])
    
    csv_content = generate_csv(headers, rows)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/products/json")
async def export_products_json(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export user's tracked products to JSON
    """
    user_products = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.is_active == True
    ).all()
    
    data = []
    for up in user_products:
        product = db.query(Product).filter(Product.id == up.product_id).first()
        if product:
            data.append({
                "product_name": product.name,
                "platform": product.platform,
                "url": product.url,
                "current_price": float(product.current_price) if product.current_price else None,
                "target_price": float(up.target_price) if up.target_price else None,
                "alert_enabled": up.alert_enabled,
                "added_at": up.added_at.isoformat(),
                "last_scraped_at": product.last_scraped_at.isoformat() if product.last_scraped_at else None,
                "in_stock": product.in_stock
            })
    
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user_email": current_user.email,
        "total_products": len(data),
        "products": data
    }
    
    json_content = json.dumps(export_data, indent=2)
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=products_{datetime.now().strftime('%Y%m%d')}.json"
        }
    )


@router.get("/full-report/json")
async def export_full_report_json(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export complete user data including products, alerts, and statistics
    """
    # Get tracked products
    user_products = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.is_active == True
    ).all()
    
    products_data = []
    for up in user_products:
        product = db.query(Product).filter(Product.id == up.product_id).first()
        if product:
            # Get price history
            price_history = db.query(PriceHistory).filter(
                PriceHistory.product_id == product.id
            ).order_by(PriceHistory.scraped_at.desc()).limit(100).all()
            
            products_data.append({
                "name": product.name,
                "url": product.url,
                "platform": product.platform,
                "current_price": float(product.current_price) if product.current_price else None,
                "target_price": float(up.target_price) if up.target_price else None,
                "price_history": [
                    {
                        "date": ph.scraped_at.isoformat(),
                        "price": float(ph.price),
                        "in_stock": ph.in_stock
                    }
                    for ph in price_history
                ]
            })
    
    # Get alerts
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.created_at.desc()).limit(100).all()
    
    alerts_data = []
    for alert in alerts:
        product = db.query(Product).filter(Product.id == alert.product_id).first()
        alerts_data.append({
            "date": alert.created_at.isoformat(),
            "product_name": product.name if product else "Unknown",
            "alert_type": alert.alert_type,
            "old_price": float(alert.old_price) if alert.old_price else None,
            "new_price": float(alert.new_price) if alert.new_price else None,
            "savings": float(alert.price_difference) if alert.price_difference else None
        })
    
    # Calculate statistics
    total_savings = sum(
        float(alert.price_difference) for alert in alerts 
        if alert.price_difference
    )
    
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "email": current_user.email,
            "name": current_user.full_name,
            "member_since": current_user.created_at.isoformat()
        },
        "statistics": {
            "total_products_tracked": len(products_data),
            "total_alerts_received": len(alerts_data),
            "total_savings": round(total_savings, 2)
        },
        "products": products_data,
        "alerts": alerts_data
    }
    
    json_content = json.dumps(export_data, indent=2)
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=full_report_{datetime.now().strftime('%Y%m%d')}.json"
        }
    )


@router.get("/savings-report/csv")
async def export_savings_report_csv(
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export monthly savings report to CSV
    """
    headers = ["Month", "Alerts", "Total Savings (₹)", "Average Savings per Alert (₹)"]
    rows = []
    
    for i in range(months):
        if i == 0:
            end_date = datetime.utcnow()
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_date = start_date - timedelta(days=1)
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        alerts = db.query(Alert).filter(
            Alert.user_id == current_user.id,
            Alert.alert_type == "price_drop",
            Alert.created_at >= start_date,
            Alert.created_at <= end_date
        ).all()
        
        month_savings = sum(
            float(alert.price_difference) for alert in alerts 
            if alert.price_difference
        )
        
        avg_savings = month_savings / len(alerts) if alerts else 0
        
        rows.insert(0, [
            start_date.strftime("%B %Y"),
            len(alerts),
            round(month_savings, 2),
            round(avg_savings, 2)
        ])
    
    # Add total row
    total_alerts = sum(row[1] for row in rows)
    total_savings = sum(row[2] for row in rows)
    rows.append(["TOTAL", total_alerts, total_savings, ""])
    
    csv_content = generate_csv(headers, rows)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=savings_report_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )
