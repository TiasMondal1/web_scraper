"""
Scheduler module for automating price tracking
Supports Windows Task Scheduler and cron-like scheduling
"""
import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

def run_price_tracker():
    """Run the price tracker"""
    try:
        # Import and run the main tracking function
        from card_scraper import track_all_products, run_price_analysis
        
        print(f"\n{'='*60}")
        print(f"Scheduled run started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        track_all_products()
        run_price_analysis()
        
        print(f"\n{'='*60}")
        print(f"Scheduled run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"Error during scheduled run: {e}")
        import traceback
        traceback.print_exc()

def schedule_daily(hour=9, minute=0):
    """Schedule daily runs at a specific time"""
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_price_tracker)
    print(f"Scheduled daily runs at {hour:02d}:{minute:02d}")

def schedule_hourly():
    """Schedule hourly runs"""
    schedule.every().hour.do(run_price_tracker)
    print("Scheduled hourly runs")

def schedule_every_n_hours(n):
    """Schedule runs every N hours"""
    schedule.every(n).hours.do(run_price_tracker)
    print(f"Scheduled runs every {n} hours")

def schedule_every_n_minutes(n):
    """Schedule runs every N minutes (for testing)"""
    schedule.every(n).minutes.do(run_price_tracker)
    print(f"Scheduled runs every {n} minutes")

def run_scheduler():
    """Run the scheduler loop"""
    print("Price Tracker Scheduler started...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Price Tracker Scheduler')
    parser.add_argument('--mode', choices=['daily', 'hourly', 'interval'], default='daily',
                        help='Scheduling mode')
    parser.add_argument('--hour', type=int, default=9, help='Hour for daily schedule (0-23)')
    parser.add_argument('--minute', type=int, default=0, help='Minute for daily schedule (0-59)')
    parser.add_argument('--interval', type=int, help='Interval in hours for interval mode')
    parser.add_argument('--test', action='store_true', help='Run every 5 minutes for testing')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    if args.once:
        run_price_tracker()
    elif args.test:
        schedule_every_n_minutes(5)
        run_scheduler()
    elif args.mode == 'daily':
        schedule_daily(args.hour, args.minute)
        run_scheduler()
    elif args.mode == 'hourly':
        schedule_hourly()
        run_scheduler()
    elif args.mode == 'interval':
        if args.interval:
            schedule_every_n_hours(args.interval)
            run_scheduler()
        else:
            print("Error: --interval required for interval mode")
            sys.exit(1)


