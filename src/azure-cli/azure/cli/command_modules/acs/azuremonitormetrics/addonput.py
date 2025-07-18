# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs._client_factory import get_container_service_client
from azure.cli.core.azclierror import (
    UnknownError,
    CLIError
)


# pylint: disable=line-too-long
def addon_put(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    client = get_container_service_client(cmd.cli_ctx, cluster_subscription).managed_clusters
    try:
        mc = client.get(cluster_resource_group_name, cluster_name)
    except CLIError as e:
        raise UnknownError(e)
    # Enable metrics if present and not already enabled
    if hasattr(mc, "azure_monitor_profile") and mc.azure_monitor_profile:
        if hasattr(mc.azure_monitor_profile, "metrics") and mc.azure_monitor_profile.metrics:
            if getattr(mc.azure_monitor_profile.metrics, "enabled", None) is False:
                mc.azure_monitor_profile.metrics.enabled = True
    try:
        client.begin_create_or_update(cluster_resource_group_name, cluster_name, mc)
    except Exception as e:
        raise UnknownError(e)
