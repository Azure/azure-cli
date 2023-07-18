# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import (IntegrationRuntimeResource,
                                       IntegrationRuntimeRegenerateKeyParameters, UpdateIntegrationRuntimeRequest)


def create(cmd, client, resource_group_name, workspace_name, integration_runtime_name, integration_runtime_type,
           description=None, if_match=None, location='AutoResolve', compute_type='General',
           core_count=8, time_to_live=0, no_wait=False):
    property_files = {}
    property_files['type'] = integration_runtime_type
    property_files['description'] = description
    if integration_runtime_type == 'Managed':
        property_files['typeProperties'] = {}
        property_files['typeProperties']['computeProperties'] = {}
        property_files['typeProperties']['computeProperties']['location'] = location
        property_files['typeProperties']['computeProperties']['dataFlowProperties'] = {}
        property_files['typeProperties']['computeProperties']['dataFlowProperties']['computeType'] = compute_type
        property_files['typeProperties']['computeProperties']['dataFlowProperties']['coreCount'] = core_count
        property_files['typeProperties']['computeProperties']['dataFlowProperties']['timeToLive'] = time_to_live
    properties = IntegrationRuntimeResource(type=integration_runtime_type, properties=property_files)
    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, workspace_name,
                       integration_runtime_name, properties, if_match)


def Managed_Create(cmd, client, resource_group_name, workspace_name, integration_runtime_name,
                   description=None, if_match=None, location='AutoResolve', compute_type='General',
                   core_count=8, time_to_live=0, no_wait=False):
    property_files = {}
    property_files['type'] = 'Managed'
    property_files['description'] = description
    property_files['typeProperties'] = {}
    property_files['typeProperties']['computeProperties'] = {}
    property_files['typeProperties']['computeProperties']['location'] = location
    property_files['typeProperties']['computeProperties']['dataFlowProperties'] = {}
    property_files['typeProperties']['computeProperties']['dataFlowProperties']['computeType'] = compute_type
    property_files['typeProperties']['computeProperties']['dataFlowProperties']['coreCount'] = core_count
    property_files['typeProperties']['computeProperties']['dataFlowProperties']['timeToLive'] = time_to_live
    properties = IntegrationRuntimeResource(type='Managed', properties=property_files)
    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, workspace_name,
                       integration_runtime_name, properties, if_match)


def Selfhosted_Create(cmd, client, resource_group_name, workspace_name, integration_runtime_name,
                      description=None, if_match=None, no_wait=False):
    property_files = {}
    property_files['type'] = 'SelfHosted'
    property_files['description'] = description
    properties = IntegrationRuntimeResource(type='SelfHosted', properties=property_files)
    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, workspace_name,
                       integration_runtime_name, properties, if_match)


def regenerate(cmd, client, resource_group_name, workspace_name, integration_runtime_name, key_name="default",
               no_wait=False):
    regenerate_key_parameters = IntegrationRuntimeRegenerateKeyParameters(key_name=key_name)
    return sdk_no_wait(no_wait, client.regenerate, resource_group_name, workspace_name, integration_runtime_name,
                       regenerate_key_parameters)


def update(cmd, client, resource_group_name, workspace_name, integration_runtime_name, auto_update,
           update_delay_offset, no_wait=False):
    update_integration_runtime_request = UpdateIntegrationRuntimeRequest(
        auto_update=auto_update,
        update_delay_offset=update_delay_offset
    )
    return sdk_no_wait(no_wait, client.update, resource_group_name, workspace_name, integration_runtime_name,
                       update_integration_runtime_request)
