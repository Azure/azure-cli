#!/usr/bin/env python

import os
from sys import argv
from azure.cli.main import main as cli

def run(command):
    cli(command.split())

USER = "admin2@azuresdkteam.onmicrosoft.com"
PASS = argv[1] if len(argv) > 1 else None
if not PASS:
    print('Required usage \'python login.py PASSWORD\'')
    exit(1)

run('login -u {} -p {}'.format(USER, PASS))
os.environ.pop('AZURE_STORAGE_CONNECTION_STRING', None)
os.environ.pop('AZURE_STORAGE_ACCOUNT', None)
os.environ.pop('AZURE_STORAGE_KEY', None)
os.environ.pop('AZURE_SAS_TOKEN', None)
exit(0)