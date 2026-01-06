#!/bin/bash
# Shell script to set up cron job for price tracker (Linux/Mac)
# This script adds a cron job that runs the price tracker daily at 9 AM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/scheduler.py"
PYTHON_PATH=$(which python3)

if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(which python)
fi

if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: scheduler.py not found at $PYTHON_SCRIPT"
    exit 1
fi

# Create cron job entry (daily at 9 AM)
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH $PYTHON_SCRIPT --once >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -v "$PYTHON_SCRIPT" > /tmp/cron_temp) || true

# Add new cron job
echo "$CRON_JOB" >> /tmp/cron_temp

# Install new cron job
crontab /tmp/cron_temp
rm /tmp/cron_temp

echo "Cron job configured successfully!"
echo "Schedule: Daily at 9:00 AM"
echo "Log file: $SCRIPT_DIR/logs/cron.log"
echo ""
echo "To view cron jobs, run: crontab -l"
echo "To remove this cron job, run: crontab -e (then delete the line)"





