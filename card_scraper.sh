#!/bin/bash
SCRIPT_DIRECTORY="$HOME/card_scraper"
PYTHON_FILE="card_scraper.py"
PYTHON_RUN_PATH=$(which python3)
LOG_FILE="$SCRIPT_DIRECTORY/logs/output.log"

cd "$SCRIPT_DIRECTORY"
"$PYTHON_RUN_PATH" "$PYTHON_FILE" >> "$LOG_FILE" 2>&1