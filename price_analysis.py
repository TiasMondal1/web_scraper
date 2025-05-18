import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import shutil

class PriceAnalyzer:
    def __init__(self, excel_file='price_history.xlsx'):
        self.excel_file = excel_file
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
        """Load data for a specific product from Excel file"""
        try:
            df = pd.read_excel(self.excel_file, sheet_name=product_name)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            print(f"Error loading data for {product_name}: {str(e)}")
            return None

    def calculate_statistics(self, df):
        """Calculate basic price statistics"""
        stats = {
            'average_price': df['Price'].mean(),
            'min_price': df['Price'].min(),
            'max_price': df['Price'].max(),
            'price_std': df['Price'].std(),
            'price_change': ((df['Price'].iloc[-1] - df['Price'].iloc[0]) / df['Price'].iloc[0]) * 100
        }
        return stats

    def analyze_trends(self, df):
        """Analyze price trends"""
        # Daily average
        daily_avg = df.groupby('Date')['Price'].mean()
        
        # Weekly average
        weekly_avg = df.resample('W', on='Date')['Price'].mean()
        
        # Monthly average
        monthly_avg = df.resample('M', on='Date')['Price'].mean()
        
        return {
            'daily_avg': daily_avg,
            'weekly_avg': weekly_avg,
            'monthly_avg': monthly_avg
        }

    def generate_price_history_graph(self, df, product_name, product_dir):
        """Generate price history line graph"""
        plt.figure(figsize=(12, 6))
        plt.plot(df['Date'], df['Price'], marker='o')
        plt.title(f'Price History for {product_name}')
        plt.xlabel('Date')
        plt.ylabel('Price (₹)')
        plt.grid(True)
        plt.xticks(rotation=45)
        
        # Save the graph in product directory
        graph_path = os.path.join(product_dir, 'price_history.png')
        plt.savefig(graph_path, bbox_inches='tight')
        plt.close()
        return graph_path

    def generate_price_distribution(self, df, product_name, product_dir):
        """Generate price distribution histogram"""
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='Price', bins=20)
        plt.title(f'Price Distribution for {product_name}')
        plt.xlabel('Price (₹)')
        plt.ylabel('Frequency')
        
        # Save the graph in product directory
        graph_path = os.path.join(product_dir, 'price_distribution.png')
        plt.savefig(graph_path, bbox_inches='tight')
        plt.close()
        return graph_path

    def generate_analysis_report(self, product_name):
        """Generate comprehensive analysis report"""
        # Create product directory
        product_dir = self.create_product_dir(product_name)
        
        # Load data
        df = self.load_product_data(product_name)
        if df is None:
            return None

        # Calculate statistics
        stats = self.calculate_statistics(df)
        trends = self.analyze_trends(df)

        # Generate graphs
        history_graph = self.generate_price_history_graph(df, product_name, product_dir)
        distribution_graph = self.generate_price_distribution(df, product_name, product_dir)

        # Create report
        report = f"""
Product Analysis Report
----------------------
Product: {product_name}
Analysis Period: {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}

Price Statistics:
- Average Price: ₹{stats['average_price']:.2f}
- Minimum Price: ₹{stats['min_price']:.2f}
- Maximum Price: ₹{stats['max_price']:.2f}
- Price Standard Deviation: ₹{stats['price_std']:.2f}
- Overall Price Change: {stats['price_change']:.2f}%

Price Trends:
- Daily Average: ₹{trends['daily_avg'].mean():.2f}
- Weekly Average: ₹{trends['weekly_avg'].mean():.2f}
- Monthly Average: ₹{trends['monthly_avg'].mean():.2f}

Graphs Generated:
- Price History: price_history.png
- Price Distribution: price_distribution.png

Recommendations:
- {'Consider buying now' if stats['price_change'] < 0 else 'Wait for better price'}
- {'Price is stable' if stats['price_std'] < stats['average_price'] * 0.1 else 'Price is volatile'}
"""
        # Save report in product directory
        report_path = os.path.join(product_dir, 'analysis_report.txt')
        with open(report_path, 'w') as f:
            f.write(report)

        return report_path

def main():
    # Example usage
    analyzer = PriceAnalyzer()
    
    # Get all product names from Excel file
    excel_file = pd.ExcelFile('price_history.xlsx')
    product_names = excel_file.sheet_names
    
    # Generate analysis for each product
    for product_name in product_names:
        print(f"\nAnalyzing {product_name}...")
        report_path = analyzer.generate_analysis_report(product_name)
        if report_path:
            print(f"Analysis report generated: {report_path}")

if __name__ == "__main__":
    main() 