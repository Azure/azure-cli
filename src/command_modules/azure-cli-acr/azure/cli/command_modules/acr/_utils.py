# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.commands.parameters import get_resources_in_subscription

from azure.mgmt.containerregistry.v2018_02_01_preview.models import SkuName, Sku

from ._constants import (
    REGISTRY_RESOURCE_TYPE,
    ACR_RESOURCE_PROVIDER,
    STORAGE_RESOURCE_TYPE,
    MANAGED_REGISTRY_SKU,
    CLASSIC_REGISTRY_SKU
)
from ._client_factory import (
    get_arm_service_client,
    get_storage_service_client,
    get_acr_service_client
)

logger = get_logger(__name__)


def _arm_get_resource_by_name(cli_ctx, resource_name, resource_type):
    """Returns the ARM resource in the current subscription with resource_name.
    :param str resource_name: The name of resource
    :param str resource_type: The type of resource
    """
    result = get_resources_in_subscription(cli_ctx, resource_type)
    elements = [item for item in result if item.name.lower() == resource_name.lower()]

    if not elements:
        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cli_ctx)
        message = "The resource with name '{}' and type '{}' could not be found".format(
            resource_name, resource_type)
        try:
            subscription = profile.get_subscription(cli_ctx.data['subscription_id'])
            raise CLIError("{} in subscription '{} ({})'.".format(message, subscription['name'], subscription['id']))
        except (KeyError, TypeError):
            raise CLIError("{} in the current subscription.".format(message))

    elif len(elements) == 1:
        return elements[0]
    else:
        raise CLIError(
            "More than one resources with type '{}' are found with name '{}'.".format(
                resource_type, resource_name))


def get_resource_group_name_by_resource_id(resource_id):
    """Returns the resource group name from parsing the resource id.
    :param str resource_id: The resource id
    """
    resource_id = resource_id.lower()
    resource_group_keyword = '/resourcegroups/'
    return resource_id[resource_id.index(resource_group_keyword) + len(
        resource_group_keyword): resource_id.index('/providers/')]


def get_resource_group_name_by_registry_name(cli_ctx, registry_name,
                                             resource_group_name=None):
    """Returns the resource group name for the container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    if not resource_group_name:
        arm_resource = _arm_get_resource_by_name(cli_ctx, registry_name, REGISTRY_RESOURCE_TYPE)
        resource_group_name = get_resource_group_name_by_resource_id(arm_resource.id)
    return resource_group_name


def get_resource_id_by_storage_account_name(cli_ctx, storage_account_name):
    """Returns the resource id for the storage account.
    :param str storage_account_name: The name of storage account
    """
    arm_resource = _arm_get_resource_by_name(cli_ctx, storage_account_name, STORAGE_RESOURCE_TYPE)
    return arm_resource.id


def get_registry_by_name(cli_ctx, registry_name, resource_group_name=None):
    """Returns a tuple of Registry object and resource group name.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    resource_group_name = get_resource_group_name_by_registry_name(
        cli_ctx, registry_name, resource_group_name)
    client = get_acr_service_client(cli_ctx).registries

    return client.get(resource_group_name, registry_name), resource_group_name


def get_registry_from_name_or_login_server(cli_ctx, login_server, registry_name=None):
    """Returns a Registry object for the specified name.
    :param str name: either the registry name or the login server of the registry.
    """
    client = get_acr_service_client(cli_ctx).registries
    registry_list = client.list()

    if registry_name:
        elements = [item for item in registry_list if
                    item.login_server.lower() == login_server.lower() or item.name.lower() == registry_name.lower()]
    else:
        elements = [item for item in registry_list if
                    item.login_server.lower() == login_server.lower()]

    if len(elements) == 1:
        return elements[0]
    elif len(elements) > 1:
        logger.warning("More than one registries were found by %s.", login_server)
    return None


def arm_deploy_template_new_storage(cli_ctx,
                                    resource_group_name,
                                    registry_name,
                                    location,
                                    sku,
                                    storage_account_name,
                                    admin_user_enabled,
                                    deployment_name=None):
    """Deploys ARM template to create a container registry with a new storage account.
    :param str resource_group_name: The name of resource group
    :param str registry_name: The name of container registry
    :param str location: The name of location
    :param str sku: The SKU of the container registry
    :param str storage_account_name: The name of storage account
    :param bool admin_user_enabled: Enable admin user
    :param str deployment_name: The name of the deployment
    """
    from azure.mgmt.resource.resources.models import DeploymentProperties
    from azure.cli.core.util import get_file_json
    import os

    parameters = _parameters(
        registry_name=registry_name,
        location=location,
        sku=sku,
        admin_user_enabled=admin_user_enabled,
        storage_account_name=storage_account_name)

    file_path = os.path.join(os.path.dirname(__file__), 'template_new_storage.json')
    template = get_file_json(file_path)
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')

    return _arm_deploy_template(
        get_arm_service_client(cli_ctx).deployments, resource_group_name, deployment_name, properties)


def arm_deploy_template_existing_storage(cli_ctx,
                                         resource_group_name,
                                         registry_name,
                                         location,
                                         sku,
                                         storage_account_name,
                                         admin_user_enabled,
                                         deployment_name=None):
    """Deploys ARM template to create a container registry with an existing storage account.
    :param str resource_group_name: The name of resource group
    :param str registry_name: The name of container registry
    :param str location: The name of location
    :param str sku: The SKU of the container registry
    :param str storage_account_name: The name of storage account
    :param bool admin_user_enabled: Enable admin user
    :param str deployment_name: The name of the deployment
    """
    from azure.mgmt.resource.resources.models import DeploymentProperties
    from azure.cli.core.util import get_file_json
    import os

    storage_account_id = get_resource_id_by_storage_account_name(cli_ctx, storage_account_name)

    parameters = _parameters(
        registry_name=registry_name,
        location=location,
        sku=sku,
        admin_user_enabled=admin_user_enabled,
        storage_account_id=storage_account_id)

    file_path = os.path.join(os.path.dirname(__file__), 'template_existing_storage.json')
    template = get_file_json(file_path)
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')

    return _arm_deploy_template(
        get_arm_service_client(cli_ctx).deployments, resource_group_name, deployment_name, properties)


def _arm_deploy_template(deployments_client,
                         resource_group_name,
                         deployment_name,
                         properties):
    """Deploys ARM template to create a container registry.
    :param obj deployments_client: ARM deployments service client
    :param str resource_group_name: The name of resource group
    :param str deployment_name: The name of the deployment
    :param DeploymentProperties properties: The properties of a deployment
    """
    if deployment_name is None:
        import random
        deployment_name = '{0}_{1}'.format(ACR_RESOURCE_PROVIDER, random.randint(100, 800))

    return deployments_client.create_or_update(resource_group_name, deployment_name, properties)


def _parameters(registry_name,
                location,
                sku,
                admin_user_enabled,
                storage_account_name=None,
                storage_account_id=None,
                registry_api_version=None):
    """Returns a dict of deployment parameters.
    :param str registry_name: The name of container registry
    :param str location: The name of location
    :param str sku: The SKU of the container registry
    :param bool admin_user_enabled: Enable admin user
    :param str storage_account_name: The name of storage account
    :param str storage_account_id: The resource ID of storage account
    :param str registry_api_version: The API version of the container registry
    """
    parameters = {
        'registryName': {'value': registry_name},
        'registryLocation': {'value': location},
        'registrySku': {'value': sku},
        'adminUserEnabled': {'value': admin_user_enabled}
    }
    if registry_api_version:
        parameters['registryApiVersion'] = {'value': registry_api_version}
    if storage_account_name:
        parameters['storageAccountName'] = {'value': storage_account_name}
    if storage_account_id:
        parameters['storageAccountId'] = {'value': storage_account_id}

    return parameters


def random_storage_account_name(cli_ctx, registry_name):
    from datetime import datetime

    client = get_storage_service_client(cli_ctx).storage_accounts
    prefix = registry_name[:18].lower()

    for x in range(10):
        time_stamp_suffix = datetime.utcnow().strftime('%H%M%S')
        storage_account_name = ''.join([prefix, time_stamp_suffix])[:24]
        logger.debug("Checking storage account %s with name '%s'.", x, storage_account_name)
        if client.check_name_availability(storage_account_name).name_available:  # pylint: disable=no-member
            return storage_account_name

    raise CLIError("Could not find an available storage account name. Please try again later.")


def validate_managed_registry(cli_ctx, registry_name, resource_group_name=None, message=None):
    """Raise CLIError if the registry in not in Managed SKU.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    registry, resource_group_name = get_registry_by_name(cli_ctx, registry_name, resource_group_name)

    if not registry.sku or registry.sku.name not in MANAGED_REGISTRY_SKU:
        raise CLIError(message or "This operation is only supported for managed registries.")

    return registry, resource_group_name


def validate_premium_registry(cli_ctx, registry_name, resource_group_name=None, message=None):
    """Raise CLIError if the registry in not in Premium SKU.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    registry, resource_group_name = get_registry_by_name(cli_ctx, registry_name, resource_group_name)

    if not registry.sku or registry.sku.name != SkuName.premium.value:
        raise CLIError(message or "This operation is only supported for managed registries in Premium SKU.")

    return registry, resource_group_name


def validate_sku_update(current_sku, sku_parameter):
    """Validates a registry SKU update parameter.
    :param object sku_parameter: The registry SKU update parameter
    """
    if sku_parameter is None:
        return

    if isinstance(sku_parameter, dict):
        if 'name' not in sku_parameter:
            _invalid_sku_update()
        if sku_parameter['name'] not in CLASSIC_REGISTRY_SKU and sku_parameter['name'] not in MANAGED_REGISTRY_SKU:
            _invalid_sku_update()
        if current_sku in MANAGED_REGISTRY_SKU and sku_parameter['name'] in CLASSIC_REGISTRY_SKU:
            _invalid_sku_downgrade()
    elif isinstance(sku_parameter, Sku):
        if current_sku in MANAGED_REGISTRY_SKU and sku_parameter.name in CLASSIC_REGISTRY_SKU:
            _invalid_sku_downgrade()
    else:
        _invalid_sku_update()


def _invalid_sku_update():
    raise CLIError("Please specify SKU by '--sku SKU' or '--set sku.name=SKU'. Allowed SKUs: {0}".format(
        MANAGED_REGISTRY_SKU))


def _invalid_sku_downgrade():
    raise CLIError("Managed registries could not be downgraded to Classic SKU.")
