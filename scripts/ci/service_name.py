#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""
Check format of service_name.json. Command and AzureServiceName are required. Others are optional.
Each highest level command group should have reference in service_name.json.
"""
import json

from azure.cli.core import MainCommandsLoader, AzCli
from azure.cli.core._help import AzCliHelp
from azure.cli.core.commands import AzCliCommandInvoker
from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args, get_all_help
from azure.cli.core.parser import AzCliCommandParser


def main():
    az_cli = AzCli(cli_name='az',
                   commands_loader_cls=MainCommandsLoader,
                   invocation_cls=AzCliCommandInvoker,
                   parser_cls=AzCliCommandParser,
                   help_cls=AzCliHelp)
    create_invoker_and_load_cmds_and_args(az_cli)
    help_files = get_all_help(az_cli)
    high_command_set = set()
    for help_file in help_files:
        if help_file.command:
            high_command_set.add(help_file.command.split()[0])
    print('high_command_set:')
    print(high_command_set)

    # Load and check service_name.json
    with open('src/azure-cli/service_name.json') as f:
        service_names = json.load(f)
    print('Verifying src/azure-cli/service_name.json')
    service_name_map = {}
    for service_name in service_names:
        command = service_name['Command']
        service = service_name['AzureServiceName']
        if not command.startswith('az '):
            raise Exception('{} does not start with az!'.format(command))
        if not service:
            raise Exception('AzureServiceName of {} is empty!'.format(command))
        service_name_map[command[3:]] = service
    print('service_name_map:')
    print(service_name_map)

    # Check existence in service_name.json
    for high_command in high_command_set:
        if high_command not in service_name_map:
            raise Exception('No entry of {} in service_name.json. Please add one to the file.'.format(high_command))


if __name__ == "__main__":
    main()
