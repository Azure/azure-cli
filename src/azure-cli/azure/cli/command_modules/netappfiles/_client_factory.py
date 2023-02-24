# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument


def cf_netappfiles(cli_ctx, *kwargs):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.netapp import NetAppManagementClient
    return get_mgmt_service_client(cli_ctx, NetAppManagementClient)


def accounts_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).accounts


def pools_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).pools


def volumes_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).volumes


def snapshots_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).snapshots


def snapshot_policies_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).snapshot_policies


def account_backups_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).account_backups


def backups_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).backups


def backup_policies_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).backup_policies


def vaults_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).vaults


def subvolumes_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).subvolumes


def volume_groups_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).volume_groups


def netapp_resource_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).net_app_resource


def volume_quota_rules_mgmt_client_factory(cli_ctx, _):
    return cf_netappfiles(cli_ctx).volume_quota_rules
