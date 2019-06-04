# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.command_modules.managedservices._client_factory import cf_registration_definitions
import uuid
from msrestazure.tools import parse_resource_id, is_valid_resource_id

logger = get_logger(__name__)
default_api_version = '2018-06-01-preview'


# region Definitions Custom Commands

# pylint: disable=unused-argument
def cli_definition_create(cmd, client,
                          name, managed_by_tenant_id, principal_id, role_definition_id,
                          plan_name=None, plan_product=None, plan_publisher=None, plan_version=None, description=None,
                          api_version=None, registration_definition_id=None, subscription=None):
    from azure.mgmt.managedservices.models import RegistrationDefinitionProperties, RegistrationDefinition, Plan, \
        Authorization

    if not registration_definition_id:
        registration_definition_id = str(uuid.uuid4())

    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id)

    if plan_name and plan_product and plan_publisher and plan_version:
        plan = Plan(plan_name, plan_publisher, plan_product, plan_version)
    else:
        plan = None

    authorization = Authorization(
        principal_id=principal_id,
        role_definition_id=role_definition_id)

    authorizations = [authorization]

    properties = RegistrationDefinitionProperties(
        description=description,
        authorizations=authorizations,
        registration_definition_name=name,
        managed_by_tenant_id=managed_by_tenant_id,
        Plan=plan,
    )

    return client.create_or_update(
        registration_definition_id=registration_definition_id,
        api_version=_get_api_version(api_version),
        scope=scope,
        properties=properties)


# pylint: disable=unused-argument
def cli_definition_get(cmd, client,
                       name_or_id,
                       api_version=None, subscription=None):
    registration_definition_id, sub_id, rg_name = _get_resource_id_parts(cmd, name_or_id, subscription)
    scope = _get_scope(sub_id, rg_name)
    return client.get(
        scope=scope,
        registration_definition_id=registration_definition_id,
        api_version=_get_api_version(api_version))


# pylint: disable=unused-argument
def cli_definition_list(cmd, client,
                        api_version=None, subscription=None):
    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id)
    return client.list(
        scope=scope,
        api_version=_get_api_version(api_version))


def cli_definition_delete(cmd, client,
                          name_or_id,
                          api_version=None, subscription=None):
    registration_definition_id, sub_id, rg_name = _get_resource_id_parts(cmd, name_or_id, subscription)
    scope = _get_scope(sub_id, rg_name)
    return client.delete(
        scope=scope,
        registration_definition_id=registration_definition_id,
        api_version=_get_api_version(api_version))


# endregion

# region Assignments Custom Commands

# pylint: disable=unused-argument
def cli_assignment_create(cmd, client,
                          registration_definition_id,
                          registration_assignment_id=None,
                          api_version=None, resource_group_name=None, subscription=None):
    from azure.mgmt.managedservices.models import RegistrationAssignmentProperties
    if not is_valid_resource_id(registration_definition_id):
        raise ValueError(
            "registration_definition_resource_id should be a valid resource id. For example, "
            "/subscriptions/id/providers/Microsoft.ManagedServices/registrationDefinitions/id")

    if not registration_assignment_id:
        registration_assignment_id = str(uuid.uuid4())

    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id, resource_group_name)
    properties = RegistrationAssignmentProperties(
        registration_definition_id=registration_definition_id)
    return client.create_or_update(
        scope=scope,
        registration_assignment_id=registration_assignment_id,
        api_version=_get_api_version(api_version),
        properties=properties)


# pylint: disable=unused-argument
def cli_assignment_get(cmd, client,
                       name_or_id,
                       api_version=None, resource_group_name=None, expand_registration_definition=False,
                       subscription=None):
    if expand_registration_definition:
        if not bool(expand_registration_definition):
            raise ValueError("expand_registration_definition should either be set to True or False")

    registration_assignment_id, sub_id, rg_name = _get_resource_id_parts(cmd, name_or_id, subscription, resource_group_name)
    scope = _get_scope(sub_id, rg_name)
    return client.get(
        scope=scope,
        registration_assignment_id=registration_assignment_id,
        api_version=_get_api_version(api_version),
        expand_registration_definition=expand_registration_definition)


# pylint: disable=unused-argument
def cli_assignment_delete(cmd, client,
                          name_or_id,
                          api_version=None, resource_group_name=None, subscription=None):
    registration_assignment_id, sub_id, rg_name = _get_resource_id_parts(cmd, name_or_id, subscription,
                                                                         resource_group_name)
    scope = _get_scope(sub_id, rg_name)
    return client.delete(
        scope=scope,
        registration_assignment_id=registration_assignment_id,
        api_version=_get_api_version(api_version))


# pylint: disable=unused-argument
def cli_assignment_list(cmd, client,
                        api_version=None,
                        resource_group_name=None,
                        subscription=None,
                        expand_registration_definition=False):
    if expand_registration_definition:
        if not bool(expand_registration_definition):
            raise ValueError("expand_registration_definition should either be set to True or False")

    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id, resource_group_name)
    api_version = _get_api_version(api_version)
    return client.list(
        scope=scope,
        api_version=api_version,
        expand_registration_definition=expand_registration_definition)


# endregion

# region private methods

def _get_subscription_id(cmd, subscription=None):
    if not subscription:
        from azure.cli.core.commands.client_factory import get_subscription_id
        sub_id = get_subscription_id(cmd.cli_ctx)
    else:
        sub_id = subscription
    return sub_id


def _get_api_version(api_version=None):
    if not api_version:
        api_version = default_api_version
    return api_version


def _get_resource_id_parts(cmd, name_or_id, subscription=None, resource_group_name=None):
    rg_name=None
    if is_valid_resource_id(name_or_id):
        id_parts = parse_resource_id(name_or_id)
        sub_id = id_parts['subscription']
        name = id_parts['name']
        if 'resource_group' in id_parts:
            rg_name = id_parts['resource_group']
    else:
        rg_name = resource_group_name
        name = name_or_id
        sub_id = _get_subscription_id(cmd, subscription)
    return name, sub_id, rg_name


def _get_scope(subscription_id, resource_group_name=None):
    if not resource_group_name:
        scope = "/subscriptions/" + subscription_id
    else:
        scope = "/subscriptions/" + subscription_id + "/resourceGroups/" + resource_group_name

    return scope
# endregion
