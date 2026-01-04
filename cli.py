"""
Command Line Interface for Price Tracker
Provides CLI for various operations
"""
import argparse
import sys
from card_scraper import track_all_products, run_price_analysis
from data_export import DataExporter
from price_comparison import PriceComparer
from advanced_analytics import AdvancedAnalytics
from database import PriceDatabase
from logging_config import setup_logging
from config import get_config

def main():
    parser = argparse.ArgumentParser(description='Price Tracker CLI')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Track command
    track_parser = subparsers.add_parser('track', help='Track prices for all products')
    track_parser.add_argument('--no-analysis', action='store_true', help='Skip price analysis')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--product', help='Export specific product')
    export_parser.add_argument('--all', action='store_true', help='Export all products')
    export_parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup database')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare products')
    compare_parser.add_argument('products', nargs='+', help='Product names to compare')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze product')
    analyze_parser.add_argument('product', help='Product name')
    analyze_parser.add_argument('--volatility', action='store_true', help='Calculate volatility')
    analyze_parser.add_argument('--predict', type=int, metavar='DAYS', help='Predict price N days ahead')
    analyze_parser.add_argument('--seasonal', action='store_true', help='Detect seasonal trends')
    
    # Best time command
    best_time_parser = subparsers.add_parser('best-time', help='Find best time to buy')
    best_time_parser.add_argument('product', help='Product name')
    best_time_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all products')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration')
    
    args = parser.parse_args()
    
    # Setup logging
    config = get_config()
    log_level = getattr(logging, config.get('logging.level', 'INFO'), logging.INFO)
    setup_logging(log_level=log_level)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'track':
            track_all_products()
            if not args.no_analysis:
                run_price_analysis()
        
        elif args.command == 'export':
            exporter = DataExporter()
            if args.product:
                if args.format == 'json':
                    file = exporter.export_product_to_json(args.product)
                else:
                    file = exporter.export_product_to_csv(args.product)
                print(f"Exported to: {file}")
            elif args.all:
                if args.format == 'json':
                    file = exporter.export_all_to_json()
                elif args.format == 'excel':
                    file = exporter.export_all_to_csv()
                else:
                    file = exporter.export_all_to_csv()
                print(f"Exported to: {file}")
            else:
                export_parser.print_help()
        
        elif args.command == 'backup':
            exporter = DataExporter()
            file = exporter.backup_database()
            print(f"Backup created: {file}")
        
        elif args.command == 'compare':
            comparer = PriceComparer()
            result = comparer.compare_products(args.products)
            import json
            print(json.dumps(result, indent=2))
        
        elif args.command == 'analyze':
            analytics = AdvancedAnalytics()
            
            if args.volatility:
                result = analytics.calculate_volatility(args.product)
                import json
                print(json.dumps(result, indent=2))
            elif args.predict:
                result = analytics.predict_price(args.product, days_ahead=args.predict)
                import json
                print(json.dumps(result, indent=2))
            elif args.seasonal:
                result = analytics.detect_seasonal_trends(args.product)
                import json
                print(json.dumps(result, indent=2))
            else:
                analyze_parser.print_help()
        
        elif args.command == 'best-time':
            comparer = PriceComparer()
            result = comparer.analyze_best_buy_time(args.product, days_back=args.days)
            import json
            print(json.dumps(result, indent=2))
        
        elif args.command == 'list':
            db = PriceDatabase()
            products = db.get_all_products()
            if products:
                print("\nTracked Products:")
                print("-" * 60)
                for product in products:
                    latest_price = db.get_latest_price(product['name'])
                    print(f"  {product['name']}")
                    print(f"    URL: {product['url']}")
                    print(f"    Latest Price: ₹{latest_price:,.2f}" if latest_price else "    Latest Price: N/A")
                    print()
            else:
                print("No products found.")
        
        elif args.command == 'config':
            config = get_config()
            import json
            print(json.dumps(config.to_dict(), indent=2))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    import logging
    main()

