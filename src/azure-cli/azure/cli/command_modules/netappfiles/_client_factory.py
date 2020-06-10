# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument


def cf_netappfiles(cli_ctx, *kwargs):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.netapp import AzureNetAppFilesManagementClient
    return get_mgmt_service_client(cli_ctx, AzureNetAppFilesManagementClient)


def accounts_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).accounts


def pools_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).pools


def volumes_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).volumes


def mount_targets_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).mount_targets


def snapshots_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).snapshots
