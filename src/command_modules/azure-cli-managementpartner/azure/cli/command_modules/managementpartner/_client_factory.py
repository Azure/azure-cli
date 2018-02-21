# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_managementpartner(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.managementpartner.ace_provisioning_management_partner_api import ACEProvisioningManagementPartnerAPI
    return get_mgmt_service_client(cli_ctx, ACEProvisioningManagementPartnerAPI, subscription_bound=False)


def managementpartner_partner_client_factory(cli_ctx, kwargs):
    return cf_managementpartner(cli_ctx, **kwargs).partner
