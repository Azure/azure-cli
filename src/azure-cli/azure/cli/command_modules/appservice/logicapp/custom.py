# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger

from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id

from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError

from azure.cli.command_modules.appservice.utils import (_list_app)
from azure.cli.command_modules.appservice._client_factory import web_client_factory
from azure.cli.command_modules.appservice.custom import (
    _format_fx_version,
    _get_extension_version_functionapp,
    get_app_insights_key,
    parse_docker_image_name,
    is_plan_elastic_premium,
    _validate_and_get_connection_string,
    update_container_settings_functionapp,
    try_create_application_insights,
    _set_remote_or_local_git, show_app,
    create_app_service_plan,
    get_site_configs,
    _generic_site_operation,
    update_app_settings,
    delete_app_settings,
    get_app_settings)

from ._constants import (DEFAULT_LOGICAPP_FUNCTION_VERSION,
                         DEFAULT_LOGICAPP_RUNTIME,
                         FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION,
                         DOTNET_RUNTIME_VERSION_TO_DOTNET_LINUX_FX_VERSION)

logger = get_logger(__name__)


def create_logicapp(cmd, resource_group_name, name, storage_account, plan=None,
                    runtime_version=None, functions_version=DEFAULT_LOGICAPP_FUNCTION_VERSION,
                    app_insights=None, app_insights_key=None, disable_app_insights=None,
                    deployment_source_url=None, deployment_source_branch='master', deployment_local_git=None,
                    docker_registry_server_password=None, docker_registry_server_user=None,
                    deployment_container_image_name=None, tags=None, https_only=False):
    # pylint: disable=too-many-statements, too-many-branches, too-many-locals
    runtime = None
    if not deployment_container_image_name:
        runtime = DEFAULT_LOGICAPP_RUNTIME
        if runtime_version is None:
            runtime_version = FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION[functions_version][runtime]

    if deployment_source_url and deployment_local_git:
        raise MutuallyExclusiveArgumentError('usage error: --deployment-source-url <url> | --deployment-local-git')

    SiteConfig, Site, NameValuePair = cmd.get_models('SiteConfig', 'Site', 'NameValuePair')

    docker_registry_server_url = parse_docker_image_name(deployment_container_image_name)

    site_config = SiteConfig(app_settings=[])
    logicapp_def = Site(location=None, site_config=site_config, tags=tags, https_only=https_only)
    client = web_client_factory(cmd.cli_ctx)
    plan_info = None
    if runtime is not None:
        runtime = runtime.lower()

    logicapp_def.kind = 'functionapp,workflowapp'

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

    if runtime == DEFAULT_LOGICAPP_RUNTIME and runtime_version is not None:
        site_config.app_settings.append(NameValuePair(
            name='WEBSITE_NODE_DEFAULT_VERSION', value=runtime_version))

    con_string = _validate_and_get_connection_string(cmd.cli_ctx, resource_group_name, storage_account)

    if is_linux:
        logicapp_def.kind = 'functionapp,workflowapp,linux'
        logicapp_def.reserved = True

    if deployment_container_image_name:
        logicapp_def.kind = 'functionapp,workflowapp,linux,container'
        site_config.app_settings.append(NameValuePair(name='DOCKER_CUSTOM_IMAGE_NAME',
                                                      value=deployment_container_image_name))
        site_config.app_settings.append(NameValuePair(name='FUNCTION_APP_EDIT_MODE', value='readOnly'))
        site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                      value='false'))
        site_config.linux_fx_version = _format_fx_version(deployment_container_image_name)

        if deployment_container_image_name is None:
            site_config.linux_fx_version = _get_linux_fx_functionapp(
                functions_version, runtime, runtime_version)
        else:
            logicapp_def.kind = 'functionapp,workflowapp'

    # adding appsetting to site to make it a workflow
    site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION',
                                                  value=_get_extension_version_functionapp(functions_version)))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsStorage', value=con_string))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsDashboard', value=con_string))
    site_config.app_settings.append(NameValuePair(
        name='AzureFunctionsJobHost__extensionBundle__id', value="Microsoft.Azure.Functions.ExtensionBundle.Workflows"))
    site_config.app_settings.append(NameValuePair(
        name='AzureFunctionsJobHost__extensionBundle__version', value="[1.*, 2.0.0)"))
    site_config.app_settings.append(
        NameValuePair(name='APP_KIND', value="workflowApp"))

    # If plan is not consumption or elastic premium or workflow standard, we need to set always on
    if (not is_plan_elastic_premium(cmd, plan_info) and not is_plan_workflow_standard(cmd, plan_info) and not
            is_plan_ASEV3(cmd, plan_info)):
        site_config.always_on = True

    # If plan is elastic premium or windows consumption, we need these app settings
    if is_plan_elastic_premium(cmd, plan_info) or is_plan_workflow_standard(cmd, plan_info):
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


def _get_linux_fx_functionapp(functions_version, runtime, runtime_version):
    if runtime_version is None:
        runtime_version = FUNCTIONS_VERSION_TO_DEFAULT_RUNTIME_VERSION[functions_version][runtime]
    if runtime == 'dotnet':
        runtime_version = DOTNET_RUNTIME_VERSION_TO_DOTNET_LINUX_FX_VERSION[runtime_version]
    else:
        runtime = runtime.upper()
    return '{}|{}'.format(runtime, runtime_version)


def show_logicapp(cmd, resource_group_name, name):
    return show_app(cmd, resource_group_name=resource_group_name, name=name)


def scale_logicapp(cmd, resource_group_name, name, minimum_instance_count=None, maximum_instance_count=None, slot=None):
    return update_logicapp_scale(cmd=cmd,
                                 resource_group_name=resource_group_name,
                                 name=name,
                                 slot=slot,
                                 function_app_scale_limit=maximum_instance_count,
                                 minimum_elastic_instance_count=minimum_instance_count)


# pylint: disable=unused-argument
def update_logicapp_scale(cmd, resource_group_name, name, slot=None,
                          function_app_scale_limit=None,
                          minimum_elastic_instance_count=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    import inspect
    frame = inspect.currentframe()

    # note: getargvalues is used already in azure.cli.core.commands.
    # and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame)  # pylint: disable=deprecated-method

    for arg in args[3:]:
        if values.get(arg, None):
            setattr(configs, arg, values[arg])

    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)


def get_logicapp_app_settings(cmd, resource_group_name, name, slot=None):
    return get_app_settings(cmd, resource_group_name, name, slot)


def update_logicapp_app_settings(cmd, resource_group_name, name, settings=None, slot=None, slot_settings=None):
    return update_app_settings(cmd, resource_group_name, name, settings, slot, slot_settings)


def delete_logicapp_app_settings(cmd, resource_group_name, name, setting_names, slot=None):
    return delete_app_settings(cmd, resource_group_name, name, setting_names, slot)
