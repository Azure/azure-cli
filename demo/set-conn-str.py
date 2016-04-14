#!/usr/bin/env python

from __future__ import print_function

import os
from subprocess import check_output
from sys import argv, stdout

RSGRP = "travistestresourcegroup"
STACC = "travistestresourcegr3014"

def run(command):
    command = command.replace('az ', '', 1)
    cmd = 'python -m azure.cli {}'.format(command)
    print(cmd)
    out = check_output(cmd)
    return str(out)

out = run('az storage account connection-string -g {} -n {}'.format(RSGRP, STACC))
connection_string = out.replace('Connection String : ', '')
os.environ['AZURE_STORAGE_CONNECTION_STRING'] = str(connection_string)

print('\n=== Listing storage containers... ===')
print(run('az storage container list'))

print('\n=== Listing storage shares... ===')
print(run('az storage container list'))

exit(0)