# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import re
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from knack.log import get_logger
from urllib.request import urlretrieve
from importlib import import_module
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait, user_confirmation
from azure.cli.core.local_context import ALL
from azure.mgmt.rdbms import mysql_flexibleservers
from azure.cli.core.azclierror import ClientRequestError, RequiredArgumentMissingError, ArgumentUsageError, InvalidArgumentValueError, ValidationError
from ._client_factory import get_mysql_flexible_management_client, cf_mysql_flexible_firewall_rules, cf_mysql_flexible_db, \
    cf_mysql_check_resource_availability, cf_mysql_check_resource_availability_without_location, cf_mysql_flexible_config, \
    cf_mysql_flexible_servers, cf_mysql_flexible_replica, cf_mysql_flexible_adadmin, cf_mysql_flexible_private_dns_zone_suffix_operations
from ._util import resolve_poller, generate_missing_parameters, get_mysql_list_skus_info, generate_password, parse_maintenance_window, \
    replace_memory_optimized_tier, build_identity_and_data_encryption, get_identity_and_data_encryption, get_tenant_id, run_subprocess, \
    run_subprocess_get_output, fill_action_template, get_git_root_dir, get_location_from_resource_group, GITHUB_ACTION_PATH
from ._network import prepare_mysql_exist_private_dns_zone, prepare_mysql_exist_private_network, prepare_private_network, prepare_private_dns_zone, prepare_public_network
from ._validators import mysql_arguments_validator, mysql_auto_grow_validator, mysql_georedundant_backup_validator, mysql_restore_tier_validator, \
    mysql_retention_validator, mysql_sku_name_validator, mysql_storage_validator, validate_mysql_replica, validate_server_name, validate_georestore_location, \
    validate_mysql_tier_update, validate_and_format_restore_point_in_time, validate_public_access_server

logger = get_logger(__name__)
DELEGATION_SERVICE_NAME = "Microsoft.DBforMySQL/flexibleServers"
RESOURCE_PROVIDER = 'Microsoft.DBforMySQL'
DEFAULT_DB_NAME = 'flexibleserverdb'
MINIMUM_IOPS = 300


def flexible_server_update_get(client, resource_group_name, server_name):
    return client.get(resource_group_name, server_name)


def flexible_server_stop(client, resource_group_name=None, server_name=None, no_wait=False):
    days = 30
    logger.warning("Server will be automatically started after %d days "
                   "if you do not perform a manual start operation", days)
    return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, server_name)


def flexible_server_update_set(client, resource_group_name, server_name, parameters):
    return client.begin_update(resource_group_name, server_name, parameters)


def server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def firewall_rule_delete_func(cmd, client, resource_group_name, server_name, firewall_rule_name, yes=None):
    validate_public_access_server(cmd, resource_group_name, server_name)

    result = None
    if not yes:
        user_confirmation(
            "Are you sure you want to delete the firewall-rule '{0}' in server '{1}', resource group '{2}'".format(
                firewall_rule_name, server_name, resource_group_name))
    try:
        result = client.begin_delete(resource_group_name, server_name, firewall_rule_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result


def firewall_rule_create_func(cmd, client, resource_group_name, server_name, firewall_rule_name=None, start_ip_address=None, end_ip_address=None):

    validate_public_access_server(cmd, resource_group_name, server_name)

    if end_ip_address is None and start_ip_address is not None:
        end_ip_address = start_ip_address
    elif start_ip_address is None and end_ip_address is not None:
        start_ip_address = end_ip_address

    if firewall_rule_name is None:
        now = datetime.now()
        firewall_rule_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                          now.second)
        if start_ip_address == '0.0.0.0' and end_ip_address == '0.0.0.0':
            logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                           'Azure resources...')
            firewall_rule_name = 'AllowAllAzureServicesAndResourcesWithinAzureIps_{}-{}-{}_{}-{}-{}'.format(now.year, now.month,
                                                                                                            now.day, now.hour,
                                                                                                            now.minute, now.second)
        elif start_ip_address == end_ip_address:
            logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip_address)
        else:
            if start_ip_address == '0.0.0.0' and end_ip_address == '255.255.255.255':
                firewall_rule_name = 'AllowAll_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day,
                                                                         now.hour, now.minute, now.second)
            logger.warning('Configuring server firewall rule to accept connections from \'%s\' to \'%s\'...', start_ip_address,
                           end_ip_address)

    parameters = {
        'name': firewall_rule_name,
        'start_ip_address': start_ip_address,
        'end_ip_address': end_ip_address
    }

    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters)


def flexible_firewall_rule_custom_getter(cmd, client, resource_group_name, server_name, firewall_rule_name):
    validate_public_access_server(cmd, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def flexible_firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters)


def flexible_firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


def firewall_rule_get_func(cmd, client, resource_group_name, server_name, firewall_rule_name):
    validate_public_access_server(cmd, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def firewall_rule_list_func(cmd, client, resource_group_name, server_name):
    validate_public_access_server(cmd, resource_group_name, server_name)
    return client.list_by_server(resource_group_name, server_name)


def database_delete_func(client, resource_group_name=None, server_name=None, database_name=None, yes=None):
    result = None
    if resource_group_name is None or server_name is None or database_name is None:
        raise CLIError("Incorrect Usage : Deleting a database needs resource-group, server-name and database-name. "
                       "If your parameter persistence is turned ON, make sure these three parameters exist in "
                       "persistent parameters using \'az config param-persist show\'. "
                       "If your parameter persistence is turned OFF, consider passing them explicitly.")
    if not yes:
        user_confirmation(
            "Are you sure you want to delete the database '{0}' of server '{1}'".format(database_name,
                                                                                        server_name), yes=yes)

    try:
        result = client.begin_delete(resource_group_name, server_name, database_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result


def create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip):
    # allow access to azure ip addresses
    cf_firewall = db_context.cf_firewall  # NOQA pylint: disable=unused-variable
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    firewall = firewall_rule_create_func(cmd=cmd,
                                         client=firewall_client,
                                         resource_group_name=resource_group_name,
                                         server_name=server_name,
                                         start_ip_address=start_ip, end_ip_address=end_ip)
    return firewall.result().name


def github_actions_setup(cmd, client, resource_group_name, server_name, database_name, administrator_login,
                         administrator_login_password, sql_file_path, repository, action_name=None, branch=None, allow_push=None):

    server = client.get(resource_group_name, server_name)
    if server.network.public_network_access == 'Disabled':
        raise ClientRequestError("This command only works with public access enabled server.")
    if allow_push and not branch:
        raise RequiredArgumentMissingError("Provide remote branch name to allow pushing the action file to your remote branch.")
    if action_name is None:
        action_name = server.name + '_' + database_name + "_deploy"
    gitcli_check_and_login()

    fill_action_template(cmd,
                         database_engine='mysql',
                         server=server,
                         database_name=database_name,
                         administrator_login=administrator_login,
                         administrator_login_password=administrator_login_password,
                         file_name=sql_file_path,
                         repository=repository,
                         action_name=action_name)

    action_path = get_git_root_dir() + GITHUB_ACTION_PATH + action_name + '.yml'
    logger.warning("Making git commit for file %s", action_path)
    run_subprocess("git add {}".format(action_path))
    run_subprocess("git commit -m \"Add github action file\"")

    if allow_push:
        logger.warning("Pushing the created action file to origin %s branch", branch)
        run_subprocess("git push origin {}".format(branch))
    else:
        logger.warning('You did not set --allow-push parameter. Please push the prepared file %s to your remote repo and run "deploy run" command to activate the workflow.', action_path)


def github_actions_run(action_name, branch):

    gitcli_check_and_login()
    logger.warning("Created an event for %s.yml in branch %s", action_name, branch)
    run_subprocess("gh workflow run {}.yml --ref {}".format(action_name, branch))


def gitcli_check_and_login():
    output = run_subprocess_get_output("gh")
    if output.returncode:
        raise ClientRequestError('Please install "Github CLI" to run this command.')

    output = run_subprocess_get_output("gh auth status")
    if output.returncode:
        run_subprocess("gh auth login", stdout_show=True)


# Custom functions for server logs
def flexible_server_log_download(client, resource_group_name, server_name, file_name):

    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name)


def flexible_server_log_list(client, resource_group_name, server_name, filename_contains=None,
                             file_last_written=None, max_file_size=None):

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


def flexible_server_version_upgrade(cmd, client, resource_group_name, server_name, version, yes=None):
    if not yes:
        user_confirmation(
            "Updating major version in server {} is irreversible. The action you're about to take can't be undone. "
            "Going further will initiate major version upgrade to the selected version on this server."
            .format(server_name), yes=yes)

    instance = client.get(resource_group_name, server_name)
    if instance.sku.tier == 'Burstable':
        raise CLIError("Major version update is not supported for the Burstable pricing tier.")

    current_version = int(instance.version.split('.')[0])
    if current_version >= int(version):
        raise CLIError("The version to upgrade to must be greater than the current version.")

    replica_operations_client = cf_mysql_flexible_replica(cmd.cli_ctx, '_')
    mysql_version_map = {
        '8': '8.0.21',
    }
    version_mapped = mysql_version_map[version]

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)

    for replica in replicas:
        current_replica_version = int(replica.version.split('.')[0])
        if current_replica_version < int(version):
            raise CLIError("Primary server version must not be greater than replica server version. "
                           "First upgrade {} server version to {} and try again.".format(replica.name, version))

    parameters = {
        'version': version_mapped
    }

    return resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Updating server {} to major version {}'.format(server_name, version)
    )


# pylint: disable=too-many-locals, too-many-statements, raise-missing-from
# Region create without args
def flexible_server_create(cmd, client,
                           resource_group_name=None, server_name=None,
                           location=None, backup_retention=None,
                           sku_name=None, tier=None,
                           storage_gb=None, administrator_login=None,
                           administrator_login_password=None, version=None,
                           tags=None, database_name=None,
                           subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                           private_dns_zone_arguments=None, public_access=None,
                           high_availability=None, zone=None, standby_availability_zone=None,
                           iops=None, auto_grow=None, auto_scale_iops=None, geo_redundant_backup=None,
                           byok_identity=None, backup_byok_identity=None, byok_key=None, backup_byok_key=None,
                           yes=False):
    # Generate missing parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name, server_name)
    db_context = DbContext(
        cmd=cmd, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
        cf_availability=cf_mysql_check_resource_availability,
        cf_availability_without_location=cf_mysql_check_resource_availability_without_location,
        cf_private_dns_zone_suffix=cf_mysql_flexible_private_dns_zone_suffix_operations,
        logging_name='MySQL', command_group='mysql', server_client=client, location=location)

    # Process parameters
    server_name = server_name.lower()

    # MySQL chnged MemoryOptimized tier to BusinessCritical (only in client tool not in list-skus return)
    if tier == 'BusinessCritical':
        tier = 'MemoryOptimized'
    mysql_arguments_validator(db_context,
                              server_name=server_name,
                              location=location,
                              tier=tier,
                              sku_name=sku_name,
                              storage_gb=storage_gb,
                              backup_retention=backup_retention,
                              high_availability=high_availability,
                              standby_availability_zone=standby_availability_zone,
                              zone=zone,
                              subnet=subnet,
                              public_access=public_access,
                              auto_grow=auto_grow,
                              version=version,
                              geo_redundant_backup=geo_redundant_backup,
                              byok_identity=byok_identity,
                              backup_byok_identity=backup_byok_identity,
                              byok_key=byok_key,
                              backup_byok_key=backup_byok_key,
                              auto_io_scaling=auto_scale_iops,
                              iops=iops)
    list_skus_info = get_mysql_list_skus_info(db_context.cmd, location)
    iops_info = list_skus_info['iops_info']

    server_result = firewall_name = None

    network, start_ip, end_ip = flexible_server_provision_network_resource(cmd=cmd,
                                                                           resource_group_name=resource_group_name,
                                                                           server_name=server_name,
                                                                           location=location,
                                                                           db_context=db_context,
                                                                           private_dns_zone_arguments=private_dns_zone_arguments,
                                                                           public_access=public_access,
                                                                           vnet=vnet,
                                                                           subnet=subnet,
                                                                           vnet_address_prefix=vnet_address_prefix,
                                                                           subnet_address_prefix=subnet_address_prefix,
                                                                           yes=yes)

    # determine IOPS
    iops = _determine_iops(storage_gb=storage_gb,
                           iops_info=iops_info,
                           iops_input=iops,
                           tier=tier,
                           sku_name=sku_name)

    storage = mysql_flexibleservers.models.Storage(storage_size_gb=storage_gb,
                                                   iops=iops,
                                                   auto_grow=auto_grow,
                                                   auto_io_scaling=auto_scale_iops)

    backup = mysql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
                                                 geo_redundant_backup=geo_redundant_backup)

    sku = mysql_flexibleservers.models.Sku(name=sku_name, tier=tier)

    high_availability = mysql_flexibleservers.models.HighAvailability(mode=high_availability,
                                                                      standby_availability_zone=standby_availability_zone)

    administrator_login_password = generate_password(administrator_login_password)

    identity, data_encryption = build_identity_and_data_encryption(db_engine='mysql',
                                                                   byok_identity=byok_identity,
                                                                   backup_byok_identity=backup_byok_identity,
                                                                   byok_key=byok_key,
                                                                   backup_byok_key=backup_byok_key)

    # Create mysql server
    # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
    server_result = _create_server(db_context, cmd, resource_group_name, server_name,
                                   tags=tags,
                                   location=location,
                                   identity=identity,
                                   sku=sku,
                                   administrator_login=administrator_login,
                                   administrator_login_password=administrator_login_password,
                                   storage=storage,
                                   backup=backup,
                                   network=network,
                                   version=version,
                                   high_availability=high_availability,
                                   availability_zone=zone,
                                   data_encryption=data_encryption)

    # Adding firewall rule
    if start_ip != -1 and end_ip != -1:
        firewall_name = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

    # Create mysql database if it does not exist
    if database_name is None:
        database_name = DEFAULT_DB_NAME
    _create_database(db_context, cmd, resource_group_name, server_name, database_name)

    user = server_result.administrator_login
    server_id = server_result.id
    loc = server_result.location
    version = server_result.version
    sku = server_result.sku.name
    host = server_result.fully_qualified_domain_name
    subnet_id = network.delegated_subnet_resource_id

    logger.warning('Make a note of your password. If you forget, you would have to reset your password with'
                   '\'az mysql flexible-server update -n %s -g %s -p <new-password>\'.',
                   server_name, resource_group_name)
    logger.warning('Try using az \'mysql flexible-server connect\' command to test out connection.')

    _update_local_contexts(cmd, server_name, resource_group_name, location, user)

    return _form_response(user, sku, loc, server_id, host, version,
                          administrator_login_password if administrator_login_password is not None else '*****',
                          _create_mysql_connection_string(host, database_name, user, administrator_login_password),
                          database_name, firewall_name, subnet_id)


def flexible_server_import_create(cmd, client,
                                  resource_group_name, server_name,
                                  data_source_type, data_source, mode=None,
                                  location=None, backup_retention=None,
                                  sku_name=None, tier=None,
                                  storage_gb=None, administrator_login=None,
                                  administrator_login_password=None, version=None,
                                  tags=None, subnet=None,
                                  subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                                  private_dns_zone_arguments=None, public_access=None,
                                  high_availability=None, zone=None, standby_availability_zone=None,
                                  iops=None, auto_grow=None, auto_scale_iops=None, geo_redundant_backup=None,
                                  byok_identity=None, backup_byok_identity=None, byok_key=None, backup_byok_key=None,
                                  yes=False):
    provider = 'Microsoft.DBforMySQL'

    # Generating source_server_id from data_source depending on whether it is a server_name or resource_id
    if not is_valid_resource_id(data_source):
        if len(data_source.split('/')) == 1:
            source_server_id = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=provider,
                type='servers',
                name=data_source)
        else:
            raise ValidationError('The provided data-source {} is invalid.'.format(data_source))
    else:
        source_server_id = data_source

    try:
        location = get_location_from_resource_group(cmd, resource_group_name, location)

        db_context = DbContext(
            cmd=cmd, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
            cf_availability=cf_mysql_check_resource_availability,
            cf_availability_without_location=cf_mysql_check_resource_availability_without_location,
            cf_private_dns_zone_suffix=cf_mysql_flexible_private_dns_zone_suffix_operations,
            logging_name='MySQL', command_group='mysql', server_client=client, location=location)

        # Process parameters
        server_name = server_name.lower()

        # MySQL chnged MemoryOptimized tier to BusinessCritical (only in client tool not in list-skus return)
        if tier == 'BusinessCritical':
            tier = 'MemoryOptimized'
        mysql_arguments_validator(db_context,
                                  data_source_type=data_source_type,
                                  mode=mode,
                                  server_name=server_name,
                                  location=location,
                                  tier=tier,
                                  sku_name=sku_name,
                                  storage_gb=storage_gb,
                                  backup_retention=backup_retention,
                                  high_availability=high_availability,
                                  standby_availability_zone=standby_availability_zone,
                                  zone=zone,
                                  subnet=subnet,
                                  public_access=public_access,
                                  auto_grow=auto_grow,
                                  version=version,
                                  geo_redundant_backup=geo_redundant_backup,
                                  byok_identity=byok_identity,
                                  backup_byok_identity=backup_byok_identity,
                                  byok_key=byok_key,
                                  backup_byok_key=backup_byok_key,
                                  auto_io_scaling=auto_scale_iops,
                                  iops=iops)
        list_skus_info = get_mysql_list_skus_info(db_context.cmd, location)
        iops_info = list_skus_info['iops_info']

        server_result = firewall_name = None

        network, start_ip, end_ip = flexible_server_provision_network_resource(cmd=cmd,
                                                                               resource_group_name=resource_group_name,
                                                                               server_name=server_name,
                                                                               location=location,
                                                                               db_context=db_context,
                                                                               private_dns_zone_arguments=private_dns_zone_arguments,
                                                                               public_access=public_access,
                                                                               vnet=vnet,
                                                                               subnet=subnet,
                                                                               vnet_address_prefix=vnet_address_prefix,
                                                                               subnet_address_prefix=subnet_address_prefix,
                                                                               yes=yes)

        # determine IOPS
        iops = _determine_iops(storage_gb=storage_gb,
                               iops_info=iops_info,
                               iops_input=iops,
                               tier=tier,
                               sku_name=sku_name)

        storage = mysql_flexibleservers.models.Storage(storage_size_gb=storage_gb,
                                                       iops=iops,
                                                       auto_grow=auto_grow,
                                                       auto_io_scaling=auto_scale_iops)

        backup = mysql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
                                                     geo_redundant_backup=geo_redundant_backup)

        sku = mysql_flexibleservers.models.Sku(name=sku_name, tier=tier)

        high_availability = mysql_flexibleservers.models.HighAvailability(mode=high_availability,
                                                                          standby_availability_zone=standby_availability_zone)

        administrator_login_password = generate_password(administrator_login_password)

        identity, data_encryption = build_identity_and_data_encryption(db_engine='mysql',
                                                                       byok_identity=byok_identity,
                                                                       backup_byok_identity=backup_byok_identity,
                                                                       byok_key=byok_key,
                                                                       backup_byok_key=backup_byok_key)

    except Exception as e:
        raise ResourceNotFoundError(e)

    # Create mysql server
    # Note : passing public_access has no effect as the accepted values are 'Enabled' and 'Disabled'. So the value ends up being ignored.
    server_result = _import_create_server(db_context, cmd, resource_group_name, server_name,
                                          tags=tags,
                                          location=location,
                                          identity=identity,
                                          sku=sku,
                                          administrator_login=administrator_login,
                                          administrator_login_password=administrator_login_password,
                                          storage=storage,
                                          backup=backup,
                                          network=network,
                                          version=version,
                                          high_availability=high_availability,
                                          availability_zone=zone,
                                          data_encryption=data_encryption,
                                          source_server_id=source_server_id)

    # Adding firewall rule
    if start_ip != -1 and end_ip != -1:
        firewall_name = create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip)

    user = server_result.administrator_login
    server_id = server_result.id
    loc = server_result.location
    version = server_result.version
    sku = server_result.sku.name
    host = server_result.fully_qualified_domain_name
    subnet_id = network.delegated_subnet_resource_id

    logger.warning('Make a note of your password. If you forget, you would have to reset your password with'
                   '\'az mysql flexible-server update -n %s -g %s -p <new-password>\'.',
                   server_name, resource_group_name)
    logger.warning('Try using az \'mysql flexible-server connect\' command to test out connection.')

    _update_local_contexts(cmd, server_name, resource_group_name, location, user)

    return _form_response(user, sku, loc, server_id, host, version,
                          administrator_login_password if administrator_login_password is not None else '*****',
                          _create_mysql_connection_string(host, None, user, administrator_login_password),
                          None, firewall_name, subnet_id)


# pylint: disable=too-many-locals, too-many-statements, raise-missing-from
def flexible_server_restore(cmd, client, resource_group_name, server_name, source_server, restore_point_in_time=None, zone=None,
                            no_wait=False, subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None,
                            private_dns_zone_arguments=None, public_access=None, yes=False, sku_name=None, tier=None,
                            storage_gb=None, auto_grow=None, backup_retention=None, geo_redundant_backup=None, tags=None):
    provider = 'Microsoft.DBforMySQL'
    server_name = server_name.lower()

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server_id = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=provider,
                type='flexibleServers',
                name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    restore_point_in_time = validate_and_format_restore_point_in_time(restore_point_in_time)

    try:
        id_parts = parse_resource_id(source_server_id)
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        location = ''.join(source_server_object.location.lower().split())
        list_skus_info = get_mysql_list_skus_info(cmd, location)

        if not zone:
            zone = source_server_object.availability_zone

        if not tier:
            tier = source_server_object.sku.tier
        else:
            mysql_restore_tier_validator(tier, source_server_object.sku.tier, list_skus_info['sku_info'])

        if not sku_name:
            sku_name = source_server_object.sku.name
        else:
            mysql_sku_name_validator(sku_name, list_skus_info['sku_info'], tier, None)

        if not storage_gb:
            storage_gb = source_server_object.storage.storage_size_gb
        else:
            mysql_storage_validator(storage_gb, list_skus_info['sku_info'], tier, source_server_object)

        if not auto_grow:
            auto_grow = source_server_object.storage.auto_grow
        else:
            mysql_auto_grow_validator(auto_grow, None, None, source_server_object)

        if not backup_retention:
            backup_retention = source_server_object.backup.backup_retention_days
        else:
            mysql_retention_validator(backup_retention, list_skus_info['sku_info'], tier)

        if not geo_redundant_backup:
            geo_redundant_backup = source_server_object.backup.geo_redundant_backup
        else:
            mysql_georedundant_backup_validator(geo_redundant_backup, list_skus_info['geo_paired_regions'])

        db_context = DbContext(
            cmd=cmd, cf_availability=cf_mysql_check_resource_availability,
            cf_availability_without_location=cf_mysql_check_resource_availability_without_location,
            logging_name='MySQL', command_group='mysql', server_client=client, location=location)
        validate_server_name(db_context, server_name, provider + '/flexibleServers')

        identity, data_encryption = get_identity_and_data_encryption(source_server_object)

        iops = _determine_iops(storage_gb=storage_gb, iops_info=list_skus_info['iops_info'],
                               iops_input=source_server_object.storage.iops, tier=tier, sku_name=sku_name)

        storage = mysql_flexibleservers.models.Storage(storage_size_gb=storage_gb, iops=iops, auto_grow=auto_grow,
                                                       auto_io_scaling=source_server_object.storage.auto_io_scaling)

        backup = mysql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
                                                     geo_redundant_backup=geo_redundant_backup)

        sku = mysql_flexibleservers.models.Sku(name=sku_name, tier=tier)

        parameters = mysql_flexibleservers.models.Server(
            tags=tags,
            location=location,
            identity=identity,
            restore_point_in_time=restore_point_in_time,
            source_server_resource_id=source_server_id,  # this should be the source server name, not id
            create_mode="PointInTimeRestore",
            availability_zone=zone,
            data_encryption=data_encryption,
            sku=sku,
            storage=storage,
            backup=backup
        )

        if any((public_access, vnet, subnet)):
            db_context = DbContext(
                cmd=cmd, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
                cf_availability=cf_mysql_check_resource_availability,
                cf_availability_without_location=cf_mysql_check_resource_availability_without_location,
                cf_private_dns_zone_suffix=cf_mysql_flexible_private_dns_zone_suffix_operations,
                logging_name='MySQL', command_group='mysql', server_client=client, location=location)

            parameters.network, _, _ = flexible_server_provision_network_resource(cmd=cmd,
                                                                                  resource_group_name=resource_group_name,
                                                                                  server_name=server_name,
                                                                                  location=location,
                                                                                  db_context=db_context,
                                                                                  private_dns_zone_arguments=private_dns_zone_arguments,
                                                                                  public_access=public_access,
                                                                                  vnet=vnet,
                                                                                  subnet=subnet,
                                                                                  vnet_address_prefix=vnet_address_prefix,
                                                                                  subnet_address_prefix=subnet_address_prefix,
                                                                                  yes=yes)
        else:
            parameters.network = source_server_object.network

    except Exception as e:
        raise ResourceNotFoundError(e)

    resolve_poller(
        client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        'Restore Server')

    restore_server_object = client.get(resource_group_name, server_name)
    restore_server_network = restore_server_object.network
    restore_server_network.public_network_access = public_access if public_access else source_server_object.network.public_network_access
    update_parameter = mysql_flexibleservers.models.ServerForUpdate(network=restore_server_network)

    return sdk_no_wait(no_wait, client.begin_update, resource_group_name, server_name, update_parameter)


# pylint: disable=too-many-locals, too-many-statements, raise-missing-from
def flexible_server_georestore(cmd, client, resource_group_name, server_name, source_server, location, zone=None, no_wait=False,
                               subnet=None, subnet_address_prefix=None, vnet=None, vnet_address_prefix=None, tags=None,
                               private_dns_zone_arguments=None, public_access=None, yes=False, sku_name=None, tier=None,
                               storage_gb=None, auto_grow=None, backup_retention=None, geo_redundant_backup=None):
    provider = 'Microsoft.DBforMySQL'
    server_name = server_name.lower()

    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server_id = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace=provider,
                type='flexibleServers',
                name=source_server)
        else:
            raise ValueError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    try:
        id_parts = parse_resource_id(source_server_id)
        source_server_object = client.get(id_parts['resource_group'], id_parts['name'])
        list_skus_info = get_mysql_list_skus_info(cmd, location)

        if not tier:
            tier = source_server_object.sku.tier
        else:
            mysql_restore_tier_validator(tier, source_server_object.sku.tier, list_skus_info['sku_info'])

        if not sku_name:
            sku_name = source_server_object.sku.name
        else:
            mysql_sku_name_validator(sku_name, list_skus_info['sku_info'], tier, None)

        if not storage_gb:
            storage_gb = source_server_object.storage.storage_size_gb
        else:
            mysql_storage_validator(storage_gb, list_skus_info['sku_info'], tier, source_server_object)

        if not auto_grow:
            auto_grow = source_server_object.storage.auto_grow
        else:
            mysql_auto_grow_validator(auto_grow, None, None, source_server_object)

        if not backup_retention:
            backup_retention = source_server_object.backup.backup_retention_days
        else:
            mysql_retention_validator(backup_retention, list_skus_info['sku_info'], tier)

        if not geo_redundant_backup:
            geo_redundant_backup = source_server_object.backup.geo_redundant_backup
        else:
            mysql_georedundant_backup_validator(geo_redundant_backup, list_skus_info['geo_paired_regions'])

        db_context = DbContext(
            cmd=cmd, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
            cf_availability=cf_mysql_check_resource_availability,
            cf_availability_without_location=cf_mysql_check_resource_availability_without_location,
            cf_private_dns_zone_suffix=cf_mysql_flexible_private_dns_zone_suffix_operations,
            logging_name='MySQL', command_group='mysql', server_client=client, location=source_server_object.location)

        validate_server_name(db_context, server_name, provider + '/flexibleServers')
        validate_georestore_location(db_context, location)

        identity, data_encryption = get_identity_and_data_encryption(source_server_object)

        iops = _determine_iops(storage_gb=storage_gb, iops_info=list_skus_info['iops_info'],
                               iops_input=source_server_object.storage.iops, tier=tier, sku_name=sku_name)

        storage = mysql_flexibleservers.models.Storage(storage_size_gb=storage_gb, iops=iops, auto_grow=auto_grow,
                                                       auto_io_scaling=source_server_object.storage.auto_io_scaling)

        backup = mysql_flexibleservers.models.Backup(backup_retention_days=backup_retention,
                                                     geo_redundant_backup=geo_redundant_backup)

        sku = mysql_flexibleservers.models.Sku(name=sku_name, tier=tier)

        parameters = mysql_flexibleservers.models.Server(
            tags=tags,
            location=location,
            source_server_resource_id=source_server_id,  # this should be the source server name, not id
            create_mode="GeoRestore",
            availability_zone=zone,
            identity=identity,
            data_encryption=data_encryption,
            sku=sku,
            storage=storage,
            backup=backup
        )

        db_context.location = location
        if source_server_object.network.public_network_access == 'Enabled' and not any((public_access, vnet, subnet)):
            public_access = 'Enabled'

        parameters.network, _, _ = flexible_server_provision_network_resource(cmd=cmd,
                                                                              resource_group_name=resource_group_name,
                                                                              server_name=server_name,
                                                                              location=location,
                                                                              db_context=db_context,
                                                                              private_dns_zone_arguments=private_dns_zone_arguments,
                                                                              public_access=public_access,
                                                                              vnet=vnet,
                                                                              subnet=subnet,
                                                                              vnet_address_prefix=vnet_address_prefix,
                                                                              subnet_address_prefix=subnet_address_prefix,
                                                                              yes=yes)

    except Exception as e:
        raise ResourceNotFoundError(e)

    resolve_poller(
        client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        'GeoRestore Server')

    restore_server_object = client.get(resource_group_name, server_name)
    restore_server_network = restore_server_object.network

    if public_access is not None:
        restore_server_network.public_network_access = public_access

    update_parameter = mysql_flexibleservers.models.ServerForUpdate(network=restore_server_network)

    return sdk_no_wait(no_wait, client.begin_update, resource_group_name, server_name, update_parameter)


# pylint: disable=too-many-branches, disable=too-many-locals, too-many-statements, raise-missing-from
def flexible_server_update_custom_func(cmd, client, instance,
                                       sku_name=None,
                                       tier=None,
                                       storage_gb=None,
                                       auto_grow=None,
                                       iops=None,
                                       auto_scale_iops=None,
                                       backup_retention=None,
                                       geo_redundant_backup=None,
                                       administrator_login_password=None,
                                       high_availability=None,
                                       standby_availability_zone=None,
                                       maintenance_window=None,
                                       tags=None,
                                       replication_role=None,
                                       byok_identity=None, backup_byok_identity=None, byok_key=None, backup_byok_key=None,
                                       disable_data_encryption=False,
                                       public_access=None):
    # validator
    location = ''.join(instance.location.lower().split())
    db_context = DbContext(
        cmd=cmd, cf_firewall=cf_mysql_flexible_firewall_rules, cf_db=cf_mysql_flexible_db,
        cf_availability=cf_mysql_check_resource_availability,
        cf_availability_without_location=cf_mysql_check_resource_availability_without_location,
        logging_name='MySQL', command_group='mysql', server_client=client, location=instance.location)

    # MySQL chnged MemoryOptimized tier to BusinessCritical (only in client tool not in list-skus return)
    if tier == 'BusinessCritical':
        tier = 'MemoryOptimized'
    mysql_arguments_validator(db_context,
                              location=location,
                              tier=tier,
                              sku_name=sku_name,
                              storage_gb=storage_gb,
                              backup_retention=backup_retention,
                              high_availability=high_availability,
                              zone=instance.availability_zone,
                              standby_availability_zone=standby_availability_zone,
                              auto_grow=auto_grow,
                              replication_role=replication_role,
                              instance=instance,
                              geo_redundant_backup=geo_redundant_backup,
                              byok_identity=byok_identity,
                              backup_byok_identity=backup_byok_identity,
                              byok_key=byok_key,
                              backup_byok_key=backup_byok_key,
                              disable_data_encryption=disable_data_encryption,
                              auto_io_scaling=auto_scale_iops,
                              iops=iops)

    list_skus_info = get_mysql_list_skus_info(db_context.cmd, location, server_name=instance.name if instance else None)
    iops_info = list_skus_info['iops_info']

    server_module_path = instance.__module__
    module = import_module(server_module_path)  # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    if sku_name:
        instance.sku.name = sku_name

    if tier:
        validate_mysql_tier_update(instance, tier)
        instance.sku.tier = tier

    if backup_retention:
        instance.backup.backup_retention_days = backup_retention

    if geo_redundant_backup:
        instance.backup.geo_redundant_backup = geo_redundant_backup

    if maintenance_window:
        # if disabled is pass in reset to default values
        if maintenance_window.lower() == "disabled":
            day_of_week = start_hour = start_minute = 0
            custom_window = "Disabled"
        else:
            day_of_week, start_hour, start_minute = parse_maintenance_window(maintenance_window)
            custom_window = "Enabled"

        # set values - if maintenance_window when is None when created then create a new object
        instance.maintenance_window.day_of_week = day_of_week
        instance.maintenance_window.start_hour = start_hour
        instance.maintenance_window.start_minute = start_minute
        instance.maintenance_window.custom_window = custom_window

        params = ServerForUpdate(maintenance_window=instance.maintenance_window)
        logger.warning("You can update maintenance window only when updating maintenance window. Please update other properties separately if you are updating them as well.")
        return params

    if high_availability:
        if high_availability.lower() != "disabled":
            instance.high_availability.mode = high_availability
            if standby_availability_zone:
                instance.high_availability.standby_availability_zone = standby_availability_zone
        else:
            instance.high_availability = mysql_flexibleservers.models.HighAvailability(mode=high_availability)

    identity, data_encryption = build_identity_and_data_encryption(db_engine='mysql',
                                                                   byok_identity=byok_identity,
                                                                   backup_byok_identity=backup_byok_identity,
                                                                   byok_key=byok_key,
                                                                   backup_byok_key=backup_byok_key)
    if disable_data_encryption:
        data_encryption = mysql_flexibleservers.models.DataEncryption(type="SystemManaged")

    if disable_data_encryption or byok_key:
        server_operations_client = cf_mysql_flexible_servers(cmd.cli_ctx, '_')
        replica_operations_client = cf_mysql_flexible_replica(cmd.cli_ctx, '_')

        from azure.cli.core.util import parse_proxy_resource_id
        resource_group_name = parse_proxy_resource_id(instance.id)['resource_group']

        replicas = replica_operations_client.list_by_server(resource_group_name, instance.name)
        for replica in replicas:
            resolve_poller(
                server_operations_client.begin_update(
                    resource_group_name=resource_group_name,
                    server_name=replica.name,
                    parameters=ServerForUpdate(identity=identity, data_encryption=data_encryption)),
                cmd.cli_ctx, 'Updating data encryption to replica {}'.format(replica.name)
            )

    if storage_gb:
        instance.storage.storage_size_gb = storage_gb

    if auto_scale_iops:
        instance.storage.auto_io_scaling = auto_scale_iops

    if not iops:
        iops = instance.storage.iops
    instance.storage.iops = _determine_iops(storage_gb=instance.storage.storage_size_gb,
                                            iops_info=iops_info,
                                            iops_input=iops,
                                            tier=instance.sku.tier,
                                            sku_name=instance.sku.name)

    if auto_grow:
        instance.storage.auto_grow = auto_grow

    if public_access:
        instance.network.public_network_access = public_access

    params = ServerForUpdate(sku=instance.sku,
                             storage=instance.storage,
                             backup=instance.backup,
                             administrator_login_password=administrator_login_password,
                             high_availability=instance.high_availability,
                             tags=tags,
                             identity=identity,
                             data_encryption=data_encryption,
                             network=instance.network)

    return params


def server_delete_func(cmd, client, resource_group_name, server_name, yes=None):
    result = None  # default return value

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name,
                                                                                              resource_group_name), yes=yes)
    try:
        result = client.begin_delete(resource_group_name, server_name)
        if cmd.cli_ctx.local_context.is_on:
            local_context_file = cmd.cli_ctx.local_context._get_local_context_file()  # pylint: disable=protected-access
            local_context_file.remove_option('mysql flexible-server', 'server_name')
            local_context_file.remove_option('mysql flexible-server', 'administrator_login')
            local_context_file.remove_option('mysql flexible-server', 'database_name')

    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
        raise CLIError(ex)
    return result


def flexible_server_restart(cmd, client, resource_group_name, server_name, fail_over=None):
    instance = client.get(resource_group_name, server_name)
    if fail_over is not None and instance.high_availability.mode != "ZoneRedundant":
        raise ArgumentUsageError("Failing over can only be triggered for zone redundant servers.")

    if fail_over is not None:
        if fail_over != 'Forced':
            raise InvalidArgumentValueError("Allowed failover parameters are 'Forced'.")
        parameters = mysql_flexibleservers.models.ServerRestartParameter(restart_with_failover='Enabled')
    else:
        parameters = mysql_flexibleservers.models.ServerRestartParameter(restart_with_failover='Disabled')

    return resolve_poller(
        client.begin_restart(resource_group_name, server_name, parameters), cmd.cli_ctx, 'MySQL Server Restart')


def flexible_server_provision_network_resource(cmd, resource_group_name, server_name,
                                               location, db_context, private_dns_zone_arguments=None, public_access=None,
                                               vnet=None, subnet=None, vnet_address_prefix=None, subnet_address_prefix=None, yes=False):
    start_ip = -1
    end_ip = -1
    network = mysql_flexibleservers.models.Network()

    if subnet is not None or vnet is not None:
        subnet_id = prepare_private_network(cmd,
                                            resource_group_name,
                                            server_name,
                                            vnet=vnet,
                                            subnet=subnet,
                                            location=location,
                                            delegation_service_name=DELEGATION_SERVICE_NAME,
                                            vnet_address_pref=vnet_address_prefix,
                                            subnet_address_pref=subnet_address_prefix,
                                            yes=yes)
        private_dns_zone_id = prepare_private_dns_zone(db_context,
                                                       'MySQL',
                                                       resource_group_name,
                                                       server_name,
                                                       private_dns_zone=private_dns_zone_arguments,
                                                       subnet_id=subnet_id,
                                                       location=location,
                                                       yes=yes)
        network.delegated_subnet_resource_id = subnet_id
        network.private_dns_zone_resource_id = private_dns_zone_id
        network.public_network_access = 'Disabled'
    elif subnet is None and vnet is None and private_dns_zone_arguments is not None:
        raise RequiredArgumentMissingError("Private DNS zone can only be used with private access setting. Use vnet or/and subnet parameters.")
    else:
        start_ip, end_ip = prepare_public_network(public_access, yes=yes)
        if public_access is not None and str(public_access).lower() == 'Disabled'.lower():
            network.public_network_access = 'Disabled'
        else:
            network.public_network_access = 'Enabled'
    return network, start_ip, end_ip


def flexible_server_exist_network_resource(cmd, resource_group_name, server_name, location, private_dns_zone_arguments=None, vnet=None, subnet=None):
    network = mysql_flexibleservers.models.Network()
    if private_dns_zone_arguments is None:
        raise RequiredArgumentMissingError("Missing Private DNS Zone. If you want to use private access, --private-dns-zone is requried.")

    if subnet is not None or vnet is not None:
        subnet_id = prepare_mysql_exist_private_network(cmd, resource_group_name, server_name, vnet, subnet, location, DELEGATION_SERVICE_NAME)

        private_dns_zone_id = prepare_mysql_exist_private_dns_zone(cmd, resource_group_name, private_dns_zone_arguments, subnet_id)

        network.delegated_subnet_resource_id = subnet_id
        network.private_dns_zone_resource_id = private_dns_zone_id
    else:
        raise RequiredArgumentMissingError("Private DNS zone can only be used with private access setting. Use vnet or/and subnet parameters.")

    return network


# Parameter update command
def flexible_parameter_update(client, server_name, configuration_name, resource_group_name, source=None, value=None):
    if source is None and value is None:
        # update the command with system default
        try:
            parameter = client.get(resource_group_name, server_name, configuration_name)
            value = parameter.default_value  # reset value to default
            source = "system-default"
        except CloudError as e:
            raise CLIError('Unable to get default parameter value: {}.'.format(str(e)))
    elif source is None:
        source = "user-override"

    parameters = mysql_flexibleservers.models.Configuration(
        name=configuration_name,
        value=value,
        source=source
    )

    return client.begin_update(resource_group_name, server_name, configuration_name, parameters)


# Replica commands
# Custom functions for server replica, will add MySQL part after backend ready in future
def flexible_replica_create(cmd, client, resource_group_name, source_server, replica_name, location=None, tags=None,
                            private_dns_zone_arguments=None, vnet=None, subnet=None, zone=None, public_access=None, no_wait=False):
    provider = 'Microsoft.DBforMySQL'
    replica_name = replica_name.lower()

    # set source server id
    if not is_valid_resource_id(source_server):
        if len(source_server.split('/')) == 1:
            source_server_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                           resource_group=resource_group_name,
                                           namespace=provider,
                                           type='flexibleServers',
                                           name=source_server)
        else:
            raise CLIError('The provided source-server {} is invalid.'.format(source_server))
    else:
        source_server_id = source_server

    source_server_id_parts = parse_resource_id(source_server_id)
    try:
        source_server_object = client.get(source_server_id_parts['resource_group'], source_server_id_parts['name'])
        validate_mysql_replica(source_server_object)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if not location:
        location = source_server_object.location

    sku_name = source_server_object.sku.name
    tier = source_server_object.sku.tier

    identity, data_encryption = get_identity_and_data_encryption(source_server_object)

    parameters = mysql_flexibleservers.models.Server(
        sku=mysql_flexibleservers.models.Sku(name=sku_name, tier=tier),
        source_server_resource_id=source_server_id,
        location=location,
        tags=tags,
        availability_zone=zone,
        identity=identity,
        data_encryption=data_encryption,
        create_mode="Replica")

    if any((vnet, subnet, private_dns_zone_arguments)):
        parameters.network = flexible_server_exist_network_resource(cmd,
                                                                    resource_group_name,
                                                                    replica_name,
                                                                    location,
                                                                    private_dns_zone_arguments,
                                                                    vnet,
                                                                    subnet)

    resolve_poller(client.begin_create(resource_group_name, replica_name, parameters), cmd.cli_ctx, 'Create Replica')

    replica_server_object = client.get(resource_group_name, replica_name)
    replica_server_network = replica_server_object.network

    if public_access is not None:
        replica_server_network.public_network_access = public_access

    update_parameter = mysql_flexibleservers.models.ServerForUpdate(network=replica_server_network)

    return sdk_no_wait(no_wait, client.begin_update, resource_group_name, replica_name, update_parameter)


def flexible_replica_stop(client, resource_group_name, server_name):
    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if server_object.replication_role is not None and server_object.replication_role.lower() != "replica":
        raise CLIError('Server {} is not a replica server.'.format(server_name))

    server_module_path = server_object.__module__
    module = import_module(server_module_path)  # replacement not needed for update in flex servers
    ServerForUpdate = getattr(module, 'ServerForUpdate')

    params = ServerForUpdate(replication_role='None')

    return client.begin_update(resource_group_name, server_name, params)


def flexible_server_mysql_get(cmd, resource_group_name, server_name):
    client = get_mysql_flexible_management_client(cmd.cli_ctx)
    return client.servers.get(resource_group_name, server_name)


def flexible_list_skus(cmd, client, location):
    result = client.list(location)
    result = replace_memory_optimized_tier(result)
    logger.warning('For prices please refer to https://aka.ms/mysql-pricing')
    return result


def _create_server(db_context, cmd, resource_group_name, server_name, tags, location, sku, administrator_login, administrator_login_password,
                   storage, backup, network, version, high_availability, availability_zone, identity, data_encryption):
    logging_name, server_client = db_context.logging_name, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/mysql-pricing for pricing details', server_name, sku.name)
    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.
    parameters = mysql_flexibleservers.models.Server(
        tags=tags,
        location=location,
        identity=identity,
        sku=sku,
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        storage=storage,
        backup=backup,
        network=network,
        version=version,
        high_availability=high_availability,
        availability_zone=availability_zone,
        data_encryption=data_encryption,
        create_mode="Create")

    return resolve_poller(
        server_client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Create'.format(logging_name))


def _import_create_server(db_context, cmd, resource_group_name, server_name, source_server_id, tags, location, sku, administrator_login, administrator_login_password,
                          storage, backup, network, version, high_availability, availability_zone, identity, data_encryption):
    logging_name, server_client = db_context.logging_name, db_context.server_client
    logger.warning('Creating %s Server \'%s\' in group \'%s\'...', logging_name, server_name, resource_group_name)

    logger.warning('Your server \'%s\' is using sku \'%s\' (Paid Tier). '
                   'Please refer to https://aka.ms/mysql-pricing for pricing details', server_name, sku.name)
    # Note : passing public-network-access has no effect as the accepted values are 'Enabled' and 'Disabled'.
    # So when you pass an IP here(from the CLI args of public_access), it ends up being ignored.
    parameters = mysql_flexibleservers.models.Server(
        tags=tags,
        location=location,
        identity=identity,
        sku=sku,
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        storage=storage,
        backup=backup,
        network=network,
        version=version,
        high_availability=high_availability,
        availability_zone=availability_zone,
        data_encryption=data_encryption,
        source_server_resource_id=source_server_id,
        create_mode="Migrate")

    return resolve_poller(
        server_client.begin_create(resource_group_name, server_name, parameters), cmd.cli_ctx,
        '{} Server Import Create'.format(logging_name))


def flexible_server_connection_string(
        server_name='{server}', database_name='{database}', administrator_login='{login}',
        administrator_login_password='{password}'):
    host = '{}.mysql.database.azure.com'.format(server_name)
    if database_name is None:
        database_name = 'mysql'
    return {
        'connectionStrings': _create_mysql_connection_strings(host, administrator_login, administrator_login_password,
                                                              database_name)
    }


def _create_mysql_connection_strings(host, user, password, database):
    result = {
        'mysql_cmd': "mysql {database} --host {host} --user {user} --password={password}",
        'ado.net': "Server={host}; Port=3306; Database={database}; Uid={user}; Pwd={password};",
        'jdbc': "jdbc:mysql://{host}:3306/{database}?user={user}&password={password}",
        'jdbc Spring': "spring.datasource.url=jdbc:mysql://{host}:3306/{database}  "
                       "spring.datasource.username={user}  "
                       "spring.datasource.password={password}",
        'node.js': "var conn = mysql.createConnection({{host: '{host}', user: '{user}', "
                   "password: {password}, database: {database}, port: 3306}});",
        'php': "$con=mysqli_init(); [mysqli_ssl_set($con, NULL, NULL, {{ca-cert filename}}, NULL, NULL);] mysqli_real_connect($con, '{host}', '{user}', '{password}', '{database}', 3306);",
        'python': "cnx = mysql.connector.connect(user='{user}', password='{password}', host='{host}', "
                  "port=3306, database='{database}')",
        'ruby': "client = Mysql2::Client.new(username: '{user}', password: '{password}', "
                "database: '{database}', host: '{host}', port: 3306)",
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


def _form_response(username, sku, location, server_id, host, version, password, connection_string, database_name=None,
                   firewall_id=None, subnet_id=None):
    output = {
        'host': host,
        'username': username,
        'password': password,
        'skuname': sku,
        'location': location,
        'id': server_id,
        'version': version,
        'connectionString': connection_string
    }
    if database_name is not None:
        output['databaseName'] = database_name
    if firewall_id is not None:
        output['firewallName'] = firewall_id
    if subnet_id is not None:
        output['subnetId'] = subnet_id
    return output


def _update_local_contexts(cmd, server_name, resource_group_name, location, user):
    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'server_name',
                                      server_name)  # Setting the server name in the local context
        cmd.cli_ctx.local_context.set([ALL], 'location',
                                      location)  # Setting the location in the local context
        cmd.cli_ctx.local_context.set([ALL], 'resource_group_name', resource_group_name)
        cmd.cli_ctx.local_context.set(['mysql flexible-server'], 'administrator_login',
                                      user)  # Setting the server name in the local context


def _create_database(db_context, cmd, resource_group_name, server_name, database_name):
    # check for existing database, create if not
    cf_db, logging_name = db_context.cf_db, db_context.logging_name
    database_client = cf_db(cmd.cli_ctx, None)

    logger.warning('Creating %s database \'%s\'...', logging_name, database_name)
    parameters = {
        'name': database_name,
        'charset': 'utf8',
        'collation': 'utf8_general_ci'
    }
    resolve_poller(
        database_client.begin_create_or_update(resource_group_name, server_name, database_name, parameters), cmd.cli_ctx,
        '{} Database Create/Update'.format(logging_name))


def database_create_func(client, resource_group_name, server_name, database_name=None, charset=None, collation=None):

    if charset is None and collation is None:
        charset = 'utf8'
        collation = 'utf8_general_ci'
        logger.warning("Creating database with utf8 charset and utf8_general_ci collation")
    elif (not charset and collation) or (charset and not collation):
        raise RequiredArgumentMissingError("charset and collation have to be input together.")

    parameters = {
        'name': database_name,
        'charset': charset,
        'collation': collation
    }

    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        database_name,
        parameters)


def _create_mysql_connection_string(host, database_name, user_name, password):
    connection_kwargs = {
        'host': host,
        'username': user_name,
        'password': password if password is not None else '{password}'
    }
    if database_name is not None:
        connection_kwargs['dbname'] = database_name
        return 'mysql {dbname} --host {host} --user {username} --password={password}'.format(**connection_kwargs)
    return 'mysql --host {host} --user {username} --password={password}'.format(**connection_kwargs)


def _determine_iops(storage_gb, iops_info, iops_input, tier, sku_name):
    max_supported_iops = iops_info[tier][sku_name]
    free_iops = get_free_iops(storage_in_mb=storage_gb * 1024,
                              iops_info=iops_info,
                              tier=tier,
                              sku_name=sku_name)

    iops = free_iops
    if iops_input and iops_input > free_iops:
        iops = min(iops_input, max_supported_iops)

    logger.warning("IOPS is %d which is either your input or free(maximum) IOPS supported for your storage size and SKU.", iops)
    return iops


def get_free_iops(storage_in_mb, iops_info, tier, sku_name):
    free_iops = MINIMUM_IOPS + (storage_in_mb // 1024) * 3
    max_supported_iops = iops_info[tier][sku_name]  # free iops cannot exceed maximum supported iops for the sku

    return min(free_iops, max_supported_iops)


# Custom functions for identity
def flexible_server_identity_assign(cmd, client, resource_group_name, server_name, identities):
    instance = client.get(resource_group_name, server_name)
    if instance.replication_role == 'Replica':
        raise CLIError("Cannot assign identities to a server with replication role. Use the primary server instead.")

    identities_map = {}
    for identity in identities:
        identities_map[identity] = {}

    parameters = {
        'identity': mysql_flexibleservers.models.Identity(
            user_assigned_identities=identities_map,
            type="UserAssigned")}

    replica_operations_client = cf_mysql_flexible_replica(cmd.cli_ctx, '_')

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)
    for replica in replicas:
        resolve_poller(
            client.begin_update(
                resource_group_name=resource_group_name,
                server_name=replica.name,
                parameters=parameters),
            cmd.cli_ctx, 'Adding identities to replica {}'.format(replica.name)
        )

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Adding identities to server {}'.format(server_name)
    )

    return result.identity


def flexible_server_identity_remove(cmd, client, resource_group_name, server_name, identities):
    instance = client.get(resource_group_name, server_name)

    if instance.replication_role == 'Replica':
        raise CLIError("Cannot remove identities from a server with replication role. Use the primary server instead.")

    if instance.data_encryption:
        primary_id = instance.data_encryption.primary_user_assigned_identity_id
        backup_id = instance.data_encryption.geo_backup_user_assigned_identity_id

        if primary_id and primary_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for data encryption.".format(primary_id))

        if backup_id and backup_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for data encryption.".format(backup_id))

    admin_operations_client = cf_mysql_flexible_adadmin(cmd.cli_ctx, '_')

    admins = admin_operations_client.list_by_server(resource_group_name, server_name)
    common_identities = [identity for identity in identities if identity.lower() in [admin.identity_resource_id.lower() for admin in admins]]
    if len(common_identities) > 0:
        raise CLIError("Cannot remove identities {} because they're used for server admin.".format(common_identities))

    identities_map = {}
    for identity in identities:
        identities_map[identity] = None

    if not (instance.identity and instance.identity.user_assigned_identities) or \
       all(key.lower() in [identity.lower() for identity in identities] for key in instance.identity.user_assigned_identities.keys()):
        parameters = {
            'identity': mysql_flexibleservers.models.Identity(
                type="None")}
    else:
        parameters = {
            'identity': mysql_flexibleservers.models.Identity(
                user_assigned_identities=identities_map,
                type="UserAssigned")}

    replica_operations_client = cf_mysql_flexible_replica(cmd.cli_ctx, '_')

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)
    for replica in replicas:
        resolve_poller(
            client.begin_update(
                resource_group_name=resource_group_name,
                server_name=replica.name,
                parameters=parameters),
            cmd.cli_ctx, 'Removing identities from replica {}'.format(replica.name)
        )

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Removing identities from server {}'.format(server_name)
    )

    return result.identity or mysql_flexibleservers.models.Identity()


def flexible_server_identity_list(client, resource_group_name, server_name):
    server = client.get(resource_group_name, server_name)
    return server.identity or mysql_flexibleservers.models.Identity()


def flexible_server_identity_show(client, resource_group_name, server_name, identity):
    server = client.get(resource_group_name, server_name)

    for key, value in server.identity.user_assigned_identities.items():
        if key.lower() == identity.lower():
            return value

    raise CLIError("Identity '{}' does not exist in server {}.".format(identity, server_name))


# Custom functions for ad-admin
def flexible_server_ad_admin_set(cmd, client, resource_group_name, server_name, login, sid, identity):
    server_operations_client = cf_mysql_flexible_servers(cmd.cli_ctx, '_')
    replica_operations_client = cf_mysql_flexible_replica(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if instance.replication_role == 'Replica':
        raise CLIError("Cannot create an AD admin on a server with replication role. Use the primary server instead.")

    parameters = {
        'identity': mysql_flexibleservers.models.Identity(
            user_assigned_identities={identity: {}},
            type="UserAssigned")}

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)
    for replica in replicas:
        if not (replica.identity and replica.identity.user_assigned_identities and
           identity.lower() in [key.lower() for key in replica.identity.user_assigned_identities.keys()]):
            resolve_poller(
                server_operations_client.begin_update(
                    resource_group_name=resource_group_name,
                    server_name=replica.name,
                    parameters=parameters),
                cmd.cli_ctx, 'Adding identity {} to replica {}'.format(identity, replica.name)
            )

    if not (instance.identity and instance.identity.user_assigned_identities and
       identity.lower() in [key.lower() for key in instance.identity.user_assigned_identities.keys()]):
        resolve_poller(
            server_operations_client.begin_update(
                resource_group_name=resource_group_name,
                server_name=server_name,
                parameters=parameters),
            cmd.cli_ctx, 'Adding identity {} to server {}'.format(identity, server_name))

    parameters = {
        'administratorType': 'ActiveDirectory',
        'login': login,
        'sid': sid,
        'tenant_id': get_tenant_id(),
        'identity_resource_id': identity
    }

    return client.begin_create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        administrator_name='ActiveDirectory',
        parameters=parameters)


def flexible_server_ad_admin_delete(cmd, client, resource_group_name, server_name):
    server_operations_client = cf_mysql_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if instance.replication_role == 'Replica':
        raise CLIError("Cannot delete an AD admin on a server with replication role. Use the primary server instead.")

    replica_operations_client = cf_mysql_flexible_replica(cmd.cli_ctx, '_')
    config_operations_client = cf_mysql_flexible_config(cmd.cli_ctx, '_')

    resolve_poller(
        client.begin_delete(
            resource_group_name=resource_group_name,
            server_name=server_name,
            administrator_name='ActiveDirectory'),
        cmd.cli_ctx, 'Dropping AD admin in server {}'.format(server_name))

    configuration_name = 'aad_auth_only'
    parameters = mysql_flexibleservers.models.Configuration(
        name=configuration_name,
        value='OFF',
        source='user-override'
    )

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)
    for replica in replicas:
        if config_operations_client.get(resource_group_name, replica.name, configuration_name).value == "ON":
            resolve_poller(
                config_operations_client.begin_update(resource_group_name, replica.name, configuration_name, parameters),
                cmd.cli_ctx, 'Disabling aad_auth_only in replica {}'.format(replica.name))

    if config_operations_client.get(resource_group_name, server_name, configuration_name).value == "ON":
        resolve_poller(
            config_operations_client.begin_update(resource_group_name, server_name, configuration_name, parameters),
            cmd.cli_ctx, 'Disabling aad_auth_only in server {}'.format(server_name))


def flexible_server_ad_admin_list(client, resource_group_name, server_name):
    return client.list_by_server(
        resource_group_name=resource_group_name,
        server_name=server_name)


def flexible_server_ad_admin_show(client, resource_group_name, server_name):
    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        administrator_name='ActiveDirectory')


def flexible_gtid_reset(client, resource_group_name, server_name, gtid_set, no_wait=False, yes=False):
    try:
        server_object = client.get(resource_group_name, server_name)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if server_object.backup.geo_redundant_backup.lower() == "enabled":
        raise CLIError("GTID reset can't be performed on a Geo-redundancy backup enabled server. Please disable Geo-redundancy to perform GTID reset on the server. "
                       "You can enable Geo-redundancy option again after GTID reset. GTID reset action invalidates all the available backups and therefore, "
                       "once Geo-redundancy is enabled again, it may take a day before geo-restore can be performed on the server.")

    user_confirmation("Resetting GTID will invalidate all the automated/on-demand backups that were taken before the reset action and you will not be able "
                      "to perform PITR (point-in-time-restore) using fastest restore point or by custom restore point if the selected restore time is before"
                      " the GTID reset time. Do you want to continue?", yes=yes)

    parameters = mysql_flexibleservers.models.ServerGtidSetParameter(
        gtid_set=gtid_set
    )
    return sdk_no_wait(no_wait, client.begin_reset_gtid, resource_group_name, server_name, parameters)


# pylint: disable=too-many-instance-attributes, too-few-public-methods, useless-object-inheritance
class DbContext(object):
    def __init__(self, cmd=None, azure_sdk=None, logging_name=None, cf_firewall=None, cf_db=None,
                 cf_availability=None, cf_availability_without_location=None, cf_private_dns_zone_suffix=None,
                 command_group=None, server_client=None, location=None):
        self.cmd = cmd
        self.azure_sdk = azure_sdk
        self.cf_firewall = cf_firewall
        self.cf_db = cf_db
        self.cf_availability = cf_availability
        self.cf_availability_without_location = cf_availability_without_location
        self.cf_private_dns_zone_suffix = cf_private_dns_zone_suffix
        self.logging_name = logging_name
        self.command_group = command_group
        self.server_client = server_client
        self.location = location
