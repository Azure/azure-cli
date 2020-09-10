# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements, line-too-long
from knack.arguments import CLIArgumentType
from argcomplete import FilesCompleter
from azure.cli.core.commands.parameters import name_type, tags_type, get_three_state_flag, get_enum_type, get_resource_name_completion_list
from azure.cli.core.util import get_json_object
from ._validators import validate_storage_account, validate_statement_language
from ._completers import get_role_definition_name_completion_list
from .constant import SparkBatchLanguage, SparkStatementLanguage

workspace_name_arg_type = CLIArgumentType(help='The workspace name.', completer=get_resource_name_completion_list('Microsoft.Synapse/workspaces'))
assignee_arg_type = CLIArgumentType(help='Represent a user, group, or service principal. Supported format: object id, user sign-in name, or service principal name.')
role_arg_type = CLIArgumentType(help='The role name/id that is assigned to the principal.', completer=get_role_definition_name_completion_list)


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
        c.argument('library_requirements', arg_group='Environment Configuration',
                   help='The library requirements file.')

        # Default Folder
        c.argument('spark_events_folder', arg_group='Default Folder', help='The Spark events folder.')
        c.argument('spark_log_folder', arg_group='Default Folder', help='The default Spark log folder.')

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
        c.argument('library_requirements', arg_group='Environment Configuration',
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

    # synapse spark job
    for scope in ['job', 'session', 'statement']:
        with self.argument_context('synapse spark ' + scope) as c:
            c.argument('workspace_name', help='The name of the workspace.')
            c.argument('spark_pool_name', help='The name of the Spark pool.')

    for scope in ['synapse spark job', 'synapse spark session']:
        with self.argument_context(scope + ' list') as c:
            c.argument('from_index', help='Optional parameter specifying which index the list should begin from.')
            c.argument('size',
                       help='The size of the returned list.By default it is 20 and that is the maximum.')

    with self.argument_context('synapse spark job submit') as c:
        c.argument('main_definition_file', help='The main file used for the job.')
        c.argument('main_class_name',
                   help='The fully-qualified identifier or the main class that is in the main definition file.')
        c.argument('command_line_arguments', options_list=['--arguments'], nargs='+',
                   help='Optional arguments to the job (Note: please use storage URIs for file arguments).')
        c.argument('archives', nargs='+', help='The array of archives.')
        c.argument('job_name', arg_type=name_type, help='The Spark job name.')
        c.argument('reference_files', nargs='+',
                   help='Additional files used for reference in the main definition file.')
        c.argument('configuration', type=get_json_object, help='The configuration of Spark job.')
        c.argument('executors', help='The number of executors.')
        c.argument('executor_size', arg_type=get_enum_type(['Small', 'Medium', 'Large']), help='The executor size')
        c.argument('tags', arg_type=tags_type)
        c.argument('language', arg_type=get_enum_type(SparkBatchLanguage, default=SparkBatchLanguage.Scala),
                   help='The Spark job language.')

    for scope in ['show', 'cancel']:
        with self.argument_context('synapse spark job ' + scope) as c:
            c.argument('job_id', options_list=['--livy-id'], arg_group='Spark job',
                       help='The id of the Spark job.')

    with self.argument_context('synapse spark session create') as c:
        c.argument('job_name', arg_type=name_type, help='The Spark session name.')
        c.argument('reference_files', nargs='+',
                   help='Additional files used for reference in the main definition file.')
        c.argument('configuration', type=get_json_object, help='The configuration of Spark session.')
        c.argument('executors', help='The number of executors.')
        c.argument('executor_size', arg_type=get_enum_type(['Small', 'Medium', 'Large']), help='The executor size')
        c.argument('tags', arg_type=tags_type)

    for scope in ['show', 'cancel', 'reset-timeout']:
        with self.argument_context('synapse spark session ' + scope) as c:
            c.argument('session_id', options_list=['--livy-id'], arg_group='Spark Session',
                       help='The id of the Spark session job.')

    with self.argument_context('synapse spark statement') as c:
        c.argument('session_id', help='The id of Spark session.')

    for scope in ['show', 'cancel']:
        with self.argument_context('synapse spark statement ' + scope) as c:
            c.argument('statement_id', options_list=['--livy-id'], arg_group="Spark statement",
                       help='The id of the statement.')

    with self.argument_context('synapse spark statement invoke') as c:
        c.argument('code', completer=FilesCompleter(),
                   help='The code of Spark statement. This is either the code contents or use `@<file path>` to load the content from a file')
        c.argument('language', arg_type=get_enum_type(SparkStatementLanguage), validator=validate_statement_language, help='The language of Spark statement.')

    # synapse workspace access-control
    for scope in ['create', 'list']:
        with self.argument_context('synapse role assignment ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('role', arg_type=role_arg_type)
            c.argument('assignee', arg_type=assignee_arg_type)

    with self.argument_context('synapse role assignment show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('role_assignment_id', options_list=['--id'], help='Id of the role that is assigned to the principal.')

    with self.argument_context('synapse role assignment delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('role', arg_type=role_arg_type)
        c.argument('assignee', arg_type=assignee_arg_type)
        c.argument('ids', nargs='+', help='space-separated role assignment ids. You should not provide --role or --assignee when --ids is provided.')

    with self.argument_context('synapse role definition show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('role', arg_type=role_arg_type)

    with self.argument_context('synapse role definition list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
