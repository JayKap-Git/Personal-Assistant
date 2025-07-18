#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start activity analyzer in the background
python3 activity_analyzer.py &
ACTIVITY_PID=$!
echo "Started activity_analyzer.py with PID $ACTIVITY_PID"

# Start PA Buddy UI
python3 pa_buddy_ui.py

# When PA Buddy UI exits, kill the activity analyzer
kill $ACTIVITY_PID 
