"""
Background service for continuous price tracking
Can run as a Windows service or Linux daemon
"""
import time
import sys
import os
from datetime import datetime
from scheduler import run_price_tracker, schedule_every_n_hours

def run_background_service(interval_hours=6):
    """Run as a background service with specified interval"""
    print(f"Starting background price tracker service...")
    print(f"Checking prices every {interval_hours} hours")
    print(f"Service started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to stop the service\n")
    
    # Schedule the task
    schedule_every_n_hours(interval_hours)
    
    try:
        while True:
            # Run pending scheduled tasks
            import schedule
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nService stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error in background service: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Background Price Tracker Service')
    parser.add_argument('--interval', type=int, default=6,
                        help='Check interval in hours (default: 6)')
    
    args = parser.parse_args()
    run_background_service(args.interval)



