# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import pkgutil

import argparse
import os
import sys
import json
import yaml
from importlib import import_module

from automation.utilities.path import filter_user_selected_modules_with_tests
from azure.cli.core.application import APPLICATION, Application
from azure.cli.core.application import Configuration
from azure.cli.core.commands import load_params, _update_command_definitions
from azure.cli.core.help_files import helps


WHITE_LIST_COMMANDS = [
    "network dns record-set ns update",
    "network dns record-set srv update",
    "network nsg update",
    "network dns record-set aaaa update",
    "acs wait",
    "network local-gateway wait",
    "network dns record-set ptr update",
    "network dns record-set mx update",
    "network express-route wait",
    "network dns record-set a update"
]

WHITE_LIST_PARAMETERS = {
    "network route-filter rule create": [
        "communities"
    ],
    "network lb inbound-nat-pool create": [
        "protocol"
    ],
    "acs install-cli": [
        "install_location",
        "client_version"
    ],
    "network lb inbound-nat-pool update": [
        "protocol"
    ],
    "storage file copy start-batch": [
        "destination_share",
        "source_sas",
        "dryrun",
        "source_uri",
        "pattern",
        "destination_path",
        "source_container",
        "source_account_key",
        "source_account_name",
        "source_share"
    ],
    "cdn endpoint create": [
        "profile_name"
    ],
    "network dns record-set ptr create": [
        "ttl"
    ],
    "dla catalog table list": [
        "database_name",
        "schema_name"
    ],
    "network nsg rule create": [
        "direction",
        "access"
    ],
    "ad sp create-for-rbac": [
        "scopes",
        "name",
        "keyvault",
        "years",
        "cert",
        "role",
        "password",
        "create_cert"
    ],
    "network watcher troubleshooting start": [
        "storage_account",
        "resource_type",
    "storage_path"
    ],
    "dls account create": [
        "default_group",
        "key_vault_id",
        "key_name",
        "key_version"
    ],
    "ad app create": [
        "password"
    ],
    "ad app list": [
        "app_id"
    ],
    "network lb inbound-nat-rule create": [
        "protocol"
    ],
    "storage blob upload-batch": [
        "max_connections"
    ],
    "network lb address-pool delete": [
        "no_wait"
    ],
    "network application-gateway auth-cert update": [
        "cert_data"
    ],
    "vmss create": [
        "image",
        "upgrade_policy_mode",
        "public_ip_address_allocation"
    ],
    "dla job wait": [
        "job_id"
    ],
    "storage metrics update": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "dls fs create": [
        "content"
    ],
    "monitor alert create": [
        "description",
        "actions",
        "disabled",
        "email_service_owners",
        "condition"
    ],
    "network nic ip-config update": [
        "private_ip_address_version"
    ],
    "acs kubernetes browse": [
        "ssh_key_file"
    ],
    "storage logging update": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "redis create": [
        "tags"
    ],
    "network dns record-set mx create": [
        "ttl"
    ],
    "vm encryption enable": [
        "key_encryption_algorithm"
    ],
    "keyvault certificate issuer admin add": [
        "first_name",
        "last_name"
    ],
    "network application-gateway url-path-map update": [
        "no_wait"
    ],
    "resource link create": [
        "link_id"
    ],
    "network lb inbound-nat-pool delete": [
        "no_wait"
    ],
    "dls account firewall create": [
        "start_ip_address",
        "end_ip_address",
        "firewall_rule_name"
    ],
    "network dns record-set ns create": [
        "ttl"
    ],
    "cdn profile create": [
        "sku"
    ],
    "vmss extension set": [
        "vmss_name"
    ],
    "storage cors list": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "network nsg rule update": [
        "direction",
        "access"
    ],
    "storage file list": [
        "exclude_dir"
    ],
    "network watcher flow-log show": [
        "nsg"
    ],
    "network application-gateway auth-cert create": [
        "cert_data"
    ],
    "network watcher configure": [
        "enabled"
    ],
    "network nic ip-config create": [
        "private_ip_address_version"
    ],
    "vm diagnostics get-default-config": [
        "is_windows_os"
    ],
    "storage account check-name": [
        "name"
    ],
    "redis import-method": [
        "files",
        "file_format"
    ],
    "network dns zone create": [
        "if_none_match"
    ],
    "storage metrics show": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "cdn custom-domain create": [
        "name",
        "endpoint_name",
        "hostname",
        "profile_name"
    ],
    "vm availability-set update": [
        "name"
    ],
    "redis export": [
        "prefix",
        "container",
        "file_format"
    ],
    "network traffic-manager endpoint update": [
        "geo_mapping"
    ],
    "resource link update": [
        "link_id"
    ],
    "dla catalog tvf list": [
        "database_name",
        "schema_name"
    ],
    "network dns record-set cname create": [
        "ttl"
    ],
    "appservice web show": [
        "app_instance"
    ],
    "network application-gateway waf-config set": [
        "rule_set_version",
        "disabled_rules",
        "disabled_rule_groups",
        "rule_set_type"
    ],
    "network watcher troubleshooting show": [
        "resource_type"
    ],
    "vmss extension show": [
        "vmss_name"
    ],
    "dla catalog credential create": [
        "credential_name",
        "database_name",
        "uri",
        "credential_user_name"
    ],
    "dls fs access set-owner": [
        "owner",
        "group"
    ],
    "vm availability-set create": [
        "no_wait"
    ],
    "network lb rule delete": [
        "no_wait"
    ],
    "monitor diagnostic-settings create": [
        "target_resource_id",
        "logs",
        "resource_group",
        "namespace",
        "metrics",
        "rule_name",
        "storage_account",
        "workspace"
    ],
    "network lb rule create": [
        "protocol",
        "probe_name"
    ],
    "network application-gateway ssl-cert create": [
        "cert_password"
    ],
    "storage cors add": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "vmss extension list": [
        "vmss_name"
    ],
    "vm unmanaged-disk attach": [
        "size_gb"
    ],
    "vmss extension delete": [
        "vmss_name"
    ],
    "ad sp reset-credentials": [
        "name",
        "keyvault",
        "years",
        "cert",
        "password",
        "create_cert"
    ],
    "network nic update": [
        "enable_ip_forwarding"
    ],
    "network dns record-set a create": [
        "ttl"
    ],
    "network dns record-set aaaa create": [
        "ttl"
    ],
    "network application-gateway frontend-ip create": [
        "subnet"
    ],
    "redis update": [
        "sku"
    ],
    "vm create": [
        "image",
        "public_ip_address_allocation"
    ],
    "functionapp config appsettings set": [
        "slot_settings"
    ],
    "network lb frontend-ip delete": [
        "no_wait"
    ],
    "dla catalog view list": [
        "database_name",
        "schema_name"
    ],
    "acs kubernetes install-cli": [
        "install_location",
        "client_version"
    ],
    "dla job submit": [
        "degree_of_parallelism",
        "job_name",
        "priority",
        "runtime_version"
    ],
    "network watcher test-ip-flow": [
        "direction",
        "protocol",
        "remote",
        "local"
    ],
    "storage file upload-batch": [
        "dryrun",
        "pattern",
        "destination",
        "source",
        "validate_content",
        "max_connections"
    ],
    "network watcher flow-log configure": [
        "enabled",
        "nsg",
        "storage_account",
        "retention"
    ],
    "network dns record-set srv create": [
        "ttl"
    ],
    "dls fs upload": [
        "destination_path",
        "source_path"
    ],
    "monitor alert update": [
        "description",
        "metric",
        "aggregation",
        "period",
        "remove_actions",
        "operator",
        "add_actions",
        "email_service_owners",
        "enabled",
        "condition",
        "threshold"
    ],
    "network application-gateway frontend-ip update": [
        "subnet"
    ],
    "lab vm claim": [
        "lab_name",
        "name"
    ],
    "managedapp definition create": [
        "lock_level"
    ],
    "network application-gateway ssl-cert update": [
        "cert_password"
    ],
    "network vpn-connection create": [
        "routing_weight"
    ],
    "network dns record-set txt create": [
        "ttl"
    ],
    "vm extension image list-versions": [
        "orderby",
        "top"
    ],
    "dla account firewall create": [
        "start_ip_address",
        "end_ip_address",
        "firewall_rule_name"
    ],
    "storage blob copy start-batch": [
        "source_sas",
        "dryrun",
        "destination_container",
        "pattern",
        "source_uri",
        "source_container",
        "source_account_key",
        "source_account_name",
        "source_share"
    ],
    "network nic ip-config delete": [
        "no_wait"
    ],
    "network watcher test-connectivity": [
        "dest_resource",
        "dest_address",
        "source_resource",
        "source_port",
        "dest_port"
    ],
    "network traffic-manager endpoint create": [
        "geo_mapping"
    ],
    "dls fs preview": [
        "length",
        "offset"
    ],
    "storage entity insert": [
        "if_exists",
        "entity",
        "table_name"
    ],
    "dls fs append": [
        "content"
    ],
    "lock create": [
        "level"
    ],
    "dls fs join": [
        "destination_path"
    ],
    "storage file download-batch": [
        "dryrun",
        "pattern",
        "destination",
        "source",
        "validate_content",
        "max_connections"
    ],
    "dla catalog credential update": [
        "credential_name",
        "database_name",
        "uri",
        "credential_user_name"
    ],
    "network application-gateway url-path-map rule create": [
        "no_wait"
    ],
    "acs dcos install-cli": [
        "install_location",
        "client_version"
    ],
    "network lb inbound-nat-rule delete": [
        "no_wait"
    ],
    "lab environment create": [
        "name",
        "parameters",
        "tags",
        "lab_name",
        "arm_template",
        "artifact_source_name"
    ],
    "redis update-settings": [
        "redis_configuration"
    ],
    "dls fs move": [
        "destination_path",
        "source_path"
    ],
    "ad app update": [
        "password"
    ],
    "dla catalog table-stats list": [
        "database_name",
        "table_name",
        "schema_name"
    ],
    "dls account update": [
        "default_group"
    ],
    "network lb create": [
        "subnet_type",
        "public_ip_address_type",
        "public_ip_address_allocation"
    ],
    "lock update": [
        "notes",
        "name",
        "level"
    ],
    "network lb rule update": [
        "protocol",
        "probe_name"
    ],
    "dla account create": [
        "default_data_lake_store",
        "query_store_retention",
        "max_job_count",
        "max_degree_of_parallelism"
    ],
    "storage logging show": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "storage cors clear": [
        "sas_token",
        "account_key",
        "connection_string",
        "account_name"
    ],
    "lab vm create": [
        "image",
        "allow_claim",
        "size",
        "subnet",
        "image_type",
        "authentication_type",
        "lab_name",
        "ip_configuration",
        "formula",
        "saved_secret",
        "admin_password",
        "vnet_name",
        "tags",
        "ssh_key",
        "disk_type",
        "generate_ssh_keys",
        "name",
        "expiration_date",
        "notes",
        "admin_username",
        "artifacts"
    ],
    "network application-gateway waf-config list-rule-sets": [
        "_type",
        "version",
        "group"
    ],
    "network application-gateway update": [
        "capacity"
    ],
    "network lb inbound-nat-rule update": [
        "protocol"
    ],
    "network watcher packet-capture create": [
        "capture_size",
        "time_limit",
        "vm",
        "storage_account",
        "filters",
        "capture_limit",
        "file_path",
        "storage_path"
    ],
    "network lb probe delete": [
        "no_wait"
    ],
    "ad user create": [
        "force_change_password_next_login",
        "password"
    ],
    "vmss diagnostics get-default-config": [
        "is_windows_os"
    ],
    "image create": [
        "os_type"
    ],
    "dls fs download": [
        "destination_path",
        "source_path"
    ],
    "lab arm-template show": [
        "artifact_source_name",
        "lab_name",
        "export_parameters",
        "name"
    ],
    "lab vm list": [
        "all",
        "order_by",
        "claimable",
        "top",
        "object_id",
        "environment",
        "lab_name",
        "filters",
        "expand"
    ]
}

WHITE_LIST_SUBGROUPS = [
    "appservice web config backup",
    "resource link",
    "appservice web deployment slot",
    "webapp config backup",
    "",
    "appservice web config hostname",
    "appservice web deployment user",
    "appservice web config container",
    "appservice web config appsettings",
    "appservice web source-control",
    "appservice web deployment",
    "appservice web config ssl",
    "appservice web log",
    "appservice web config",
    "consumption usage"
]


def dump_no_help(modules):
    APPLICATION.initialize(Configuration())
    cmd_table = APPLICATION.configuration.get_command_table()

    exit_val = 0
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()

    for mod in modules:
        try:
            import_module('azure.cli.command_modules.' + mod).load_params(mod)
        except Exception as ex:
            print("EXCEPTION: " + str(mod))

    _update_command_definitions(cmd_table)

    command_list = []
    subgroups_list = []
    parameters = {}
    for cmd in cmd_table:
        if not cmd_table[cmd].description and cmd not in helps and cmd not in WHITE_LIST_COMMANDS:
            command_list.append(cmd)
            exit_val = 1
        group_name = " ".join(cmd.split()[:-1])
        if group_name not in helps:
            exit_val = 1
            if group_name not in subgroups_list and group_name not in WHITE_LIST_SUBGROUPS:
                subgroups_list.append(group_name)

        param_list = []
        for key in cmd_table[cmd].arguments:
            name = cmd_table[cmd].arguments[key].name
            if not cmd_table[cmd].arguments[key].type.settings.get('help') and \
                    name not in WHITE_LIST_PARAMETERS.get(cmd, []):
                exit_val = 1
                param_list.append(name)
        if param_list:
            parameters[cmd] = param_list

    for cmd in helps:
        diction_help = yaml.load(helps[cmd])
        if "short-summary" in diction_help and "type" in diction_help:
            if diction_help["type"] == "command" and cmd in command_list:
                command_list.remove(cmd)
            elif diction_help["type"] == "group" and cmd in subgroups_list:
                subgroups_list.remove(cmd)
        if "parameters" in diction_help:
            for param in diction_help["parameters"]:
                if "short-summary" in param and param["name"].split()[0] in parameters:
                    parameters.pop(cmd, None)

    data = {
        "subgroups": subgroups_list,
        "commands": command_list,
        "parameters": parameters
    }

    return exit_val, data


if __name__ == '__main__':
    try:
        mods_ns_pkg = import_module('azure.cli.command_modules')
        installed_command_modules = [modname for _, modname, _ in
                                     pkgutil.iter_modules(mods_ns_pkg.__path__)]
    except ImportError:
        pass

    result, failed_commands = dump_no_help(installed_command_modules)

    if failed_commands or result != 0:
        print('==== FAILED COMMANDS ====')
        print(json.dumps(failed_commands, sort_keys=True, indent=4))
    else:
        print('==== ALL COMMANDS PASS! ====')

    sys.exit(result)
