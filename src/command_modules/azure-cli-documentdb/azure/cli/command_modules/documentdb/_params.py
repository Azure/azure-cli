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
from azure.cli.command_modules.documentdb.sdk.models.document_db_enums import DefaultConsistencyLevel
from azure.cli.command_modules.documentdb.sdk.models.failover_policy import FailoverPolicy
from azure.cli.command_modules.documentdb.sdk.models.location import Location
from azure.cli.command_modules.documentdb.sdk.models.location import Location


def validate_failover_policies(ns):
    ''' Extracts multiple space-separated failoverPolcies in region=failoverPriority format '''
    fp_dict = []
    for item in ns.failover_policies:
        comps = item.split('=', 1)
        fp_dict.append(FailoverPolicy(comps[0], int(comps[1])))
    ns.failover_policies = fp_dict
    return ns

def validate_locations(ns):
    ''' Extracts multiple space-separated locations in regionName=failoverPriority format '''
    loc_dict = []
    for item in ns.locations:
        comps = item.split('=', 1)
        loc_dict.append(Location(location_name=comps[0], failover_priority=int(comps[1])))
    ns.locations = loc_dict
    return ns

register_cli_argument('documentdb', 'account_name', arg_type=name_type, help='Name of the DocumentDB Database Account', completer=get_resource_name_completion_list('Microsoft.DocumentDb/databaseAccounts'), id_part="name")

register_cli_argument('documentdb regenerate-key', 'key_kind', **enum_choice_list(KeyKind))
register_cli_argument('documentdb failover-priority-change', 'failover_policies', validator=validate_failover_policies, help="space separated failover policies in 'regionName=failoverPriority' format. E.g \"East US\"=0", nargs='+')

register_cli_argument('documentdb create', 'resource_group_location', help="location of the resource group")
register_cli_argument('documentdb create', 'locations', validator=validate_locations, help="space separated locations in 'regionName=failoverPriority' format. E.g \"East US\"=0", nargs='+')
register_cli_argument('documentdb create', 'default_consistency_level', help="default consistency level", **enum_choice_list(DefaultConsistencyLevel))
register_cli_argument('documentdb create', 'resource_group_location', help="location of the resource group")
register_cli_argument('documentdb create', 'max_staleness_prefix', help="maximum staleness prefix", type=int)
register_cli_argument('documentdb create', 'max_interval_in_seconds', help="max_interval_in_seconds", type=int)
register_cli_argument('documentdb create', 'ip_range_filter', help="IP Range Filter")
