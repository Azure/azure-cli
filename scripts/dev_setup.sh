#! /bin/bash
set -e
echo "Running dev setup..."
echo "Executing: pip install -r requirements.txt"
pip install -r requirements.txt
echo "Executing: pip install -e ."
pip install -e .
echo "python scripts/command_modules/install.py"
python scripts/command_modules/install.py 
