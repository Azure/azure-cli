# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from azure.synapse.artifacts.models import (LinkedService, Dataset, PipelineResource, RunFilterParameters,
                                            Trigger, DataFlow, BigDataPoolReference, NotebookSessionProperties,
                                            Notebook)
from azure.cli.core.util import sdk_no_wait, CLIError
from .sparkpool import get_spark_pool
from .workspace import get_resource_group_by_workspace_name
from .._client_factory import (cf_synapse_linked_service, cf_synapse_dataset, cf_synapse_pipeline,
                               cf_synapse_pipeline_run, cf_synapse_trigger, cf_synapse_trigger_run,
                               cf_synapse_data_flow, cf_synapse_notebook, cf_synapse_client_bigdatapool_factory,
                               cf_synapse_client_workspace_factory)
from ..constant import EXECUTOR_SIZE, SPARK_SERVICE_ENDPOINT_API_VERSION


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


# Trigger
def list_triggers(cmd, workspace_name):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return client.get_triggers_by_workspace()


def get_trigger(cmd, workspace_name, trigger_name):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return client.get_trigger(trigger_name)


def create_or_update_trigger(cmd, workspace_name, trigger_name, definition_file, no_wait=False):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    properties = Trigger.from_dict(definition_file['properties'])
    return sdk_no_wait(no_wait, client.begin_create_or_update_trigger,
                       trigger_name, properties, polling=True)


def delete_trigger(cmd, workspace_name, trigger_name, no_wait=False):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_trigger, trigger_name, polling=True)


def subscribe_trigger_to_events(cmd, workspace_name, trigger_name, no_wait=False):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_subscribe_trigger_to_events, trigger_name, polling=True)


def get_event_subscription_status(cmd, workspace_name, trigger_name):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return client.get_event_subscription_status(trigger_name)


def unsubscribe_trigger_from_events(cmd, workspace_name, trigger_name, no_wait=False):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_unsubscribe_trigger_from_events, trigger_name, polling=True)


def start_trigger(cmd, workspace_name, trigger_name, no_wait=False):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_start_trigger, trigger_name, polling=True)


def stop_trigger(cmd, workspace_name, trigger_name, no_wait=False):
    client = cf_synapse_trigger(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_stop_trigger, trigger_name, polling=True)


# Trigger run
def rerun_trigger(cmd, workspace_name, trigger_name, run_id):
    client = cf_synapse_trigger_run(cmd.cli_ctx, workspace_name)
    return client.rerun_trigger_instance(trigger_name, run_id)


def query_trigger_runs_by_workspace(cmd, workspace_name, last_updated_after, last_updated_before,
                                    continuation_token=None, filters=None, order_by=None):
    client = cf_synapse_trigger_run(cmd.cli_ctx, workspace_name)
    return client.query_trigger_runs_by_workspace(RunFilterParameters(last_updated_after=last_updated_after,
                                                                      last_updated_before=last_updated_before,
                                                                      continuation_token=continuation_token,
                                                                      filters=filters, order_by=order_by))


# Data flow
def list_data_flows(cmd, workspace_name):
    client = cf_synapse_data_flow(cmd.cli_ctx, workspace_name)
    return client.get_data_flows_by_workspace()


def get_data_flow(cmd, workspace_name, data_flow_name):
    client = cf_synapse_data_flow(cmd.cli_ctx, workspace_name)
    return client.get_data_flow(data_flow_name)


def create_or_update_data_flow(cmd, workspace_name, data_flow_name, definition_file, no_wait=False):
    client = cf_synapse_data_flow(cmd.cli_ctx, workspace_name)
    properties = DataFlow.from_dict(definition_file['properties'])
    return sdk_no_wait(no_wait, client.begin_create_or_update_data_flow,
                       data_flow_name, properties, polling=True)


def delete_data_flow(cmd, workspace_name, data_flow_name, no_wait=False):
    client = cf_synapse_data_flow(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_data_flow, data_flow_name, polling=True)


# Notebook
def create_or_update_notebook(cmd, workspace_name, definition_file, notebook_name, spark_pool_name=None,
                              executor_size="Small", executor_count=2, no_wait=False):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    if spark_pool_name is not None:
        endpoint = '{}{}{}'.format("https://", workspace_name, cmd.cli_ctx.cloud.suffixes.synapse_analytics_endpoint)
        resource_group_name = get_resource_group_by_workspace_name(cmd,
                                                                   cf_synapse_client_workspace_factory(cmd.cli_ctx),
                                                                   workspace_name)
        spark_pool_info = get_spark_pool(cmd, cf_synapse_client_bigdatapool_factory(cmd.cli_ctx), resource_group_name,
                                         workspace_name, spark_pool_name)
        metadata = definition_file['metadata']
        options = {}
        options['auth'] = {'type': 'AAD',
                           'authResource': '{}{}'.format("https://",
                                                         cmd.cli_ctx.cloud.suffixes.synapse_analytics_endpoint[1:])}
        options['cores'] = EXECUTOR_SIZE[executor_size]['Cores']
        options['memory'] = EXECUTOR_SIZE[executor_size]['Memory']
        options['nodeCount'] = executor_count
        options['endpoint'] = '{}{}{}{}{}'.format(endpoint, '/livyApi/versions/', SPARK_SERVICE_ENDPOINT_API_VERSION,
                                                  '/sparkPools/', spark_pool_name)
        options['extraHeader'] = {}
        options['id'] = spark_pool_info.id
        options['name'] = spark_pool_name
        options['sparkVersion'] = spark_pool_info.spark_version
        options['type'] = 'Spark'
        metadata['a365ComputeOptions'] = options

        definition_file['bigDataPool'] = BigDataPoolReference(type='BigDataPoolReference',
                                                              reference_name=spark_pool_name)
        definition_file['sessionProperties'] = NotebookSessionProperties(driver_memory=options['memory'],
                                                                         driver_cores=options['cores'],
                                                                         executor_memory=options['memory'],
                                                                         executor_cores=options['cores'],
                                                                         num_executors=executor_count)
    properties = Notebook.from_dict(definition_file)
    return sdk_no_wait(no_wait, client.begin_create_or_update_notebook,
                       notebook_name, properties, polling=True)


def list_notebooks(cmd, workspace_name):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    return client.get_notebooks_by_workspace()


def get_notebook(cmd, workspace_name, notebook_name):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    return client.get_notebook(notebook_name)


def export_notebook(cmd, workspace_name, output_folder, notebook_name=None):
    def write_to_file(notebook, path):
        try:
            with open(path, 'w') as f:
                json.dump(notebook.properties.as_dict(), f, indent=4)
        except IOError:
            raise CLIError('Unable to export to file: {}'.format(path))

    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    if notebook_name is not None:
        notebook = client.get_notebook(notebook_name)
        path = os.path.join(output_folder, notebook.name + '.ipynb')
        print(notebook.properties.as_dict())
        write_to_file(notebook, path)
    else:
        notebooks = client.get_notebooks_by_workspace()
        for notebook in notebooks:
            path = os.path.join(output_folder, notebook.name + '.ipynb')
            print(notebook.properties.as_dict())
            write_to_file(notebook, path)


def delete_notebook(cmd, workspace_name, notebook_name, no_wait=False):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_notebook, notebook_name, polling=True)
