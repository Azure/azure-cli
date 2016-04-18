#!/usr/bin/env python

from __future__ import print_function

import os
from subprocess import check_output
from sys import argv, stdout

RSGRP = "travistestresourcegroup"
STACC = "travistestresourcegr3014"

def cmd(command):
    """ Accepts a command line command as a string and returns stdout in UTF-8 format """
    if os.name == 'nt':
        command = command.replace('az', 'az.bat')
    return check_output([str(x) for x in command.split()]).decode('utf-8')

def set_env(key, val):
    """ set environment variable """
    os.environ[key] = val

def pop_env(key):
    """ pop environment variable or None """
    return os.environ.pop(key, None)

# get storage account connection string
out = cmd('az storage account connection-string -g {} -n {}'.format(RSGRP, STACC))
connection_string = out.replace('Connection String : ', '')
set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

sas_token = cmd('az storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2017-01-01T00:00Z'
          .format(connection_string)).strip()
pop_env('AZURE_STORAGE_CONNECTION_STRING')
set_env('AZURE_STORAGE_ACCOUNT', STACC)
set_env('AZURE_SAS_TOKEN', sas_token)

print('\n=== Listing storage containers...===')
print(cmd('az storage container list'))

print('\n=== Trying to list storage shares *SHOULD FAIL*... ===')
print('az storage container list --sas-token \"{}\"'.format(sas_token))
print(cmd('az storage share list'))

exit(0)