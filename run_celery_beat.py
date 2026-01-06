"""
Script to run Celery Beat scheduler
Usage: python run_celery_beat.py
"""
import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("Starting Celery Beat scheduler...")
    print("Make sure Redis is running on localhost:6379")
    
    # Start Celery Beat
    subprocess.run([
        'celery', '-A', 'app.tasks:celery_app', 'beat',
        '--loglevel=info'
    ])
