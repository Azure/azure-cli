# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements, line-too-long
from knack.arguments import CLIArgumentType
from argcomplete import FilesCompleter
from azure.cli.core.commands.parameters import name_type, tags_type, get_three_state_flag, get_enum_type, get_resource_name_completion_list
from azure.cli.core.util import get_json_object, shell_safe_json_parse
from ._validators import validate_storage_account, validate_statement_language
from ._completers import get_role_definition_name_completion_list
from .constant import SparkBatchLanguage, SparkStatementLanguage
from .action import AddFilters, AddOrderBy

workspace_name_arg_type = CLIArgumentType(help='The workspace name.', completer=get_resource_name_completion_list('Microsoft.Synapse/workspaces'))
assignee_arg_type = CLIArgumentType(help='Represent a user, group, or service principal. Supported format: object id, user sign-in name, or service principal name.')
role_arg_type = CLIArgumentType(help='The role name/id that is assigned to the principal.', completer=get_role_definition_name_completion_list)
definition_file_arg_type = CLIArgumentType(options_list=['--file'], completer=FilesCompleter(), type=shell_safe_json_parse, help='Properties may be supplied from a JSON file using the `@{path}` syntax or a JSON string.')


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

    # synapse artifacts linked-service
    for scope in ['create', 'update']:
        with self.argument_context('synapse linked-service ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('linked_service_name', arg_type=name_type, help='The linked service name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)

    with self.argument_context('synapse linked-service list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    with self.argument_context('synapse linked-service show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('linked_service_name', arg_type=name_type, help='The linked service name.')

    with self.argument_context('synapse linked-service delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('linked_service_name', arg_type=name_type, help='The linked service name.')

    # synapse artifacts dataset
    for scope in ['create', 'update']:
        with self.argument_context('synapse dataset ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('dataset_name', arg_type=name_type, help='The dataset name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)

    with self.argument_context('synapse dataset list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    with self.argument_context('synapse dataset show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('dataset_name', arg_type=name_type, help='The dataset name.')

    with self.argument_context('synapse dataset delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('dataset_name', arg_type=name_type, help='The dataset name.')

    # synapse artifacts pipeline
    for scope in ['create', 'update']:
        with self.argument_context('synapse pipeline ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('pipeline_name', arg_type=name_type, help='The pipeline name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)

    with self.argument_context('synapse pipeline list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    with self.argument_context('synapse pipeline show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('pipeline_name', arg_type=name_type, help='The pipeline name.')

    with self.argument_context('synapse pipeline delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('pipeline_name', arg_type=name_type, help='The pipeline name.')

    with self.argument_context('synapse pipeline create-run') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('pipeline_name', arg_type=name_type, help='The pipeline name.')
        c.argument('reference_pipeline_run_id', options_list=['--reference-pipeline-run-id', '--run-id'],
                   help='The pipeline run ID for rerun. If run ID is specified, the parameters of the specified run will be used to create a new run.')
        c.argument('is_recovery', arg_type=get_three_state_flag(),
                   help='Recovery mode flag. If recovery mode is set to true, the specified referenced pipeline run and the new run will be grouped under the same groupId.')
        c.argument('start_activity_name', help='In recovery mode, the rerun will start from this activity. If not specified, all activities will run.')
        c.argument('parameters', completer=FilesCompleter(), type=shell_safe_json_parse,
                   help='Parameters for pipeline run. Can be supplied from a JSON file using the `@{path}` syntax or a JSON string.')

    # synapse artifacts pipeline run
    with self.argument_context('synapse pipeline-run query-by-workspace') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('continuation_token', help='The continuation token for getting the next page of results. Null for first page.')
        c.argument('last_updated_after', help='The time at or after which the run event was updated in \'ISO 8601\' format.')
        c.argument('last_updated_before', help='The time at or before which the run event was updated in \'ISO 8601\' format.')
        c.argument('filters', action=AddFilters, nargs='*', help='List of filters.')
        c.argument('order_by', action=AddOrderBy, nargs='*', help='List of OrderBy option.')

    with self.argument_context('synapse pipeline-run show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('run_id', help='The pipeline run identifier.')

    with self.argument_context('synapse pipeline-run cancel') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('run_id', help='The pipeline run identifier.')
        c.argument('is_recursive', arg_type=get_three_state_flag(),
                   help='If true, cancel all the Child pipelines that are triggered by the current pipeline.')

    with self.argument_context('synapse activity-run query-by-pipeline-run') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('pipeline_name', arg_type=name_type, help='The pipeline name.')
        c.argument('run_id', help='The pipeline run identifier.')
        c.argument('continuation_token', help='The continuation token for getting the next page of results. Null for first page.')
        c.argument('last_updated_after', help='The time at or after which the run event was updated in \'ISO 8601\' format.')
        c.argument('last_updated_before', help='The time at or before which the run event was updated in \'ISO 8601\' format.')
        c.argument('filters', action=AddFilters, nargs='*', help='List of filters.')
        c.argument('order_by', action=AddOrderBy, nargs='*', help='List of OrderBy option.')

    # synapse artifacts trigger
    for scope in ['create', 'update']:
        with self.argument_context('synapse trigger ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('trigger_name', arg_type=name_type, help='The trigger name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)

    with self.argument_context('synapse trigger list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    with self.argument_context('synapse trigger show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    with self.argument_context('synapse trigger delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    with self.argument_context('synapse trigger subscribe-to-event') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    with self.argument_context('synapse trigger get-event-subscription-status') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    with self.argument_context('synapse trigger unsubscribe-from-event') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    with self.argument_context('synapse trigger start') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    with self.argument_context('synapse trigger stop') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')

    # synapse artifacts trigger run
    with self.argument_context('synapse trigger-run rerun') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('trigger_name', arg_type=name_type, help='The trigger name.')
        c.argument('run_id', help='The trigger run identifier.')

    with self.argument_context('synapse trigger-run query-by-workspace') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('continuation_token', help='The continuation token for getting the next page of results. Null for first page.')
        c.argument('last_updated_after', help='The time at or after which the run event was updated in \'ISO 8601\' format.')
        c.argument('last_updated_before', help='The time at or before which the run event was updated in \'ISO 8601\' format.')
        c.argument('filters', action=AddFilters, nargs='*', help='List of filters.')
        c.argument('order_by', action=AddOrderBy, nargs='*', help='List of OrderBy option.')

    # synapse artifacts data flow
    for scope in ['create', 'update']:
        with self.argument_context('synapse data-flow ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('data_flow_name', arg_type=name_type, help='The data flow name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)

    with self.argument_context('synapse data-flow list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    with self.argument_context('synapse data-flow show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('data_flow_name', arg_type=name_type, help='The data flow name.')

    with self.argument_context('synapse data-flow delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('data_flow_name', arg_type=name_type, help='The data flow name.')

    # synapse artifacts notebook
    for scope in ['create', 'update', 'import']:
        with self.argument_context('synapse notebook ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('notebook_name', arg_type=name_type, help='The notebook name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)
            c.argument('spark_pool_name', help='The name of the Spark pool.')
            c.argument('executor_size', arg_type=get_enum_type(['Small', 'Medium', 'Large']),
                       help='Number of core and memory to be used for executors allocated in the specified Spark pool for the job.')
            c.argument('executor_count', help='Number of executors to be allocated in the specified Spark pool for the job.')

    with self.argument_context('synapse notebook list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    with self.argument_context('synapse notebook show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('notebook_name', arg_type=name_type, help='The notebook name.')

    with self.argument_context('synapse notebook export') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('output_folder', help='The folder where the notebook should be placed.')
        c.argument('notebook_name', arg_type=name_type, help='The notebook name.')

    with self.argument_context('synapse notebook delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('notebook_name', arg_type=name_type, help='The notebook name.')
