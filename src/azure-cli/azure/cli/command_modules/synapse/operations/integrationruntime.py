# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import IntegrationRuntime


def create(cmd, client, resource_group_name, workspace_name, integration_runtime_name, integration_runtime_type,
           description=None, if_match=None, location='AutoResolve', compute_type='General',
           core_count=8, time_to_live=0, no_wait=False):
    properties = {}
    properties['type'] = integration_runtime_type
    properties['description'] = description
    if integration_runtime_type == 'Managed':
        properties['typeProperties'] = {}
        properties['typeProperties']['computeProperties'] = {}
        properties['typeProperties']['computeProperties']['location'] = location
        properties['typeProperties']['computeProperties']['dataFlowProperties'] = {}
        properties['typeProperties']['computeProperties']['dataFlowProperties']['computeType'] = compute_type
        properties['typeProperties']['computeProperties']['dataFlowProperties']['coreCount'] = core_count
        properties['typeProperties']['computeProperties']['dataFlowProperties']['timeToLive'] = time_to_live
    properties = IntegrationRuntime.from_dict(properties)
    return sdk_no_wait(no_wait, client.create, resource_group_name, workspace_name,
                       integration_runtime_name, properties, if_match)
