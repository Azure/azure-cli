#!/usr/bin/env python

from __future__ import print_function
from azure.cli.utils.command_test_util import cmd, set_env, pop_env

def test_script():
    RSGRP = "travistestresourcegroup"
    STACC = "travistestresourcegr3014"

    # get storage account connection string
    out = cmd('storage account connection-string -g {} -n {}'.format(RSGRP, STACC))
    connection_string = out.replace('Connection String : ', '')
    set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

    sas_token = cmd('storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2017-01-01T00:00Z'
              .format(connection_string)).strip()
    pop_env('AZURE_STORAGE_CONNECTION_STRING')
    set_env('AZURE_STORAGE_ACCOUNT', STACC)
    set_env('AZURE_SAS_TOKEN', sas_token)

    print('\n=== Listing storage containers...===')
    print(cmd('storage container list'))

    print('\n=== Trying to list storage shares *SHOULD FAIL*... ===')
    print('storage container list --sas-token \"{}\"'.format(sas_token))
    print(cmd('storage share list'))

test_script()
exit(0)