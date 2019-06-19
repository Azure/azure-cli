# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from builtins import ValueError, bool

import uuid
from knack.log import get_logger
from msrestazure.tools import parse_resource_id, is_valid_resource_id

logger = get_logger(__name__)
default_api_version = '2018-06-01-preview'


# region Definitions Custom Commands

# pylint: disable=unused-argument
def cli_definition_create(cmd, client,
                          name, tenant_id, principal_id, role_definition_id,
                          plan_name=None, plan_product=None, plan_publisher=None, plan_version=None, description=None,
                          definition_id=None, **kwargs):
    from azure.mgmt.managedservices.models import RegistrationDefinitionProperties, Plan, \
        Authorization

    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)

    if not definition_id:
        definition_id = str(uuid.uuid4())

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
        managed_by_tenant_id=tenant_id,
        Plan=plan,
    )

    return client.create_or_update(
        registration_definition_id=definition_id,
        api_version=_get_api_version(api_version),
        scope=scope,
        properties=properties)


# pylint: disable=unused-argument
def cli_definition_get(cmd, client,
                       definition,
                       **kwargs):
    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    definition_id, sub_id, rg_name = _get_resource_id_parts(cmd, definition, subscription)
    scope = _get_scope(sub_id, rg_name)
    return client.get(
        scope=scope,
        registration_definition_id=definition_id,
        api_version=_get_api_version(api_version))


# pylint: disable=unused-argument
def cli_definition_list(cmd, client, **kwargs):
    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id)
    return client.list(
        scope=scope,
        api_version=_get_api_version(api_version))


def cli_definition_delete(cmd, client,
                          definition, **kwargs):
    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    definition_id, sub_id, rg_name = _get_resource_id_parts(cmd, definition, subscription)
    scope = _get_scope(sub_id, rg_name)
    return client.delete(
        scope=scope,
        registration_definition_id=definition_id,
        api_version=_get_api_version(api_version))


# endregion

# region Assignments Custom Commands

# pylint: disable=unused-argument
def cli_assignment_create(cmd, client,
                          definition_id,
                          assignment_id=None,
                          **kwargs):
    from azure.mgmt.managedservices.models import RegistrationAssignmentProperties
    if not is_valid_resource_id(definition_id):
        raise ValueError(
            "registration_definition_resource_id should be a valid resource id. For example, "
            "/subscriptions/id/providers/Microsoft.ManagedServices/registrationDefinitions/id")

    if not assignment_id:
        assignment_id = str(uuid.uuid4())

    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    resource_group_name = kwargs.pop('resource_group_name', None)

    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id, resource_group_name)
    properties = RegistrationAssignmentProperties(
        registration_definition_id=definition_id)
    return client.create_or_update(
        scope=scope,
        registration_assignment_id=assignment_id,
        api_version=_get_api_version(api_version),
        properties=properties)


# pylint: disable=unused-argument
def cli_assignment_get(cmd, client,
                       assignment,
                       **kwargs):
    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    resource_group_name = kwargs.pop('resource_group_name', None)
    include_definition = kwargs.pop('include_definition', None)

    if include_definition:
        if not bool(include_definition):
            raise ValueError("include_definition should either be set to True or False")

    assignment_id, sub_id, rg_name = _get_resource_id_parts(cmd, assignment, subscription, resource_group_name)
    scope = _get_scope(sub_id, rg_name)
    return client.get(
        scope=scope,
        registration_assignment_id=assignment_id,
        api_version=_get_api_version(api_version),
        expand_registration_definition=include_definition)


# pylint: disable=unused-argument
def cli_assignment_delete(cmd, client,
                          assignment,
                          **kwargs):
    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    resource_group_name = kwargs.pop('resource_group_name', None)
    assignment_id, sub_id, rg_name = _get_resource_id_parts(cmd, assignment, subscription, resource_group_name)
    scope = _get_scope(sub_id, rg_name)
    return client.delete(
        scope=scope,
        registration_assignment_id=assignment_id,
        api_version=_get_api_version(api_version))


# pylint: disable=unused-argument
def cli_assignment_list(cmd, client,
                        **kwargs):
    subscription = kwargs.pop('subscription', None)
    api_version = kwargs.pop('api_version', None)
    resource_group_name = kwargs.pop('resource_group_name', None)
    include_definition = kwargs.pop('include_definition', None)

    if include_definition:
        if not bool(include_definition):
            raise ValueError("include_definition should either be set to True or False")

    sub_id = _get_subscription_id(cmd, subscription)
    scope = _get_scope(sub_id, resource_group_name)
    api_version = _get_api_version(api_version)
    return client.list(
        scope=scope,
        api_version=api_version,
        expand_registration_definition=include_definition)


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
    rg_name = None
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
