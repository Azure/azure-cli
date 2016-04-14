#!/usr/bin/env python

import os
from sys import argv, stdout
from azure.cli.main import main as cli
from six import StringIO

def run(command, file=stdout):
    cli(command.split(), file=file)

RSGRP = "travistestresourcegroup"
STACC = "travistestresourcegr3014"

io = StringIO()
run('storage account connection-string -g {} -n {}'.format(RSGRP, STACC), file=io)
connection_string = io.getvalue().replace('Connection String : ', '')
os.environ['AZURE_STORAGE_CONNECTION_STRING'] = str(connection_string)

print('\n=== Listing storage containers... ===')
run('storage container list', file=io)
print(io.getvalue())

print('\n=== Listing storage shares... ===')
run('storage container list', file=io)
print(io.getvalue())

exit(0)