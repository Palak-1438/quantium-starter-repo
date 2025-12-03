#!/usr/bin/env bash

# Stop script on errors
set -e

# Activate virtual environment
# Supports Windows Git Bash and Linux/Mac
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found."
    exit 1
fi

echo "✔ Virtual environment activated."

# Run the test suite
echo "▶ Running test suite..."
python -m pytest

# Capture exit code
TEST_STATUS=$?

if [ $TEST_STATUS -eq 0 ]; then
    echo "✔ All tests passed!"
    exit 0
else
    echo "❌ Tests failed!"
    exit 1
fi
