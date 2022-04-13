# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import logging
import os
from azure.synapse.artifacts.models import (LinkedService, Dataset, PipelineResource, RunFilterParameters,
                                            Trigger, DataFlow, BigDataPoolReference, NotebookSessionProperties,
                                            NotebookResource, SparkJobDefinition, SqlScriptResource, SqlScriptFolder,
                                            SqlScriptContent, SqlScriptMetadata, SqlScript, SqlConnection,
                                            NotebookFolder,LinkConnectionResource,LinkTableRequest,QueryTableStatusRequest,
                                            SecureString)
from azure.cli.core.util import sdk_no_wait, CLIError
from azure.core.exceptions import ResourceNotFoundError
from .._client_factory import (cf_synapse_linked_service, cf_synapse_dataset, cf_synapse_pipeline,
                               cf_synapse_pipeline_run, cf_synapse_trigger, cf_synapse_trigger_run,
                               cf_synapse_data_flow, cf_synapse_notebook, cf_synapse_spark_pool,
                               cf_synapse_spark_job_definition, cf_synapse_library, cf_synapse_sql_script,
                               cf_synapse_link_connection)
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


def cancel_trigger(cmd, workspace_name, trigger_name, run_id):
    client = cf_synapse_trigger_run(cmd.cli_ctx, workspace_name)
    return client.cancel_trigger_instance(trigger_name, run_id)


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
                              folder_path=None, executor_size="Small", executor_count=2, no_wait=False):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    spark_pool_client = cf_synapse_spark_pool(cmd.cli_ctx, workspace_name)
    if spark_pool_name is not None:
        endpoint = '{}{}{}'.format("https://", workspace_name, cmd.cli_ctx.cloud.suffixes.synapse_analytics_endpoint)
        spark_pool_info = spark_pool_client.get(spark_pool_name)
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
    definition_file['folder'] = NotebookFolder(name=folder_path)
    properties = NotebookResource(name=notebook_name, properties=definition_file)
    return sdk_no_wait(no_wait, client.begin_create_or_update_notebook,
                       notebook_name, properties, polling=True)


def list_notebooks(cmd, workspace_name):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    return client.get_notebooks_by_workspace()


def get_notebook(cmd, workspace_name, notebook_name):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    return client.get_notebook(notebook_name)


def export_notebook(cmd, workspace_name, output_folder, notebook_name=None):
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


def metadata_processing(notebook_properties, displayedWidgets):
    synapseWidgetNotebookMetadataVersion = '0.1'
    metadata = {}
    notebook_properties_metadata = {}
    for key in list(notebook_properties.keys()):
        if key == 'metadata':
            notebook_properties_metadata = notebook_properties['metadata']

    if notebook_properties_metadata is None:
        return metadata, displayedWidgets

    for elementkey in list(notebook_properties_metadata.keys()):
        if elementkey == 'language_info':
            if notebook_properties_metadata['language_info'] and \
                    'codemirror_mode' in notebook_properties_metadata['language_info']:
                notebook_properties_metadata['language_info'].pop('codemirror_mode')
            metadata['language_info'] = notebook_properties_metadata['language_info']
        elif elementkey == 'description':
            metadata['description'] = notebook_properties_metadata['description']
        elif elementkey == 'saveOutput':
            metadata['save_output'] = notebook_properties_metadata['saveOutput']
        elif elementkey == 'kernelspec':
            metadata['kernelspec'] = notebook_properties_metadata['kernelspec']
        elif elementkey == 'synapse_widget' and \
                'state' in notebook_properties_metadata['synapse_widget']:
            for ekey in list(notebook_properties_metadata['synapse_widget']['state'].keys()):
                for i in reversed(range(len(displayedWidgets))):
                    if displayedWidgets[i]['widget_id'] == ekey:
                        displayedWidgets.pop(i)
            metadata['synapse_widget'] = notebook_properties_metadata['synapse_widget']
            metadata['synapse_widget']['version'] = synapseWidgetNotebookMetadataVersion
    return metadata, displayedWidgets


def write_to_file(notebook, path):
    try:
        notebook_properties = notebook.properties.as_dict()
        livyStatementMetaOutputContentType = 'application/vnd.livy.statement-meta+json'
        synapseWidgetViewOutputContentType = 'application/vnd.synapse.widget-view+json'
        notebook_result = {}
        displayedWidgets = []
        notebook_result['nbformat'] = 4
        notebook_result['nbformat_minor'] = 2
        for cell in notebook_properties['cells']:
            if cell['cell_type'] == 'code' and cell['outputs']:
                for output in cell['outputs']:
                    if output['output_type'] == 'display_data' and \
                            synapseWidgetViewOutputContentType in output['data']:
                        displayedWidgets.append(output["data"]["application/vnd.synapse.widget-view+json"])

        metadata_results, displayedWidgets_results = \
            metadata_processing(notebook_properties, displayedWidgets)

        if len(displayedWidgets_results) > 0:
            logging.info('Detected widget with missing data.')

        for cell in notebook_properties['cells']:
            if cell['cell_type'] == 'code' and cell['outputs']:
                for output in cell['outputs']:
                    if output['output_type'] == 'display_data' and output['data'] and \
                            livyStatementMetaOutputContentType in output['data']:
                        output['data'].pop(livyStatementMetaOutputContentType)

        notebook_result['metadata'] = metadata_results
        notebook_result['cells'] = notebook_properties['cells']
        with open(path, 'w') as f:
            json.dump(notebook_result, f, indent=4)
    except IOError:
        raise CLIError('Unable to export to file: {}'.format(path))


def delete_notebook(cmd, workspace_name, notebook_name, no_wait=False):
    client = cf_synapse_notebook(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_notebook, notebook_name, polling=True)


# Workspace package
def list_workspace_package(cmd, workspace_name):
    client = cf_synapse_library(cmd.cli_ctx, workspace_name)
    return client.list()


def get_workspace_package(cmd, workspace_name, package_name):
    client = cf_synapse_library(cmd.cli_ctx, workspace_name)
    return client.get(package_name)


def upload_workspace_package(cmd, workspace_name, package, progress_callback=None):
    client = cf_synapse_library(cmd.cli_ctx, workspace_name)
    package_name = os.path.basename(package)

    # Check if the package already exists
    if test_workspace_package(client, package_name):
        raise CLIError("A workspace package with name '{0}' already exists.".format(
                       package_name))

    # Create package
    client.begin_create(package_name).result()
    # Upload package content
    package_size = os.path.getsize(package)
    chunk_size = 4 * 1024 * 1024
    if progress_callback is not None:
        progress_callback(0, package_size)
    with open(package, 'rb') as stream:
        index = 0
        while True:
            read_size = min(chunk_size, package_size - index)
            data = stream.read(read_size)

            if data == b'':
                break

            client.append(package_name, data)
            index += len(data)
            if progress_callback is not None:
                progress_callback(index, package_size)
    # Call Flush API as a completion signal
    client.begin_flush(package_name).result()

    return client.get(package_name)


def workspace_package_upload_batch(cmd, workspace_name, source, progress_callback=None):
    # Tell progress reporter to reuse the same hook
    if progress_callback:
        progress_callback.reuse = True

    source_files = []
    results = []
    for root, _, files in os.walk(source):
        for f in files:
            full_path = os.path.join(root, f)
            source_files.append(full_path)

    for index, source_file in enumerate(source_files):
        # add package name and number to progress message
        if progress_callback:
            progress_callback.message = '{}/{}: "{}"'.format(
                index + 1, len(source_files), os.path.basename(source_file))

        results.append(upload_workspace_package(cmd, workspace_name, source_file, progress_callback))

    # end progress hook
    if progress_callback:
        progress_callback.hook.end()

    return results


def test_workspace_package(client, package_name):
    try:
        client.get(package_name)
        return True
    except ResourceNotFoundError:
        return False


def delete_workspace_package(cmd, workspace_name, package_name, no_wait=False):
    client = cf_synapse_library(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete, package_name)


# Spark job definition
def list_spark_job_definition(cmd, workspace_name):
    client = cf_synapse_spark_job_definition(cmd.cli_ctx, workspace_name)
    return client.get_spark_job_definitions_by_workspace()


def get_spark_job_definition(cmd, workspace_name, spark_job_definition_name):
    client = cf_synapse_spark_job_definition(cmd.cli_ctx, workspace_name)
    return client.get_spark_job_definition(spark_job_definition_name)


def delete_spark_job_definition(cmd, workspace_name, spark_job_definition_name, no_wait=False):
    client = cf_synapse_spark_job_definition(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_spark_job_definition, spark_job_definition_name, polling=True)


def create_or_update_spark_job_definition(cmd, workspace_name, spark_job_definition_name, definition_file,
                                          folder_path=None, no_wait=False):
    client = cf_synapse_spark_job_definition(cmd.cli_ctx, workspace_name)
    folder = {}
    folder['name'] = folder_path
    definition_file['folder'] = folder
    properties = SparkJobDefinition.from_dict(definition_file)
    return sdk_no_wait(no_wait, client.begin_create_or_update_spark_job_definition,
                       spark_job_definition_name, properties, polling=True)


def list_sql_scripts(cmd, workspace_name):
    client = cf_synapse_sql_script(cmd.cli_ctx, workspace_name)
    return client.get_sql_scripts_by_workspace()


def get_sql_script(cmd, workspace_name, sql_script_name):
    client = cf_synapse_sql_script(cmd.cli_ctx, workspace_name)
    return client.get_sql_script(sql_script_name)


def delete_sql_script(cmd, workspace_name, sql_script_name, no_wait=False):
    client = cf_synapse_sql_script(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_sql_script, sql_script_name, polling=True)


def create_sql_script(cmd, workspace_name, sql_script_name, definition_file, result_limit=5000,
                      folder_name=None, description=None, sql_pool_name=None,
                      sql_database_name=None, additional_properties=None, no_wait=False):
    client = cf_synapse_sql_script(cmd.cli_ctx, workspace_name)
    try:
        with open(definition_file, 'r') as stream:
            query = stream.read()
    except:
        from azure.cli.core.azclierror import InvalidArgumentValueError
        err_msg = 'Definition file path is invalid'
        raise InvalidArgumentValueError(err_msg)
    if sql_pool_name:
        if sql_pool_name.lower() == 'built-in':
            sql_pool_type = 'SqlOnDemand'
            current_connection = SqlConnection(type=sql_pool_type,
                                               pool_name='Built-in',
                                               database_name=sql_database_name)
        else:
            sql_pool_type = 'SqlPool'
            current_connection = SqlConnection(type=sql_pool_type,
                                               pool_name=sql_pool_name,
                                               database_name=sql_database_name)
    else:
        current_connection = SqlConnection(type='SqlOnDemand',
                                           pool_name='Built-in',
                                           database_name='master')

    sql_script_content = SqlScriptContent(query=query,
                                          current_connection=current_connection,
                                          result_limit=result_limit,
                                          metadata=SqlScriptMetadata(language='sql'))
    sql_script_folder = SqlScriptFolder(name=folder_name)
    properties = SqlScript(additional_properties=additional_properties,
                           description=description,
                           type='SqlQuery',
                           content=sql_script_content,
                           folder=sql_script_folder)
    sql_script = SqlScriptResource(name=sql_script_name, properties=properties)
    return sdk_no_wait(no_wait, client.begin_create_or_update_sql_script,
                       sql_script_name, sql_script, polling=True)


def export_sql_script(cmd, workspace_name, output_folder, sql_script_name=None):
    client = cf_synapse_sql_script(cmd.cli_ctx, workspace_name)
    if sql_script_name is not None:
        sql_script_query = client.get_sql_script(sql_script_name).properties.content.query
        path = os.path.join(output_folder, sql_script_name + '.sql')
        try:
            with open(path, 'w') as f:
                f.write(sql_script_query)
            print(sql_script_name + 'export success')
        except:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            err_msg = 'Unable to export to file: {}'.format(path)
            raise InvalidArgumentValueError(err_msg)
    else:
        sql_scripts = client.get_sql_scripts_by_workspace()
        for sql_script in sql_scripts:
            sql_script_query = client.get_sql_script(sql_script.name).properties.content.query
            path = os.path.join(output_folder, sql_script.name + '.sql')
            try:
                with open(path, 'w') as f:
                    f.write(sql_script_query)
                print(sql_script.name + 'export success')
            except:
                from azure.cli.core.azclierror import InvalidArgumentValueError
                err_msg = 'Unable to export to file: {}'.format(path)
                raise InvalidArgumentValueError(err_msg)


def list_link_connection(cmd, workspace_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.get_link_connections_by_workspace()


def get_link_connection(cmd, workspace_name, link_connection_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.get_link_connection(link_connection_name)


def create_or_update_link_connection(cmd, workspace_name, link_connection_name, definition_file):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    properties = LinkConnectionResource.from_dict(definition_file['properties'])
    return client.create_or_update_link_connection(link_connection_name, properties)


def delete_link_connection(cmd, workspace_name, link_connection_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.delete_link_connection(link_connection_name)


def get_link_connection_status(cmd, workspace_name, link_connection_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.get_detailed_status(link_connection_name)


def start_link_connection(cmd, workspace_name, link_connection_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.start(link_connection_name)


def stop_link_connection(cmd, workspace_name, link_connection_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.stop(link_connection_name)


def synapse_list_link_table(cmd, workspace_name, link_connection_name):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    return client.list_link_tables(link_connection_name).value


def synapse_edit_link_table(cmd, workspace_name, link_connection_name, definition_file):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    linkTableRequset_list = []
    for i in range(0, len(definition_file['linkTables'])):
        linkTableRequset = LinkTableRequest.from_dict(definition_file['linkTables'][i])
        linkTableRequset_list.append(linkTableRequset)
    return client.edit_tables(link_connection_name, linkTableRequset_list)


def synapse_get_link_tables_status(cmd, workspace_name, link_connection_name, max_segment_count=50, continuation_token=None):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    query_table_status_request = QueryTableStatusRequest(
        max_segment_count=max_segment_count,
        continuation_token=continuation_token
    )
    return client.query_table_status(link_connection_name, query_table_status_request)


def synapse_update_landing_zone_credential(cmd, workspace_name, link_connection_name, sas_token_type, sas_token_value):
    client = cf_synapse_link_connection(cmd.cli_ctx, workspace_name)
    sas_token = SecureString(
        value = sas_token_value
    )
    return client.update_landing_zone_credential(link_connection_name, sas_token)