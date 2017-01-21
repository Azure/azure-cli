# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list,
    enum_choice_list,
    name_type)
from azure.cli.core.commands import register_cli_argument
import azure.cli.core.commands.arm # pylint: disable=unused-import
from azure.cli.core.commands import CliArgumentType
from azure.cli.command_modules.documentdb.sdk.models.document_db_enums import KeyKind
from azure.cli.command_modules.documentdb.sdk.models.failover_policy import FailoverPolicy


def validate_failover_policies(ns):
    ''' Extracts multiple space-separated failoverPolcies in region=failoverPriority format '''
    tags_dict = []
    for item in ns.failover_policies:
        print(item)
        comps = item.split('=', 1)
        tags_dict.append(FailoverPolicy(comps[0], int(comps[1])))
    ns.failover_policies = tags_dict
    return ns


register_cli_argument('documentdb', 'account_name', arg_type=name_type, help='name of the DocumentDB Database Account', completer=get_resource_name_completion_list('Microsoft.DocumentDb/databaseAccounts'), id_part="name")

register_cli_argument('documentdb regenerate-key', 'key_kind', **enum_choice_list(KeyKind))
register_cli_argument('documentdb failover-priority-change', 'failover_policies', validator=validate_failover_policies, help="space separated failover policies in 'region=failoverPriority' format. E.g \"East US\"=0", nargs='+')
# register_cli_argument('documentdb create', )