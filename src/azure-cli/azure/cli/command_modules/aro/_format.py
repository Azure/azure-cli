# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections

from azure.mgmt.core.tools import parse_resource_id


def aro_list_table_format(results):
    return [aro_show_table_format(r) for r in results]


def aro_show_table_format(result):
    parts = parse_resource_id(result['id'])

    worker_profiles = result['workerProfiles'] or []

    return collections.OrderedDict(
        Name=result['name'],
        ResourceGroup=parts['resource_group'],
        Location=result['location'],
        ProvisioningState=result['provisioningState'],
        WorkerCount=sum(wp['count'] or 0 for wp in worker_profiles),
        URL=result['consoleProfile']['url'],
    )


def aro_version_table_format(result):
    return [aro_build_version_table(r) for r in result]


def aro_build_version_table(result):
    return collections.OrderedDict(
        Version=result
    )
