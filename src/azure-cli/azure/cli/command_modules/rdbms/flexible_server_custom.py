# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import uuid
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
import psycopg2
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt.rdbms.mysql.operations._servers_operations import ServersOperations as MySqlServersOperations
from azure.mgmt.rdbms.mysql.flexibleservers.operations._servers_operations import ServersOperations as MySqlFlexibleServersOperations
from azure.mgmt.rdbms.mariadb.operations._servers_operations import ServersOperations as MariaDBServersOperations
from ._client_factory import get_mariadb_management_client, get_mysql_flexible_management_client, get_postgresql_flexible_management_client, cf_postgres_firewall_rules, cf_postgres_db, cf_postgres_config
from ._util import resolve_poller

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
logger = get_logger(__name__)

## Parity methods with Sterling, but for Meru servers
def _server_create(cmd, client, resource_group_name, server_name, sku_name, no_wait=False,
                   location=None, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None, infrastructure_encryption=None, minimal_tls_version=None):
    provider = 'Microsoft.DBforPostgreSQL' # default is postgresql
    if isinstance(client, MySqlFlexibleServersOperations):
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        provider = 'Microsoft.DBforMariaDB'

    parameters = None
    if provider == 'Microsoft.DBforMySQL':
        from azure.mgmt.rdbms import mysql
        parameters = mysql.flexibleservers.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                minimal_tls_version=minimal_tls_version,
                public_network_access=public_network_access,
                infrastructure_encryption=infrastructure_encryption,
                storage_profile=mysql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb,
                    storage_autogrow=auto_grow)),
            location=location,
            tags=tags)
        if assign_identity:
            parameters.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
    elif provider == 'Microsoft.DBforPostgreSQL':
        from azure.mgmt.rdbms import postgresql

        # MOLJAIN TO DO: The SKU should not be hardcoded, need a fix with new swagger or need to manually parse sku provided
        parameters = postgresql.flexibleservers.models.Server(
            sku=postgresql.flexibleservers.models.Sku(name=sku_name, tier="GeneralPurpose", capacity=4),
            administrator_login=administrator_login,
            administrator_login_password=administrator_login_password,
            version=version,
            ssl_enforcement=ssl_enforcement,
            public_network_access=public_network_access,
            infrastructure_encryption=infrastructure_encryption,
            storage_profile=postgresql.flexibleservers.models.StorageProfile(
                backup_retention_days=backup_retention,
                # geo_redundant_backup=geo_redundant_backup,
                storage_mb=storage_mb),
                #storage_autogrow=auto_grow),
            location=location,
            create_mode="Create", #MOLJAIN hardcoding is ok?
            tags=tags)

        if assign_identity:
            parameters.identity = postgresql.models.ResourceIdentity(type=postgresql.models.IdentityType.system_assigned.value)
    elif provider == 'Microsoft.DBforMariaDB':
        from azure.mgmt.rdbms import mariadb
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                public_network_access=public_network_access,
                storage_profile=mariadb.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb,
                    storage_autogrow=auto_grow)),
            location=location,
            tags=tags)

    return client.create(resource_group_name, server_name, parameters)

# region create without args
def _server_create_without_args_pg(cmd, client, resource_group_name=None, server_name=None, location=None, backup_retention=None,
                                   sku_name=None, geo_redundant_backup=None, storage_mb=None, administrator_login=None,
                                   administrator_login_password=None, version=None, ssl_enforcement=None, database_name=None, tags=None):
    from azure.mgmt.rdbms import postgresql
    db_context = DbContext(
        azure_sdk=postgresql, cf_firewall=cf_postgres_firewall_rules, cf_db=cf_postgres_db,
        cf_config=cf_postgres_config, logging_name='PostgreSQL', connector=psycopg2, command_group='postgres',
        server_client=client)

    try:
        server_result = client.get(resource_group_name, server_name)
        logger.warning('Found existing PostgreSQL Server \'%s\' in group \'%s\'',
                       server_name, resource_group_name)
        # update server if needed
        server_result = _update_server(
            db_context, cmd, client, server_result, resource_group_name, server_name, backup_retention,
            geo_redundant_backup, storage_mb, administrator_login_password, version, ssl_enforcement, tags)
    except CloudError:
        # Create postgresql server
        if administrator_login_password is None:
            administrator_login_password = str(uuid.uuid4())
        server_result = _create_server(
            db_context, cmd, resource_group_name, server_name, location, backup_retention,
            sku_name, geo_redundant_backup, storage_mb, administrator_login, administrator_login_password, version,
            ssl_enforcement, tags)

        # # Set timeout configuration
        # logger.warning('Configuring wait timeout to 8 hours...')
        # config_client = cf_postgres_config(cmd.cli_ctx, None)
        # resolve_poller(
        #     config_client.create_or_update(
        #         resource_group_name, server_name, 'idle_in_transaction_session_timeout', '28800000'),
        #     cmd.cli_ctx, 'PostgreSQL Configuration Update')

    # Create postgresql database if it does not exist
    _create_database(db_context, cmd, resource_group_name, server_name, database_name)

    # check ip address(es) of the user and configure firewall rules
    postgres_errors = (psycopg2.OperationalError)
    host, user = _configure_firewall_rules(
        db_context, postgres_errors, cmd, server_result, resource_group_name, server_name, administrator_login,
        administrator_login_password, database_name)

    # Create firewall rule to allow for Azure IPs
    # - Moved here to run every time after other firewall rules are configured because
    #   bug on server disables this whenever other firewall rules are added.
    _create_azure_firewall_rule(db_context, cmd, resource_group_name, server_name)

    # connect to postgresql and run some commands
    if administrator_login_password is not None:
        _run_postgresql_commands(host, user, administrator_login_password, database_name)

    return _form_response(
        _create_postgresql_connection_string(host, user, administrator_login_password, database_name),
        host, user,
        administrator_login_password if administrator_login_password is not None else '*****'
    )

def _configure_firewall_rules(
        db_context, connector_errors, cmd, server_result, resource_group_name, server_name, administrator_login,
        administrator_login_password, database_name, extra_connector_args=None):
    import re

    # unpack from context
    connector, cf_firewall, command_group, logging_name = (
        db_context.connector, db_context.cf_firewall, db_context.command_group, db_context.logging_name)

    # Check for user's ip address(es)
    user = '{}@{}'.format(administrator_login, server_name)
    host = server_result.fully_qualified_domain_name
    kwargs = {'user': user, 'host': host, 'database': database_name}
    if administrator_login_password is not None:
        kwargs['password'] = administrator_login_password
    kwargs.update(extra_connector_args or {})
    addresses = set()
    logger.warning('Checking your ip address...')
    for _ in range(20):
        try:
            connection = connector.connect(**kwargs)
            connection.close()
        except connector_errors as ex:
            pattern = re.compile(r'.*[\'"](?P<ipAddress>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[\'"]')
            try:
                addresses.add(pattern.match(str(ex)).groupdict().get('ipAddress'))
            except AttributeError:
                pass

    # Create firewall rules for devbox if needed
    firewall_client = cf_firewall(cmd.cli_ctx, None)

    if addresses and len(addresses) == 1:
        ip_address = addresses.pop()
        logger.warning('Configuring server firewall rule, \'devbox\', to allow for your ip address: %s', ip_address)
        resolve_poller(
            firewall_client.create_or_update(resource_group_name, server_name, 'devbox', ip_address, ip_address),
            cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))
    elif addresses:
        logger.warning('Detected dynamic IP address, configuring firewall rules for IP addresses encountered...')
        logger.warning('IP Addresses: %s', ', '.join(list(addresses)))
        firewall_results = []
        for i, ip_address in enumerate(addresses):
            firewall_results.append(firewall_client.create_or_update(
                resource_group_name, server_name, 'devbox' + str(i), ip_address, ip_address))
        for result in firewall_results:
            resolve_poller(result, cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))
    logger.warning('If %s server declines your IP address, please create a new firewall rule using:', logging_name)
    logger.warning('    `az %s server firewall-rule create -g %s -s %s -n {rule_name} '
                   '--start-ip-address {ip_address} --end-ip-address {ip_address}`',
                   command_group, resource_group_name, server_name)

    return host, user

def _create_server(db_context, cmd, resource_group_name, server_name, location, backup_retention, sku_name,
                   geo_redundant_backup, storage_mb, administrator_login, administrator_login_password, version,
                   ssl_enforcement, tags):
    logging_name, azure_sdk, server_client = db_context.logging_name, db_context.azure_sdk, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    parameters = azure_sdk.models.ServerForCreate(
        sku=azure_sdk.models.Sku(name=sku_name),
        properties=azure_sdk.models.ServerPropertiesForDefaultCreate(
            administrator_login=administrator_login,
            administrator_login_password=administrator_login_password,
            version=version,
            ssl_enforcement=ssl_enforcement,
            storage_profile=azure_sdk.models.StorageProfile(
                backup_retention_days=backup_retention,
                geo_redundant_backup=geo_redundant_backup,
                storage_mb=storage_mb)),
        location=location,
        tags=tags)

    return resolve_poller(
        server_client.create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))

def _update_server(db_context, cmd, client, server_result, resource_group_name, server_name, backup_retention,
                   geo_redundant_backup, storage_mb, administrator_login_password, version, ssl_enforcement, tags):
    # storage profile params
    storage_profile_kwargs = {}
    db_sdk, logging_name = db_context.azure_sdk, db_context.logging_name
    if backup_retention != server_result.storage_profile.backup_retention_days:
        update_kwargs(storage_profile_kwargs, 'backup_retention_days', backup_retention)
    if geo_redundant_backup != server_result.storage_profile.geo_redundant_backup:
        update_kwargs(storage_profile_kwargs, 'geo_redundant_backup', geo_redundant_backup)
    if storage_mb != server_result.storage_profile.storage_mb:
        update_kwargs(storage_profile_kwargs, 'storage_mb', storage_mb)

    # update params
    server_update_kwargs = {
        'storage_profile': db_sdk.models.StorageProfile(**storage_profile_kwargs)
    } if storage_profile_kwargs else {}
    update_kwargs(server_update_kwargs, 'administrator_login_password', administrator_login_password)
    if version != server_result.version:
        update_kwargs(server_update_kwargs, 'version', version)
    if ssl_enforcement != server_result.ssl_enforcement:
        update_kwargs(server_update_kwargs, 'ssl_enforcement', ssl_enforcement)
    update_kwargs(server_update_kwargs, 'tags', tags)

    if server_update_kwargs:
        logger.warning('Updating existing %s Server \'%s\' with given arguments', logging_name, server_name)
        params = db_sdk.models.ServerUpdateParameters(**server_update_kwargs)
        return resolve_poller(client.update(
            resource_group_name, server_name, params), cmd.cli_ctx, '{} Server Update'.format(logging_name))
    return server_result

def _create_database(db_context, cmd, resource_group_name, server_name, database_name):
    # check for existing database, create if not
    cf_db, logging_name = db_context.cf_db, db_context.logging_name
    database_client = cf_db(cmd.cli_ctx, None)
    try:
        database_client.get(resource_group_name, server_name, database_name)
    except CloudError:
        logger.warning('Creating %s database \'%s\'...', logging_name, database_name)
        resolve_poller(
            database_client.create_or_update(resource_group_name, server_name, database_name), cmd.cli_ctx,
            '{} Database Create/Update'.format(logging_name))

def _create_azure_firewall_rule(db_context, cmd, resource_group_name, server_name):
    # allow access to azure ip addresses
    cf_firewall, logging_name = db_context.cf_firewall, db_context.logging_name
    logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                   'Azure resources...')
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    resolve_poller(
        firewall_client.create_or_update(resource_group_name, server_name, 'azure-access', '0.0.0.0', '0.0.0.0'),
        cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))

def _create_azure_firewall_rule(db_context, cmd, resource_group_name, server_name):
    # allow access to azure ip addresses
    cf_firewall, logging_name = db_context.cf_firewall, db_context.logging_name
    logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                   'Azure resources...')
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    resolve_poller(
        firewall_client.create_or_update(resource_group_name, server_name, 'azure-access', '0.0.0.0', '0.0.0.0'),
        cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))

def _run_postgresql_commands(host, user, password, database):
    # Connect to postgresql and get cursor to run sql commands
    connection = psycopg2.connect(user=user, host=host, password=password, database=database)
    connection.set_session(autocommit=True)
    logger.warning('Successfully Connected to PostgreSQL.')
    cursor = connection.cursor()
    try:
        db_password = _create_db_password(database)
        cursor.execute("CREATE USER root WITH ENCRYPTED PASSWORD '{}'".format(db_password))
        logger.warning("Ran Database Query: `CREATE USER root WITH ENCRYPTED PASSWORD '%s'`", db_password)
    except psycopg2.ProgrammingError:
        pass
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE {} TO root".format(database))
    logger.warning("Ran Database Query: `GRANT ALL PRIVILEGES ON DATABASE %s TO root`", database)

def update_kwargs(kwargs, key, value):
    if value is not None:
        kwargs[key] = value

def _create_db_password(database_name):
    return '{}{}{}'.format(database_name[0].upper(), database_name[1:], '1')

def _form_response(connection_strings, host, username, password):
    return {
        'connectionStrings': connection_strings,
        'host': host,
        'username': username,
        'password': password
    }

def _create_postgresql_connection_string(host, user, password, database):
    result = {
        'psql_cmd': "psql --host={host} --port=5432 --username={user} --dbname={database}",
        'ado.net': "Server={host};Database={database};Port=5432;User Id={user};Password={password};",
        'jdbc': "jdbc:postgresql://{host}:5432/{database}?user={user}&password={password}",
        'jdbc Spring': "spring.datasource.url=jdbc:postgresql://{host}:5432/{database}  "
                       "spring.datasource.username={user}  "
                       "spring.datasource.password={password}",
        'node.js': "var client = new pg.Client('postgres://{user}:{password}@{host}:5432/{database}');",
        'php': "host={host} port=5432 dbname={database} user={user} password={password}",
        'python': "cnx = psycopg2.connect(database='{database}', user='{user}', host='{host}', password='{password}', "
                  "port='5432')",
        'ruby': "cnx = PG::Connection.new(:host => '{host}', :user => '{user}', :dbname => '{database}', "
                ":port => '5432', :password => '{password}')",
        'webapp': "Database={database}; Data Source={host}; User Id={user}; Password={password}"
    }

    connection_kwargs = {
        'host': host,
        'user': user,
        'password': password if password is not None else '{password}',
        'database': database
    }

    for k, v in result.items():
        result[k] = v.format(**connection_kwargs)
    return result

# pylint: disable=too-many-instance-attributes,too-few-public-methods
class DbContext:
    def __init__(self, azure_sdk=None, cf_firewall=None, cf_db=None, cf_config=None, logging_name=None,
                 connector=None, command_group=None, server_client=None):
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_db = cf_db
        self.cf_config = cf_config
        self.logging_name = logging_name
        self.connector = connector
        self.command_group = command_group
        self.server_client = server_client
# end region
