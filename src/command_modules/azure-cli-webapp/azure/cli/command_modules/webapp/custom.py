#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,too-many-lines
from __future__ import print_function
import json
import threading
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse # pylint: disable=import-error

from azure.mgmt.web.models import (Site, SiteConfig, User, ServerFarmWithRichSku,
                                   SkuDescription, SslState, HostNameBinding)

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import is_valid_resource_id, parse_resource_id
from azure.cli.core.commands import LongRunningOperation

import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from ._params import web_client_factory, _generic_site_operation

logger = _logging.get_az_logger(__name__)

#pylint:disable=no-member

#workaround that app service's error doesn't comform to LRO spec
class AppServiceLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods

    def __init__(self, creating_plan=False):
        super(AppServiceLongRunningOperation, self).__init__(self)
        self._creating_plan = creating_plan

    def __call__(self, poller):
        try:
            return super(AppServiceLongRunningOperation, self).__call__(poller)
        except Exception as ex:
            raise self._get_detail_error(ex)

    def _get_detail_error(self, ex):
        try:
            detail = json.loads(ex.response.text)['Message']
            if self._creating_plan:
                if 'Requested features are not supported in region' in detail:
                    detail = ("Plan with linux worker is not supported in current region. " +
                              "Run 'az appservice list-locations --linux-workers-enabled' " +
                              "to cross check")
                elif 'Not enough available reserved instance servers to satisfy' in detail:
                    detail = ("Plan with Linux worker can only be created in a group " +
                              "which has never contained a Windows worker. Please use " +
                              "a new resource group. Original error:" + detail)
            return CLIError(detail)
        except: #pylint: disable=bare-except
            return ex

def create_webapp(resource_group_name, name, plan):
    client = web_client_factory()
    if is_valid_resource_id(plan):
        plan = parse_resource_id(plan)['name']
    location = _get_location_from_app_service_plan(client, resource_group_name, plan)
    webapp_def = Site(server_farm_id=plan, location=location)
    poller = client.sites.create_or_update_site(resource_group_name, name, webapp_def)
    return AppServiceLongRunningOperation()(poller)

def show_webapp(resource_group_name, name, slot=None):
    webapp = _generic_site_operation(resource_group_name, name, 'get_site', slot)
    return _rename_server_farm_props(webapp)

def list_webapp(resource_group_name):
    client = web_client_factory()
    result = client.sites.get_sites(resource_group_name)
    for webapp in result:
        _rename_server_farm_props(webapp)
    return result

def _rename_server_farm_props(webapp):
    #Should be renamed in SDK in a future release
    setattr(webapp, 'app_service_plan_id', webapp.server_farm_id)
    del webapp.server_farm_id
    return webapp

def delete_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'delete_site', slot)

def stop_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'stop_site', slot)

def restart_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'restart_site', slot)

def get_site_configs(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'get_site_config', slot)

def get_app_settings(resource_group_name, name, slot=None):
    result = _generic_site_operation(resource_group_name, name, 'list_site_app_settings', slot)
    return result.properties

#for any modifications to the non-optional parameters, adjust the reflection logic accordingly
#in the method
def update_site_configs(resource_group_name, name, slot=None,
                        php_version=None, python_version=None,#pylint: disable=unused-argument
                        net_framework_version=None, #pylint: disable=unused-argument
                        java_version=None, java_container=None, java_container_version=None,#pylint: disable=unused-argument
                        remote_debugging_enabled=None, web_sockets_enabled=None,#pylint: disable=unused-argument
                        always_on=None, auto_heal_enabled=None,#pylint: disable=unused-argument
                        use32_bit_worker_process=None,#pylint: disable=unused-argument
                        app_command_line=None):#pylint: disable=unused-argument
    configs = get_site_configs(resource_group_name, name, slot)
    import inspect
    frame = inspect.currentframe()
    #note: getargvalues is used already in azure.cli.core.commands.
    #and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame) #pylint: disable=deprecated-method
    for arg in args[3:]:
        if arg is not None:
            setattr(configs, arg, values[arg])

    return _generic_site_operation(resource_group_name, name, 'update_site_config', slot, configs)

def update_app_settings(resource_group_name, name, settings, slot=None):
    app_settings = _generic_site_operation(resource_group_name, name,
                                           'list_site_app_settings', slot)
    for name_value in settings:
        #split at the first '=', appsetting should not have '=' in the name
        settings_name, value = name_value.split('=', 1)
        app_settings.properties[settings_name] = value

    result = _generic_site_operation(resource_group_name, name, 'update_site_app_settings',
                                     slot, app_settings)
    return result.properties

def delete_app_settings(resource_group_name, name, setting_names, slot=None):
    app_settings = _generic_site_operation(resource_group_name, name,
                                           'list_site_app_settings', slot)
    for setting_name in setting_names:
        app_settings.properties.pop(setting_name, None)

    return _generic_site_operation(resource_group_name, name, 'update_site_app_settings',
                                   slot, app_settings)

CONTAINER_APPSETTING_NAMES = ['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                              'DOCKER_REGISTRY_SERVER_PASSWORD', 'DOCKER_CUSTOM_IMAGE_NAME']

def update_container_settings(resource_group_name, name, docker_registry_server_url=None,
                              docker_custom_image_name=None, docker_registery_server_user=None,
                              docker_registery_server_password=None, slot=None):
    settings = []
    if docker_registry_server_url is not None:
        settings.append('DOCKER_REGISTRY_SERVER_URL=' + docker_registry_server_url)
    if docker_registery_server_user is not None:
        settings.append('DOCKER_REGISTRY_SERVER_USERNAME=' + docker_registery_server_user)
    if docker_registery_server_password is not None:
        settings.append('DOCKER_REGISTRY_SERVER_PASSWORD=' + docker_registery_server_password)
    if docker_custom_image_name is not None:
        settings.append('DOCKER_CUSTOM_IMAGE_NAME=' + docker_custom_image_name)
    settings = update_app_settings(resource_group_name, name, settings, slot)
    return _filter_for_container_settings(settings)

def delete_container_settings(resource_group_name, name, slot=None):
    delete_app_settings(resource_group_name, name, CONTAINER_APPSETTING_NAMES, slot)

def list_container_settings(resource_group_name, name, slot=None):
    settings = get_app_settings(resource_group_name, name, slot)
    return _filter_for_container_settings(settings)

def _filter_for_container_settings(settings):
    return {x: settings[x] for x in settings if x in CONTAINER_APPSETTING_NAMES}

def add_hostname(resource_group_name, webapp, name, slot=None):
    client = web_client_factory()
    webapp = client.sites.get_site(resource_group_name, webapp)
    binding = HostNameBinding(webapp.location, host_name_binding_name=name, site_name=webapp)
    if slot is None:
        return client.sites.create_or_update_site_host_name_binding(resource_group_name, webapp,
                                                                    name, binding)
    else:
        return client.sites.create_or_update_site_host_name_binding_slot(resource_group_name,
                                                                         webapp, name,
                                                                         binding, slot)

def delete_hostname(resource_group_name, webapp, name, slot=None):
    client = web_client_factory()
    if slot is None:
        return client.sites.delete_site_host_name_binding(resource_group_name, webapp, name)
    else:
        return client.sites.delete_site_host_name_binding_slot(resource_group_name,
                                                               webapp, slot, name)

def list_hostnames(resource_group_name, webapp, slot=None):
    return _generic_site_operation(resource_group_name, webapp, 'get_site_host_name_bindings',
                                   slot)

#TODO: figure out the 'configuration_source' and add related param descriptions
def create_webapp_slot(resource_group_name, webapp, slot, configuration_source=None):
    client = web_client_factory()
    site = client.sites.get_site(resource_group_name, webapp)
    location = site.location
    if configuration_source is None:
        slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    elif configuration_source.lower() == webapp.lower(): #clone from production
        slot_def = site #pylint: disable=redefined-variable-type
    else: # from other slot
        slot_def = client.sites.get_site_slot(resource_group_name, webapp, slot)

    return client.sites.create_or_update_site_slot(resource_group_name, webapp, slot_def, slot)

def enable_local_git(resource_group_name, name, slot=None):
    client = web_client_factory()
    location = _get_location_from_webapp(client, resource_group_name, name)
    site_config = SiteConfig(location)
    site_config.scm_type = 'LocalGit'
    if slot is None:
        client.sites.create_or_update_site_config(resource_group_name, name, site_config)
    else:
        client.sites.create_or_update_site_config_slot(resource_group_name, name, site_config, slot)

    return {'url' : _get_git_url(client, resource_group_name, name, slot)}

def create_app_service_plan(resource_group_name, name, sku, is_linux, number_of_workers=None,
                            location=None):
    client = web_client_factory()
    sku = _normalize_sku(sku)
    if location is None:
        location = _get_location_from_resource_group(resource_group_name)

    #the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=_get_sku_name(sku), name=sku, capacity=number_of_workers)
    plan_def = ServerFarmWithRichSku(location, server_farm_with_rich_sku_name=name,
                                     sku=sku_def, reserved=(is_linux or None))
    poller = client.server_farms.create_or_update_server_farm(resource_group_name, name, plan_def)
    return AppServiceLongRunningOperation(creating_plan=True)(poller)

def update_app_service_plan(instance, sku=None, number_of_workers=None,
                            admin_site_name=None):
    sku_def = instance.sku
    if sku is not None:
        sku = _normalize_sku(sku)
        sku_def.tier = _get_sku_name(sku)
        sku_def.name = sku

    if number_of_workers is not None:
        sku_def.capacity = number_of_workers

    instance.sku = sku_def
    if admin_site_name is not None:
        instance.admin_site_name = admin_site_name
    return instance

def _normalize_sku(sku):
    sku = sku.upper()
    if sku == 'FREE':
        return 'F1'
    elif sku == 'SHARED':
        return 'D1'
    else:
        return sku

def _get_sku_name(tier):
    tier = tier.upper()
    if tier == 'F1':
        return 'FREE'
    elif tier == 'D1':
        return 'SHARED'
    elif tier in ['B1', 'B2', 'B3']:
        return 'BASIC'
    elif tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    elif tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    else:
        raise CLIError("Invalid sku(pricing tier), please refer to command help for valid values")

def _get_location_from_resource_group(resource_group_name):
    from azure.mgmt.resource.resources import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    group = client.resource_groups.get(resource_group_name)
    return group.location

def _get_location_from_webapp(client, resource_group_name, webapp):
    webapp = client.sites.get_site(resource_group_name, webapp)
    return webapp.location

def _get_location_from_app_service_plan(client, resource_group_name, plan):
    plan = client.server_farms.get_server_farm(resource_group_name, plan)
    return plan.location

def get_git_url(resource_group_name, name, slot=None):
    client = web_client_factory()
    return {'url' : _get_git_url(client, resource_group_name, name, slot)}

def _get_git_url(client, resource_group_name, name, slot=None):
    user = client.provider.get_publishing_user()
    repo_url = _get_repo_url(client, resource_group_name, name, slot)
    parsed = urlparse(repo_url)
    git_url = '{}://{}@{}/{}.git'.format(parsed.scheme, user.publishing_user_name,
                                         parsed.netloc, name)
    return git_url

def _get_repo_url(client, resource_group_name, name, slot=None):
    scc = _generic_site_operation(resource_group_name, name, 'get_site_source_control',
                                  slot, client=client)
    if scc.repo_url is None:
        raise CLIError("Please enable Git deployment, say, run 'webapp git enable-local'")
    return scc.repo_url

def set_deployment_user(user_name, password=None):
    '''
    Update deployment credentials.(Note, all webapps in your subscription will be impacted)
    '''
    client = web_client_factory()
    user = User(location='not-really-needed') #TODO: open bug for this one is not needed
    user.publishing_user_name = user_name
    if password is None:
        import getpass
        password = getpass.getpass('Password: ')

    user.publishing_password = password
    result = client.provider.update_publishing_user(user)
    return result

def view_in_browser(resource_group_name, name, slot=None):
    import webbrowser
    site = _generic_site_operation(resource_group_name, name, 'get_site', slot)
    url = site.default_host_name
    ssl_host = next((h for h in site.host_name_ssl_states
                     if h.ssl_state != SslState.disabled), None)
    url = ('https' if ssl_host else 'http') + '://' + url
    webbrowser.open(url, new=2) # 2 means: open in a new tab, if possible

#TODO: expose new blob suport
def config_diagnostics(resource_group_name, name, level=None,
                       application_logging=None, web_server_logging=None,
                       detailed_error_messages=None, failed_request_tracing=None,
                       slot=None):
    from azure.mgmt.web.models import (FileSystemApplicationLogsConfig, ApplicationLogsConfig,
                                       SiteLogsConfig, HttpLogsConfig,
                                       FileSystemHttpLogsConfig, EnabledConfig)
    client = web_client_factory()
    #TODO: ensure we call get_site only once
    site = client.sites.get_site(resource_group_name, name)
    location = site.location

    application_logs = None
    if application_logging is not None:
        if not application_logging:
            level = 'Off'
        elif level is None:
            level = 'Error'
        fs_log = FileSystemApplicationLogsConfig(level)
        application_logs = ApplicationLogsConfig(fs_log)

    http_logs = None
    if web_server_logging is not None:
        enabled = web_server_logging
        #100 mb max log size, retenting last 3 days. Yes we hard code it, portal does too
        fs_server_log = FileSystemHttpLogsConfig(100, 3, enabled)
        http_logs = HttpLogsConfig(fs_server_log)

    detailed_error_messages_logs = (None if detailed_error_messages is None
                                    else EnabledConfig(detailed_error_messages))
    failed_request_tracing_logs = (None if failed_request_tracing is None
                                   else EnabledConfig(failed_request_tracing))
    site_log_config = SiteLogsConfig(location,
                                     application_logs=application_logs,
                                     http_logs=http_logs,
                                     failed_requests_tracing=failed_request_tracing_logs,
                                     detailed_error_messages=detailed_error_messages_logs)

    return _generic_site_operation(resource_group_name, name, 'update_site_logs_config',
                                   slot, site_log_config)


def config_slot_auto_swap(resource_group_name, webapp, slot, auto_swap_slot=None, disable=None):
    client = web_client_factory()
    site_config = client.sites.get_site_config_slot(resource_group_name, webapp, slot)
    site_config.auto_swap_slot_name = '' if disable else (auto_swap_slot or 'production')
    return client.sites.update_site_config_slot(resource_group_name, webapp, site_config, slot)

def get_streaming_log(resource_group_name, name, provider=None, slot=None):
    client = web_client_factory()
    repo_url = _get_repo_url(client, resource_group_name, name, slot)
    streaming_url = repo_url + '/logstream'
    import time
    if provider:
        streaming_url += ('/' + provider.lstrip('/'))

    user, password = _get_site_credential(client, resource_group_name, name)
    t = threading.Thread(target=_stream_trace, args=(streaming_url, user, password))
    t.daemon = True
    t.start()

    while True:
        time.sleep(100) #so that ctrl+c can stop the command

def download_historical_logs(resource_group_name, name, log_file=None, slot=None):
    '''
    Download historical logs as a zip file
    '''
    client = web_client_factory()
    user, password = _get_site_credential(client, resource_group_name, name)
    repo_url = _get_repo_url(client, resource_group_name, name, slot)
    host = urlparse(repo_url).netloc
    url = "https://{}:{}@{}/dump".format(user, password, host)
    import requests
    r = requests.get(url, stream=True)
    with open(log_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    logger.warning('Downloaded logs to %s', log_file)

def _get_site_credential(client, resource_group_name, name):
    creds = client.sites.list_site_publishing_credentials(resource_group_name, name)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)

def _stream_trace(streaming_url, user_name, password):
    import sys
    import certifi
    import urllib3
    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

    std_encoding = sys.stdout.encoding
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    headers = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    r = http.request(
        'GET',
        streaming_url,
        headers=headers,
        preload_content=False
    )
    for chunk in r.stream():
        if chunk:
            # Extra encode() and decode for stdout which does not surpport 'utf-8'
            print(chunk.decode(encoding='utf-8', errors='replace')
                  .encode(std_encoding, errors='replace')
                  .decode(std_encoding, errors='replace'), end='') # each line of log has CRLF.
    r.release_conn()
