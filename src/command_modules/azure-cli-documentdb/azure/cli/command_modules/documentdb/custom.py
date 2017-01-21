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

from azure.cli.command_modules.documentdb.sdk.models import (
    ConsistencyPolicy,
    DatabaseAccountCreateUpdateParameters,
    DatabaseAccountKind,
    DatabaseAccountOfferType,
    DefaultConsistencyLevel,
    Location
)

def cli_documentdb_create(client,
                          resource_group_name,
                          name,
                          resource_group_location,
                          locations,
                          default_consistency_level=None,
                          max_staleness_prefix=100,
                          max_interval_in_seconds=5,
                          ip_range_filter=None):
    # pylint:disable=line-too-long
    """Create new DocumentDB Database Account
    :param resource_group_name: Name of resource group
    :param name: Name of DocumentDB Database Account
    :param location: Resource group location
    """
    consistency_policy = None
    if not default_consistency_level is None:
        consistency_policy = ConsistencyPolicy(default_consistency_level, max_staleness_prefix, max_interval_in_seconds)

    params = DatabaseAccountCreateUpdateParameters(
        resource_group_location,
        locations,
        consistency_policy=consistency_policy,
        ip_range_filter=ip_range_filter)

    return client.database_accounts.create_or_update(resource_group_name, name, params)