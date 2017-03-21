# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# --locations
# -ipRangeFilter
# -defaultConsistencyLevel
# - MaxIntervalInSeconds
# - MaxStalenessPrefix
# - resource-group-location
# -Kind

from azure.mgmt.documentdb.models import (
    ConsistencyPolicy,
    DatabaseAccountCreateUpdateParameters,
    Location
)
from azure.mgmt.documentdb.models.document_db_enums import DatabaseAccountKind


# pylint:disable=too-many-arguments
def cli_documentdb_create(client,
                          resource_group_name,
                          account_name,
                          locations=None,
                          kind=DatabaseAccountKind.global_document_db.value,
                          default_consistency_level=None,
                          max_staleness_prefix=100,
                          max_interval=5,
                          ip_range_filter=None):
    # pylint:disable=line-too-long
    """Create a new Azure DocumentDB database account.
    """

    consistency_policy = None
    if default_consistency_level is not None:
        consistency_policy = ConsistencyPolicy(default_consistency_level, max_staleness_prefix, max_interval)

    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    resource_client = get_mgmt_service_client(ResourceManagementClient)
    rg = resource_client.resource_groups.get(resource_group_name)
    resource_group_location = rg.location  # pylint: disable=no-member

    if not locations:
        locations.append(Location(location_name=resource_group_location, failover_priority=0))

    params = DatabaseAccountCreateUpdateParameters(
        resource_group_location,
        locations,
        kind=kind,
        consistency_policy=consistency_policy,
        ip_range_filter=ip_range_filter)

    async_docdb_create = client.database_accounts.create_or_update(resource_group_name, account_name, params)
    docdb_account = async_docdb_create.result()
    docdb_account = client.database_accounts.get(resource_group_name, account_name) # Workaround
    return docdb_account

def cli_documentdb_update(client,
                          resource_group_name,
                          account_name,
                          locations=None,
                          default_consistency_level=None,
                          max_staleness_prefix=None,
                          max_interval=None,
                          ip_range_filter=None):
    # pylint:disable=line-too-long
    """Update an existing Azure DocumentDB database account.
    """
    existing = client.database_accounts.get(resource_group_name, account_name)

    update_consistency_policy = False
    if max_interval is not None or max_staleness_prefix is not None or default_consistency_level is not None:
        update_consistency_policy = True

    if max_staleness_prefix is None:
        max_staleness_prefix = existing.consistency_policy.max_staleness_prefix

    if max_interval is None:
        max_interval = existing.consistency_policy.max_interval_in_seconds

    if default_consistency_level is None:
        default_consistency_level = existing.consistency_policy.default_consistency_level

    consistency_policy = None
    if update_consistency_policy:
        consistency_policy = ConsistencyPolicy(default_consistency_level, max_staleness_prefix, max_interval)
    else:
        consistency_policy = existing.consistency_policy

    if not locations:
        for loc in existing.read_locations:
            locations.append(Location(location_name=loc.location_name, failover_priority=loc.failover_priority))

    if ip_range_filter is None:
        ip_range_filter = existing.ip_range_filter

    params = DatabaseAccountCreateUpdateParameters(
        existing.location,
        locations,
        kind=existing.kind,
        consistency_policy=consistency_policy,
        ip_range_filter=ip_range_filter)

    async_docdb_create = client.database_accounts.create_or_update(resource_group_name, account_name, params)
    docdb_account = async_docdb_create.result()
    docdb_account = client.database_accounts.get(resource_group_name, account_name) # Workaround
    return docdb_account


def cli_documentdb_list(client,
                        resource_group_name=None):
    """Lists all Azure DocumentDB database accounts within a given resource group or subscription.
    """

    if resource_group_name:
        return client.database_accounts.list_by_resource_group(resource_group_name)
    else:
        return client.database_accounts.list()
