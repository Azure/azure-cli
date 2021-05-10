# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import SqlPool, SqlPoolPatchInfo, Sku
from knack.util import CLIError
from .._client_factory import cf_synapse_client_workspace_factory
from ..constant import SynapseSqlCreateMode, SqlPoolConnectionClientAuthenticationType, SqlPoolConnectionClientType


# Synapse sqlpool
def create_sql_pool(cmd, client, resource_group_name, workspace_name, sql_pool_name, performance_level, tags=None,
                    no_wait=False):
    workspace_client = cf_synapse_client_workspace_factory(cmd.cli_ctx)
    workspace_object = workspace_client.get(resource_group_name, workspace_name)
    location = workspace_object.location

    sku = Sku(name=performance_level)

    sql_pool_info = SqlPool(sku=sku, location=location, create_mode=SynapseSqlCreateMode.Default, tags=tags)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, workspace_name, sql_pool_name, sql_pool_info)


def update_sql_pool(cmd, client, resource_group_name, workspace_name, sql_pool_name, sku_name=None, tags=None):
    sku = Sku(name=sku_name)
    sql_pool_patch_info = SqlPoolPatchInfo(sku=sku, tags=tags)
    return client.update(resource_group_name, workspace_name, sql_pool_name, sql_pool_patch_info)


def restore_sql_pool(cmd, client, resource_group_name, workspace_name, sql_pool_name, destination_name,
                     performance_level=None, restore_point_in_time=None, source_database_deletion_date=None,
                     no_wait=False, **kwargs):
    """
    Restores an existing or deleted SQL pool (i.e. create with 'Restore'
    or 'PointInTimeRestore' create mode.)

    Custom function makes create mode more convenient.
    """
    if not (restore_point_in_time or source_database_deletion_date):
        raise CLIError('Either --time or --deleted-time must be specified.')

    # Set create mode properties
    is_deleted = source_database_deletion_date is not None
    create_mode = SynapseSqlCreateMode.Restore if is_deleted else SynapseSqlCreateMode.PointInTimeRestore

    source_sql_pool_info = client.get(resource_group_name, workspace_name, sql_pool_name)

    # get the default performance_level
    if performance_level is None:
        performance_level = source_sql_pool_info.sku.name

    # create source database id
    source_database_id = _construct_database_resource_id(cmd.cli_ctx, resource_group_name, workspace_name,
                                                         sql_pool_name)

    sku = Sku(name=performance_level)
    dest_sql_pool_info = SqlPool(sku=sku, location=source_sql_pool_info.location, create_mode=create_mode,
                                 restore_point_in_time=restore_point_in_time, source_database_id=source_database_id)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, workspace_name, destination_name,
                       dest_sql_pool_info)


def sql_pool_show_connection_string(
        cmd,
        client_provider,
        sql_pool_name='<sql pool name>',
        workspace_name='<workspace name>',
        auth_type=SqlPoolConnectionClientAuthenticationType.SqlPassword.value):
    """
    Builds a SQL connection string for a specified client provider.
    """

    workspace_sql_pool_compute_suffix = cmd.cli_ctx.cloud.suffixes.synapse_analytics_endpoint.replace('dev', 'sql')

    conn_str_props = {
        'workspace': workspace_name,
        'workspace_fqdn': '{}{}'.format(workspace_name, workspace_sql_pool_compute_suffix),
        'workspace_suffix': workspace_sql_pool_compute_suffix,
        'sql_pool': sql_pool_name
    }

    formats = {
        SqlPoolConnectionClientType.AdoDotNet: {
            SqlPoolConnectionClientAuthenticationType.SqlPassword:
                'Server=tcp:{workspace_fqdn},1433;Initial Catalog={sql_pool};Persist Security Info=False;'
                'User ID=<username>;Password=<password>;MultipleActiveResultSets=False;Encrypt=True;'
                'TrustServerCertificate=False;Connection Timeout=30;',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryPassword:
                'Server=tcp:{workspace_fqdn},1433;Initial Catalog={sql_pool};Persist Security Info=False;'
                'User ID=<username>;Password=<password>;MultipleActiveResultSets=False;Encrypt=True;'
                'TrustServerCertificate=False;Authentication="Active Directory Password";',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryIntegrated:
                'Server=tcp:{workspace_fqdn},1433;Initial Catalog={sql_pool};Persist Security Info=False;'
                'User ID=<username>;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;'
                'Authentication="Active Directory Integrated";'
        },
        SqlPoolConnectionClientType.Jdbc: {
            SqlPoolConnectionClientAuthenticationType.SqlPassword:
                'jdbc:sqlserver://{workspace_fqdn}:1433;database={sql_pool};user=<username>@{workspace};'
                'password=<password>;encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{workspace_suffix};loginTimeout=30;',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryPassword:
                'jdbc:sqlserver://{workspace_fqdn}:1433;database={sql_pool};user=<username>;'
                'password=<password>;encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{workspace_suffix};loginTimeout=30;authentication=ActiveDirectoryPassword',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryIntegrated:
                'jdbc:sqlserver://{workspace_fqdn}:1433;database={sql_pool};'
                'encrypt=true;trustServerCertificate=false;'
                'hostNameInCertificate=*{workspace_suffix};loginTimeout=30;Authentication=ActiveDirectoryIntegrated',
        },
        SqlPoolConnectionClientType.Odbc: {
            SqlPoolConnectionClientAuthenticationType.SqlPassword:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{workspace_fqdn},1433;'
                'Database={sql_pool};Uid=<username>;Pwd=<password>;Encrypt=yes;'
                'TrustServerCertificate=no;Connection Timeout=30;',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryPassword:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{workspace_fqdn},1433;'
                'Database={sql_pool};Uid=<username>;Pwd=<password>;Encrypt=yes;'
                'TrustServerCertificate=no;Connection Timeout=30;Authentication=ActiveDirectoryPassword',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryIntegrated:
                'Driver={{ODBC Driver 13 for SQL Server}};Server=tcp:{workspace_fqdn},1433;'
                'Database={sql_pool};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
                'Authentication=ActiveDirectoryIntegrated',
        },
        SqlPoolConnectionClientType.Php: {
            # pylint: disable=line-too-long
            SqlPoolConnectionClientAuthenticationType.SqlPassword:
                '$connectionOptions = array("UID"=>"<username>@{workspace}", "PWD"=>"<password>", "Database"=>{sql_pool}, "LoginTimeout" => 30, "Encrypt" => 1, "TrustServerCertificate" => 0); $serverName = "tcp:{workspace_fqdn},1433"; $conn = sqlsrv_connect($serverName, $connectionOptions);',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryPassword:
                CLIError('PHP sqlsrv driver only supports SQL Password authentication.'),
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryIntegrated:
                CLIError('PHP sqlsrv driver only supports SQL Password authentication.'),
        },
        SqlPoolConnectionClientType.PhpPdo: {
            # pylint: disable=line-too-long
            SqlPoolConnectionClientAuthenticationType.SqlPassword:
                '$conn = new PDO("sqlsrv:server = tcp:{workspace_fqdn},1433; Database = {sql_pool}; LoginTimeout = 30; Encrypt = 1; TrustServerCertificate = 0;", "<username>", "<password>");',
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryPassword:
                CLIError('PHP Data Object (PDO) driver only supports SQL Password authentication.'),
            SqlPoolConnectionClientAuthenticationType.ActiveDirectoryIntegrated:
                CLIError('PHP Data Object (PDO) driver only supports SQL Password authentication.'),
        }
    }

    f = formats[client_provider][auth_type]

    if isinstance(f, Exception):
        # Error
        raise f

    # Success
    return f.format(**conn_str_props)


def _construct_database_resource_id(cli_ctx, resource_group_name, server_name, database_name):
    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from six.moves.urllib.parse import quote  # pylint: disable=import-error
    from azure.cli.core.commands.client_factory import get_subscription_id

    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Sql/servers/{}/databases/{}'.format(
        quote(get_subscription_id(cli_ctx)),
        quote(resource_group_name),
        quote(server_name),
        quote(database_name))
