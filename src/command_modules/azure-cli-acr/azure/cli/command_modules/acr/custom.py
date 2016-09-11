#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import (
    cli_command,
    LongRunningOperation
)
from azure.cli.core._util import CLIError
from azure.cli.command_modules.role.custom import _create_role_assignment

from azure.cli.command_modules.acr.mgmt_acr.models import (
    RegistryUpdateParameters,
    RegistryPropertiesCreateParameters
)

from ._constants import (
    DEFAULT_ROLE
)
from ._factory import get_acr_service_client
from ._arm_utils import (
    arm_get_registries_in_subscription,
    arm_get_registries_in_resource_group,
    arm_get_registry_by_name,
    arm_deploy_template,
    add_tag_storage_account,
    delete_tag_storage_account
)
from ._utils import (
    get_registry_by_name,
    get_resource_group_name_by_resource_id,
    create_service_principal,
    registry_not_found
)

from ._format import output_format

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

def acr_list(resource_group_name=None):
    '''List container registries.
    :param str resource_group_name: The name of resource group
    '''
    if resource_group_name:
        return arm_get_registries_in_resource_group(resource_group_name)
    else:
        return arm_get_registries_in_subscription()

def acr_create(registry_name, #pylint: disable=too-many-arguments
               resource_group_name,
               location,
               storage_account_name=None,
               new_sp=False,
               app_id=None,
               password=None,
               role=DEFAULT_ROLE,
               enable_admin=False):
    '''Create a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str location: The name of location
    :param str storage_account_name: The name of storage account
    :param bool new_sp: Create a new service principal
    :param str app_id: The app id of an existing service principal
    :param str password: The password used to log into the container registry
    :param str role: The name of role
    :param bool enable_admin: Enable admin user
    '''
    if new_sp and app_id:
        raise CLIError('new-service-principal and app-id should not be specified together.')

    session_key = None
    # Create a service principal
    if new_sp:
        (app_id,
         password,
         session_key) = create_service_principal(registry_name, password)

    # Create a container registry
    LongRunningOperation()(
        arm_deploy_template(resource_group_name,
                            registry_name,
                            location,
                            storage_account_name,
                            enable_admin)
    )

    client = get_acr_service_client().registries
    registry = client.get_properties(resource_group_name, registry_name)
    add_tag_storage_account(storage_account_name, registry_name)

    logger.warning('\nCreate a new service principal and assign access:')
    logger.warning(
        '  az ad sp create-for-rbac --scopes %s --role Owner --secret <password>',
        registry.id) #pylint: disable=E1101
    logger.warning('\nUse an existing service principal and assign access:')
    logger.warning(
        '  az role assignment create --scope %s --role Owner --assignee <app-id>',
        registry.id) #pylint: disable=E1101

    # Create role assignment
    if app_id:
        _create_role_assignment(role,
                                app_id,
                                scope=registry.id, #pylint: disable=E1101
                                ocp_aad_session_key=session_key)
        logger.warning('Service principal has been configured.')
        logger.warning('  id(client_id):           %s', app_id)
        if password:
            logger.warning('  password(client_secret): %s', password)

    return registry

def acr_delete(registry_name, resource_group_name=None):
    '''Delete a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    '''
    registry = arm_get_registry_by_name(registry_name)
    if registry is None:
        registry_not_found(registry_name)

    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_resource_id(registry.id)

    client = get_acr_service_client().registries

    storage_account_name = client.get_properties( #pylint: disable=E1101
        resource_group_name, registry_name).properties.storage_account.name
    delete_tag_storage_account(storage_account_name, registry_name)

    return client.delete(resource_group_name, registry_name)

def acr_show(registry_name, resource_group_name=None):
    '''Get a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    '''
    registry = arm_get_registry_by_name(registry_name)
    if registry is None:
        registry_not_found(registry_name)

    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_resource_id(registry.id)

    client = get_acr_service_client().registries

    return client.get_properties(resource_group_name, registry_name)

def acr_update(registry_name, #pylint: disable=too-many-arguments
               resource_group_name=None,
               tags=None,
               new_sp=False,
               app_id=None,
               password=None,
               role=DEFAULT_ROLE,
               disable_admin=False,
               enable_admin=False,
               tenant_id=None):
    '''Update a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param dict tags: The set of tags
    :param bool new_sp: Create a new service principal
    :param str app_id: The app id of an existing service principal
    :param str password: The password used to log into the container registry
    :param str role: The name of role
    :param bool disable_admin: Disable admin user
    :param bool enable_admin: Enable admin user
    :param str tenant_id: Tenant id for service principal login
    '''
    if new_sp and app_id:
        raise CLIError('new_sp and app-id should not be specified together.')

    if disable_admin and enable_admin:
        raise CLIError('disable_admin and enable_admin should not be specified together.')

    registry = get_registry_by_name(registry_name)
    if registry is None:
        registry_not_found(registry_name)

    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_resource_id(registry.id)

    client = get_acr_service_client().registries

    session_key = None
    # Create a service principal
    if new_sp:
        (app_id,
         password,
         session_key) = create_service_principal(registry_name, password)

    # Create role assignment
    if app_id:
        _create_role_assignment(role,
                                app_id,
                                scope=registry.id, #pylint: disable=E1101
                                ocp_aad_session_key=session_key)
        logger.warning('Service principal has been configured.')
        logger.warning('  id(client_id):           %s', app_id)
        if password:
            logger.warning('  password(client_secret): %s', password)

    # Set admin_user_enabled
    admin_user_enabled = None
    if disable_admin:
        admin_user_enabled = False
    if enable_admin:
        admin_user_enabled = True
    if admin_user_enabled is None:
        admin_user_enabled = registry.properties.admin_user_enabled

    # Set tags
    newTags = registry.tags
    if isinstance(tags, dict):
        if tags:
            for key in tags:
                if tags[key]:
                    newTags[key] = tags[key]
                elif key in newTags:
                    del newTags[key]
        else:
            newTags = {}

    return client.update(
        resource_group_name, registry_name,
        RegistryUpdateParameters(
            tags=newTags,
            properties=RegistryPropertiesCreateParameters(
                tenant_id=tenant_id,
                admin_user_enabled=admin_user_enabled
            )
        )
    )

cli_command('acr list', acr_list, table_transformer=output_format)
cli_command('acr create', acr_create, table_transformer=output_format)
cli_command('acr delete', acr_delete, table_transformer=output_format)
cli_command('acr show', acr_show, table_transformer=output_format)
cli_command('acr update', acr_update, table_transformer=output_format)
