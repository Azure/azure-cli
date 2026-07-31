# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from datetime import datetime, timedelta
from importlib import import_module
import re
from dateutil.tz import tzutc   # pylint: disable=import-error
from knack.log import get_logger
from knack.util import todict
from urllib.request import urlretrieve
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.core.local_context import ALL
from azure.mgmt.core.tools import resource_id, is_valid_resource_id, parse_resource_id
from azure.mgmt.rdbms import mysql, mariadb
from azure.mgmt.rdbms.mysql.operations._servers_operations import ServersOperations as MySqlServersOperations
from azure.mgmt.rdbms.mariadb.operations._servers_operations import ServersOperations as MariaDBServersOperations
from azure.mgmt.rdbms.mariadb.operations._location_based_performance_tier_operations import LocationBasedPerformanceTierOperations as MariaDBLocationOperations
from ._client_factory import get_mariadb_management_client, get_mysql_management_client, cf_mysql_db, cf_mariadb_db, \
    cf_mysql_check_resource_availability_sterling, cf_mariadb_check_resource_availability_sterling
from ._flexible_server_util import generate_missing_parameters, generate_password, resolve_poller
from ._util import parse_public_network_access_input, create_firewall_rule

logger = get_logger(__name__)


SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
DEFAULT_DB_NAME = 'defaultdb'
MYSQL_RETIRE_WARNING_MSG = 'Azure Database for MySQL - Single Server is scheduled for retirement (https://go.microsoft.com/fwlink/?linkid=2216041) by September 16, 2024. Migrate (https://go.microsoft.com/fwlink/?linkid=2202255) to Azure Database for MySQL- Flexible Server now.'
MARIADB_RETIRE_WARNING_MSG = 'Azure Database for MariaDB is scheduled for retirement (https://go.microsoft.com/fwlink/?linkid=2248931) by September 19, 2025. Migrate (https://go.microsoft.com/fwlink/?linkid=2263092) to Azure Database for MySQL- Flexible Server now.'


# pylint: disable=too-many-locals, too-many-statements, raise-missing-from
def _server_create(cmd, client, resource_group_name=None, server_name=None, sku_name=None, no_wait=False,
                   location=None, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None, infrastructure_encryption=None, minimal_tls_version=None):
    provider = ''
    if isinstance(client, MySqlServersOperations):
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        provider = 'Microsoft.DBforMariaDB'

    server_result = firewall_id = None
    administrator_login_password = generate_password(administrator_login_password)
    start_ip = end_ip = ''

    if public_network_access is not None and str(public_network_access).lower() != 'enabled' and str(public_network_access).lower() != 'disabled':
        if str(public_network_access).lower() == 'all':
            start_ip, end_ip = '0.0.0.0', '255.255.255.255'
        else:
            start_ip, end_ip = parse_public_network_access_input(public_network_access)
        # if anything but 'disabled' is passed on to the args,
        # then the public network access value passed on to the API is Enabled.
        public_network_access = 'Enabled'

    # Check availability for server name if it is supplied by the user
    if provider == 'Microsoft.DBforMySQL':
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
        engine_name = 'mysql'
        pricing_link = 'https://aka.ms/mysql-pricing'
        location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                                 server_name, engine_name)
        check_name_client = cf_mysql_check_resource_availability_sterling(cmd.cli_ctx, None)
        name_availability_resquest = mysql.models.NameAvailabilityRequest(name=server_name, type="Microsoft.DBforMySQL/servers")
        check_server_name_availability(check_name_client, name_availability_resquest)
        logger.warning('Creating %s Server \'%s\' in group \'%s\'...', engine_name, server_name, resource_group_name)
        logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                       'Please refer to %s  for pricing details', server_name, sku_name, pricing_link)
        parameters = mysql.models.ServerForCreate(
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
    elif provider == 'Microsoft.DBforMariaDB':
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
        engine_name = 'mariadb'
        pricing_link = 'https://aka.ms/mariadb-pricing'
        location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                                 server_name, engine_name)
        check_name_client = cf_mariadb_check_resource_availability_sterling(cmd.cli_ctx, None)
        name_availability_resquest = mariadb.models.NameAvailabilityRequest(name=server_name, type="Microsoft.DBforMariaDB")
        check_server_name_availability(check_name_client, name_availability_resquest)
        logger.warning('Creating %s Server \'%s\' in group \'%s\'...', engine_name, server_name, resource_group_name)
        logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                       'Please refer to %s  for pricing details', server_name, sku_name, pricing_link)
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
                version=version,
                ssl_enforcement=ssl_enforcement,
                minimal_tls_version=minimal_tls_version,
                public_network_access=public_network_access,
                storage_profile=mariadb.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup,
                    storage_mb=storage_mb,
                    storage_autogrow=auto_grow)),
            location=location,
            tags=tags)

    server_result = resolve_poller(
        client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(engine_name))
    user = server_result.administrator_login
    version = server_result.version
    host = server_result.fully_qualified_domain_name

    # Adding firewall rule
    if public_network_access is not None and start_ip != '':
        firewall_id = create_firewall_rule(cmd, resource_group_name, server_name, start_ip, end_ip, engine_name)

    logger.warning('Make a note of your password. If you forget, you would have to '
                   'reset your password with \'az %s server update -n %s -g %s -p <new-password>\'.',
                   engine_name, server_name, resource_group_name)

    update_local_contexts(cmd, provider, server_name, resource_group_name, location, user)

    # Serves both - MySQL and MariaDB
    # Create mysql database if it does not exist
    database_name = DEFAULT_DB_NAME
    create_database(cmd, resource_group_name, server_name, database_name, engine_name)
    return form_response(server_result, administrator_login_password if administrator_login_password is not None else '*****',
                         host=host,
                         connection_string=create_mysql_connection_string(server_name, host, database_name, user, administrator_login_password),
                         database_name=database_name, firewall_id=firewall_id)


# Need to replace source server name with source server id, so customer server restore function
# The parameter list should be the same as that in factory to use the ParametersContext
# arguments and validators
def _server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time, no_wait=False):
    provider = ''
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
        provider = 'Microsoft.DBforMariaDB'

    parameters = None
    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=provider,
                type='servers',
                name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))

    if provider == 'Microsoft.DBforMySQL':
        parameters = mysql.models.ServerForCreate(
            properties=mysql.models.ServerPropertiesForRestore(
                source_server_id=source_server,
                restore_point_in_time=restore_point_in_time),
            location=None)
    elif provider == 'Microsoft.DBforMariaDB':
        parameters = mariadb.models.ServerForCreate(
            properties=mariadb.models.ServerPropertiesForRestore(
                source_server_id=source_server,
                restore_point_in_time=restore_point_in_time),
            location=None)

    parameters.properties.source_server_id = source_server
    parameters.properties.restore_point_in_time = restore_point_in_time

    # Here is a workaround that we don't support cross-region restore currently,
    # so the location must be set as the same as source server (not the resource group)
    id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        parameters.location = source_server_object.location
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


# need to replace source server name with source server id, so customer server georestore function
# The parameter list should be the same as that in factory to use the ParametersContext
# auguments and validators
def _server_georestore(cmd, client, resource_group_name, server_name, sku_name, location, source_server,
                       backup_retention=None, geo_redundant_backup=None, no_wait=False, **kwargs):
    provider = ''
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
        provider = 'Microsoft.DBforMariaDB'

    parameters = None

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                        resource_group=resource_group_name,
                                        namespace=provider,
                                        type='servers',
                                        name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))

    if provider == 'Microsoft.DBforMySQL':
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForGeoRestore(
                storage_profile=mysql.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup),
                source_server_id=source_server),
            location=location)
    elif provider == 'Microsoft.DBforMariaDB':
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForGeoRestore(
                storage_profile=mariadb.models.StorageProfile(
                    backup_retention_days=backup_retention,
                    geo_redundant_backup=geo_redundant_backup),
                source_server_id=source_server),
            location=location)

    parameters.properties.source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
        if parameters.sku.name is None:
            parameters.sku.name = source_server_object.sku.name
    except Exception as e:
        raise ValueError('Unable to get source server: {}.'.format(str(e)))

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


# Custom functions for server replica, will add PostgreSQL part after backend ready in future
def _replica_create(cmd, client, resource_group_name, server_name, source_server, no_wait=False, location=None, sku_name=None, **kwargs):
    provider = ''
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
        provider = 'Microsoft.DBforMySQL'
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
        provider = 'Microsoft.DBforMariaDB'
    # set source server id
    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                        resource_group=resource_group_name,
                                        namespace=provider,
                                        type='servers',
                                        name=source_server)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(source_server))

    source_server_id_parts = parse_resource_id(source_server)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
    except HttpResponseError as e:
        raise CLIError('Unable to get source server: {}.'.format(str(e)))

    if location is None:
        location = source_server_object.location

    if sku_name is None:
        sku_name = source_server_object.sku.name

    parameters = None
    if provider == 'Microsoft.DBforMySQL':
        parameters = mysql.models.ServerForCreate(
            sku=mysql.models.Sku(name=sku_name),
            properties=mysql.models.ServerPropertiesForReplica(source_server_id=source_server),
            location=location)
    elif provider == 'Microsoft.DBforMariaDB':
        parameters = mariadb.models.ServerForCreate(
            sku=mariadb.models.Sku(name=sku_name),
            properties=mariadb.models.ServerPropertiesForReplica(source_server_id=source_server),
            location=location)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, server_name, parameters)


def _replica_stop(client, resource_group_name, server_name):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise CLIError('Unable to get server: {}.'.format(str(e)))

    if server_object.replication_role.lower() != "replica":
        raise CLIError('Server {} is not a replica server.'.format(server_name))

    server_module_path = server_object.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerUpdateParameters = getattr(module, 'ServerUpdateParameters')

    params = ServerUpdateParameters(replication_role='None')

    return client.begin_update(resource_group_name, server_name, params)


def _server_update_custom_func(client,
                               instance,
                               sku_name=None,
                               storage_mb=None,
                               backup_retention=None,
                               administrator_login_password=None,
                               ssl_enforcement=None,
                               tags=None,
                               auto_grow=None,
                               assign_identity=False,
                               public_network_access=None,
                               minimal_tls_version=None):

    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    server_module_path = instance.__module__
    module = import_module(server_module_path.replace('server', 'server_update_parameters'))
    ServerUpdateParameters = getattr(module, 'ServerUpdateParameters')

    if sku_name:
        instance.sku.name = sku_name
        instance.sku.capacity = None
        instance.sku.family = None
        instance.sku.tier = None
    else:
        instance.sku = None

    if storage_mb:
        instance.storage_profile.storage_mb = storage_mb

    if backup_retention:
        instance.storage_profile.backup_retention_days = backup_retention

    if auto_grow:
        instance.storage_profile.storage_autogrow = auto_grow

    params = ServerUpdateParameters(sku=instance.sku,
                                    storage_profile=instance.storage_profile,
                                    administrator_login_password=administrator_login_password,
                                    version=None,
                                    ssl_enforcement=ssl_enforcement,
                                    tags=tags,
                                    public_network_access=public_network_access,
                                    minimal_tls_version=minimal_tls_version)

    if assign_identity:
        if server_module_path.find('mysql'):
            if instance.identity is None:
                instance.identity = mysql.models.ResourceIdentity(type=mysql.models.IdentityType.system_assigned.value)
            params.identity = instance.identity

    return params


def _server_mysql_upgrade(cmd, client, resource_group_name, server_name, target_server_version):
    logger.warning(MYSQL_RETIRE_WARNING_MSG)

    parameters = mysql.models.ServerUpgradeParameters(
        target_server_version=target_server_version
    )

    client.begin_upgrade(resource_group_name, server_name, parameters)


def _server_mariadb_get(cmd, resource_group_name, server_name):
    logger.warning(MARIADB_RETIRE_WARNING_MSG)
    client = get_mariadb_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _server_mysql_get(cmd, resource_group_name, server_name):
    logger.warning(MYSQL_RETIRE_WARNING_MSG)
    client = get_mysql_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def _server_stop(cmd, client, resource_group_name, server_name):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    logger.warning("Server will be automatically started after 7 days "
                   "if you do not perform a manual start operation")
    return client.begin_stop(resource_group_name, server_name)


def _server_update_get(client, resource_group_name, server_name):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    return client.get(resource_group_name, server_name)


def _server_update_set(client, resource_group_name, server_name, parameters):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    return client.begin_update(resource_group_name, server_name, parameters)


def _server_delete(cmd, client, resource_group_name, server_name):
    database_engine = ''
    if isinstance(client, MySqlServersOperations):
        database_engine = 'mysql'
        logger.warning(MYSQL_RETIRE_WARNING_MSG)

    result = client.begin_delete(resource_group_name, server_name)

    if cmd.cli_ctx.local_context.is_on:
        local_context_file = cmd.cli_ctx.local_context._get_local_context_file()  # pylint: disable=protected-access
        local_context_file.remove_option('{}'.format(database_engine), 'server_name')

    return result.result()


def _get_sku_name(tier, family, capacity):
    return '{}_{}_{}'.format(SKU_TIER_MAP[tier], family, str(capacity))


def _firewall_rule_create(client, resource_group_name, server_name, firewall_rule_name, start_ip_address, end_ip_address):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    parameters = {'name': firewall_rule_name, 'start_ip_address': start_ip_address, 'end_ip_address': end_ip_address}

    return client.begin_create_or_update(resource_group_name, server_name, firewall_rule_name, parameters)


def _firewall_rule_custom_getter(client, resource_group_name, server_name, firewall_rule_name):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    return client.get(resource_group_name, server_name, firewall_rule_name)


def _firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters)


def _firewall_rule_update_custom_func(client, instance, start_ip_address=None, end_ip_address=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


def _vnet_rule_create(client, resource_group_name, server_name, virtual_network_rule_name, virtual_network_subnet_id, ignore_missing_vnet_service_endpoint=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    parameters = {
        'name': virtual_network_rule_name,
        'virtual_network_subnet_id': virtual_network_subnet_id,
        'ignore_missing_vnet_service_endpoint': ignore_missing_vnet_service_endpoint
    }

    return client.begin_create_or_update(resource_group_name, server_name, virtual_network_rule_name, parameters)


def _custom_vnet_update_getter(client, resource_group_name, server_name, virtual_network_rule_name):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    return client.get(resource_group_name, server_name, virtual_network_rule_name)


def _custom_vnet_update_setter(client, resource_group_name, server_name, virtual_network_rule_name, parameters):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        virtual_network_rule_name,
        parameters)


def _vnet_rule_update_custom_func(client, instance, virtual_network_subnet_id, ignore_missing_vnet_service_endpoint=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    instance.virtual_network_subnet_id = virtual_network_subnet_id
    if ignore_missing_vnet_service_endpoint is not None:
        instance.ignore_missing_vnet_service_endpoint = ignore_missing_vnet_service_endpoint
    return instance


def _configuration_update(client, resource_group_name, server_name, configuration_name, value=None, source=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    parameters = {
        'name': configuration_name,
        'value': value,
        'source': source
    }

    return client.begin_create_or_update(resource_group_name, server_name, configuration_name, parameters)


def _db_create(client, resource_group_name, server_name, database_name, charset=None, collation=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
    parameters = {
        'name': database_name,
        'charset': charset,
        'collation': collation
    }

    return client.begin_create_or_update(resource_group_name, server_name, database_name, parameters)


# Custom functions for server logs
def _download_log_files(
        client,
        resource_group_name,
        server_name,
        file_name):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    # list all files
    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name)


def _list_log_files_with_filter(client, resource_group_name, server_name, filename_contains=None,
                                file_last_written=None, max_file_size=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    # list all files
    all_files = client.list_by_server(resource_group_name, server_name)
    files = []

    if file_last_written is None:
        file_last_written = 72
    time_line = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(hours=file_last_written)

    for f in all_files:
        if f.last_modified_time < time_line:
            continue
        if filename_contains is not None and re.search(filename_contains, f.name) is None:
            continue
        if max_file_size is not None and f.size_in_kb > max_file_size:
            continue

        del f.created_time
        files.append(f)

    return files


# Custom functions for list servers
def _server_list_custom_func(client, resource_group_name=None):
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


# region private_endpoint
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, server_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):  # pylint: disable=unused-argument
    private_endpoint_connection = client.get(resource_group_name=resource_group_name, server_name=server_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)
    new_status = 'Approved' if is_approved else 'Rejected'

    private_link_service_connection_state = {
        'status': new_status,
        'description': description
    }

    private_endpoint_connection.private_link_service_connection_state = private_link_service_connection_state

    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         server_name=server_name,
                                         private_endpoint_connection_name=private_endpoint_connection_name,
                                         parameters=private_endpoint_connection)


def approve_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                        description=None):
    """Approve a private endpoint connection request for a server."""
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=True,
        description=description)


def reject_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                       description=None):
    """Reject a private endpoint connection request for a server."""
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
    elif isinstance(client, MariaDBServersOperations):
        logger.warning(MARIADB_RETIRE_WARNING_MSG)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=False,
        description=description)


def server_key_create(client, resource_group_name, server_name, kid):
    """Create Server Key."""
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)

    key_name = _get_server_key_name_from_uri(kid)

    parameters = {
        'uri': kid,
        'server_key_type': "AzureKeyVault"
    }

    return client.begin_create_or_update(server_name, key_name, resource_group_name, parameters)


def server_key_get(client, resource_group_name, server_name, kid):

    """Get Server Key."""
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)

    key_name = _get_server_key_name_from_uri(kid)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def server_key_delete(cmd, client, resource_group_name, server_name, kid):

    """Drop Server Key."""
    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)

    key_name = _get_server_key_name_from_uri(kid)

    return client.begin_delete(
        resource_group_name=resource_group_name,
        server_name=server_name,
        key_name=key_name)


def _get_server_key_name_from_uri(uri):
    '''
    Gets the key's name to use as a server key.

    The SQL server key API requires that the server key has a specific name
    based on the vault, key and key version.
    '''

    match = re.match(r'https://(.)+\.(managedhsm.azure.net|managedhsm-preview.azure.net|vault.azure.net|vault-int.azure-int.net|vault.azure.cn|managedhsm.azure.cn|vault.usgovcloudapi.net|managedhsm.usgovcloudapi.net|vault.microsoftazure.de|managedhsm.microsoftazure.de|vault.cloudapi.eaglex.ic.gov|vault.cloudapi.microsoft.scloud)(:443)?\/keys/[^\/]+\/[0-9a-zA-Z]+$', uri)

    if match is None:
        raise CLIError('The provided uri is invalid. Please provide a valid Azure Key Vault key id. For example: '
                       '"https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901" or "https://YourManagedHsmRegion.YourManagedHsmName.managedhsm.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

    vault = uri.split('.')[0].split('/')[-1]
    key = uri.split('/')[-2]
    version = uri.split('/')[-1]
    return '{}_{}_{}'.format(vault, key, version)


def server_ad_admin_set(client, resource_group_name, server_name, login=None, sid=None):
    '''
    Sets a server's AD admin.
    '''

    if isinstance(client, MySqlServersOperations):
        logger.warning(MYSQL_RETIRE_WARNING_MSG)

    parameters = {
        'administratorType': 'ActiveDirectory',
        'login': login,
        'sid': sid,
        'tenant_id': _get_tenant_id()
    }

    return client.begin_create_or_update(
        server_name=server_name,
        resource_group_name=resource_group_name,
        properties=parameters)


def _get_tenant_id():
    '''
    Gets tenantId from current subscription.
    '''
    profile = Profile()
    sub = profile.get_subscription()
    return sub['tenantId']
# endregion


# region new create experience
def create_mysql_connection_string(server_name, host, database_name, user_name, password):
    connection_kwargs = {
        'host': host,
        'dbname': database_name,
        'username': user_name,
        'servername': server_name,
        'password': password if password is not None else '{password}'
    }
    return 'mysql {dbname} --host {host} --user {username}@{servername} --password={password}'.format(**connection_kwargs)


def create_database(cmd, resource_group_name, server_name, database_name, engine_name):
    if engine_name == 'mysql':
        # check for existing database, create if not present
        database_client = cf_mysql_db(cmd.cli_ctx, None)
    elif engine_name == 'mariadb':
        database_client = cf_mariadb_db(cmd.cli_ctx, None)
    parameters = {
        'name': database_name,
        'charset': 'utf8'
    }
    try:
        database_client.get(resource_group_name, server_name, database_name)
    except ResourceNotFoundError:
        logger.warning('Creating %s database \'%s\'...', engine_name, database_name)
        database_client.begin_create_or_update(resource_group_name, server_name, database_name, parameters)


def form_response(server_result, password, host, connection_string, database_name=None, firewall_id=None):
    result = todict(server_result)
    result['connectionString'] = connection_string
    result['password'] = password
    if firewall_id is not None:
        result['firewallName'] = firewall_id
    if database_name is not None:
        result['databaseName'] = database_name
    return result


def check_server_name_availability(check_name_client, parameters):
    server_availability = check_name_client.execute(parameters)
    if not server_availability.name_available:
        raise CLIError(server_availability.message)
    return True


def update_local_contexts(cmd, provider, server_name, resource_group_name, location, user):
    engine = 'mysql'
    if provider == 'Microsoft.DBforMariaDB':
        engine = 'mariadb'

    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set([engine], 'server_name',
                                      server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([engine], 'administrator_login',
                                      user)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([ALL], 'location',
                                      location)  # Setting the location in the local context
        cmd.cli_ctx.local_context.set([ALL], 'resource_group_name', resource_group_name)


def get_connection_string(cmd, client, server_name='{server}', database_name='{database}', administrator_login='{username}', administrator_login_password='{password}'):
    provider = 'MySQL'
    if isinstance(client, MariaDBLocationOperations):
        provider = 'MariaDB'

    if provider == 'MySQL':
        logger.warning(MYSQL_RETIRE_WARNING_MSG)
        server_endpoint = cmd.cli_ctx.cloud.suffixes.mysql_server_endpoint
        host = '{}{}'.format(server_name, server_endpoint)
        result = {
            'mysql_cmd': "mysql {database} --host {host} --user {user}@{server} --password={password}",
            'ado.net': "Server={host}; Port=3306; Database={database}; Uid={user}@{server}; Pwd={password}",
            'jdbc': "jdbc:mysql://{host}:3306/{database}?user={user}@{server}&password={password}",
            'node.js': "var conn = mysql.createConnection({{host: '{host}', user: '{user}@{server}',"
                       "password: {password}, database: {database}, port: 3306}});",
            'php': "$con=mysqli_init(); [mysqli_ssl_set($con, NULL, NULL, {{ca-cert filename}}, NULL, NULL);] mysqli_real_connect($con, '{host}', '{user}@{server}', '{password}', '{database}', 3306);",
            'python': "cnx = mysql.connector.connect(user='{user}@{server}', password='{password}', host='{host}', "
                      "port=3306, database='{database}')",
            'ruby': "client = Mysql2::Client.new(username: '{user}@{server}', password: '{password}', "
                    "database: '{database}', host: '{host}', port: 3306)"
        }

        connection_kwargs = {
            'host': host,
            'user': administrator_login,
            'password': administrator_login_password if administrator_login_password is not None else '{password}',
            'database': database_name,
            'server': server_name
        }

        for k, v in result.items():
            result[k] = v.format(**connection_kwargs)

    if provider == 'MariaDB':
        logger.warning(MARIADB_RETIRE_WARNING_MSG)
        server_endpoint = cmd.cli_ctx.cloud.suffixes.mariadb_server_endpoint
        host = '{}{}'.format(server_name, server_endpoint)
        result = {
            'ado.net': "Server={host}; Port=3306; Database={database}; Uid={user}@{server}; Pwd={password}",
            'jdbc': "jdbc:mariadb://{host}:3306/{database}?user={user}@{server}&password={password}",
            'node.js': "var conn = mysql.createConnection({{host: '{host}', user: '{user}@{server}',"
                       "password: {password}, database: {database}, port: 3306}});",
            'php': "$con=mysqli_init(); [mysqli_ssl_set($con, NULL, NULL, {{ca-cert filename}}, NULL, NULL);] mysqli_real_connect($con, '{host}', '{user}@{server}', '{password}', '{database}', 3306);",
            'python': "cnx = mysql.connector.connect(user='{user}@{server}', password='{password}', host='{host}', "
                      "port=3306, database='{database}')",
            'ruby': "client = Mysql2::Client.new(username: '{user}@{server}', password: '{password}', "
                    "database: '{database}', host: '{host}', port: 3306)"
        }

        connection_kwargs = {
            'host': host,
            'user': administrator_login,
            'password': administrator_login_password if administrator_login_password is not None else '{password}',
            'database': database_name,
            'server': server_name
        }

        for k, v in result.items():
            result[k] = v.format(**connection_kwargs)

    return {
        'connectionStrings': result
    }
