# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list,
    enum_choice_list,
    name_type,
    ignore_type)
from azure.cli.core.commands import register_cli_argument
import azure.cli.core.commands.arm # pylint: disable=unused-import
from azure.mgmt.documentdb.models.document_db_enums import KeyKind
from azure.mgmt.documentdb.models.document_db_enums import DefaultConsistencyLevel
from azure.mgmt.documentdb.models.document_db_enums import DatabaseAccountKind
from azure.mgmt.documentdb.models.failover_policy import FailoverPolicy
from azure.mgmt.documentdb.models.location import Location


def validate_failover_policies(ns):
    ''' Extracts multiple space-separated failoverPolicies in regionName=failoverPriority format '''
    fp_dict = []
    for item in ns.failover_policies:
        comps = item.split('=', 1)
        fp_dict.append(FailoverPolicy(comps[0], int(comps[1])))
    ns.failover_policies = fp_dict

def validate_locations(ns):
    ''' Extracts multiple space-separated locations in regionName=failoverPriority format '''
    if ns.locations is None:
        ns.locations = []
        return
    loc_dict = []
    for item in ns.locations:
        comps = item.split('=', 1)
        loc_dict.append(Location(location_name=comps[0], failover_priority=int(comps[1])))
    ns.locations = loc_dict

def validate_ip_range_filter(ns):
    if ns.ip_range_filter:
        ns.ip_range_filter = ",".join(ns.ip_range_filter)

register_cli_argument('documentdb', 'account_name', arg_type=name_type, help='Name of the DocumentDB database account', completer=get_resource_name_completion_list('Microsoft.DocumentDb/databaseAccounts'), id_part="name")

register_cli_argument('documentdb regenerate-key', 'key_kind', **enum_choice_list(KeyKind))
register_cli_argument('documentdb failover-priority-change', 'failover_policies', validator=validate_failover_policies, help="space separated failover policies in 'regionName=failoverPriority' format. E.g \"East US\"=0 \"West US\"=1", nargs='+')
register_cli_argument('documentdb create', 'account_name', completer=None)
register_cli_argument('documentdb create', 'resource_group_name', help="name of the resource group")
register_cli_argument('documentdb create', 'resource_group_location', ignore_type)
register_cli_argument('documentdb create', 'locations', validator=validate_locations, help="space separated locations in 'regionName=failoverPriority' format. E.g \"East US\"=0 \"West US\"=1. Failover priority values are 0 for write regions and greater than 0 for read regions. A failover priority value must be unique and less than the total number of regions. Default: single region account in the location of the specified resource group.", nargs='+')
register_cli_argument('documentdb create', 'default_consistency_level', help="default consistency level of the DocumentDB database account", **enum_choice_list(DefaultConsistencyLevel))
register_cli_argument('documentdb create', 'max_staleness_prefix', help="when used with Bounded Staleness consistency, this value represents the number of stale requests tolerated. Accepted range for this value is 1 - 2,147,483,647", type=int)
register_cli_argument('documentdb create', 'max_interval', help="when used with Bounded Staleness consistency, this value represents the time amount of staleness (in seconds) tolerated. Accepted range for this value is 1 - 100", type=int)
register_cli_argument('documentdb create', 'ip_range_filter', validator=validate_ip_range_filter, help="firewall support. Specifies the set of IP addresses or IP address ranges in CIDR form to be included as the allowed list of client IPs for a given database account. IP addresses/ranges must be comma separated and must not contain any spaces", nargs='+')
register_cli_argument('documentdb create', 'kind', help='The type of DocumentDB database account to create', **enum_choice_list(DatabaseAccountKind))

register_cli_argument('documentdb update', 'account_name', completer=None)
register_cli_argument('documentdb update', 'resource_group_name', help="name of the resource group")
register_cli_argument('documentdb update', 'locations', validator=validate_locations, help="space separated locations in 'regionName=failoverPriority' format. E.g \"East US\"=0. Failover priority values are 0 for write regions and greater than 0 for read regions. A failover priority value must be unique and less than the total number of regions.", nargs='+')
register_cli_argument('documentdb update', 'default_consistency_level', help="default consistency level of the DocumentDB database account", **enum_choice_list(DefaultConsistencyLevel))
register_cli_argument('documentdb update', 'max_staleness_prefix', help="when used with Bounded Staleness consistency, this value represents the number of stale requests tolerated. Accepted range for this value is 1 - 2,147,483,647", type=int)
register_cli_argument('documentdb update', 'max_interval', help="when used with Bounded Staleness consistency, this value represents the time amount of staleness (in seconds) tolerated. Accepted range for this value is 1 - 100", type=int)
register_cli_argument('documentdb update', 'ip_range_filter', validator=validate_ip_range_filter, help="firewall support. Specifies the set of IP addresses or IP address ranges in CIDR form to be included as the allowed list of client IPs for a given database account. IP addresses/ranges must be comma separated and must not contain any spaces", nargs='+')
