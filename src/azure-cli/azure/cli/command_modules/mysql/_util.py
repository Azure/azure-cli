# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel, raise-missing-from
from enum import Enum
import json
import math
import os
import random
import secrets
import string
import subprocess
import yaml
from time import sleep
import datetime as dt
from datetime import datetime
from knack.log import get_logger
from knack.arguments import ignore_type
from knack.prompting import prompt_pass, prompt_y_n, NoTTYException
from azure.mgmt.core.tools import parse_resource_id
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.commands.progress import IndeterminateProgressBar
from azure.cli.core.util import CLIError, run_cmd
from azure.core.exceptions import HttpResponseError
from azure.core.paging import ItemPaged
from azure.core.rest import HttpRequest
from azure.cli.core.commands import LongRunningOperation, AzArgumentContext, _is_poller
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError, AuthenticationError
from azure.cli.command_modules.role.custom import create_service_principal_for_rbac
from azure.mgmt.mysqlflexibleservers import models
from azure.mgmt.resource.resources.models import ResourceGroup
from ._client_factory import resource_client_factory, cf_mysql_flexible_location_capabilities, get_mysql_flexible_management_client
from azure.cli.core.commands.validators import get_default_location_from_resource_group, validate_tags
from urllib.parse import urlencode, urlparse, parse_qsl

logger = get_logger(__name__)

DEFAULT_LOCATION = 'westus2'
AZURE_CREDENTIALS = 'AZURE_CREDENTIALS'
AZURE_POSTGRESQL_CONNECTION_STRING = 'AZURE_POSTGRESQL_CONNECTION_STRING'
AZURE_MYSQL_CONNECTION_STRING = 'AZURE_MYSQL_CONNECTION_STRING'
GITHUB_ACTION_PATH = '/.github/workflows/'


# pylint: disable=too-few-public-methods, import-outside-toplevel
class MysqlArgumentContext(AzArgumentContext):

    def __init__(self, command_loader, scope, **kwargs):    # pylint: disable=unused-argument
        super().__init__(command_loader, scope)
        self.validators = []

    def expand(self, dest, model_type, group_name=None, patches=None):
        super().expand(dest, model_type, group_name, patches)

        # Remove the validator and store it into a list
        arg = self.command_loader.argument_registry.arguments[self.command_scope].get(dest, None)
        if not arg:  # when the argument context scope is N/A
            return

        self.validators.append(arg.settings['validator'])
        dest_option = ['--__{}'.format(dest.upper())]
        if dest == 'parameters':
            self.argument(dest,
                          arg_type=ignore_type,
                          options_list=dest_option,
                          validator=get_combined_validator(self.validators))
        else:
            self.argument(dest, options_list=dest_option, arg_type=ignore_type, validator=None)


def get_combined_validator(validators):
    def _final_validator_impl(cmd, namespace):
        # do additional creation validation
        verbs = cmd.name.rsplit(' ', 2)
        if verbs[1] == 'server' and verbs[2] == 'create':
            if not namespace.administrator_login_password:
                try:
                    namespace.administrator_login_password = prompt_pass(msg='Admin Password: ')
                except NoTTYException:
                    raise CLIError('Please specify password in non-interactive mode.')

            get_default_location_from_resource_group(cmd, namespace)

        validate_tags(namespace)

        for validator in validators:
            validator(namespace)

    return _final_validator_impl


def retryable_method(retries=3, interval_sec=5, exception_type=Exception, condition=None):
    def decorate(func):
        def call(*args, **kwargs):
            current_retry = retries
            while True:
                try:
                    return func(*args, **kwargs)
                except exception_type as ex:  # pylint: disable=broad-except
                    if condition and not condition(ex):
                        raise ex
                    current_retry -= 1
                    if current_retry <= 0:
                        raise ex
                sleep(interval_sec)
        return call
    return decorate


def resolve_poller(result, cli_ctx, name, progress_bar=None):
    if _is_poller(result):
        return LongRunningOperation(cli_ctx, 'Starting {}'.format(name), progress_bar=progress_bar)(result)
    return result


def create_random_resource_name(prefix='azure', length=15):
    append_length = length - len(prefix)
    digits = [str(random.randrange(10)) for i in range(append_length)]
    return prefix + ''.join(digits)


def generate_missing_parameters(cmd, location, resource_group_name, server_name):
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
            location = DEFAULT_LOCATION
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
            raise InvalidArgumentValueError('incorrect usage: --public-access. Acceptable values are \'all\',\'none\',\'<startIP>\' and \'<startIP>-<destinationIP>\' '
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


def get_mysql_list_skus_info(cmd, location, server_name=None):
    list_skus_client = cf_mysql_flexible_location_capabilities(cmd.cli_ctx, '_')
    params = {'serverName': server_name} if server_name else None
    list_skus_result = list_skus_client.list(location, params=params)
    return _mysql_parse_list_skus(list_skus_result)


def _mysql_parse_list_skus(result):
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
        tier_dict["storage_sizes"] = (int(storage_info.min_storage_size) // 1024,
                                      int(storage_info.max_storage_size) // 1024)
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


# pylint: disable=protected-access
def _check_resource_group_existence(cmd, resource_group_name, resource_client=None):
    if resource_client is None:
        resource_client = resource_client_factory(cmd.cli_ctx)

    exists = False

    try:
        exists = resource_client.resource_groups.check_existence(resource_group_name)
    except HttpResponseError as e:
        if e.status_code == 403:
            raise CLIError("You don't have authorization to perform action 'Microsoft.Resources/subscriptions/resourceGroups/read' over scope '/subscriptions/{}/resourceGroups/{}'."
                           .format(resource_client._config.subscription_id, resource_group_name))

    return exists


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
    parent_path = ''
    if parent_name and parent_type:
        parent_path = '{}/{}'.format(parent_type, parent_name)

    api_version = _resolve_api_version(resource_client, provider_namespace, resource_type, parent_path)

    resource = None

    try:
        resource = resource_client.resources.get(resource_group, provider_namespace, parent_path,
                                                 resource_type, value, api_version)
    except HttpResponseError as e:
        if e.status_code == 403 and e.error and e.error.code == 'AuthorizationFailed':
            raise CLIError(e)

    return resource is not None


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
        process = subprocess.Popen(command)
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    if process.returncode:
        logger.warning(process.stderr.read().strip().decode('UTF-8'))


def register_credential_secrets(cmd, database_engine, server, repository):
    logger.warning('Adding secret "AZURE_CREDENTIALS" to github repository')
    resource_group = parse_resource_id(server.id)["resource_group"]
    provider = "DBforMySQL"
    if database_engine == "postgresql":
        provider = "DBforPostgreSQL"
    scope = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.{}/flexibleServers/{}".format(
        get_subscription_id(cmd.cli_ctx), resource_group, provider, server.name)

    app = create_service_principal_for_rbac(cmd, display_name=server.name, role='contributor', scopes=[scope])
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
    run_subprocess(["gh", "secret", "set", AZURE_CREDENTIALS, "--repo", repository, "<", credential_file])
    os.remove(credential_file)


def register_connection_secrets(server, database_name, administrator_login,
                                administrator_login_password, repository, connection_string_name):
    logger.warning("Added secret %s to github repository", connection_string_name)
    connection_string = "Server={}; Port=3306; Database={}; Uid={}; Pwd={}; SslMode=Preferred;".format(
        server.fully_qualified_domain_name, database_name, administrator_login, administrator_login_password)
    run_subprocess(['gh', 'secret', 'set', connection_string_name, '--repo', repository, '-b', connection_string])


def fill_action_template(cmd, database_engine, server, database_name, administrator_login,
                         administrator_login_password, file_name, action_name, repository):

    action_dir = get_git_root_dir() + GITHUB_ACTION_PATH
    if not os.path.exists(action_dir):
        os.makedirs(action_dir)

    process = run_cmd(["gh", "secret", "list", "--repo", repository], capture_output=True)
    github_secrets = process.stdout.strip().decode('UTF-8')

    if AZURE_CREDENTIALS not in github_secrets:
        try:
            register_credential_secrets(cmd,
                                        database_engine=database_engine,
                                        server=server,
                                        repository=repository)
        except HttpResponseError:
            raise AuthenticationError('You do not have authorization to create a service principal to run azure service in github actions. \n'
                                      'Please create a service principal that has access to the database server and add "AZURE_CREDENTIALS" secret to your github repository. \n'
                                      'Follow the instruction here "aka.ms/github-actions-azure-credentials".')

    connection_string_name = server.name.upper().replace("-", "_") + "_" + database_name.upper().replace("-", "_") + "_" + database_engine.upper() + "_CONNECTION_STRING"
    if connection_string_name not in github_secrets:
        register_connection_secrets(server=server,
                                    database_name=database_name,
                                    administrator_login=administrator_login,
                                    administrator_login_password=administrator_login_password,
                                    repository=repository,
                                    connection_string_name=connection_string_name)

    current_location = os.path.dirname(__file__)

    with open(current_location + "/templates/" + database_engine + "_githubaction_template.yaml", "r") as template_file:
        template = yaml.safe_load(template_file)
        template['jobs']['build']['steps'][2]['with']['server-name'] = server.fully_qualified_domain_name
        template['jobs']['build']['steps'][2]['with']['sql-file'] = file_name
        template['jobs']['build']['steps'][2]['with']['connection-string'] = "${{ secrets." + connection_string_name + " }}"
        with open(action_dir + action_name + '.yml', 'w', encoding='utf8') as yml_file:
            yml_file.write("on: [workflow_dispatch]\n")
            yml_file.write(yaml.dump(template))


def get_git_root_dir():
    process = run_cmd(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    return process.stdout.strip().decode('UTF-8')


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


def replace_memory_optimized_tier(result):
    result = _get_list_from_paged_response(result)
    for capability in result:
        for edition_idx, edition in enumerate(capability.supported_flexible_server_editions):
            if edition.name == 'MemoryOptimized':
                capability.supported_flexible_server_editions[edition_idx].name = 'BusinessCritical'

    return result


def _is_resource_name(resource):
    if len(resource.split('/')) == 1:
        return True
    return False


def build_identity_and_data_encryption(db_engine, byok_identity=None, backup_byok_identity=None,
                                       byok_key=None, backup_byok_key=None):
    identity, data_encryption = None, None

    if byok_identity and byok_key:
        identities = {byok_identity: {}}

        if backup_byok_identity:
            identities[backup_byok_identity] = {}

        if db_engine == 'mysql':
            identity = models.MySQLServerIdentity(user_assigned_identities=identities, type="UserAssigned")

            data_encryption = models.DataEncryption(
                primary_user_assigned_identity_id=byok_identity,
                primary_key_uri=byok_key,
                geo_backup_user_assigned_identity_id=backup_byok_identity,
                geo_backup_key_uri=backup_byok_key,
                type="AzureKeyVault")
        else:
            raise CLIError('Unsupported db engine.')

    return identity, data_encryption


def get_identity_and_data_encryption(server):
    identity, data_encryption = server.identity, server.data_encryption

    if identity and identity.type == 'UserAssigned':
        for current_id in identity.user_assigned_identities:
            identity.user_assigned_identities[current_id] = {}
    else:
        identity = None

    if not (data_encryption and data_encryption.type == 'AzureKeyVault'):
        data_encryption = None

    return identity, data_encryption


def get_tenant_id():
    from azure.cli.core._profile import Profile
    profile = Profile()
    sub = profile.get_subscription()
    return sub['tenantId']


def get_single_to_flex_sku_mapping(source_single_server_sku, tier, sku_name):
    single_to_flex_sku_mapping = {"Basic": {1: "Standard_B1ms", 2: "Standard_B2ms"},
                                  "GeneralPurpose": {2: "Standard_D2ds_v4", 4: "Standard_D4ds_v4", 8: "Standard_D8ds_v4", 16: "Standard_D16ds_v4", 32: "Standard_D32ds_v4", 64: "Standard_D64ds_v4"},
                                  "MemoryOptimized": {2: "Standard_E2ds_v4", 4: "Standard_E4ds_v4", 8: "Standard_E8ds_v4", 16: "Standard_E16ds_v4", 32: "Standard_E32ds_v4"}}
    if not tier:
        single_server_tier = source_single_server_sku.tier
        if single_server_tier == 'Basic':
            tier = 'Burstable'
        else:
            tier = single_server_tier
    if not sku_name:
        if tier == 'Burstable':
            sku_name = single_to_flex_sku_mapping.get('Basic').get(source_single_server_sku.capacity)
        else:
            sku_name = single_to_flex_sku_mapping.get(tier).get(source_single_server_sku.capacity)
    return tier, sku_name


def get_firewall_rules_from_paged_response(firewall_rules):
    return list(firewall_rules) if isinstance(firewall_rules, ItemPaged) else firewall_rules


def get_current_utc_time():
    return datetime.utcnow().replace(tzinfo=dt.timezone.utc)


class ImportFromStorageState(Enum):
    PROVISIONING = "Provisioning Server"
    IMPORTING = "Importing"
    DEFAULT = "Running"


class ImportFromStorageProgressHook:

    def __init__(self):
        self._import_started = False
        self._import_state = ImportFromStorageState.DEFAULT
        self._import_estimated_completion_time = None

    def update_progress(self, operation_progress_response):
        if operation_progress_response is not None:
            try:
                jsonresp = json.loads(operation_progress_response.text())
                self._update_import_from_storage_progress_status(jsonresp)
            except Exception:  # pylint: disable=broad-except
                pass

    def get_progress_message(self):
        msg = self._import_state.value
        if self._import_estimated_completion_time is not None:
            msg = msg + " " + self._get_eta_time_duration_in_user_readable_string()
        elif self._import_state == ImportFromStorageState.IMPORTING:
            msg = msg + " " + "Preparing (This might take few minutes)"
        return msg

    def _get_eta_time_duration_in_user_readable_string(self):
        time_remaining = datetime.fromisoformat(self._import_estimated_completion_time) - get_current_utc_time()
        msg = " ETA : "
        if time_remaining.total_seconds() < 60:
            return msg + "Few seconds remaining"
        days = time_remaining.days
        hours, remainder = divmod(time_remaining.seconds, 3600)
        minutes = math.ceil(remainder / 60.0)
        if days > 0:
            msg = msg + str(days) + " days "
        if hours > 0:
            msg = msg + str(hours) + " hours "
        if minutes > 0:
            msg = msg + str(minutes) + " minutes "
        return msg + " remaining"

    def _update_import_from_storage_progress_status(self, progress_resp_json):
        if "status" in progress_resp_json:
            progress_status = progress_resp_json["status"]
            previous_import_state = self._import_state

            # Updating the import state
            if progress_status == "Importing":
                self._import_started = True
                self._import_state = ImportFromStorageState.IMPORTING
            elif progress_status == "InProgress" and self._import_started is False:
                self._import_state = ImportFromStorageState.PROVISIONING
            else:
                self._import_state = ImportFromStorageState.DEFAULT

            # Updating the estimated completion time
            is_state_same = self._import_state == previous_import_state
            if is_state_same is False:
                self._import_estimated_completion_time = None
            if "properties" in progress_resp_json and "estimatedCompletionTime" in progress_resp_json["properties"]:
                self._import_estimated_completion_time = str(progress_resp_json["properties"]["estimatedCompletionTime"])


class OperationProgressBar(IndeterminateProgressBar):

    """ Define progress bar update view for operation progress """
    def __init__(self, cli_ctx, poller, operation_progress_hook, progress_message_update_interval_in_sec=60.0):
        self._poller = poller
        self._operation_progress_hook = operation_progress_hook
        self._operation_progress_request = self._get_operation_progress_request()
        self._client = get_mysql_flexible_management_client(cli_ctx)
        self._progress_message_update_interval_in_sec = progress_message_update_interval_in_sec
        self._progress_message_last_updated = None
        super().__init__(cli_ctx)

    def update_progress(self):
        self._safe_update_progress_message()
        super().update_progress()

    def _safe_update_progress_message(self):
        try:
            if self._should_update_progress_message():
                operation_progress_resp = self._client._send_request(self._operation_progress_request)
                self._operation_progress_hook.update_progress(operation_progress_resp)
                self.message = self._operation_progress_hook.get_progress_message()
                self._progress_message_last_updated = get_current_utc_time()
        except Exception:  # pylint: disable=broad-except
            pass

    def _should_update_progress_message(self):
        return (self._progress_message_last_updated is None) or ((get_current_utc_time() - self._progress_message_last_updated).total_seconds() > self._progress_message_update_interval_in_sec)

    def _get_operation_progress_request(self):
        location_url = self._poller._polling_method._initial_response.http_response.headers["Location"]
        operation_progress_url = location_url.replace('operationResults', 'operationProgress')
        operation_progress_url_parsed = urlparse(operation_progress_url)
        query_params = dict(parse_qsl(operation_progress_url_parsed.query))
        query_params['api-version'] = "2023-12-01-preview"
        updated_operation_progress_url = operation_progress_url_parsed._replace(query=urlencode(query_params)).geturl()
        return HttpRequest('GET', updated_operation_progress_url)
