# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.util import get_file_json, shell_safe_json_parse
from azure.cli.core.commands.client_factory import get_mgmt_service_client


def _process_parameters(parameter_lists):
    def _try_parse_json_object(value):
        try:
            parsed = shell_safe_json_parse(value)
            return parsed.get('parameters', parsed)
        except CLIError:
            return None

    parameters = {}
    for params in parameter_lists or []:
        for item in params:
            param_obj = _try_parse_json_object(item)
            if param_obj:
                parameters.update(param_obj)

    return parameters


def deploy_arm_template(cli_ctx, resource_group_name,  # pylint: disable=too-many-arguments
                        template_file=None, deployment_name=None,
                        parameters=None, mode=None):
    DeploymentProperties, _ = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                      'DeploymentProperties', 'TemplateLink', mod='models')
    template = None
    template = get_file_json(template_file, preserve_order=True)
    template_obj = template

    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(parameters) or {}

    import json
    template = json.loads(json.dumps(template))
    parameters = json.loads(json.dumps(parameters))

    properties = DeploymentProperties(template=template, template_link=None,
                                      parameters=parameters, mode=mode)

    smc = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    return smc.deployments.create_or_update(resource_group_name, deployment_name, properties, raw=False)


def web_client_factory(cli_ctx, **_):
    from azure.mgmt.web import WebSiteManagementClient
    mgmt_client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient)
    return mgmt_client


def _generic_site_operation(cli_ctx, resource_group_name, name, operation_name, slot=None,
                            extra_parameter=None, client=None):
    client = client or web_client_factory(cli_ctx)
    operation = getattr(client.web_apps,
                        operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (operation(resource_group_name, name)
                if extra_parameter is None else operation(resource_group_name,
                                                          name, extra_parameter))

    return (operation(resource_group_name, name, slot)
            if extra_parameter is None else operation(resource_group_name,
                                                      name, extra_parameter, slot))


def _get_site_credential(cli_ctx, resource_group_name, name, slot=None):
    creds = _generic_site_operation(cli_ctx, resource_group_name, name, 'list_publishing_credentials', slot)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)


def _build_app_settings_output(app_settings, slot_cfg_names):
    slot_cfg_names = slot_cfg_names or []
    return [{'name': p,
             'value': app_settings[p],
             'slotSetting': p in slot_cfg_names} for p in app_settings]


def get_app_settings(cmd, resource_group_name, name, slot=None):
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_application_settings', slot)
    client = web_client_factory(cmd.cli_ctx)
    slot_app_setting_names = client.web_apps.list_slot_configuration_names(resource_group_name, name).app_setting_names
    return _build_app_settings_output(result.properties, slot_app_setting_names)


def _get_scm_url(cmd, resource_group_name, name, slot=None):
    from azure.mgmt.web.models import HostType
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    for host in webapp.host_name_ssl_states or []:
        if host.host_type == HostType.repository:
            return "https://{}".format(host.name)

    # this should not happen, but throw anyway
    raise ValueError('Failed to retrieve Scm Uri')


def enable_zip_deploy(cmd, resource_group_name, name, src, slot=None):
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    zip_url = scm_url + '/api/zipdeploy'

    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization
    headers['content-type'] = 'application/octet-stream'

    import requests
    import os
    # Read file content
    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        r = requests.post(zip_url, data=zip_content, headers=headers)
        if r.status_code != 200:
            raise CLIError("Zip deployment {} failed with status code '{}' and reason '{}'".format(
                zip_url, r.status_code, r.text))

    # on successful deployment navigate to the app, display the latest deployment json response
    response = requests.get(scm_url + '/api/deployments/latest', headers=authorization)
    return response.json()
