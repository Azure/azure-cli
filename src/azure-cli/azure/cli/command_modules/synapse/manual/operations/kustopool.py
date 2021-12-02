# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import sdk_no_wait
from .._client_factory import cf_synapse_client_workspace_factory


# Synapse kustopool
def synapse_kusto_pool_create(cmd,
                              client,
                              workspace_name,
                              resource_group_name,
                              kusto_pool_name,
                              location,
                              sku,
                              if_match=None,
                              if_none_match=None,
                              tags=None,
                              optimized_autoscale=None,
                              enable_streaming_ingest=None,
                              enable_purge=None,
                              workspace_uid=None,
                              no_wait=False):
    parameters = {}
    if tags is not None:
        parameters['tags'] = tags
    parameters['location'] = location
    parameters['sku'] = sku
    if optimized_autoscale is not None:
        parameters['optimized_autoscale'] = optimized_autoscale
    if enable_streaming_ingest is not None:
        parameters['enable_streaming_ingest'] = enable_streaming_ingest
    else:
        parameters['enable_streaming_ingest'] = False
    if enable_purge is not None:
        parameters['enable_purge'] = enable_purge
    else:
        parameters['enable_purge'] = False
    if workspace_uid is not None:
        parameters['workspace_uid'] = workspace_uid
    else:
        workspace_client = cf_synapse_client_workspace_factory(cmd.cli_ctx)
        workspace_object = workspace_client.get(resource_group_name, workspace_name)
        parameters['workspace_uid'] = workspace_object.workspace_uid
    return sdk_no_wait(no_wait,
                       client.begin_create_or_update,
                       workspace_name=workspace_name,
                       resource_group_name=resource_group_name,
                       kusto_pool_name=kusto_pool_name,
                       if_match=if_match,
                       if_none_match=if_none_match,
                       parameters=parameters)


def synapse_kusto_pool_update(cmd,
                              client,
                              workspace_name,
                              resource_group_name,
                              kusto_pool_name,
                              if_match=None,
                              tags=None,
                              sku=None,
                              optimized_autoscale=None,
                              enable_streaming_ingest=None,
                              enable_purge=None,
                              workspace_uid=None,
                              no_wait=False):
    parameters = {}
    if tags is not None:
        parameters['tags'] = tags
    if sku is not None:
        parameters['sku'] = sku
    if optimized_autoscale is not None:
        parameters['optimized_autoscale'] = optimized_autoscale
    if enable_streaming_ingest is not None:
        parameters['enable_streaming_ingest'] = enable_streaming_ingest
    else:
        parameters['enable_streaming_ingest'] = False
    if enable_purge is not None:
        parameters['enable_purge'] = enable_purge
    else:
        parameters['enable_purge'] = False
    if workspace_uid is not None:
        parameters['workspace_uid'] = workspace_uid
    else:
        workspace_client = cf_synapse_client_workspace_factory(cmd.cli_ctx)
        workspace_object = workspace_client.get(resource_group_name, workspace_name)
        parameters['workspace_uid'] = workspace_object.workspace_uid
    return sdk_no_wait(no_wait,
                       client.begin_update,
                       workspace_name=workspace_name,
                       resource_group_name=resource_group_name,
                       kusto_pool_name=kusto_pool_name,
                       if_match=if_match,
                       parameters=parameters)


def synapse_kusto_pool_remove_language_extension(client,
                                                 workspace_name,
                                                 kusto_pool_name,
                                                 resource_group_name,
                                                 value=None,
                                                 no_wait=False):
    language_extensions_to_remove = {}
    language_extensions_to_remove['value'] = value
    return sdk_no_wait(no_wait,
                       client.begin_remove_language_extensions,
                       workspace_name=workspace_name,
                       kusto_pool_name=kusto_pool_name,
                       resource_group_name=resource_group_name,
                       language_extensions_to_remove=language_extensions_to_remove)


def synapse_kusto_pool_add_language_extension(client,
                                              workspace_name,
                                              kusto_pool_name,
                                              resource_group_name,
                                              value=None,
                                              no_wait=False):
    language_extensions_to_add = {}
    language_extensions_to_add['value'] = value
    return sdk_no_wait(no_wait,
                       client.begin_add_language_extensions,
                       workspace_name=workspace_name,
                       kusto_pool_name=kusto_pool_name,
                       resource_group_name=resource_group_name,
                       language_extensions_to_add=language_extensions_to_add)


def synapse_kusto_pool_detach_follower_database(client,
                                                workspace_name,
                                                kusto_pool_name,
                                                resource_group_name,
                                                kusto_pool_resource_id,
                                                attached_database_configuration_name,
                                                no_wait=False):

    from azure.mgmt.synapse.models import FollowerDatabaseDefinition
    follower_database_to_remove = \
        FollowerDatabaseDefinition(kusto_pool_resource_id=kusto_pool_resource_id,
                                   attached_database_configuration_name=attached_database_configuration_name)
    return sdk_no_wait(no_wait,
                       client.begin_detach_follower_databases,
                       workspace_name=workspace_name,
                       kusto_pool_name=kusto_pool_name,
                       resource_group_name=resource_group_name,
                       follower_database_to_remove=follower_database_to_remove)
