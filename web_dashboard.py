"""
Web Dashboard for Price Tracker
Flask-based web interface for viewing and managing price tracking
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for
from database import PriceDatabase
import json
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
db = PriceDatabase()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    """Get all products with latest price info"""
    products = db.get_all_products()
    result = []
    
    for product in products:
        latest_price = db.get_latest_price(product['name'])
        stats = db.get_statistics(product['name'])
        
        product_info = {
            'id': product['id'],
            'name': product['name'],
            'url': product['url'],
            'latest_price': latest_price,
            'created_at': product['created_at'],
            'updated_at': product['updated_at'],
            'stats': stats
        }
        result.append(product_info)
    
    return jsonify(result)

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product"""
    data = request.json
    name = data.get('name')
    url = data.get('url')
    
    if not name or not url:
        return jsonify({'error': 'Name and URL are required'}), 400
    
    try:
        product_id = db.add_product(name, url)
        # Also add to products.json
        try:
            with open('products.json', 'r') as f:
                config = json.load(f)
            config['products'].append({'name': name, 'url': url})
            with open('products.json', 'w') as f:
                json.dump(config, f, indent=4)
        except:
            pass
        
        return jsonify({'success': True, 'product_id': product_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        products = db.get_all_products()
        product_name = None
        for p in products:
            if p['id'] == product_id:
                product_name = p['name']
                break
        
        if not product_name:
            return jsonify({'error': 'Product not found'}), 404
        
        success = db.delete_product(product_name)
        
        if success:
            # Remove from products.json
            try:
                with open('products.json', 'r') as f:
                    config = json.load(f)
                config['products'] = [p for p in config['products'] if p['name'] != product_name]
                with open('products.json', 'w') as f:
                    json.dump(config, f, indent=4)
            except:
                pass
            
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Failed to delete product'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/history')
def get_price_history(product_id):
    """Get price history for a product"""
    try:
        products = db.get_all_products()
        product_name = None
        for p in products:
            if p['id'] == product_id:
                product_name = p['name']
                break
        
        if not product_name:
            return jsonify({'error': 'Product not found'}), 404
        
        df = db.get_price_history(product_name)
        
        if df.empty:
            return jsonify({'data': [], 'labels': []})
        
        # Convert to format suitable for charts
        dates = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        prices = df['Price'].tolist()
        
        return jsonify({
            'labels': dates,
            'data': prices
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/stats')
def get_product_stats(product_id):
    """Get statistics for a product"""
    try:
        products = db.get_all_products()
        product_name = None
        for p in products:
            if p['id'] == product_id:
                product_name = p['name']
                break
        
        if not product_name:
            return jsonify({'error': 'Product not found'}), 404
        
        stats = db.get_statistics(product_name)
        
        # Calculate additional stats
        if stats:
            df = db.get_price_history(product_name)
            if not df.empty and len(df) > 1:
                stats['price_change_percent'] = ((df['Price'].iloc[-1] - df['Price'].iloc[0]) / df['Price'].iloc[0]) * 100
            else:
                stats['price_change_percent'] = 0
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get overall dashboard statistics"""
    products = db.get_all_products()
    
    total_products = len(products)
    total_price_points = 0
    products_with_drops = 0
    
    for product in products:
        stats = db.get_statistics(product['name'])
        if stats:
            total_price_points += stats.get('count', 0)
            if stats.get('price_change_percent', 0) < 0:
                products_with_drops += 1
    
    return jsonify({
        'total_products': total_products,
        'total_price_points': total_price_points,
        'products_with_drops': products_with_drops
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

