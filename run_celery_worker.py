"""
Script to run Celery worker
Usage: python run_celery_worker.py
"""
import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("Starting Celery worker...")
    print("Make sure Redis is running on localhost:6379")
    
    # Start Celery worker
    subprocess.run([
        'celery', '-A', 'app.tasks:celery_app', 'worker',
        '--loglevel=info',
        '--concurrency=4'  # Number of worker processes
    ])
