@echo off
cls
python -m unittest discover -s src/azure/cli/tests --buffer
python scripts/command_modules/test.py