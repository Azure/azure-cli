@echo off
pylint -d I0013 -r n src/azure
python scripts/command_modules/pylint.py