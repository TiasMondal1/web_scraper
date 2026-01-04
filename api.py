"""
REST API for Price Tracker
Provides endpoints for product management, price queries, and manual scraping
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import PriceDatabase
from card_scraper import get_price, load_products, update_price_data
from alerts import AlertManager
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

db = PriceDatabase()
alert_manager = AlertManager()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'price-tracker-api'
    })

@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Get all products"""
    try:
        products = db.get_all_products()
        result = []
        for product in products:
            latest_price = db.get_latest_price(product['name'])
            stats = db.get_statistics(product['name'])
            
            result.append({
                'id': product['id'],
                'name': product['name'],
                'url': product['url'],
                'latest_price': latest_price,
                'created_at': product['created_at'],
                'updated_at': product['updated_at'],
                'stats': stats
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.json
        name = data.get('name')
        url = data.get('url')
        alert_threshold = data.get('alert_threshold')
        
        if not name or not url:
            return jsonify({'error': 'Name and URL are required'}), 400
        
        product_id = db.add_product(name, url)
        
        # Add to products.json
        try:
            with open('products.json', 'r') as f:
                config = json.load(f)
            product_entry = {'name': name, 'url': url}
            if alert_threshold:
                product_entry['alert_threshold'] = alert_threshold
            config['products'].append(product_entry)
            with open('products.json', 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not update products.json: {e}")
        
        return jsonify({
            'id': product_id,
            'name': name,
            'url': url,
            'message': 'Product created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        products = db.get_all_products()
        for product in products:
            if product['id'] == product_id:
                latest_price = db.get_latest_price(product['name'])
                stats = db.get_statistics(product['name'])
                return jsonify({
                    'id': product['id'],
                    'name': product['name'],
                    'url': product['url'],
                    'latest_price': latest_price,
                    'created_at': product['created_at'],
                    'updated_at': product['updated_at'],
                    'stats': stats
                }), 200
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product_api(product_id):
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
            
            return jsonify({'message': 'Product deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete product'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/prices', methods=['GET'])
def get_product_prices(product_id):
    """Get price history for a product"""
    try:
        limit = request.args.get('limit', type=int)
        products = db.get_all_products()
        product_name = None
        for p in products:
            if p['id'] == product_id:
                product_name = p['name']
                break
        
        if not product_name:
            return jsonify({'error': 'Product not found'}), 404
        
        df = db.get_price_history(product_name, limit=limit)
        
        prices = []
        for _, row in df.iterrows():
            prices.append({
                'date': row['Date'].isoformat() if hasattr(row['Date'], 'isoformat') else str(row['Date']),
                'time': str(row['Time']),
                'price': float(row['Price'])
            })
        
        return jsonify({
            'product_id': product_id,
            'product_name': product_name,
            'count': len(prices),
            'prices': prices
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/stats', methods=['GET'])
def get_product_stats_api(product_id):
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
        
        # Calculate price change percentage
        if stats:
            df = db.get_price_history(product_name)
            if not df.empty and len(df) > 1:
                stats['price_change_percent'] = ((df['Price'].iloc[-1] - df['Price'].iloc[0]) / df['Price'].iloc[0]) * 100
            else:
                stats['price_change_percent'] = 0
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/scrape', methods=['POST'])
def scrape_product(product_id):
    """Manually trigger price scraping for a product"""
    try:
        products = db.get_all_products()
        product = None
        for p in products:
            if p['id'] == product_id:
                product = p
                break
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get current price
        current_price = get_price(product['url'])
        
        if current_price is None:
            return jsonify({'error': 'Failed to fetch price'}), 500
        
        # Update price in database
        previous_price = db.get_latest_price(product['name'])
        db.add_price_record(product['name'], current_price)
        
        # Check alerts
        if previous_price is not None:
            product_config = None
            try:
                with open('products.json', 'r') as f:
                    config = json.load(f)
                    for p in config['products']:
                        if p['name'] == product['name']:
                            product_config = p
                            break
            except:
                pass
            
            alert_threshold = product_config.get('alert_threshold') if product_config else None
            alert_manager.check_and_send_alerts(
                product['name'],
                current_price,
                previous_price,
                product['url'],
                alert_threshold
            )
        
        return jsonify({
            'product_id': product_id,
            'product_name': product['name'],
            'current_price': current_price,
            'previous_price': previous_price,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape/all', methods=['POST'])
def scrape_all_products():
    """Manually trigger price scraping for all products"""
    try:
        products = load_products()
        if not products:
            return jsonify({'error': 'No products found'}), 404
        
        results = []
        for product in products:
            try:
                current_price = get_price(product['url'])
                if current_price:
                    previous_price = db.get_latest_price(product['name'])
                    db.add_product(product['name'], product['url'])
                    db.add_price_record(product['name'], current_price)
                    results.append({
                        'name': product['name'],
                        'price': current_price,
                        'previous_price': previous_price,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'name': product['name'],
                        'status': 'failed',
                        'error': 'Could not fetch price'
                    })
            except Exception as e:
                results.append({
                    'name': product['name'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_overall_stats():
    """Get overall statistics"""
    try:
        products = db.get_all_products()
        
        total_products = len(products)
        total_price_points = 0
        products_with_drops = 0
        
        for product in products:
            stats = db.get_statistics(product['name'])
            if stats:
                total_price_points += stats.get('count', 0)
                df = db.get_price_history(product['name'])
                if not df.empty and len(df) > 1:
                    price_change = ((df['Price'].iloc[-1] - df['Price'].iloc[0]) / df['Price'].iloc[0]) * 100
                    if price_change < 0:
                        products_with_drops += 1
        
        return jsonify({
            'total_products': total_products,
            'total_price_points': total_price_points,
            'products_with_drops': products_with_drops
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

