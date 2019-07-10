# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid
from knack.log import get_logger
from msrestazure.tools import parse_resource_id, is_valid_resource_id

logger = get_logger(__name__)

# region Definitions Custom Commands


# pylint: disable=unused-argument
def cli_definition_create(cmd, client,
                          name, tenant_id, principal_id, role_definition_id,
                          plan_name=None, plan_product=None, plan_publisher=None, plan_version=None, description=None,
                          definition_id=None):
    from azure.mgmt.managedservices.models import RegistrationDefinitionProperties, Plan, \
        Authorization

    if not definition_id:
        definition_id = str(uuid.uuid4())

    subscription = _get_subscription_id_from_cmd(cmd)
    scope = _get_scope(subscription)

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
        scope=scope,
        properties=properties)


# pylint: disable=unused-argument
def cli_definition_get(cmd, client,
                       definition):
    subscription = _get_subscription_id_from_cmd(cmd)
    definition_id, sub_id, rg_name = _get_resource_id_parts(cmd, definition, subscription)
    scope = _get_scope(sub_id, rg_name)
    return client.get(
        scope=scope,
        registration_definition_id=definition_id)


# pylint: disable=unused-argument
def cli_definition_list(cmd, client):
    subscription = _get_subscription_id_from_cmd(cmd)
    scope = _get_scope(subscription)
    return client.list(scope=scope)


def cli_definition_delete(cmd, client, definition):
    subscription = _get_subscription_id_from_cmd(cmd)
    definition_id, sub_id, rg_name = _get_resource_id_parts(cmd, definition, subscription)
    scope = _get_scope(sub_id, rg_name)
    return client.delete(
        scope=scope,
        registration_definition_id=definition_id)


# endregion

# region Assignments Custom Commands

# pylint: disable=unused-argument
def cli_assignment_create(cmd, client,
                          definition,
                          assignment_id=None,
                          resource_group_name=None):
    from azure.mgmt.managedservices.models import RegistrationAssignmentProperties
    if not is_valid_resource_id(definition):
        raise ValueError(
            "definition should be a valid resource id. For example, "
            "/subscriptions/id/providers/Microsoft.ManagedServices/registrationDefinitions/id")

    if not assignment_id:
        assignment_id = str(uuid.uuid4())

    subscription = _get_subscription_id_from_cmd(cmd)
    scope = _get_scope(subscription, resource_group_name)
    properties = RegistrationAssignmentProperties(
        registration_definition_id=definition)
    return client.create_or_update(
        scope=scope,
        registration_assignment_id=assignment_id,
        properties=properties)


# pylint: disable=unused-argument
def cli_assignment_get(cmd, client,
                       assignment,
                       resource_group_name=None,
                       include_definition=None):
    subscription = _get_subscription_id_from_cmd(cmd)
    assignment_id, sub_id, rg_name = _get_resource_id_parts(cmd, assignment, subscription, resource_group_name)
    scope = _get_scope(sub_id, rg_name)
    return client.get(
        scope=scope,
        registration_assignment_id=assignment_id,
        expand_registration_definition=include_definition)


# pylint: disable=unused-argument
def cli_assignment_delete(cmd, client,
                          assignment,
                          resource_group_name=None):
    subscription = _get_subscription_id_from_cmd(cmd)
    assignment_id, sub_id, rg_name = _get_resource_id_parts(cmd, assignment, subscription, resource_group_name)
    scope = _get_scope(sub_id, rg_name)
    return client.delete(
        scope=scope,
        registration_assignment_id=assignment_id)


# pylint: disable=unused-argument
def cli_assignment_list(cmd, client,
                        resource_group_name=None,
                        include_definition=None):
    sub_id = _get_subscription_id_from_cmd(cmd)
    scope = _get_scope(sub_id, resource_group_name)
    return client.list(
        scope=scope,
        expand_registration_definition=include_definition)

# endregion

# region private methods


def _get_subscription_id_from_cmd(cmd):
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription = get_subscription_id(cmd.cli_ctx)
    return subscription


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
        sub_id = _get_subscription_id_from_cmd(cmd)
    return name, sub_id, rg_name


def _get_scope(subscription_id, resource_group_name=None):
    if not resource_group_name:
        scope = "/subscriptions/" + subscription_id
    else:
        scope = "/subscriptions/" + subscription_id + "/resourceGroups/" + resource_group_name

    return scope
# endregion
