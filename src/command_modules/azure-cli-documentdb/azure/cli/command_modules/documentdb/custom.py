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
    docdb_account = async_docdb_create.result() # Will be empty, shouldn't
    docdb_account = client.database_accounts.get(resource_group_name, account_name) # Workaround
    return docdb_account
