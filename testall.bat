@echo off
python scripts/command_modules/pylint.py
python -m unittest discover -s src/azure/cli/tests
python scripts/command_modules/test.py