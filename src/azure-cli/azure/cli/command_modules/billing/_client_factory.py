# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_billing(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.billing import BillingManagementClient
    return get_mgmt_service_client(cli_ctx, BillingManagementClient)


def invoices_mgmt_client_factory(cli_ctx, kwargs):
    return cf_billing(cli_ctx, **kwargs).invoices


def enrollment_accounts_mgmt_client_factory(cli_ctx, kwargs):
    return cf_billing(cli_ctx, **kwargs).enrollment_accounts
