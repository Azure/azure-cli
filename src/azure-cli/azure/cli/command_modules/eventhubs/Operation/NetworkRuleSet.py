# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=unused-variable
# pylint: disable=too-many-locals
# pylint: disable=too-many-return-statements

def add_network_rule_set_ip_rule(cmd, resource_group_name, namespace_name, ip_address, action='Allow'):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Show

    eventhubs_ip_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    ip_rule_list = []
    for i in eventhubs_ip_rule["ipRules"]:
        ip_dict = {
            "ip_mask": i["ipMask"],
            "action": i["action"]
        }
        ip_rule_list.append(ip_dict)

    ip_rule_list.append({
        "ip_mask": ip_address,
        "action": action
    })
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "ip_rules": ip_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def remove_network_rule_set_ip_rule(cmd, resource_group_name, namespace_name, ip_address):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Show
    eventhubs_ip_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    ip_rule_list = []
    for i in eventhubs_ip_rule["ipRules"]:
        ip_rule_dict = {
            "ip_mask": i["ipMask"],
            "action": i["action"]
        }
        ip_rule_list.append(ip_rule_dict)

    for i in ip_rule_list:
        if i['ip_mask'] == ip_address:
            ip_rule_list.remove(i)
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "ip_rules": ip_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def add_virtual_network_rule(cmd, resource_group_name, namespace_name, subnet=None,
                             vnet_name=None, ignore_missing_endpoint=False):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Show
    eventhubs_nw_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    virtual_network_rule_list = []
    for i in eventhubs_nw_rule["virtualNetworkRules"]:
        subnet_dict = {
            "subnet": i["subnet"]["id"],
            "ignore_missing_endpoint": i["ignoreMissingVnetServiceEndpoint"]
        }
        virtual_network_rule_list.append(subnet_dict)

    virtual_network_rule_list.append({
        "subnet": subnet,
        "ignore_missing_endpoint": ignore_missing_endpoint
    })
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "virtual_network_rules": virtual_network_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def remove_virtual_network_rule(cmd, resource_group_name, namespace_name, subnet, vnet_name=None):

    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace.network_rule_set import Show
    eventhubs_nw_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    virtual_network_rule_list = []
    for i in eventhubs_nw_rule["virtualNetworkRules"]:
        subnet_dict = {
            "subnet": i["subnet"]["id"],
            "ignore_missing_endpoint": i["ignoreMissingVnetServiceEndpoint"]
        }
        virtual_network_rule_list.append(subnet_dict)

    for i in virtual_network_rule_list:
        if i['subnet'].lower() == subnet.lower():
            virtual_network_rule_list.remove(i)
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "virtual_network_rules": virtual_network_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)