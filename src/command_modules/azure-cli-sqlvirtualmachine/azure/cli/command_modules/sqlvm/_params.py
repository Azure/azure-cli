# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=too-many-lines

import itertools
from enum import Enum

from knack.arguments import CLIArgumentType, ignore_type

from azure.mgmt.sqlvirtualmachine.models import (
    SqlVirtualMachine,
    SqlVirtualMachineGroup,
    AvailabilityGroupListener
)

from azure.cli.core.commands.parameters import (
    get_three_state_flag,
    get_enum_type,
    get_resource_name_completion_list,
    get_location_type,
    tags_type
)


# pylint: disable=too-many-statements
def load_arguments(self, _):

    for scope in ['sqlvm', 'sqlvm group']:
        with self.argument_context(scope) as c:
            c.argument('tags', tags_type)

    with self.argument_context('sqlvm') as c:
        c.argument('sql_virtual_machine_name',
                   options_list=['--name', '-n'])

    with self.argument_context('sqlvm group') as c:
        c.argument('sql_virtual_machine_group_name',
                   options_list=['--name', '-n'])

    with self.argument_context('sqlvm aglistener') as c:
        c.argument('availability_group_listener_name',
                    options_list=['--name', '-n'])
        c.argument('sql_virtual_machine_group_name',
                    options_list=['--group-name, -gn'])

    with self.argument_context('sqlvm group create', arg_group='WSFC Domain Profile') as c:
        c.argument('domain_fqdn',
                    help='Fully qualified name of the domain.')
        c.argument('cluster_operator_account',
                    help='Account name used for operating cluster i.e. will be part of administrators group on all the participating virtual machines in the cluster.')
        c.argument('sql_service_account',
                    help='Account name under which SQL service will run on all participating SQL virtual machines in the cluster.')
        c.argument('storage_account_url',
                    help='Fully qualified ARM resource id of the witness storage account.')
        c.argument('storage_account_key',
                    help='Primary key of the witness storage account.')
        c.argument('cluster_bootstrap_account',
                    help='Account name used for creating cluster (at minimum needs permissions to \'Create Computer Objects\' in domain).')
        c.argument('file_share_witness_path',
                    help='Optional path for fileshare witness.')
        c.argument('ou_path',
                    help='OU path in which the nodes and cluster will be present.')

    with self.argument_context('sqlvm aglistener create', arg_group='Load Balancer Configuration') as c:
        c.argument('ip_address',
                    help='Private IP address bound to the availability group listener.')
        c.argument('subnet_resource_id',
                    help='Subnet used to include private IP.')
        c.argument('public_ip_address_resource_id',
                    help='Resource id of the public IP.')
        c.argument('load_balancer_resource_id',
                    help='Subnet used to include private IP.')
        c.argument('probe_port',
                    help='Probe port.')
        c.argument('sql_virtual_machine_instances',
                    help='List of the SQL virtual machine instance resource id\'s that are enrolled into the availability group listener.')

