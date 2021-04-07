# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements, line-too-long, too-many-branches
from knack.arguments import CLIArgumentType
from argcomplete import FilesCompleter
from azure.mgmt.synapse.models import TransparentDataEncryptionStatus, SecurityAlertPolicyState, BlobAuditingPolicyState
from azure.cli.core.commands.parameters import name_type, tags_type, get_three_state_flag, get_enum_type, \
    get_resource_name_completion_list, get_location_type
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.util import get_json_object, shell_safe_json_parse
from ._validators import validate_storage_account, validate_statement_language
from ._completers import get_role_definition_name_completion_list
from .constant import SparkBatchLanguage, SparkStatementLanguage, SqlPoolConnectionClientType, PrincipalType, \
    SqlPoolConnectionClientAuthenticationType, ItemType
from .action import AddFilters, AddOrderBy

workspace_name_arg_type = CLIArgumentType(help='The workspace name.',
                                          completer=get_resource_name_completion_list('Microsoft.Synapse/workspaces'))
assignee_arg_type = CLIArgumentType(
    help='Represent a user or service principal. Supported format: object id, user sign-in name, or service principal name.')

assignee_object_id_arg_type = CLIArgumentType(
    help="Use this parameter instead of '--assignee' to bypass Graph API invocation in case of insufficient privileges. "
         "This parameter only works with object ids for users, groups, service principals, and "
         "managed identities. For managed identities use the principal id. For service principals, "
         "use the object id and not the app id.")

role_arg_type = CLIArgumentType(help='The role name/id that is assigned to the principal.',
                                completer=get_role_definition_name_completion_list)
definition_file_arg_type = CLIArgumentType(options_list=['--file'], completer=FilesCompleter(),
                                           type=shell_safe_json_parse,
                                           help='Properties may be supplied from a JSON file using the `@{path}` syntax or a JSON string.')
time_format_help = 'Time should be in following format: "YYYY-MM-DDTHH:MM:SS".'
storage_arg_group = "Storage"
policy_arg_group = 'Policy'


def _configure_security_or_audit_policy_storage_params(arg_ctx):
    arg_ctx.argument('storage_account',
                     options_list=['--storage-account'],
                     arg_group=storage_arg_group,
                     help='Name of the storage account.')

    arg_ctx.argument('storage_account_access_key',
                     options_list=['--storage-key'],
                     arg_group=storage_arg_group,
                     help='Access key for the storage account.')

    arg_ctx.argument('storage_endpoint',
                     arg_group=storage_arg_group,
                     help='The storage account endpoint.')


def load_arguments(self, _):
    # synapse workspace
    for scope in ['show', 'create', 'update', 'delete', 'activate']:
        with self.argument_context('synapse workspace ' + scope) as c:
            c.argument('workspace_name', arg_type=name_type, id_part='name', help='The workspace name.')

    for scope in ['create', 'update']:
        with self.argument_context('synapse workspace ' + scope) as c:
            c.argument('sql_admin_login_password', options_list=['--sql-admin-login-password', '-p'],
                       help='The sql administrator login password.')
            c.argument('tags', arg_type=tags_type)
            c.argument('allowed_aad_tenant_ids', options_list=['--allowed-tenant-ids'], nargs='+', help="The approved Azure AD tenants which outbound data traffic allowed to. The Azure AD tenant of the current user will be included by default. Use ""(\'""\' in PowerShell) to disable all allowed tenant ids.")
            c.argument('key_name', help='The workspace customer-managed key display name. All existing keys can be found using "az synapse workspace key list" cmdlet.')

    with self.argument_context('synapse workspace create') as c:
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument("storage_account", validator=validate_storage_account,
                   help='The data lake storage account name or resource id.')
        c.argument('file_system', help='The file system of the data lake storage account.')
        c.argument('sql_admin_login_user', options_list=['--sql-admin-login-user', '-u'],
                   help='The sql administrator login user name.')
        c.argument('enable_managed_virtual_network', options_list=['--enable-managed-vnet',
                                                                   '--enable-managed-virtual-network'],
                   arg_type=get_three_state_flag(),
                   help='The flag indicates whether enable managed virtual network.')
        c.argument('prevent_data_exfiltration', arg_type=get_three_state_flag(),
                   help='The flag indicates whether enable data exfiltration.', options_list=['--prevent-exfiltration', '--prevent-data-exfiltration'])
        c.argument('key_identifier', help='The customer-managed key used to encrypt all data at rest in the workspace. Key identifier should be in the format of: https://{keyvaultname}.vault.azure.net/keys/{keyname}.', options_list=['--key-identifier', '--cmk'])

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

    with self.argument_context('synapse sql pool list-deleted') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    for scope in ['show', 'create', 'delete', 'update', 'pause', 'resume', 'restore', 'show-connection-string']:
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

    with self.argument_context('synapse sql pool restore') as c:
        c.argument('performance_level', help='The performance level.')
        c.argument('destination_name', options_list=['--dest-name', '--destination-name'],
                   help='Name of the sql pool that will be created as the restore destination.')

        restore_point_arg_group = 'Restore Point'
        c.argument('restore_point_in_time',
                   options_list=['--time', '-t'],
                   arg_group=restore_point_arg_group,
                   help='The point in time of the source database that will be restored to create the new database. Must be greater than or equal to the source database\'s earliestRestoreDate value. Either --time or --deleted-time (or both) must be specified. {0}'.format(
                       time_format_help))
        c.argument('source_database_deletion_date',
                   options_list=['--deleted-time'],
                   arg_group=restore_point_arg_group,
                   help='If specified, restore from a deleted database instead of from an existing database. Must match the deleted time of a deleted database in the same server. Either --time or --deleted-time (or both) must be specified. {0}'.format(
                       time_format_help))

    with self.argument_context('synapse sql pool show-connection-string') as c:
        c.argument('client_provider',
                   options_list=['--client', '-c'],
                   help='Type of client connection provider.',
                   arg_type=get_enum_type(SqlPoolConnectionClientType))

        auth_group = 'Authentication'
        c.argument('auth_type',
                   options_list=['--auth-type', '-a'],
                   arg_group=auth_group,
                   help='Type of authentication.',
                   arg_type=get_enum_type(SqlPoolConnectionClientAuthenticationType))

    # synapse sql pool classification
    with self.argument_context('synapse sql pool classification') as c:
        c.argument('sql_pool_name', arg_type=name_type, id_part='child_name_1', help='The SQL pool name.')

    with self.argument_context('synapse sql pool classification list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    with self.argument_context('synapse sql pool classification recommendation list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')
        c.argument('include_disabled_recommendations', options_list=['--included-disabled'],
                   arg_type=get_three_state_flag(),
                   help='Indicates whether the result should include disabled recommendations')

    for scope in ['show', 'create', 'update', 'delete', 'recommendation enable', 'recommendation disable']:
        with self.argument_context('synapse sql pool classification ' + scope) as c:
            c.argument('schema_name', help='The name of schema.', options_list=['--schema'])
            c.argument('table_name', help='The name of table.', options_list=['--table'])
            c.argument('column_name', help='The name of column.', options_list=['--column'])
            c.argument('information_type', help='The information type.')
            c.argument('label_name', help='The label name.', options_list=['--label'])

    # synapse sql pool tde
    with self.argument_context('synapse sql pool tde') as c:
        c.argument('sql_pool_name', arg_type=name_type, id_part='child_name_1', help='The SQL pool name.')
        c.argument('status', arg_type=get_enum_type(TransparentDataEncryptionStatus),
                   required=True, help='Status of the transparent data encryption.')

    # synapse sql pool threat-policy
    with self.argument_context('synapse sql pool threat-policy') as c:
        c.argument('sql_pool_name', arg_type=name_type, id_part='child_name_1', help='The SQL pool name.')

    with self.argument_context('synapse sql pool threat-policy update') as c:
        _configure_security_or_audit_policy_storage_params(c)
        notification_arg_group = 'Notification'

        c.argument('state',
                   arg_group=policy_arg_group,
                   help='Threat detection policy state',
                   arg_type=get_enum_type(SecurityAlertPolicyState))
        c.argument('retention_days',
                   type=int,
                   arg_group=policy_arg_group,
                   help='The number of days to retain threat detection logs.')
        c.argument('disabled_alerts',
                   arg_group=policy_arg_group,
                   help='List of disabled alerts.',
                   nargs='+')
        c.argument('email_addresses',
                   arg_group=notification_arg_group,
                   help='List of email addresses that alerts are sent to.',
                   nargs='+')
        c.argument('email_account_admins',
                   arg_group=notification_arg_group,
                   help='Whether the alert is sent to the account administrators.',
                   arg_type=get_three_state_flag())

    # synapse sql pool audit-policy
    with self.argument_context('synapse sql pool audit-policy') as c:
        c.argument('sql_pool_name', arg_type=name_type, id_part='child_name_1', help='The SQL pool name.')

    for scope in ['synapse sql pool audit-policy', 'synapse sql audit-policy']:
        with self.argument_context(scope + ' update') as c:
            _configure_security_or_audit_policy_storage_params(c)
            c.argument('storage_account_subscription_id', arg_group=storage_arg_group,
                       options_list=['--storage-subscription'],
                       help='The subscription id of storage account')
            c.argument('is_storage_secondary_key_in_use', arg_group=storage_arg_group,
                       arg_type=get_three_state_flag(), options_list=['--use-secondary-key'],
                       help='Indicates whether using the secondary storeage key or not')
            c.argument('is_azure_monitor_target_enabled', options_list=['--enable-azure-monitor'],
                       help='Whether enabling azure monitor target or not.',
                       arg_type=get_three_state_flag())
            c.argument('state',
                       arg_group=policy_arg_group,
                       help='Auditing policy state',
                       arg_type=get_enum_type(BlobAuditingPolicyState))
            c.argument('audit_actions_and_groups',
                       options_list=['--actions'],
                       arg_group=policy_arg_group,
                       help='List of actions and action groups to audit.',
                       nargs='+')
            c.argument('retention_days',
                       type=int,
                       arg_group=policy_arg_group,
                       help='The number of days to retain audit logs.')

    with self.argument_context('synapse sql audit-policy update') as c:
        c.argument('queue_delay_milliseconds', type=int,
                   options_list=['--queue-delay-time', '--queue-delay-milliseconds'],
                   help='The amount of time in milliseconds that can elapse before audit actions are forced to be processed')

    with self.argument_context('synapse sql ad-admin') as c:
        c.argument('workspace_name', help='The workspace name.')
    for scope in ['create', 'update']:
        with self.argument_context('synapse sql ad-admin ' + scope) as c:
            c.argument('login_name', options_list=['--display-name', '-u'],
                       help='Display name of the Azure AD administrator user or group.')
            c.argument('object_id', options_list=['--object-id', '-i'],
                       help='The unique ID of the Azure AD administrator.')

    # synapse workspace firewall-rule
    with self.argument_context('synapse workspace firewall-rule') as c:
        c.argument('workspace_name', id_part='name', help='The workspace name.')

    with self.argument_context('synapse workspace firewall-rule list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    for scope in ['show', 'create', 'update', 'delete']:
        with self.argument_context('synapse workspace firewall-rule ' + scope) as c:
            c.argument('rule_name', arg_type=name_type, id_part='child_name_1', help='The IP firewall rule name')

    for scope in ['create', 'update']:
        with self.argument_context('synapse workspace firewall-rule ' + scope) as c:
            c.argument('start_ip_address', help='The start IP address of the firewall rule. Must be IPv4 format.')
            c.argument('end_ip_address', help='The end IP address of the firewall rule. Must be IPv4 format. '
                                              'Must be greater than or equal to startIpAddress.')

    # synapse workspace key
    with self.argument_context('synapse workspace key') as c:
        c.argument('workspace_name', id_part='name', help='The workspace name.')

    with self.argument_context('synapse workspace key list') as c:
        c.argument('workspace_name', id_part=None, help='The workspace name.')

    for scope in ['show', 'create', 'delete', 'update']:
        with self.argument_context('synapse workspace key ' + scope) as c:
            c.argument('key_name', arg_type=name_type, id_part='child_name_1', help='The workspace customer-managed key display name. All existing keys can be found using /"az synapse workspace key list/" cmdlet.')

    with self.argument_context('synapse workspace key create') as c:
        c.argument('key_identifier', help='The Key Vault Url of the workspace encryption key. should be in the format of: https://{keyvaultname}.vault.azure.net/keys/{keyname}.')

    with self.argument_context('synapse workspace key update') as c:
        c.argument('key_identifier', help='The Key Vault Url of the workspace encryption key. should be in the format of: https://{keyvaultname}.vault.azure.net/keys/{keyname}.')
        c.argument('is_active', arg_type=get_three_state_flag(), help='Set True to change the workspace state from pending to success state.')

    # synapse workspace managed-identity
    with self.argument_context('synapse workspace managed-identity') as c:
        c.argument('workspace_name', id_part='name', help='The workspace name.')

    for scope in ['grant-sql-access', 'revoke-sql-access', ' show-sql-access']:
        with self.argument_context('synapse workspace managed-identity ' + scope) as c:
            c.argument('workspace_name', id_part='name', help='The workspace name.')

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
        c.argument('language', arg_type=get_enum_type(SparkStatementLanguage), validator=validate_statement_language,
                   help='The language of Spark statement.')

    # synapse workspace access-control
    for scope in ['create', 'list']:
        with self.argument_context('synapse role assignment ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('role', arg_type=role_arg_type)
            c.argument('assignee', arg_type=assignee_arg_type)
            c.argument('assignee_object_id', arg_type=assignee_object_id_arg_type)
            c.argument('scope', help='A scope defines the resources or artifacts that the access applies to. Synapse supports hierarchical scopes. '
                                     'Permissions granted at a higher-level scope are inherited by objects at a lower level. '
                                     'In Synapse RBAC, the top-level scope is a workspace. '
                                     'Assigning a role with workspace scope grants permissions to all applicable objects in the workspace.')
            c.argument('item', help='Item granted access in the workspace. Using with --item-type to combine the scope of assignment')
            c.argument('item_type', arg_type=get_enum_type(ItemType), help='Item type granted access in the workspace. Using with --item to combine the scope of assignment.')

    with self.argument_context('synapse role assignment create') as c:
        c.argument('assignee_principal_type', options_list=['--assignee-principal-type', '--assignee-type'], arg_type=get_enum_type(PrincipalType),
                   help='use with --assignee-object-id to avoid errors caused by propagation latency in AAD Graph')
        c.argument('assignment_id', help='Custom role assignment id in guid format, if not specified, assignment id will be randomly generated.')

    with self.argument_context('synapse role assignment show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('role_assignment_id', options_list=['--id'],
                   help='Id of the role that is assigned to the principal.')

    with self.argument_context('synapse role assignment delete') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('role', arg_type=role_arg_type)
        c.argument('assignee', arg_type=assignee_arg_type)
        c.argument('assignee_object_id', arg_type=assignee_object_id_arg_type)
        c.argument('scope', help='A scope defines the resources or artifacts that the access applies to. Synapse supports hierarchical scopes. '
                                 'Permissions granted at a higher-level scope are inherited by objects at a lower level. '
                                 'In Synapse RBAC, the top-level scope is a workspace. '
                                 'Using az role assignment with filter condition before executing delete operation '
                                 'to be clearly aware of which assignments will be deleted.')
        c.argument('ids', nargs='+',
                   help='space-separated role assignment ids. You should not provide --role or --assignee when --ids is provided.')
        c.argument('item', help='Item granted access in the workspace. Using with --item-type to combine the scope of assignment.'
                                'Using az role assignment with filter condition before executing delete operation '
                                'to be clearly aware of which assignments will be deleted.')
        c.argument('item_type', arg_type=get_enum_type(ItemType), help='Item type granted access in the workspace. Using with --item to combine the scope of assignment.'
                                                                       'Using az role assignment with filter condition before executing delete operation '
                                                                       'to be clearly aware of which assignments will be deleted.')

    with self.argument_context('synapse role definition show') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('role', arg_type=role_arg_type)

    with self.argument_context('synapse role definition list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('is_built_in', arg_type=get_three_state_flag(), help='Is a Synapse Built-In Role or not.')

    with self.argument_context('synapse role scope list') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)

    # synapse artifacts linked-service
    for scope in ['create', 'set']:
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
    for scope in ['create', 'set']:
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
    for scope in ['create', 'set']:
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
        c.argument('start_activity_name',
                   help='In recovery mode, the rerun will start from this activity. If not specified, all activities will run.')
        c.argument('parameters', completer=FilesCompleter(), type=shell_safe_json_parse,
                   help='Parameters for pipeline run. Can be supplied from a JSON file using the `@{path}` syntax or a JSON string.')

    # synapse artifacts pipeline run
    with self.argument_context('synapse pipeline-run query-by-workspace') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type)
        c.argument('continuation_token',
                   help='The continuation token for getting the next page of results. Null for first page.')
        c.argument('last_updated_after',
                   help='The time at or after which the run event was updated in \'ISO 8601\' format.')
        c.argument('last_updated_before',
                   help='The time at or before which the run event was updated in \'ISO 8601\' format.')
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
        c.argument('continuation_token',
                   help='The continuation token for getting the next page of results. Null for first page.')
        c.argument('last_updated_after',
                   help='The time at or after which the run event was updated in \'ISO 8601\' format.')
        c.argument('last_updated_before',
                   help='The time at or before which the run event was updated in \'ISO 8601\' format.')
        c.argument('filters', action=AddFilters, nargs='*', help='List of filters.')
        c.argument('order_by', action=AddOrderBy, nargs='*', help='List of OrderBy option.')

    # synapse artifacts trigger
    for scope in ['create', 'set']:
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
        c.argument('continuation_token',
                   help='The continuation token for getting the next page of results. Null for first page.')
        c.argument('last_updated_after',
                   help='The time at or after which the run event was updated in \'ISO 8601\' format.')
        c.argument('last_updated_before',
                   help='The time at or before which the run event was updated in \'ISO 8601\' format.')
        c.argument('filters', action=AddFilters, nargs='*', help='List of filters.')
        c.argument('order_by', action=AddOrderBy, nargs='*', help='List of OrderBy option.')

    # synapse artifacts data flow
    for scope in ['create', 'set']:
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
    for scope in ['create', 'set', 'import']:
        with self.argument_context('synapse notebook ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type)
            c.argument('notebook_name', arg_type=name_type, help='The notebook name.')
            c.argument('definition_file', arg_type=definition_file_arg_type)
            c.argument('spark_pool_name', help='The name of the Spark pool.')
            c.argument('executor_size', arg_type=get_enum_type(['Small', 'Medium', 'Large']),
                       help='Number of core and memory to be used for executors allocated in the specified Spark pool for the job.')
            c.argument('executor_count',
                       help='Number of executors to be allocated in the specified Spark pool for the job.')

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

    # synapse integration runtime
    with self.argument_context('synapse integration-runtime') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type, id_part='name')

    for scope in ['list', 'list-auth-key', 'wait']:
        with self.argument_context('synapse integration-runtime ' + scope) as c:
            c.argument('workspace_name', arg_type=workspace_name_arg_type, id_part=None)

    for scope in ['list-auth-key', 'wait']:
        with self.argument_context('synapse integration-runtime ' + scope) as c:
            c.argument('integration_runtime_name', arg_type=name_type, help='The integration runtime name.', id_part=None)

    for scope in ['show', 'create', 'delete', 'wait', 'update', 'upgrade', 'regenerate-auth-key', 'get-monitoring-data', 'sync-credentials', 'get-connection-info', 'get-status']:
        with self.argument_context('synapse integration-runtime ' + scope) as c:
            c.argument('integration_runtime_name', arg_type=name_type, help='The integration runtime name.', id_part='child_name_1')

    with self.argument_context('synapse integration-runtime create') as c:
        c.argument('integration_runtime_type', options_list=['--type'], arg_type=get_enum_type(['Managed', 'SelfHosted']), help='The integration runtime type.')
        c.argument('description', help='The integration runtime description.')
        c.argument('if_match', help='ETag of the integration runtime entity. Should only be specified for update, for '
                   'which it should match existing entity or can be * for unconditional update.')
        # Managed
        c.argument('location', arg_group='Managed', help='The integration runtime location.')
        c.argument('compute_type', arg_group='Managed', arg_type=get_enum_type(['General', 'MemoryOptimized', 'ComputeOptimized']),
                   help='Compute type of the data flow cluster which will execute data flow job.')
        c.argument('core_count', arg_group='Managed', help='Core count of the data flow cluster which will execute data flow job.')
        c.argument('time_to_live', arg_group='Managed', help='Time to live (in minutes) setting of the data flow cluster which will execute data flow job.')

    with self.argument_context('synapse integration-runtime update') as c:
        c.argument('auto_update', arg_type=get_enum_type(['On', 'Off']), help='Enable or disable the self-hosted integration runtime auto-update.')
        c.argument('update_delay_offset', help='The time of the day for the self-hosted integration runtime auto-update.')

    with self.argument_context('synapse integration-runtime regenerate-auth-key') as c:
        c.argument('key_name', arg_type=get_enum_type(['authKey1', 'authKey2']), help='The name of the authentication key to regenerate.')

    with self.argument_context('synapse integration-runtime-node') as c:
        c.argument('workspace_name', arg_type=workspace_name_arg_type, id_part='name')
        c.argument('integration_runtime_name', arg_type=name_type, help='The integration runtime name.', id_part='child_name_1')

    for scope in ['show', 'update', 'delete', 'get-ip-address']:
        with self.argument_context('synapse integration-runtime-node ' + scope) as c:
            c.argument('node_name', help='The integration runtime node name.')

    with self.argument_context('synapse integration-runtime-node update') as c:
        c.argument('concurrent_jobs_limit', options_list=['--concurrent-jobs'], help='The number of concurrent jobs permitted to '
                   'run on the integration runtime node. Values between 1 and maxConcurrentJobs are allowed.')
