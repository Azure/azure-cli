# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def dms_client_factory(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.datamigration import DataMigrationManagementClient
    return get_mgmt_service_client(cli_ctx, DataMigrationManagementClient)


def dms_cf_services(cli_ctx, *_):
    return dms_client_factory(cli_ctx).services


def dms_cf_skus(cli_ctx, *_):
    return dms_client_factory(cli_ctx).resource_skus


def dms_cf_projects(cli_ctx, *_):
    return dms_client_factory(cli_ctx).projects


def dms_cf_tasks(cli_ctx, *_):
    return dms_client_factory(cli_ctx).tasks


def get_resource_groups_client(cli_ctx, subscription_id=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   subscription_id=subscription_id).resource_groups
