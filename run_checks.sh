#!/bin/bash

echo "Nexhan Nova (Don) Self-Check Runner"
echo "=================================="

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Activated virtual environment"
else
    echo "Virtual environment not found, using system Python"
fi

# Run self-check
echo "Running self-check..."
python -c "from don.self_check import run_self_check_and_report; run_self_check_and_report()"

echo ""
echo "Self-check completed."