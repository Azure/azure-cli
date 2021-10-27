# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel, raise-missing-from
import datetime as dt
from datetime import datetime
import os
import random
import subprocess
import secrets
import string
import yaml
from knack.log import get_logger
from knack.prompting import prompt_y_n, NoTTYException
from msrestazure.tools import parse_resource_id
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.util import CLIError
from azure.cli.core.azclierror import AuthenticationError
from azure.core.paging import ItemPaged
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.commands import LongRunningOperation, _is_poller
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError
from azure.cli.command_modules.role.custom import create_service_principal_for_rbac
from azure.mgmt.resource.resources.models import ResourceGroup
from ._client_factory import resource_client_factory, cf_mysql_flexible_location_capabilities, cf_postgres_flexible_location_capabilities

logger = get_logger(__name__)

DEFAULT_LOCATION_PG = 'eastus'  # For testing: 'eastus2euap'
DEFAULT_LOCATION_MySQL = 'westus2'
AZURE_CREDENTIALS = 'AZURE_CREDENTIALS'
AZURE_POSTGRESQL_CONNECTION_STRING = 'AZURE_POSTGRESQL_CONNECTION_STRING'
AZURE_MYSQL_CONNECTION_STRING = 'AZURE_MYSQL_CONNECTION_STRING'
GITHUB_ACTION_PATH = '/.github/workflows/'


def resolve_poller(result, cli_ctx, name):
    if _is_poller(result):
        return LongRunningOperation(cli_ctx, 'Starting {}'.format(name))(result)
    return result


def create_random_resource_name(prefix='azure', length=15):
    append_length = length - len(prefix)
    digits = [str(random.randrange(10)) for i in range(append_length)]
    return prefix + ''.join(digits)


def generate_missing_parameters(cmd, location, resource_group_name, server_name, db_engine):
    # If resource group is there in local context, check for its existence.
    if resource_group_name is not None:
        logger.warning('Checking the existence of the resource group \'%s\'...', resource_group_name)
        resource_group_exists = _check_resource_group_existence(cmd, resource_group_name)
        logger.warning('Resource group \'%s\' exists ? : %s ', resource_group_name, resource_group_exists)
    else:
        resource_group_exists = False

    # set location to be same as RG's if not specified
    if not resource_group_exists:
        if not location:
            location = DEFAULT_LOCATION_PG if db_engine == 'postgres' else DEFAULT_LOCATION_MySQL
        resource_group_name = _create_resource_group(cmd, location, resource_group_name)
    else:
        resource_group_client = resource_client_factory(cmd.cli_ctx).resource_groups
        resource_group = resource_group_client.get(resource_group_name=resource_group_name)
        if not location:
            location = resource_group.location

    # If servername is not passed, always create a new server - even if it is stored in the local context
    if server_name is None:
        server_name = create_random_resource_name('server')

    return location, resource_group_name, server_name.lower()


def generate_password(administrator_login_password):
    if administrator_login_password is None:
        passwordlength = 16
        administrator_login_password = secrets.token_urlsafe(passwordlength)
        index = administrator_login_password.find("-")
        if index != -1:
            replaced_char = random.choice(string.ascii_letters)
            administrator_login_password = administrator_login_password.replace("-", replaced_char)
    return administrator_login_password


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
    return _postgres_parse_list_skus(list_skus_result, 'postgres')


def get_mysql_list_skus_info(cmd, location):
    list_skus_client = cf_mysql_flexible_location_capabilities(cmd.cli_ctx, '_')
    list_skus_result = list_skus_client.list(location)
    return _mysql_parse_list_skus(list_skus_result, 'mysql')


def _postgres_parse_list_skus(result, database_engine):
    result = _get_list_from_paged_response(result)

    if not result:
        raise InvalidArgumentValueError("No available SKUs in this location")
    single_az = not result[0].zone_redundant_ha_supported

    tiers = result[0].supported_flexible_server_editions
    tiers_dict = {}
    for tier_info in tiers:
        tier_name = tier_info.name
        tier_dict = {}

        skus = set()
        versions = set()
        for version in tier_info.supported_server_versions:
            versions.add(version.name)
            for vcores in version.supported_vcores:
                skus.add(vcores.name)
        tier_dict["skus"] = skus
        tier_dict["versions"] = versions

        storage_info = tier_info.supported_storage_editions[0]
        storage_sizes = set()
        for size in storage_info.supported_storage_mb:
            storage_sizes.add(int(size.storage_size_mb // 1024))
        tier_dict["storage_sizes"] = storage_sizes

        tiers_dict[tier_name] = tier_dict

    return {'sku_info': tiers_dict,
            'single_az': single_az}


def _mysql_parse_list_skus(result, database_engine):
    result = _get_list_from_paged_response(result)
    if not result:
        raise InvalidArgumentValueError("No available SKUs in this location")
    single_az = 'ZoneRedundant' not in result[0].supported_ha_mode
    geo_paried_region = result[0].supported_geo_backup_regions

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
            for supported_sku in version.supported_skus:
                skus.add(supported_sku.name)
                sku_iops_dict[supported_sku.name] = supported_sku.supported_iops
        tier_dict["skus"] = skus
        tier_dict["versions"] = versions

        storage_info = tier_info.supported_storage_editions[0]

        tier_dict["backup_retention"] = (storage_info.min_backup_retention_days, storage_info.max_backup_retention_days)
        tier_dict["storage_sizes"] = (int(storage_info.min_storage_size) // 1024, int(storage_info.max_storage_size) // 1024)
        iops_dict[tier_name] = sku_iops_dict
        tiers_dict[tier_name] = tier_dict

    return {'sku_info': tiers_dict,
            'single_az': single_az,
            'iops_info': iops_dict,
            'geo_paired_regions': geo_paried_region}


def _get_available_values(sku_info, argument, tier=None):
    result = {key: val[argument] for key, val in sku_info.items()}
    return result[tier]


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, ItemPaged) else obj_list


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
    name = parsed_rid['name']
    child_name = parsed_rid['child_name_1'] if 'child_name_1' in parsed_rid else None

    return subscription, resource_group, name, child_name


def check_existence(resource_client, value, resource_group, provider_namespace, resource_type,
                    parent_name=None, parent_type=None):
    from azure.core.exceptions import HttpResponseError
    parent_path = ''
    if parent_name and parent_type:
        parent_path = '{}/{}'.format(parent_type, parent_name)

    api_version = _resolve_api_version(resource_client, provider_namespace, resource_type, parent_path)

    try:
        resource_client.resources.get(resource_group, provider_namespace, parent_path, resource_type, value, api_version)
    except HttpResponseError:
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


def run_subprocess(command, stdout_show=None):
    if stdout_show:
        process = subprocess.Popen(command, shell=True)
    else:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    if process.returncode:
        logger.warning(process.stderr.read().strip().decode('UTF-8'))


def run_subprocess_get_output(command):
    commands = command.split()
    process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    return process


def register_credential_secrets(cmd, database_engine, server, repository):
    logger.warning('Adding secret "AZURE_CREDENTIALS" to github repository')
    resource_group = parse_resource_id(server.id)["resource_group"]
    provider = "DBforMySQL"
    if database_engine == "postgresql":
        provider = "DBforPostgreSQL"
    scope = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.{}/flexibleServers/{}".format(get_subscription_id(cmd.cli_ctx), resource_group, provider, server.name)

    app = create_service_principal_for_rbac(cmd, name=server.name, role='contributor', scopes=[scope])
    app['clientId'], app['clientSecret'], app['tenantId'] = app.pop('appId'), app.pop('password'), app.pop('tenant')
    app['subscriptionId'] = get_subscription_id(cmd.cli_ctx)
    app.pop('displayName')
    app.pop('name')

    app_key_val = []
    for key, val in app.items():
        app_key_val.append('"{}": "{}"'.format(key, val))

    app_json = ',\n  '.join(app_key_val)
    app_json = '{\n  ' + app_json + '\n}'
    credential_file = "./temp_app_credential.txt"
    with open(credential_file, "w") as f:
        f.write(app_json)
    run_subprocess('gh secret set {} --repo {} < {}'.format(AZURE_CREDENTIALS, repository, credential_file))
    os.remove(credential_file)


def register_connection_secrets(cmd, database_engine, server, database_name, administrator_login, administrator_login_password, repository, connection_string_name):
    logger.warning("Added secret %s to github repository", connection_string_name)
    if database_engine == 'postgresql':
        connection_string = "host={} port=5432 dbname={} user={} password={} sslmode=require".format(server.fully_qualified_domain_name, database_name, administrator_login, administrator_login_password)
        run_subprocess('gh secret set {} --repo {} -b"{}"'.format(connection_string_name, repository, connection_string))
    elif database_engine == 'mysql':
        connection_string = "Server={}; Port=3306; Database={}; Uid={}; Pwd={}; SslMode=Preferred;".format(server.fully_qualified_domain_name, database_name, administrator_login, administrator_login_password)
        run_subprocess('gh secret set {} --repo {} -b"{}"'.format(connection_string_name, repository, connection_string))


def fill_action_template(cmd, database_engine, server, database_name, administrator_login, administrator_login_password, file_name, action_name, repository):

    action_dir = get_git_root_dir() + GITHUB_ACTION_PATH
    if not os.path.exists(action_dir):
        os.makedirs(action_dir)

    process = run_subprocess_get_output("gh secret list --repo {}".format(repository))
    github_secrets = process.stdout.read().strip().decode('UTF-8')
    # connection_string = AZURE_POSTGRESQL_CONNECTION_STRING if database_engine == 'postgresql' else AZURE_MYSQL_CONNECTION_STRING

    if AZURE_CREDENTIALS not in github_secrets:
        try:
            register_credential_secrets(cmd,
                                        database_engine=database_engine,
                                        server=server,
                                        repository=repository)
        except CloudError:
            raise AuthenticationError('You do not have authorization to create a service principal to run azure service in github actions. \n'
                                      'Please create a service principal that has access to the database server and add "AZURE_CREDENTIALS" secret to your github repository. \n'
                                      'Follow the instruction here "aka.ms/github-actions-azure-credentials".')

    connection_string_name = server.name.upper().replace("-", "_") + "_" + database_name.upper().replace("-", "_") + "_" + database_engine.upper() + "_CONNECTION_STRING"
    if connection_string_name not in github_secrets:
        register_connection_secrets(cmd,
                                    database_engine=database_engine,
                                    server=server,
                                    database_name=database_name,
                                    administrator_login=administrator_login,
                                    administrator_login_password=administrator_login_password,
                                    repository=repository,
                                    connection_string_name=connection_string_name)

    current_location = os.path.dirname(__file__)

    with open(current_location + "/templates/" + database_engine + "_githubaction_template.yaml", "r") as template_file:
        template = yaml.safe_load(template_file)
        template['jobs']['build']['steps'][2]['with']['server-name'] = server.fully_qualified_domain_name
        if database_engine == 'postgresql':
            template['jobs']['build']['steps'][2]['with']['plsql-file'] = file_name
        else:
            template['jobs']['build']['steps'][2]['with']['sql-file'] = file_name
        template['jobs']['build']['steps'][2]['with']['connection-string'] = "${{ secrets." + connection_string_name + " }}"
        with open(action_dir + action_name + '.yml', 'w', encoding='utf8') as yml_file:
            yml_file.write("on: [workflow_dispatch]\n")
            yml_file.write(yaml.dump(template))


def get_git_root_dir():
    process = run_subprocess_get_output("git rev-parse --show-toplevel")
    return process.stdout.read().strip().decode('UTF-8')


def get_user_confirmation(message, yes=False):
    if yes:
        return True
    try:
        if not prompt_y_n(message):
            return False
        return True
    except NoTTYException:
        raise CLIError(
            'Unable to prompt for confirmation as no tty available. Use --yes.')


def _is_resource_name(resource):
    if len(resource.split('/')) == 1:
        return True
    return False
