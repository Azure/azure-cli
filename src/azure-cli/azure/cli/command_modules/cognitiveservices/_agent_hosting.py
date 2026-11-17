# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from azure.core.exceptions import AzureError, HttpResponseError
from azure.mgmt.core.tools import parse_resource_id
from azure.cli.core.azclierror import ValidationError
from knack.log import get_logger

from ._agent_hosting_preflight import (
    build_request, preflight, _accepted_role_ids, _missing_identity_fields,
    _resource_name, _role_guid, _storage_parameters,
)
from ._client_factory import get_agent_hosting_clients


logger = get_logger(__name__)


def prepare_agent_hosting(cmd, resource_group_name, account_name, location, tags, *,
                          kind=None, custom_domain=None, **inputs):
    request = build_request(cmd, resource_group_name, account_name, location, **inputs)
    checked = preflight(cmd.cli_ctx, request, kind=kind, custom_domain=custom_domain)
    if checked.existing_account:
        resources = checked.resources
        return {'storage': resources.storage, 'management_identity': resources.management_identity,
                'workload_identity': resources.workload_identity}
    try:
        return provision(cmd.cli_ctx, checked, tags, request=request)
    except (AzureError, ValidationError):
        logger.warning('BYO AKS dependency preparation failed. Resources and role assignments created before the '
                       'failure were not deleted. Review the preceding messages before retrying.')
        raise


def provision(cli_ctx, checked, tags, request=None):
    resources = checked.resources
    tags = dict(tags or {})
    account = parse_resource_id(resources.account_id)
    clients = get_agent_hosting_clients(cli_ctx, account['subscription'])
    management = _ensure_identity(
        clients.identity, resources.management_identity, checked.management_identity,
        resources.location, tags, warn_reuse=bool(request and request.management_identity is None))
    workload = _ensure_identity(
        clients.identity, resources.workload_identity, checked.workload_identity,
        resources.location, tags, workload=True, warn_reuse=bool(request and request.workload_identity is None))
    _ensure_storage(
        clients.storage, resources.storage, checked.storage, resources.location, tags, checked.storage_sku,
        warn_reuse=bool(request and request.storage is None))
    principals = {
        resources.management_identity: management.principal_id, resources.workload_identity: workload.principal_id,
    }
    authorization_clients = {account['subscription'].lower(): clients.authorization}
    for grant in checked.grants:
        subscription = parse_resource_id(grant.scope)['subscription']
        if subscription.lower() not in authorization_clients:
            authorization_clients[subscription.lower()] = get_agent_hosting_clients(cli_ctx, subscription).authorization
        _ensure_grant(authorization_clients[subscription.lower()], grant, principals[grant.identity_id])
    return {'storage': resources.storage, 'management_identity': resources.management_identity,
            'workload_identity': resources.workload_identity}


def _ensure_identity(client, arm_id, existing, location, tags, workload=False, warn_reuse=False):
    from azure.mgmt.msi.models import Identity
    identity_type = 'workload' if workload else 'hosting-management'
    name = _resource_name(arm_id)
    if existing is not None:
        if warn_reuse:
            logger.warning("Using existing %s identity '%s'.", identity_type, name)
        return existing
    parts = parse_resource_id(arm_id)
    logger.warning("Creating %s identity '%s' ...", identity_type, name)
    identity = client.user_assigned_identities.create_or_update(
        parts['resource_group'], parts['name'], Identity(location=location, tags=tags))
    missing = _missing_identity_fields(identity, workload)
    if missing:
        raise ValidationError(f"Created identity '{name}' has missing metadata: {', '.join(missing)}. "
                              'Wait for identity provisioning to complete and inspect it before retrying.')
    return identity


def _ensure_storage(client, arm_id, existing, location, tags, sku, warn_reuse=False):
    name = _resource_name(arm_id)
    if existing is not None:
        if warn_reuse:
            logger.warning("Using existing storage account '%s'.", name)
        return existing
    if sku is None:
        raise ValidationError(f"Storage SKU was not resolved for '{name}'. Run preflight again.")
    parts = parse_resource_id(arm_id)
    logger.warning("Creating storage account '%s' (%s) ...", name, sku)
    return client.storage_accounts.begin_create(
        parts['resource_group'], parts['name'], _storage_parameters(location, tags, sku)).result()


def _find_grant(client, grant, principal, exact_scope=False):
    accepted = {_role_guid(grant.role_id)} if exact_scope else _accepted_role_ids(grant.name)
    for assignment in client.role_assignments.list_for_scope(grant.scope, filter='atScope()'):
        properties = assignment.properties
        if not properties or not properties.principal_id or not properties.role_definition_id:
            continue
        if (properties.principal_id.lower() == principal.lower() and
                _role_guid(properties.role_definition_id) in accepted and not properties.condition):
            if not exact_scope or (properties.scope and
                                   properties.scope.rstrip('/').lower() == grant.scope.rstrip('/').lower()):
                return assignment
    return None


def _ensure_grant(client, grant, principal):
    if _find_grant(client, grant, principal) is not None:
        return
    identity_name = _resource_name(grant.identity_id)
    scope_name = _resource_name(grant.scope)
    name = str(uuid.uuid5(uuid.NAMESPACE_URL, f'{grant.scope}/{principal}/{grant.role_id}'.lower()))
    logger.info("Assigning role '%s' to '%s' on '%s'", grant.name, identity_name, scope_name)
    try:
        client.role_assignments.create(grant.scope, name, {'properties': {
            'principalId': principal, 'roleDefinitionId': grant.role_id, 'principalType': 'ServicePrincipal'}})
    except HttpResponseError as error:
        if error.status_code == 409 and error.error and error.error.code == 'RoleAssignmentExists':
            try:
                existing = _find_grant(client, grant, principal, exact_scope=True)
            except AzureError as read_error:
                logger.warning("Could not verify conflicting '%s' role assignment for '%s' on '%s': %s",
                               grant.name, identity_name, scope_name, read_error)
                existing = None
            if existing is not None:
                return
        raise
