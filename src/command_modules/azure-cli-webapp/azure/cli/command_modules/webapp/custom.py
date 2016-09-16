#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,too-many-lines
import threading
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse # pylint: disable=import-error

from azure.mgmt.web.models import (Site, SiteConfig, User, ServerFarmWithRichSku,
                                   SkuDescription, SslState)

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import is_valid_resource_id, parse_resource_id
import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from ._params import web_client_factory

logger = _logging.get_az_logger(__name__)

#pylint:disable=no-member

def create_webapp(resource_group, name, plan):
    client = web_client_factory()
    if is_valid_resource_id(plan):
        plan = parse_resource_id(plan)['name']
    location = _get_location_from_app_service_plan(client, resource_group, plan)
    webapp_def = Site(server_farm_id=plan, location=location)
    return client.sites.create_or_update_site(resource_group, name, webapp_def)

def _generic_site_operation(resource_group, name, operation_name, slot=None,
                            extra_parameter=None, client=None):
    client = client or web_client_factory()
    m = getattr(client.sites,
                operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (m(resource_group, name)
                if extra_parameter is None else m(resource_group, name, extra_parameter))
    else:
        return (m(resource_group, name, slot)
                if extra_parameter is None else m(resource_group, name, extra_parameter, slot))

#TODO: incorporate 'include_properties' once webapp team makes the decision to do it
def show_webapp(resource_group, name, slot=None):
    return _generic_site_operation(resource_group, name, 'get_site', slot)

def delete_webapp(resource_group, name, slot=None):
    return _generic_site_operation(resource_group, name, 'delete_site', slot)

def stop_webapp(resource_group, name, slot=None):
    return _generic_site_operation(resource_group, name, 'stop_site', slot)

def restart_webapp(resource_group, name, slot=None):
    return _generic_site_operation(resource_group, name, 'restart_site', slot)

def get_site_configs(resource_group, name, slot=None):
    return _generic_site_operation(resource_group, name, 'get_site_config', slot)

def get_app_settings(resource_group, name, slot=None):
    result = _generic_site_operation(resource_group, name, 'list_site_app_settings', slot)
    return result.properties

def update_site_configs(resource_group, name, name_value_pairs, slot=None):
    configs = get_site_configs(resource_group, name, slot)
    for name_value in name_value_pairs:
        name, value = name_value.split('=')
        setattr(configs.properties, name, value)

    return _generic_site_operation(resource_group, name, 'update_site_config', slot, configs)

def update_app_settings(resource_group, name, settings, slot=None):
    app_settings = _generic_site_operation(resource_group, name, 'list_site_app_settings', slot)
    for name_value in settings:
        #split at the first '=', appsetting should not have '=' in the name
        settings_name, value = name_value.split('=', 1)
        app_settings.properties[settings_name] = value

    return _generic_site_operation(resource_group, name, 'update_site_app_settings',
                                   slot, app_settings)

def delete_app_settings(resource_group, name, setting_names, slot=None):
    app_settings = _generic_site_operation(resource_group, name, 'list_site_app_settings', slot)
    for setting_name in setting_names:
        app_settings.properties.pop(setting_name, None)

    return _generic_site_operation(resource_group, name, 'update_site_app_settings',
                                   slot, app_settings)

#TODO: figure out the 'configuration_source' and add related param descriptions
def create_webapp_slot(resource_group, webapp, slot, configuration_source=None):
    client = web_client_factory()
    site = client.sites.get_site(resource_group, webapp)
    location = site.location
    if configuration_source is None:
        slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    elif configuration_source.lower() == webapp.lower(): #clone from production
        slot_def = site #pylint: disable=redefined-variable-type
    else: # from other slot
        slot_def = client.sites.get_site_slot(resource_group, webapp, slot)

    return client.sites.create_or_update_site_slot(resource_group, webapp, slot_def, slot)

def enable_local_git(resource_group, name, slot=None):
    client = web_client_factory()
    location = _get_location_from_webapp(client, resource_group, name)
    site_config = SiteConfig(location)
    site_config.scm_type = 'LocalGit'
    if slot is None:
        client.sites.create_or_update_site_config(resource_group, name, site_config)
    else:
        client.sites.create_or_update_site_config_slot(resource_group, name, site_config, slot)

    return _get_git_url(client, resource_group, name, slot)

#TODO: logic comes from powershell, cross check with with upcoming xplat styles
def create_app_service_plan(resource_group, name, tier=None, number_of_workers=None,
                            worker_size=None, location=None):
    client = web_client_factory()
    if location is None:
        location = _get_location_from_resource_group(resource_group)

    sku_name = _get_sku_name(tier, worker_size)
    sku = SkuDescription(name=sku_name, tier=tier, capacity=number_of_workers)
    plan_def = ServerFarmWithRichSku(location, server_farm_with_rich_sku_name=name, sku=sku)
    #TODO: handle bad error on creating too many F1 plans:
    #  Operation failed with status: 'Conflict'. Details: 409 Client Error: Conflict for url:
    return client.server_farms.create_or_update_server_farm(resource_group, name, plan_def)

def update_app_service_plan(resource_group, name, tier=None, number_of_workers=None,
                            worker_size=None, admin_site_name=None):
    client = web_client_factory()
    plan = client.server_farms.get_server_farm(resource_group, name)
    sku = plan.sku
    if tier is not None:
        sku.tier = tier
    if number_of_workers is not None:
        sku.capacity = number_of_workers
    if worker_size is not None or tier is not None:
        if worker_size:
            sku.name = _get_sku_name(sku.tier.lower(), worker_size)
        else:
            sku.name = _get_sku_prefix(sku.tier) + sku.name[1::1]

    plan_def = ServerFarmWithRichSku(plan.location, server_farm_with_rich_sku_name=name,
                                     sku=sku, admin_site_name=admin_site_name)
    return client.server_farms.create_or_update_server_farm(resource_group, name, plan_def)

def _get_sku_prefix(tier):
    return 'D' if tier.lower() == 'shared' else tier[0:1]

def _get_sku_name(tier, worker_size):
    worker_size_mappings = {
        'small': '1',
        'medium': '2',
        'large': '3',
        'extralarge': '4'
    }
    sku = _get_sku_prefix(tier) + worker_size_mappings[worker_size.lower()]
    return sku

def _get_location_from_resource_group(resource_group):
    from azure.mgmt.resource.resources import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    group = client.resource_groups.get(resource_group)
    return group.location

def _get_location_from_webapp(client, resource_group, webapp):
    webapp = client.sites.get_site(resource_group, webapp)
    return webapp.location

def _get_location_from_app_service_plan(client, resource_group, plan):
    plan = client.server_farms.get_server_farm(resource_group, plan)
    return plan.location

def get_git_url(resource_group, name, slot=None):
    client = web_client_factory()
    return _get_git_url(client, resource_group, name, slot)

def _get_git_url(client, resource_group, name, slot=None):
    user = client.provider.get_publishing_user()
    repo_url = _get_repo_url(client, resource_group, name, slot)
    parsed = urlparse(repo_url)
    git_url = '{}://{}@{}/{}.git'.format(parsed.scheme, user.publishing_user_name,
                                         parsed.netloc, name)
    return git_url

def _get_repo_url(client, resource_group, name, slot=None):
    scc = _generic_site_operation(resource_group, name, 'get_site_source_control',
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

def view_in_browser(resource_group, name, slot=None):
    import webbrowser
    site = _generic_site_operation(resource_group, name, 'get_site', slot)
    url = site.default_host_name
    ssl_host = next((h for h in site.host_name_ssl_states
                     if h.ssl_state != SslState.disabled), None)
    url = ('https' if ssl_host else 'http') + '://' + url
    webbrowser.open(url, new=2) # 2 means: open in a new tab, if possible

#TODO: expose new blob suport
def config_diagnostics(resource_group, name, level=None,
                       application_logging=None, web_server_logging=None,
                       detailed_error_messages=None, failed_request_tracing=None,
                       slot=None):
    from azure.mgmt.web.models import (FileSystemApplicationLogsConfig, ApplicationLogsConfig,
                                       SiteLogsConfig, HttpLogsConfig,
                                       FileSystemHttpLogsConfig, EnabledConfig)
    client = web_client_factory()
    #TODO: ensure we call get_site only once
    site = client.sites.get_site(resource_group, name)
    location = site.location

    application_logs = None
    if application_logging:
        if application_logging == 'off': #TODO share the same choice list in _params.py
            level = 'Off'
        elif level is None:
            level = 'Error'
        fs_log = FileSystemApplicationLogsConfig(level)
        application_logs = ApplicationLogsConfig(fs_log)

    http_logs = None
    if web_server_logging:
        enabled = web_server_logging != 'off'
        #100 mb max log size, retenting last 3 days. Yes we hard code it, portal does too
        fs_server_log = FileSystemHttpLogsConfig(100, 3, enabled)
        http_logs = HttpLogsConfig(fs_server_log)

    detailed_error_messages_logs = (None if detailed_error_messages is None
                                    else EnabledConfig(detailed_error_messages == 'on'))
    failed_request_tracing_logs = (None if failed_request_tracing is None
                                   else EnabledConfig(failed_request_tracing == 'on'))
    site_log_config = SiteLogsConfig(location,
                                     application_logs=application_logs,
                                     http_logs=http_logs,
                                     failed_requests_tracing=failed_request_tracing_logs,
                                     detailed_error_messages=detailed_error_messages_logs)

    return _generic_site_operation(resource_group, name, 'update_site_logs_config',
                                   slot, site_log_config)


def config_slot_auto_swap(resource_group, webapp, slot, auto_swap_slot=None, disable=None):
    client = web_client_factory()
    site_config = client.sites.get_site_config_slot(resource_group, webapp, slot)
    site_config.auto_swap_slot_name = '' if disable else (auto_swap_slot or 'production')
    return client.sites.update_site_config_slot(resource_group, webapp, site_config, slot)

def get_streaming_log(resource_group, name, provider=None, slot=None):
    client = web_client_factory()
    repo_url = _get_repo_url(client, resource_group, name, slot)
    streaming_url = repo_url + '/logstream'
    import time
    if provider:
        streaming_url += ('/' + provider.lstrip('/'))

    user, password = _get_site_credential(client, resource_group, name)
    t = threading.Thread(target=_stream_trace, args=(streaming_url, user, password))
    t.daemon = True
    t.start()

    while True:
        time.sleep(100) #so that ctrl+c can stop the command

def download_historical_logs(resource_group, name, log_file=None, slot=None):
    '''
    Download historical logs as a zip file
    '''
    client = web_client_factory()
    user, password = _get_site_credential(client, resource_group, name)
    repo_url = _get_repo_url(client, resource_group, name, slot)
    host = urlparse(repo_url).netloc
    url = "https://{}:{}@{}/dump".format(user, password, host)
    import requests
    r = requests.get(url, stream=True)
    with open(log_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    logger.warning('Downloaded logs to %s', log_file)

def _get_site_credential(client, resource_group, name):
    creds = client.sites.list_site_publishing_credentials(resource_group, name)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)

def _stream_trace(streaming_url, user_name, password):
    import pycurl
    import certifi
    c = pycurl.Curl()
    c.setopt(c.URL, streaming_url)
    c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(c.USERPWD, '{}:{}'.format(user_name, password))
    c.perform()
