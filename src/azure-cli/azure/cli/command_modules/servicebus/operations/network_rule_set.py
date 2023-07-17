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

def add_network_rule_set_ip_rule(cmd, resource_group_name, namespace_name, ip_rule=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Show
    from azure.cli.core import CLIError
    servicebus_ip_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    ip_rule_list = []
    for i in servicebus_ip_rule["ipRules"]:
        ip_dict = {
            "ip_address": i["ipMask"],
            "action": i["action"]
        }
        ip_rule_list.append(ip_dict)
    for i in ip_rule:
        rule = {
            "ip_address": i["ip-address"],
            "action": i["action"]
        }
        if rule not in ip_rule_list:
            ip_rule_list.append(rule)
        else:
            raise CLIError('Duplicate Ip-rules Found.')
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "ip_rules": ip_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def remove_network_rule_set_ip_rule(cmd, resource_group_name, namespace_name, ip_rule=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Show
    servicebus_ip_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    ip_rule_list = []
    for i in servicebus_ip_rule["ipRules"]:
        ip_rule_dict = {
            "ip_address": i["ipMask"],
            "action": i["action"]
        }
        ip_rule_list.append(ip_rule_dict)

    for i in ip_rule:
        for j in ip_rule_list[:]:
            if i['ip-address'] == j["ip_address"]:
                ip_rule_list.remove(j)
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "ip_rules": ip_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def add_virtual_network_rule(cmd, resource_group_name, namespace_name, subnet=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Show
    from azure.cli.core import CLIError
    servicebus_nw_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    virtual_network_rule_list = []
    for i in servicebus_nw_rule["virtualNetworkRules"]:
        subnet_dict = {
            "subnet": i["subnet"]["id"],
            "ignore_missing_endpoint": i["ignoreMissingVnetServiceEndpoint"]
        }
        virtual_network_rule_list.append(subnet_dict)
    for i in subnet:
        rule = {
            "subnet": i["id"],
            "ignore_missing_endpoint": i["ignore_missing_endpoint"]
        }
        if rule not in virtual_network_rule_list:
            virtual_network_rule_list.append(rule)
        else:
            raise CLIError('Duplicate Subnet-rules Found.')
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "virtual_network_rules": virtual_network_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def remove_virtual_network_rule(cmd, resource_group_name, namespace_name, subnet=None):

    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.network_rule_set import Show
    servicebus_nw_rule = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    virtual_network_rule_list = []
    for i in servicebus_nw_rule["virtualNetworkRules"]:
        subnet_dict = {
            "subnet": i["subnet"]["id"],
            "ignore_missing_endpoint": i["ignoreMissingVnetServiceEndpoint"]
        }
        virtual_network_rule_list.append(subnet_dict)

    for i in subnet:
        for j in virtual_network_rule_list[:]:
            if i['id'].lower() == j['subnet'].lower():
                virtual_network_rule_list.remove(j)
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "virtual_network_rules": virtual_network_rule_list
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)
