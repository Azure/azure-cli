# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from azure.cli.core.util import empty_on_404

from ._client_factory import servicefabric_fabric_client_factory

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    custom_path = 'azure.cli.command_modules.servicefabric.custom#{}'
    mgmt_path = 'azure.mgmt.servicefabric.operations.clusters_operations#{}'

    factory = servicefabric_fabric_client_factory

    cli_command(__name__, 'sf cluster show', mgmt_path.format('ClustersOperations.get'), factory, exception_handler=empty_on_404)

    cli_command(__name__, 'sf cluster list',
                custom_path.format('list_cluster'), factory)

    cli_command(__name__, 'sf cluster create',
                custom_path.format('new_cluster'), factory)

    cli_command(__name__, 'sf cluster certificate add',
                custom_path.format('add_cluster_cert'), factory)

    cli_command(__name__, 'sf cluster certificate remove', custom_path.format('remove_cluster_cert'), factory)

    cli_command(__name__, 'sf cluster client-certificate add',
                custom_path.format('add_client_cert'), factory)

    cli_command(__name__, 'sf cluster client-certificate remove',
                custom_path.format('remove_client_cert'), factory)

    cli_command(__name__, 'sf cluster setting set',
                custom_path.format('set_cluster_setting'), factory)

    cli_command(__name__, 'sf cluster setting remove',
                custom_path.format('remove_cluster_setting'), factory)

    cli_command(__name__, 'sf cluster reliability update',
                custom_path.format('update_cluster_reliability_level'), factory)

    cli_command(__name__, 'sf cluster durability update',
                custom_path.format('update_cluster_durability'), factory)

    cli_command(__name__, 'sf cluster node-type add',
                custom_path.format('add_cluster_node_type'), factory)

    cli_command(__name__, 'sf cluster node add',
                custom_path.format('add_cluster_node'), factory)

    cli_command(__name__, 'sf cluster node remove', custom_path.format('remove_cluster_node'), factory)

    cli_command(__name__, 'sf cluster upgrade-type set',
                custom_path.format('update_cluster_upgrade_type'), factory)

    cli_command(__name__, 'sf application certificate add',
                custom_path.format('add_app_cert'), factory)
