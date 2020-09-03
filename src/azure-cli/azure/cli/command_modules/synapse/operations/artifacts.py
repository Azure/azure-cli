# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.synapse.artifacts.models import LinkedService, Dataset, PipelineResource, RunFilterParameters
from azure.cli.core.util import sdk_no_wait
from .._client_factory import (cf_synapse_linked_service, cf_synapse_dataset, cf_synapse_pipeline,
                               cf_synapse_pipeline_run)


# Linked Service
def list_linked_service(cmd, workspace_name):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    return client.get_linked_services_by_workspace()


def get_linked_service(cmd, workspace_name, linked_service_name):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    return client.get_linked_service(linked_service_name)


def create_or_update_linked_service(cmd, workspace_name, linked_service_name, definition_file, no_wait=False):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    properties = LinkedService.from_dict(definition_file['properties'])
    return sdk_no_wait(no_wait, client.begin_create_or_update_linked_service,
                       linked_service_name, properties, polling=True)


def delete_linked_service(cmd, workspace_name, linked_service_name, no_wait=False):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_linked_service, linked_service_name, polling=True)


# Dataset
def list_datasets(cmd, workspace_name):
    client = cf_synapse_dataset(cmd.cli_ctx, workspace_name)
    return client.get_datasets_by_workspace()


def get_dataset(cmd, workspace_name, dataset_name):
    client = cf_synapse_dataset(cmd.cli_ctx, workspace_name)
    return client.get_dataset(dataset_name)


def create_or_update_dataset(cmd, workspace_name, dataset_name, definition_file, no_wait=False):
    client = cf_synapse_dataset(cmd.cli_ctx, workspace_name)
    properties = Dataset.from_dict(definition_file['properties'])
    return sdk_no_wait(no_wait, client.begin_create_or_update_dataset,
                       dataset_name, properties, polling=True)


def delete_dataset(cmd, workspace_name, dataset_name, no_wait=False):
    client = cf_synapse_dataset(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_dataset, dataset_name, polling=True)


# Pipeline
def list_pipelines(cmd, workspace_name):
    client = cf_synapse_pipeline(cmd.cli_ctx, workspace_name)
    return client.get_pipelines_by_workspace()


def get_pipeline(cmd, workspace_name, pipeline_name):
    client = cf_synapse_pipeline(cmd.cli_ctx, workspace_name)
    return client.get_pipeline(pipeline_name)


def create_or_update_pipeline(cmd, workspace_name, pipeline_name, definition_file, no_wait=False):
    client = cf_synapse_pipeline(cmd.cli_ctx, workspace_name)
    properties = PipelineResource.from_dict(definition_file['properties'])
    return sdk_no_wait(no_wait, client.begin_create_or_update_pipeline,
                       pipeline_name, properties, polling=True)


def delete_pipeline(cmd, workspace_name, pipeline_name, no_wait=False):
    client = cf_synapse_pipeline(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_pipeline, pipeline_name, polling=True)


def create_pipeline_run(cmd, workspace_name, pipeline_name, reference_pipeline_run_id=None, is_recovery=None,
                        start_activity_name=None, parameters=None):
    client = cf_synapse_pipeline(cmd.cli_ctx, workspace_name)
    return client.create_pipeline_run(pipeline_name, reference_pipeline_run_id, is_recovery,
                                      start_activity_name, parameters)


# Pipline run
def query_pipeline_runs_by_workspace(cmd, workspace_name, last_updated_after, last_updated_before,
                                     continuation_token=None, filters=None, order_by=None):
    client = cf_synapse_pipeline_run(cmd.cli_ctx, workspace_name)
    return client.query_pipeline_runs_by_workspace(RunFilterParameters(last_updated_after=last_updated_after,
                                                                       last_updated_before=last_updated_before,
                                                                       continuation_token=continuation_token,
                                                                       filters=filters, order_by=order_by))


def get_pipeline_run(cmd, workspace_name, run_id):
    client = cf_synapse_pipeline_run(cmd.cli_ctx, workspace_name)
    return client.get_pipeline_run(run_id)


def query_activity_runs(cmd, workspace_name, pipeline_name, run_id, last_updated_after, last_updated_before,
                        continuation_token=None, filters=None, order_by=None):
    client = cf_synapse_pipeline_run(cmd.cli_ctx, workspace_name)
    return client.query_activity_runs(pipeline_name, run_id,
                                      RunFilterParameters(last_updated_after=last_updated_after,
                                                          last_updated_before=last_updated_before,
                                                          continuation_token=continuation_token,
                                                          filters=filters, order_by=order_by))


def cancel_pipeline_run(cmd, workspace_name, run_id, is_recursive=None):
    client = cf_synapse_pipeline_run(cmd.cli_ctx, workspace_name)
    return client.cancel_pipeline_run(run_id, is_recursive)
