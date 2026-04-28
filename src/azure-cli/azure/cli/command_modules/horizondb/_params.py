# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_location_type,
    tags_type,
    get_enum_type)
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction


def load_arguments(self, _):    # pylint: disable=too-many-statements, too-many-locals

    # HorizonDB
    # pylint: disable=too-many-locals, too-many-branches
    def _horizondb_params():

        yes_arg_type = CLIArgumentType(
            options_list=['--yes', '-y'],
            action='store_true',
            help='Do not prompt for confirmation.'
        )

        cluster_name_arg_type = CLIArgumentType(
            metavar='NAME',
            options_list=['--name', '-n'],
            id_part='name',
            help="Name of the cluster. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
            local_context_attribute=LocalContextAttribute(
                name='cluster_name',
                actions=[LocalContextAction.SET, LocalContextAction.GET],
                scopes=['horizondb']))

        administrator_login_arg_type = CLIArgumentType(
            options_list=['--admin-user', '-u'],
            help='The administrator login name for the cluster.')

        administrator_login_password_arg_type = CLIArgumentType(
            options_list=['--admin-password', '-p'],
            help='The administrator login password.')

        version_arg_type = CLIArgumentType(
            options_list=['--version', '-v'],
            help='The version of the HorizonDb cluster.')

        replica_count_arg_type = CLIArgumentType(
            options_list=['--replica-count'],
            type=int,
            help='Number of replicas.')

        v_cores_arg_type = CLIArgumentType(
            options_list=['--v-cores'],
            type=int,
            help='Number of vCores.')

        zone_placement_policy_arg_type = CLIArgumentType(
            options_list=['--zone-placement-policy'],
            arg_type=get_enum_type(['Strict', 'BestEffort']),
            help='Defines how replicas are placed across availability zones.')

        with self.argument_context('horizondb') as c:
            c.argument('resource_group_name', arg_type=resource_group_name_type)
            c.argument('cluster_name', arg_type=cluster_name_arg_type)

        with self.argument_context('horizondb create') as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx))
            c.argument('tags', tags_type)
            c.argument('administrator_login', arg_type=administrator_login_arg_type)
            c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
            c.argument('version', arg_type=version_arg_type)
            c.argument('replica_count', arg_type=replica_count_arg_type)
            c.argument('v_cores', arg_type=v_cores_arg_type)
            c.argument('zone_placement_policy', arg_type=zone_placement_policy_arg_type)

        with self.argument_context('horizondb delete') as c:
            c.argument('yes', arg_type=yes_arg_type)

    _horizondb_params()
