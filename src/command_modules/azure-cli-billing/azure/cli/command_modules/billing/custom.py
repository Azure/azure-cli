# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.billing.models import ErrorResponseException
from azure.cli.core.util import CLIError

def cli_billing_list_invoices(client, generate_url=False):
    '''List all available invoices of the subscription'''
    try:
        if generate_url:
            invoices = client.list(expand='downloadUrl')
        else:
            invoices = client.list()
        return list(invoices)
    except ErrorResponseException as ex:
        message = ex.error.error.message
        raise CLIError(message)       

def cli_billing_get_invoice(client, name):
    '''Retrieve invioce of specific name of the subscription'''
    try:
        return client.get(name)
    except ErrorResponseException as ex:
        message = ex.error.error.message
        raise CLIError(message)       

def cli_billing_get_billing_period(client, name):
    '''Retrieve billing period of specific name of the subscription'''
    try:
        return client.get(name)
    except ErrorResponseException as ex:
        message = ex.error.error.message
        raise CLIError(message)      
    
def cli_billing_list_billing_periods(client):
    '''List all available billing periods of the subscription'''
    try:
        return list(client.list())
    except ErrorResponseException as ex:
        message = ex.error.error.message
        raise CLIError(message)    