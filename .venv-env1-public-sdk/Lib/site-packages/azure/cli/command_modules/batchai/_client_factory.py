# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def batchai_client_factory(cli_ctx, _=None):
    from azure.mgmt.batchai import BatchAI as BatchAIManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, BatchAIManagementClient)


def workspace_client_factory(cli_ctx, _):
    return batchai_client_factory(cli_ctx).workspaces


def cluster_client_factory(cli_ctx, _):
    return batchai_client_factory(cli_ctx).clusters


def experiment_client_factory(cli_ctx, _):
    return batchai_client_factory(cli_ctx).experiments


def job_client_factory(cli_ctx, _):
    return batchai_client_factory(cli_ctx).jobs


def file_server_client_factory(cli_ctx, _):
    return batchai_client_factory(cli_ctx).file_servers


def usage_client_factory(cli_ctx, _):
    return batchai_client_factory(cli_ctx).usages
