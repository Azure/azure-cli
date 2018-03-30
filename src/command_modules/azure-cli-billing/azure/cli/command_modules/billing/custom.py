# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cli_billing_list_invoices(client, generate_url=False):
    """List all available invoices of the subscription"""
    return client.list(expand='downloadUrl' if generate_url else None)


def cli_billing_get_invoice(client, name=None):
    """Retrieve invoice of specific name of the subscription"""
    if name:
        return client.get(name)
    return client.get_latest()
