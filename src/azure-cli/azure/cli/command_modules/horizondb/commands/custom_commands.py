# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals

from knack.log import get_logger
from azure.cli.core.util import sdk_no_wait

logger = get_logger(__name__)


def horizondb_cluster_create(cmd, client, resource_group_name, cluster_name, location,
                             administrator_login, administrator_login_password,
                             tags=None, version=None, 
                             replica_count=None, v_cores=None,
                             zone_placement_policy=None,
                             no_wait=False):
    from azure.mgmt.horizondb.models import HorizonDbCluster, HorizonDbClusterProperties

    properties = HorizonDbClusterProperties(
        administrator_login=administrator_login,
        administrator_login_password=administrator_login_password,
        version=version,
        create_mode="Create",
        replica_count=replica_count,
        v_cores=v_cores,
        zone_placement_policy=zone_placement_policy,
    )

    resource = HorizonDbCluster(
        location=location,
        tags=tags,
        properties=properties,
    )

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       resource=resource)


def horizondb_cluster_delete(cmd, client, resource_group_name, cluster_name, no_wait=False):
    return sdk_no_wait(no_wait, client.begin_delete,
                       resource_group_name=resource_group_name,
                       cluster_name=cluster_name)


def horizondb_cluster_list(cmd, client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name=resource_group_name)
    return client.list_by_subscription()