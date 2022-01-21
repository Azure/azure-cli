# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from binascii import hexlify
from os import urandom

from knack.log import get_logger

from msrestazure.tools import is_valid_resource_id, parse_resource_id

from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.azclierror import InvalidArgumentValueError, MutuallyExclusiveArgumentError

from azure.cli.command_modules.appservice.utils import (_list_app)
from azure.cli.command_modules.appservice._client_factory import web_client_factory
from azure.cli.command_modules.appservice.custom import (
    _format_fx_version,
    _get_extension_version_functionapp,
    get_app_insights_key,
    parse_docker_image_name,
    list_consumption_locations,
    is_plan_elastic_premium,
    _validate_and_get_connection_string,
    update_container_settings_functionapp,
    try_create_application_insights,
    _set_remote_or_local_git,
    _show_app, create_app_service_plan)

from ._constants import (DEFAULT_LOGICAPP_FUNCTION_VERSION,
                         DEFAULT_LOGICAPP_RUNTIME,
                         DEFAULT_LOGICAPP_RUNTIME_VERSION,
                         FUNCTIONS_VERSION_TO_SUPPORTED_RUNTIME_VERSIONS,
                         FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION,
                         DOTNET_RUNTIME_VERSION_TO_DOTNET_LINUX_FX_VERSION)

logger = get_logger(__name__)


def create_logicapp(cmd, resource_group_name, name, storage_account, plan=None,
                    os_type=None, consumption_plan_location=None,
                    app_insights=None, app_insights_key=None, disable_app_insights=None,
                    deployment_source_url=None, deployment_source_branch='master', deployment_local_git=None,
                    docker_registry_server_password=None, docker_registry_server_user=None,
                    deployment_container_image_name=None, tags=None):
    # pylint: disable=too-many-statements, too-many-branches, too-many-locals
    functions_version = DEFAULT_LOGICAPP_FUNCTION_VERSION
    runtime = None
    runtime_version = None

    if consumption_plan_location or not deployment_container_image_name:
        runtime = DEFAULT_LOGICAPP_RUNTIME
        runtime_version = DEFAULT_LOGICAPP_RUNTIME_VERSION

    if deployment_source_url and deployment_local_git:
        raise MutuallyExclusiveArgumentError('usage error: --deployment-source-url <url> | --deployment-local-git')

    if consumption_plan_location and plan:
        raise MutuallyExclusiveArgumentError("Consumption Plan and Plan cannot be used together")

    SiteConfig, Site, NameValuePair = cmd.get_models('SiteConfig', 'Site', 'NameValuePair')

    docker_registry_server_url = parse_docker_image_name(
        deployment_container_image_name)

    site_config = SiteConfig(app_settings=[])
    logicapp_def = Site(location=None, site_config=site_config, tags=tags)
    client = web_client_factory(cmd.cli_ctx)
    plan_info = None
    if runtime is not None:
        runtime = runtime.lower()

    if consumption_plan_location:
        locations = list_consumption_locations(cmd)
        location = next((loc for loc in locations if loc['name'].lower(
        ) == consumption_plan_location.lower()), None)
        if location is None:
            raise InvalidArgumentValueError(
                "Location is invalid. Use: az logicapp list-consumption-locations")
        logicapp_def.location = consumption_plan_location
        logicapp_def.kind = 'functionapp,workflowapp'
        # if os_type is None, the os type is windows
        is_linux = os_type and os_type.lower() == 'linux'

    else:
        if not plan:  # no plan passed in, so create a WS1 ASP
            plan_name = "{}_app_service_plan".format(name)
            create_app_service_plan(cmd, resource_group_name, plan_name, False, False, sku='WS1')
            logger.warning("Created App Service Plan %s in resource group %s", plan_name, resource_group_name)
            plan_info = client.app_service_plans.get(resource_group_name, plan_name)
        else:  # apps with SKU based plan
            if is_valid_resource_id(plan):
                parse_result = parse_resource_id(plan)
                plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
            else:
                plan_info = client.app_service_plans.get(resource_group_name, plan)

        is_linux = plan_info.reserved
        logicapp_def.server_farm_id = plan_info.id
        logicapp_def.location = plan_info.location

    if runtime:
        site_config.app_settings.append(NameValuePair(
            name='FUNCTIONS_WORKER_RUNTIME', value=runtime))

    con_string = _validate_and_get_connection_string(cmd.cli_ctx, resource_group_name, storage_account)

    if is_linux:
        logicapp_def.kind = 'functionapp,workflowapp,linux'
        logicapp_def.reserved = True
        is_consumption = consumption_plan_location is not None
        if not is_consumption:
            site_config.app_settings.append(NameValuePair(name='MACHINEKEY_DecryptionKey',
                                                          value=str(hexlify(urandom(32)).decode()).upper()))
            if deployment_container_image_name:
                logicapp_def.kind = 'functionapp,workflowapp,linux,container'
                site_config.app_settings.append(NameValuePair(name='DOCKER_CUSTOM_IMAGE_NAME',
                                                              value=deployment_container_image_name))
                site_config.app_settings.append(NameValuePair(
                    name='FUNCTION_APP_EDIT_MODE', value='readOnly'))
                site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                              value='false'))
                site_config.linux_fx_version = _format_fx_version(
                    deployment_container_image_name)
            else:
                site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                              value='true'))
                if runtime not in FUNCTIONS_VERSION_TO_SUPPORTED_RUNTIME_VERSIONS[functions_version]:
                    raise InvalidArgumentValueError(
                        "An appropriate linux image for runtime:'{}', "
                        "functions_version: '{}' was not found".format(runtime, functions_version))
        if deployment_container_image_name is None:
            site_config.linux_fx_version = _get_linux_fx_functionapp(
                functions_version, runtime, runtime_version)
    else:
        logicapp_def.kind = 'functionapp,workflowapp'

    # adding appsetting to site to make it a workflow
    site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION',
                                                  value=_get_extension_version_functionapp(functions_version)))
    site_config.app_settings.append(NameValuePair(
        name='AzureWebJobsStorage', value=con_string))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsDashboard', value=con_string))
    site_config.app_settings.append(NameValuePair(
        name='AzureFunctionsJobHost__extensionBundle__id', value="Microsoft.Azure.Functions.ExtensionBundle.Workflows"))
    site_config.app_settings.append(NameValuePair(
        name='AzureFunctionsJobHost__extensionBundle__version', value="[1.*, 2.0.0)"))
    site_config.app_settings.append(
        NameValuePair(name='APP_KIND', value="workflowApp"))

    # If plan is not consumption or elastic premium or workflow standard, we need to set always on
    if (consumption_plan_location is None and
            not is_plan_elastic_premium(cmd, plan_info) and
            not is_plan_workflow_standard(cmd, plan_info) and not is_plan_ASEV3(cmd, plan_info)):
        site_config.always_on = True

    # If plan is elastic premium or windows consumption, we need these app settings
    is_windows_consumption = consumption_plan_location is not None and not is_linux
    if is_plan_elastic_premium(cmd, plan_info) or is_windows_consumption:
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
                                                      value=con_string))
        site_config.app_settings.append(NameValuePair(
            name='WEBSITE_CONTENTSHARE', value=name.lower()))

    create_app_insights = False

    if app_insights_key is not None:
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=app_insights_key))
    elif app_insights is not None:
        instrumentation_key = get_app_insights_key(
            cmd.cli_ctx, resource_group_name, app_insights)
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=instrumentation_key))
    elif not disable_app_insights:
        create_app_insights = True

    poller = client.web_apps.begin_create_or_update(
        resource_group_name, name, logicapp_def)
    logicapp = LongRunningOperation(cmd.cli_ctx)(poller)

    if consumption_plan_location and is_linux:
        logger.warning("Your Linux logic app '%s', that uses a consumption plan has been successfully "
                       "created but is not active until content is published using "
                       "Azure Portal or the Functions Core Tools.", name)
    else:
        _set_remote_or_local_git(cmd, logicapp, resource_group_name, name, deployment_source_url,
                                 deployment_source_branch, deployment_local_git)

    if create_app_insights:
        try:
            try_create_application_insights(cmd, logicapp)
        except Exception:  # pylint: disable=broad-except
            logger.warning('Error while trying to create and configure an Application Insights for the Logic App. '
                           'Please use the Azure Portal to create and configure the Application Insights, if needed.')

    if deployment_container_image_name:
        update_container_settings_functionapp(cmd, resource_group_name, name, docker_registry_server_url,
                                              deployment_container_image_name, docker_registry_server_user,
                                              docker_registry_server_password)

    return logicapp


def is_plan_workflow_standard(cmd, plan_info):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier == 'WorkflowStandard'
    return False


def is_plan_ASEV3(cmd, plan_info):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier == 'IsolatedV2'
    return False


def list_logicapp(cmd, resource_group_name=None):
    return list(filter(lambda x: x.kind is not None and "workflow" in x.kind.lower(),
                       _list_app(cmd.cli_ctx, resource_group_name)))


def show_logicapp(cmd, resource_group_name, name, slot=None):
    return _show_app(cmd, resource_group_name, name, "logicapp", slot)


def _get_linux_fx_functionapp(functions_version, runtime, runtime_version):
    if runtime_version is None:
        runtime_version = FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION[functions_version][runtime]
    if runtime == 'dotnet':
        runtime_version = DOTNET_RUNTIME_VERSION_TO_DOTNET_LINUX_FX_VERSION[runtime_version]
    else:
        runtime = runtime.upper()
    return '{}|{}'.format(runtime, runtime_version)


def _get_java_version_functionapp(functions_version, runtime_version):
    if runtime_version is None:
        runtime_version = FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION[functions_version]['java']
    if runtime_version == '8':
        return '1.8'
    return runtime_version
