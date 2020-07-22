# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from argcomplete import FilesCompleter
from azure.cli.core.commands.parameters import name_type, tags_type, get_three_state_flag, get_enum_type
from ._validators import validate_storage_account


def load_arguments(self, _):
    # synapse workspace
    for scope in ['show', 'create', 'update', 'delete']:
        with self.argument_context('synapse workspace ' + scope) as c:
            c.argument('workspace_name', arg_type=name_type, id_part='name', help='The workspace name.')

    for scope in ['create', 'update']:
        with self.argument_context('synapse workspace ' + scope) as c:
            c.argument('sql_admin_login_password', options_list=['--sql-admin-login-password', '-p'],
                       help='The sql administrator login password.')
            c.argument('tags', arg_type=tags_type)

    with self.argument_context('synapse workspace create') as c:
        c.argument("storage_account", validator=validate_storage_account,
                   help='The data lake storage account name or resource id.')
        c.argument('file_system', help='The file system of the data lake storage account.')
        c.argument('sql_admin_login_user', options_list=['--sql-admin-login-user', '-u'],
                   help='The sql administrator login user name.')

    with self.argument_context('synapse workspace check-name') as c:
        c.argument('name', arg_type=name_type, help='The name you wanted to check.')

    # synapse spark pool
    with self.argument_context('synapse spark pool') as c:
        c.argument('workspace_name', id_part='name', help='The workspace name.')

    with self.argument_context('synapse spark pool list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    for scope in ['show', 'create', 'update', 'delete']:
        with self.argument_context('synapse spark pool ' + scope) as c:
            c.argument('spark_pool_name', arg_type=name_type, id_part='child_name_1',
                       help='The name of the Spark pool.')

    with self.argument_context('synapse spark pool create') as c:
        # Node
        c.argument('node_count', type=int, arg_group='Node', help='The number of node.')
        c.argument('node_size_family', arg_group='Node', help='The node size family.')
        c.argument('node_size', arg_group='Node', arg_type=get_enum_type(['Small', 'Medium', 'Large']),
                   help='The node size.')

        # AutoScale
        c.argument('enable_auto_scale', arg_type=get_three_state_flag(), arg_group='AutoScale',
                   help='The flag of enabling auto scale.')
        c.argument('max_node_count', type=int, arg_group='AutoScale', help='The max node count.')
        c.argument('min_node_count', type=int, arg_group='AutoScale', help='The min node count.')

        # AutoPause
        c.argument('enable_auto_pause', arg_type=get_three_state_flag(), arg_group='AutoPause',
                   help='The flag of enabling auto pause.')
        c.argument('delay', arg_group='AutoPause', help='The delay time whose unit is minute.')

        # Environment Configuration
        c.argument('library_requirements_file', arg_group='Environment Configuration',
                   help='The library requirements file.')

        # Default Folder
        c.argument('spark_events_folder', arg_group='Default Folder', help='The Spark events folder.')
        c.argument('default_spark_log_folder', arg_group='Default Folder', help='The default Spark log folder.')

        # Component Version
        c.argument('spark_version', arg_group='Component Version', help='The supported Spark version is 2.4 now.')

        c.argument('tags', arg_type=tags_type)

    with self.argument_context('synapse spark pool update') as c:
        c.argument('tags', arg_type=tags_type)
        # Node
        c.argument('node_count', type=int, arg_group='Node', help='The number of node.')
        c.argument('node_size_family', arg_group='Node', help='The node size family.')

        c.argument('node_size', arg_group='Node', arg_type=get_enum_type(['Small', 'Medium', 'Large']),
                   help='The node size.')
        # AutoScale
        c.argument('enable_auto_scale', arg_type=get_three_state_flag(), arg_group='AutoScale',
                   help='The flag of enabling auto scale.')
        c.argument('max_node_count', type=int, arg_group='AutoScale', help='The max node count.')
        c.argument('min_node_count', type=int, arg_group='AutoScale', help='The min node count.')

        # AutoPause
        c.argument('enable_auto_pause', arg_type=get_three_state_flag(), arg_group='AutoPause',
                   help='The flag of enabling auto pause.')
        c.argument('delay', arg_group='AutoPause', help='The delay time whose unit is minute.')

        # Environment Configuration
        c.argument('library_requirements_file', arg_group='Environment Configuration',
                   help='The library requirements file.')
        c.argument('force', arg_type=get_three_state_flag(), help='The flag of force operation.')

    # synapse sql pool
    with self.argument_context('synapse sql pool') as c:
        c.argument('workspace_name', id_part='name', help='The workspace name.')

    with self.argument_context('synapse sql pool list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    for scope in ['show', 'create', 'delete', 'update', 'pause', 'resume']:
        with self.argument_context('synapse sql pool ' + scope) as c:
            c.argument('sql_pool_name', arg_type=name_type, id_part='child_name_1', help='The SQL pool name.')

    with self.argument_context('synapse sql pool create') as c:
        c.argument('performance_level', help='The performance level.')
        c.argument('source_database_id', help='The source database id.')
        c.argument('recoverable_database_id', help='The recoverable database id.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('synapse sql pool update') as c:
        c.argument('sku_name', options_list=['--performance-level'], help='The performance level.')
        c.argument('tags', arg_type=tags_type)

    # synapse workspace firewall-rule
    with self.argument_context('synapse workspace firewall-rule') as c:
        c.argument('workspace_name', id_part='name', help='The workspace name.')

    with self.argument_context('synapse workspace firewall-rule list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    for scope in ['show', 'create', 'delete']:
        with self.argument_context('synapse workspace firewall-rule ' + scope) as c:
            c.argument('rule_name', arg_type=name_type, id_part='child_name_1', help='The IP firewall rule name')

    with self.argument_context('synapse workspace firewall-rule create') as c:
        c.argument('start_ip_address', help='The start IP address of the firewall rule. Must be IPv4 format.')
        c.argument('end_ip_address', help='The end IP address of the firewall rule. Must be IPv4 format. '
                                          'Must be greater than or equal to startIpAddress.')
