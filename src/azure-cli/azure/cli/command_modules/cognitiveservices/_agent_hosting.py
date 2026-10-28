# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from azure.core.exceptions import AzureError, HttpResponseError
from azure.mgmt.core.tools import parse_resource_id
from azure.cli.core.azclierror import ValidationError
from knack.log import get_logger

from ._agent_hosting_preflight import build_request, preflight, _missing_identity_fields, _storage_parameters
from ._client_factory import get_agent_hosting_clients


logger = get_logger(__name__)


def prepare_agent_hosting(cmd, resource_group_name, account_name, location, tags, *,
                          kind=None, custom_domain=None, **inputs):
    request = build_request(cmd, resource_group_name, account_name, location, **inputs)
    checked = preflight(cmd.cli_ctx, request, kind=kind, custom_domain=custom_domain)
    try:
        return provision(cmd.cli_ctx, checked, tags)
    except (AzureError, ValidationError):
        logger.warning('BYO AKS dependency preparation failed. Previously created resources and role assignments '
                       'are not automatically deleted. Inspect the resource IDs reported above before retrying.')
        raise


def provision(cli_ctx, checked, tags):
    resources = checked.resources
    tags = dict(tags or {})
    account = parse_resource_id(resources.account_id)
    clients = get_agent_hosting_clients(cli_ctx, account['subscription'])
    management = _ensure_identity(clients.identity, resources.management_identity, checked.management_identity,
                                  resources.location, tags)
    workload = _ensure_identity(clients.identity, resources.workload_identity, checked.workload_identity,
                                resources.location, tags, workload=True)
    _ensure_storage(clients.storage, resources.storage, checked.storage, resources.location, tags, checked.storage_sku)
    principals = {
        resources.management_identity: management.principal_id, resources.workload_identity: workload.principal_id,
    }
    authorization_clients = {account['subscription'].lower(): clients.authorization}
    for grant in checked.grants:
        subscription = parse_resource_id(grant.scope)['subscription']
        if subscription.lower() not in authorization_clients:
            authorization_clients[subscription.lower()] = get_agent_hosting_clients(cli_ctx, subscription).authorization
        _ensure_grant(authorization_clients[subscription.lower()], grant, principals[grant.identity_id])
    logger.info('BYO AKS dependencies are ready: management identity=%s; workload identity=%s; Storage=%s. '
                'If Account creation fails, inspect these resources; they are not automatically deleted.',
                resources.management_identity, resources.workload_identity, resources.storage)
    return {'storage': resources.storage, 'management_identity': resources.management_identity,
            'workload_identity': resources.workload_identity}


def _ensure_identity(client, arm_id, existing, location, tags, workload=False):
    from azure.mgmt.msi.models import Identity
    if existing is not None:
        logger.info('Reusing managed identity %s', arm_id)
        return existing
    parts = parse_resource_id(arm_id)
    logger.warning('Creating managed identity %s', arm_id)
    identity = client.user_assigned_identities.create_or_update(
        parts['resource_group'], parts['name'], Identity(location=location, tags=tags))
    missing = _missing_identity_fields(identity, workload)
    if missing:
        raise ValidationError(f'Created identity {arm_id} has missing metadata: {", ".join(missing)}. '
                              'Wait for identity provisioning to complete and inspect it before retrying.')
    return identity


def _ensure_storage(client, arm_id, existing, location, tags, sku):
    if existing is not None:
        logger.info('Reusing Storage %s', arm_id)
        return existing
    if sku is None:
        raise ValidationError(f'Storage SKU was not resolved for {arm_id}. Run preflight again.')
    parts = parse_resource_id(arm_id)
    logger.warning('Creating Storage %s', arm_id)
    return client.storage_accounts.begin_create(
        parts['resource_group'], parts['name'], _storage_parameters(location, tags, sku)).result()


def _find_grant(client, grant, principal, exact_scope=False):
    for assignment in client.role_assignments.list_for_scope(grant.scope, filter='atScope()'):
        properties = assignment.properties
        if not properties or not properties.principal_id or not properties.role_definition_id:
            continue
        if (properties.principal_id.lower() == principal.lower() and
                properties.role_definition_id.lower() == grant.role_id.lower() and not properties.condition):
            if not exact_scope or (properties.scope and
                                   properties.scope.rstrip('/').lower() == grant.scope.rstrip('/').lower()):
                return assignment
    return None


def _ensure_grant(client, grant, principal):
    existing = _find_grant(client, grant, principal)
    if existing is not None:
        logger.info('Reusing role assignment %s', existing.id)
        return
    name = str(uuid.uuid5(uuid.NAMESPACE_URL, f'{grant.scope}/{principal}/{grant.role_id}'.lower()))
    arm_id = f'{grant.scope}/providers/Microsoft.Authorization/roleAssignments/{name}'
    logger.warning('Creating %s role assignment %s for principal %s', grant.name, arm_id, principal)
    try:
        client.role_assignments.create(grant.scope, name, {'properties': {
            'principalId': principal, 'roleDefinitionId': grant.role_id, 'principalType': 'ServicePrincipal'}})
    except HttpResponseError as error:
        if error.status_code == 409 and error.error and error.error.code == 'RoleAssignmentExists':
            try:
                existing = _find_grant(client, grant, principal, exact_scope=True)
            except AzureError as read_error:
                logger.warning('Could not verify conflicting role assignment %s: %s', arm_id, read_error)
                existing = None
            if existing is not None:
                logger.info('Reusing role assignment %s', existing.id)
                return
        raise
