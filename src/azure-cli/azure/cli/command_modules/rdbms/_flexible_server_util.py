# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
import datetime as dt
from datetime import datetime
import random
from knack.log import get_logger
from azure.core.paging import ItemPaged
from azure.cli.core.commands import LongRunningOperation, _is_poller
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError
from azure.mgmt.resource.resources.models import ResourceGroup
from msrestazure.tools import parse_resource_id
from msrestazure.azure_exceptions import CloudError
from ._client_factory import resource_client_factory, cf_mysql_flexible_location_capabilities, cf_postgres_flexible_location_capabilities
from .flexible_server_custom_common import firewall_rule_create_func
logger = get_logger(__name__)

DEFAULT_LOCATION_PG = 'eastus'  # For testing: 'eastus2euap'
DEFAULT_LOCATION_MySQL = 'westus2'


def resolve_poller(result, cli_ctx, name):
    if _is_poller(result):
        return LongRunningOperation(cli_ctx, 'Starting {}'.format(name))(result)
    return result


def create_random_resource_name(prefix='azure', length=15):
    append_length = length - len(prefix)
    digits = [str(random.randrange(10)) for i in range(append_length)]
    return prefix + ''.join(digits)


def generate_missing_parameters(cmd, location, resource_group_name, server_name, db_engine):
    # if location is not passed as a parameter or is missing from local context
    if location is None:
        if db_engine == 'postgres':
            location = DEFAULT_LOCATION_PG
        else:
            location = DEFAULT_LOCATION_MySQL

    # If resource group is there in local context, check for its existence.
    resource_group_exists = True
    if resource_group_name is not None:
        logger.warning('Checking the existence of the resource group \'%s\'...', resource_group_name)
        resource_group_exists = _check_resource_group_existence(cmd, resource_group_name)
        logger.warning('Resource group \'%s\' exists ? : %s ', resource_group_name, resource_group_exists)

    # If resource group is not passed as a param or is not in local context or the rg in the local context has been deleted
    if not resource_group_exists or resource_group_name is None:
        resource_group_name = _create_resource_group(cmd, location, resource_group_name)

    # If servername is not passed, always create a new server - even if it is stored in the local context
    if server_name is None:
        server_name = create_random_resource_name('server')

    # This is for the case when user does not pass a location but the resource group exists in the local context.
    #  In that case, the location needs to be set to the location of the rg, not the default one.

    # TODO: Fix this because it changes the default location even when I pass in a location param
    # location = _update_location(cmd, resource_group_name)

    return location, resource_group_name, server_name.lower()


def generate_password(administrator_login_password):
    import secrets
    import string
    if administrator_login_password is None:
        passwordlength = 16
        administrator_login_password = secrets.token_urlsafe(passwordlength)
        index = administrator_login_password.find("-")
        if index != -1:
            replaced_char = random.choice(string.ascii_letters)
            administrator_login_password = administrator_login_password.replace("-", replaced_char)
    return administrator_login_password


def create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip):
    # allow access to azure ip addresses
    cf_firewall, logging_name = db_context.cf_firewall, db_context.logging_name  # NOQA pylint: disable=unused-variable
    now = datetime.now()
    firewall_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                 now.second)
    if start_ip == '0.0.0.0' and end_ip == '0.0.0.0':
        logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                       'Azure resources...')
        firewall_name = 'AllowAllAzureServicesAndResourcesWithinAzureIps_{}-{}-{}_{}-{}-{}'.format(now.year, now.month,
                                                                                                   now.day, now.hour,
                                                                                                   now.minute,
                                                                                                   now.second)
    elif start_ip == end_ip:
        logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip)
    else:
        if start_ip == '0.0.0.0' and end_ip == '255.255.255.255':
            firewall_name = 'AllowAll_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                now.second)
        logger.warning('Configuring server firewall rule to accept connections from \'%s\' to \'%s\'...', start_ip,
                       end_ip)
    firewall_client = cf_firewall(cmd.cli_ctx, None)

    # Commenting out until firewall_id is properly returned from RP
    # return resolve_poller(
    #    firewall_client.create_or_update(resource_group_name, server_name, firewall_name , start_ip, end_ip),
    #    cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))

    firewall = firewall_rule_create_func(firewall_client, resource_group_name, server_name, firewall_rule_name=firewall_name,
                                         start_ip_address=start_ip, end_ip_address=end_ip)

    return firewall.result().name


# pylint: disable=inconsistent-return-statements
def parse_public_access_input(public_access):
    # pylint: disable=no-else-return
    if public_access is not None:
        parsed_input = public_access.split('-')
        if len(parsed_input) == 1:
            return parsed_input[0], parsed_input[0]
        elif len(parsed_input) == 2:
            return parsed_input[0], parsed_input[1]
        else:
            raise InvalidArgumentValueError('incorrect usage: --public-access. Acceptable values are \'all\', \'none\',\'<startIP>\' and \'<startIP>-<destinationIP>\' '
                                            'where startIP and destinationIP ranges from 0.0.0.0 to 255.255.255.255')


def server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def flexible_firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


def update_kwargs(kwargs, key, value):
    if value is not None:
        kwargs[key] = value


def parse_maintenance_window(maintenance_window_string):
    parsed_input = maintenance_window_string.split(':')
    # pylint: disable=no-else-return
    if len(parsed_input) == 1:
        return _map_maintenance_window(parsed_input[0]), None, None
    elif len(parsed_input) == 2:
        return _map_maintenance_window(parsed_input[0]), parsed_input[1], None
    elif len(parsed_input) == 3:
        return _map_maintenance_window(parsed_input[0]), parsed_input[1], parsed_input[2]
    return None, None, None


def get_mysql_versions(sku_info, tier):
    return _get_available_values(sku_info, 'versions', tier)


def get_mysql_skus(sku_info, tier):
    return _get_available_values(sku_info, 'skus', tier)


def get_mysql_storage_size(sku_info, tier):
    return _get_available_values(sku_info, 'storage_sizes', tier)


def get_mysql_backup_retention(sku_info, tier):
    return _get_available_values(sku_info, 'backup_retention', tier)


def get_mysql_tiers(sku_info):
    return list(sku_info.keys())


def get_postgres_versions(sku_info, tier):
    return _get_available_values(sku_info, 'versions', tier)


def get_postgres_skus(sku_info, tier):
    return _get_available_values(sku_info, 'skus', tier)


def get_postgres_storage_sizes(sku_info, tier):
    return _get_available_values(sku_info, 'storage_sizes', tier)


def get_postgres_tiers(sku_info):
    return list(sku_info.keys())


def get_postgres_list_skus_info(cmd, location):
    list_skus_client = cf_postgres_flexible_location_capabilities(cmd.cli_ctx, '_')
    list_skus_result = list_skus_client.execute(location)
    return _parse_list_skus(list_skus_result, 'postgres')


def get_mysql_list_skus_info(cmd, location):
    list_skus_client = cf_mysql_flexible_location_capabilities(cmd.cli_ctx, '_')
    list_skus_result = list_skus_client.list(location)
    return _parse_list_skus(list_skus_result, 'mysql')


def _parse_list_skus(result, database_engine):
    result = _get_list_from_paged_response(result)
    if not result:
        raise InvalidArgumentValueError("No available SKUs in this location")

    tiers = result[0].supported_flexible_server_editions
    tiers_dict = {}
    iops_dict = {}
    for tier_info in tiers:
        tier_name = tier_info.name
        tier_dict = {}
        sku_iops_dict = {}

        skus = set()
        versions = set()
        for version in tier_info.supported_server_versions:
            versions.add(version.name)
            for vcores in version.supported_vcores:
                skus.add(vcores.name)
                if database_engine == 'mysql':
                    sku_iops_dict[vcores.name] = vcores.supported_iops
        tier_dict["skus"] = skus
        tier_dict["versions"] = versions

        storage_info = tier_info.supported_storage_editions[0]
        if database_engine == 'mysql':
            tier_dict["backup_retention"] = (storage_info.min_backup_retention_days, storage_info.max_backup_retention_days)
            tier_dict["storage_sizes"] = (int(storage_info.min_storage_size.storage_size_mb) // 1024,
                                          int(storage_info.max_storage_size.storage_size_mb) // 1024)
            iops_dict[tier_name] = sku_iops_dict
        elif database_engine == 'postgres':
            storage_sizes = set()
            for size in storage_info.supported_storage_mb:
                storage_sizes.add(int(size.storage_size_mb // 1024))
            tier_dict["storage_sizes"] = storage_sizes

        tiers_dict[tier_name] = tier_dict

    if database_engine == 'mysql':
        return tiers_dict, iops_dict
    return tiers_dict


def _get_available_values(sku_info, argument, tier=None):
    result = {key: val[argument] for key, val in sku_info.items()}
    return result[tier]


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, ItemPaged) else obj_list


def _update_location(cmd, resource_group_name):
    resource_client = resource_client_factory(cmd.cli_ctx)
    rg = resource_client.resource_groups.get(resource_group_name)
    location = rg.location
    return location


def _create_resource_group(cmd, location, resource_group_name):
    if resource_group_name is None:
        resource_group_name = create_random_resource_name('group')
    params = ResourceGroup(location=location)
    resource_client = resource_client_factory(cmd.cli_ctx)
    logger.warning('Creating Resource Group \'%s\'...', resource_group_name)
    resource_client.resource_groups.create_or_update(resource_group_name, params)
    return resource_group_name


def _check_resource_group_existence(cmd, resource_group_name):
    resource_client = resource_client_factory(cmd.cli_ctx)
    return resource_client.resource_groups.check_existence(resource_group_name)


# Map day_of_week string to integer to day of week
# Possible values can be 0 - 6
def _map_maintenance_window(day_of_week):
    options = {"Mon": 1,
               "Tue": 2,
               "Wed": 3,
               "Thu": 4,
               "Fri": 5,
               "Sat": 6,
               "Sun": 0,
               }
    return options[day_of_week]


def get_current_time():
    return datetime.utcnow().replace(tzinfo=dt.timezone.utc, microsecond=0).isoformat()


def get_id_components(rid):
    parsed_rid = parse_resource_id(rid)
    subscription = parsed_rid['subscription']
    resource_group = parsed_rid['resource_group']
    vnet_name = parsed_rid['name']
    subnet_name = parsed_rid['child_name_1'] if 'child_name_1' in parsed_rid else None

    return subscription, resource_group, vnet_name, subnet_name


def check_existence(resource_client, value, resource_group, provider_namespace, resource_type,
                    parent_name=None, parent_type=None):

    parent_path = ''
    if parent_name and parent_type:
        parent_path = '{}/{}'.format(parent_type, parent_name)

    api_version = _resolve_api_version(resource_client, provider_namespace, resource_type, parent_path)

    try:
        resource_client.resources.get(resource_group, provider_namespace, parent_path, resource_type, value, api_version)
    except CloudError:
        return False
    return True


def _resolve_api_version(client, provider_namespace, resource_type, parent_path):
    provider = client.providers.get(provider_namespace)

    # If available, we will use parent resource's api-version
    resource_type_str = (parent_path.split('/')[0] if parent_path else resource_type)

    rt = [t for t in provider.resource_types  # pylint: disable=no-member
          if t.resource_type.lower() == resource_type_str.lower()]
    if not rt:
        raise InvalidArgumentValueError('Resource type {} not found.'.format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    raise RequiredArgumentMissingError(
        'API version is required and could not be resolved for resource {}'
        .format(resource_type))
