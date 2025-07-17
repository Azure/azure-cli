# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client


def cf_migrate(cli_ctx, **_):
    """Client factory for Azure Migrate operations."""
    # Since Azure Migrate may not have a standard management client,
    # we'll create a generic client that can be used for REST API calls
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_MIGRATE)


def cf_migrate_projects(cli_ctx, **_):
    """Client factory for Azure Migrate projects."""
    # For now, return the base client. In a real implementation,
    # this would return a specific operation group
    return cf_migrate(cli_ctx)


def cf_migrate_assessments(cli_ctx, **_):
    """Client factory for Azure Migrate assessments."""
    return cf_migrate(cli_ctx)


def cf_migrate_machines(cli_ctx, **_):
    """Client factory for Azure Migrate machines."""
    return cf_migrate(cli_ctx)


def cf_migrate_solutions(cli_ctx, **_):
    """Client factory for Azure Migrate solutions.""" 
    return cf_migrate(cli_ctx)
