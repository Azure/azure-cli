# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _deploymentmanager_client_factory(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.deploymentmanager import DeploymentManagerClient
    return get_mgmt_service_client(cli_ctx, DeploymentManagerClient)


def cf_artifact_sources(cli_ctx, *_):
    return _deploymentmanager_client_factory(cli_ctx).artifact_sources


def cf_service_topologies(cli_ctx, *_):
    return _deploymentmanager_client_factory(cli_ctx).service_topologies


def cf_services(cli_ctx, *_):
    return _deploymentmanager_client_factory(cli_ctx).services


def cf_service_units(cli_ctx, *_):
    return _deploymentmanager_client_factory(cli_ctx).service_units


def cf_steps(cli_ctx, *_):
    return _deploymentmanager_client_factory(cli_ctx).steps


def cf_rollouts(cli_ctx, *_):
    return _deploymentmanager_client_factory(cli_ctx).rollouts
