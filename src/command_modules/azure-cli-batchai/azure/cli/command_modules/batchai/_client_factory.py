# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def batchai_client_factory(_=None):
    from azure.mgmt.batchai import BatchAIManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(BatchAIManagementClient)


def cluster_client_factory(_):
    return batchai_client_factory().clusters


def job_client_factory(_):
    return batchai_client_factory().jobs


def file_client_factory(_):
    return batchai_client_factory().jobs


def file_server_client_factory(_):
    return batchai_client_factory().file_servers
