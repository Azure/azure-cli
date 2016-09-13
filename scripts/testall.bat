@echo off
cls
python -m unittest discover -s src/azure-cli/azure/cli/tests --buffer
python -m unittest discover -s src/azure-cli-core/azure/cli/core/tests --buffer
python scripts/command_modules/test.py