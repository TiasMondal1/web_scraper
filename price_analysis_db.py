import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import shutil
from database_manager import DatabaseManager

class PriceAnalyzerDB:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DatabaseManager()
        self.analysis_dir = 'analysis'
        
        # Clean up previous analysis
        self.cleanup_previous_analysis()

    def cleanup_previous_analysis(self):
        """Delete previous analysis directory if it exists"""
        if os.path.exists(self.analysis_dir):
            print("Cleaning up previous analysis...")
            shutil.rmtree(self.analysis_dir)
        # Create fresh analysis directory
        os.makedirs(self.analysis_dir, exist_ok=True)

    def create_product_dir(self, product_name):
        """Create directory structure for a specific product"""
        # Create product directory
        product_dir = os.path.join(self.analysis_dir, product_name)
        os.makedirs(product_dir, exist_ok=True)
        return product_dir

    def load_product_data(self, product_name):
        """Load data for a specific product from database"""
        try:
            df = self.db_manager.get_product_data(product_name)
            if df is not None and not df.empty:
                # Ensure Date is datetime
                df['Date'] = pd.to_datetime(df['Date'])
                return df
            else:
                print(f"No data found for product: {product_name}")
                return None
        except Exception as e:
            print(f"Error loading data for {product_name}: {str(e)}")
            return None

    def calculate_statistics(self, df):
        """Calculate basic price statistics"""
        if df is None or df.empty:
            return None
        
        stats = {
            'average_price': df['Price'].mean(),
            'min_price': df['Price'].min(),
            'max_price': df['Price'].max(),
            'price_std': df['Price'].std(),
            'record_count': len(df)
        }
        
        # Calculate price change if we have more than one record
        if len(df) > 1:
            stats['price_change'] = ((df['Price'].iloc[-1] - df['Price'].iloc[0]) / df['Price'].iloc[0]) * 100
        else:
            stats['price_change'] = 0.0
            
        return stats

    def analyze_trends(self, df):
        """Analyze price trends"""
        if df is None or df.empty:
            return None
        
        # Set Date as index for resampling
        df_indexed = df.set_index('Date')
        
        # Daily average (groupby date)
        daily_avg = df_indexed.groupby(df_indexed.index.date)['Price'].mean()
        
        # Weekly average (only if we have enough data)
        weekly_avg = None
        monthly_avg = None
        
        try:
            if len(df_indexed) > 7:
                weekly_avg = df_indexed.resample('W')['Price'].mean().dropna()
            if len(df_indexed) > 30:
                monthly_avg = df_indexed.resample('M')['Price'].mean().dropna()
        except Exception as e:
            print(f"Error calculating trends: {e}")
        
        return {
            'daily_avg': daily_avg,
            'weekly_avg': weekly_avg,
            'monthly_avg': monthly_avg
        }

    def generate_price_history_graph(self, df, product_name, product_dir):
        """Generate price history line graph"""
        if df is None or df.empty:
            return None
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['Date'], df['Price'], marker='o', linewidth=2, markersize=4)
        plt.title(f'Price History for {product_name}', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Price (₹)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Add trend line if we have enough data
        if len(df) > 2:
            z = np.polyfit(range(len(df)), df['Price'], 1)
            p = np.poly1d(z)
            plt.plot(df['Date'], p(range(len(df))), "r--", alpha=0.8, label='Trend')
            plt.legend()
        
        # Save the graph in product directory
        graph_path = os.path.join(product_dir, 'price_history.png')
        plt.savefig(graph_path, bbox_inches='tight', dpi=300)
        plt.close()
        return graph_path

    def generate_price_distribution(self, df, product_name, product_dir):
        """Generate price distribution histogram"""
        if df is None or df.empty:
            return None
        
        plt.figure(figsize=(10, 6))
        
        # Use appropriate number of bins based on data size
        bins = min(20, max(5, len(df) // 3))
        
        sns.histplot(data=df, x='Price', bins=bins, kde=True if len(df) > 5 else False)
        plt.title(f'Price Distribution for {product_name}', fontsize=14, fontweight='bold')
        plt.xlabel('Price (₹)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        
        # Add statistics to the plot
        mean_price = df['Price'].mean()
        plt.axvline(mean_price, color='red', linestyle='--', label=f'Mean: ₹{mean_price:.2f}')
        plt.legend()
        
        # Save the graph in product directory
        graph_path = os.path.join(product_dir, 'price_distribution.png')
        plt.savefig(graph_path, bbox_inches='tight', dpi=300)
        plt.close()
        return graph_path

    def generate_analysis_report(self, product_name):
        """Generate comprehensive analysis report"""
        # Create product directory
        product_dir = self.create_product_dir(product_name)
        
        # Load data from database
        df = self.load_product_data(product_name)
        if df is None or df.empty:
            print(f"No data available for {product_name}")
            return None

        # Get additional statistics from database
        db_stats = self.db_manager.get_price_statistics(product_name)
        
        # Calculate statistics
        stats = self.calculate_statistics(df)
        trends = self.analyze_trends(df)

        # Generate graphs
        history_graph = self.generate_price_history_graph(df, product_name, product_dir)
        distribution_graph = self.generate_price_distribution(df, product_name, product_dir)

        # Create enhanced report
        date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
        
        # Determine recommendations
        volatility = "volatile" if stats['price_std'] > stats['average_price'] * 0.1 else "stable"
        trend_recommendation = "Consider buying now" if stats['price_change'] < -5 else "Wait for better price" if stats['price_change'] > 5 else "Price is stable"
        
        report = f"""
Product Analysis Report (Database Version)
==========================================
Product: {product_name}
Analysis Period: {date_range}
Data Points: {stats['record_count']} price records

Price Statistics:
-----------------
- Average Price: ₹{stats['average_price']:.2f}
- Minimum Price: ₹{stats['min_price']:.2f}
- Maximum Price: ₹{stats['max_price']:.2f}
- Price Standard Deviation: ₹{stats['price_std']:.2f}
- Overall Price Change: {stats['price_change']:.2f}%
- Price Range: ₹{stats['max_price'] - stats['min_price']:.2f}

Database Statistics:
-------------------
- First Record: {db_stats['first_recorded'] if db_stats else 'N/A'}
- Last Record: {db_stats['last_recorded'] if db_stats else 'N/A'}
- Total Records in DB: {db_stats['record_count'] if db_stats else 'N/A'}

Price Trends:
------------"""

        if trends and trends['daily_avg'] is not None:
            report += f"\n- Daily Average: ₹{trends['daily_avg'].mean():.2f}"
        if trends and trends['weekly_avg'] is not None and not trends['weekly_avg'].empty:
            report += f"\n- Weekly Average: ₹{trends['weekly_avg'].mean():.2f}"
        if trends and trends['monthly_avg'] is not None and not trends['monthly_avg'].empty:
            report += f"\n- Monthly Average: ₹{trends['monthly_avg'].mean():.2f}"

        report += f"""

Visualizations Generated:
------------------------
- Price History: price_history.png
- Price Distribution: price_distribution.png

Analysis & Recommendations:
--------------------------
- Price Volatility: {volatility.title()}
- Trend Analysis: {trend_recommendation}
- Best Price Seen: ₹{stats['min_price']:.2f}
- Worst Price Seen: ₹{stats['max_price']:.2f}

Purchase Recommendation:
-----------------------"""

        if stats['price_change'] < -10:
            report += "\n🟢 STRONG BUY: Price has dropped significantly"
        elif stats['price_change'] < -5:
            report += "\n🟡 BUY: Price is trending downward"
        elif stats['price_change'] > 10:
            report += "\n🔴 AVOID: Price has increased significantly"
        elif stats['price_change'] > 5:
            report += "\n🟡 WAIT: Price is trending upward"
        else:
            report += "\n🔵 NEUTRAL: Price is relatively stable"

        if volatility == "volatile":
            report += "\n⚠️  CAUTION: High price volatility detected"
        else:
            report += "\n✅ STABLE: Low price volatility"

        report += f"""

Data Quality:
------------
- Analysis based on {stats['record_count']} data points
- Date range covers {(df['Date'].max() - df['Date'].min()).days} days
- Data source: SQLite database
"""

        # Save report in product directory
        report_path = os.path.join(product_dir, 'analysis_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        return report_path

    def generate_summary_report(self):
        """Generate a summary report for all products"""
        products = self.db_manager.get_all_products()
        
        if not products:
            print("No products found in database")
            return None
        
        summary_path = os.path.join(self.analysis_dir, 'summary_report.txt')
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("PRICE TRACKING SUMMARY REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for product_name in products:
                f.write(f"\n{product_name}:\n")
                f.write("-" * len(product_name) + "\n")
                
                stats = self.db_manager.get_price_statistics(product_name)
                latest = self.db_manager.get_latest_price(product_name)
                
                if stats and latest:
                    f.write(f"Latest Price: ₹{latest['price']:.2f}\n")
                    f.write(f"Average Price: ₹{stats['avg_price']:.2f}\n")
                    f.write(f"Price Range: ₹{stats['min_price']:.2f} - ₹{stats['max_price']:.2f}\n")
                    f.write(f"Records: {stats['record_count']}\n")
                    
                    # Quick recommendation
                    if latest['price'] <= stats['min_price'] * 1.05:
                        f.write("Status: 🟢 GOOD PRICE\n")
                    elif latest['price'] >= stats['max_price'] * 0.95:
                        f.write("Status: 🔴 HIGH PRICE\n")
                    else:
                        f.write("Status: 🟡 AVERAGE PRICE\n")
                else:
                    f.write("No data available\n")
        
        print(f"Summary report generated: {summary_path}")
        return summary_path


# Import numpy for trend analysis
try:
    import numpy as np
except ImportError:
    print("Warning: numpy not available, trend lines will be skipped")
    np = None


def main():
    """Example usage and testing"""
    db_manager = DatabaseManager()
    analyzer = PriceAnalyzerDB(db_manager)
    
    # Get all product names from database
    product_names = db_manager.get_all_products()
    
    if not product_names:
        print("No products found in database")
        return
    
    # Generate analysis for each product
    for product_name in product_names:
        print(f"\nAnalyzing {product_name}...")
        report_path = analyzer.generate_analysis_report(product_name)
        if report_path:
            print(f"Analysis report generated: {report_path}")
    
    # Generate summary report
    print("\nGenerating summary report...")
    analyzer.generate_summary_report()


if __name__ == "__main__":
    main() 