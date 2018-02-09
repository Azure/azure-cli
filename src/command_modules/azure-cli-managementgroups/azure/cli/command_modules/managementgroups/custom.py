# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
def _register_rp(cli_ctx, subscription_id=None):
    rp = "Microsoft.Management"
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    import time
    rcf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, subscription_id)
    rcf.providers.register(rp)
    while True:
        time.sleep(10)
        rp_info = rcf.providers.get(rp)
        if rp_info.registration_state == 'Registered':
            break


def cli_managementgroups_group_list(cmd, client):
    _register_rp(cmd.cli_ctx)
    return client.list()

def cli_managementgroups_group_get(cmd, client, group_name, expand=False, recurse=False):
    _register_rp(cmd.cli_ctx)
    if expand:
        return client.get(group_name, "children", recurse)
    else:
        return client.get(group_name)

def cli_managementgroups_group_new(cmd, client, group_name, display_name=None, parent_id=None):
    _register_rp(cmd.cli_ctx)
    return client.create_or_update(group_name, "no-cache", display_name, parent_id)


def cli_managementgroups_group_update(cmd, client, group_name, display_name=None, parent_id=None):
    _register_rp(cmd.cli_ctx)
    return client.update(group_name, "no-cache", display_name, parent_id)

def cli_managementgroups_group_remove(cmd, client, group_name):
    _register_rp(cmd.cli_ctx)
    return client.delete(group_name)

def cli_managementgroups_subscription_new(cmd, client, group_name, subscription_id):
    _register_rp(cmd.cli_ctx)
    _register_rp(cmd.cli_ctx, subscription_id)
    return client.create(group_name, subscription_id)

def cli_managementgroups_subscription_remove(cmd, client, group_name, subscription_id):
    _register_rp(cmd.cli_ctx)
    _register_rp(cmd.cli_ctx, subscription_id)
    return client.delete(group_name, subscription_id)
