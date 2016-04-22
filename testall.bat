@echo off
cls
python -m unittest discover -s src/azure/cli/tests
python scripts/command_modules/test.py