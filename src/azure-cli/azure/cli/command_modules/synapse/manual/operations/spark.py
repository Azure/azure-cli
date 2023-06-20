# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from knack.util import CLIError
from azure.synapse.spark.models import SparkBatchJobOptions, SparkSessionOptions, SparkStatementOptions
from .._client_factory import cf_synapse_spark_batch, cf_synapse_spark_session
from ..util import categorized_files, check_udfs_folder
from ..constant import DOTNET_CLASS, DOTNET_FILE, SPARK_DOTNET_UDFS_FOLDER_NAME, EXECUTOR_SIZE, \
    SPARK_DOTNET_ASSEMBLY_SEARCH_PATHS_KEY, SparkBatchLanguage
from shlex import split


# Spark batch job
def get_spark_batch_job(cmd, job_id, workspace_name, spark_pool_name):
    client = cf_synapse_spark_batch(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.get_spark_batch_job(job_id, detailed=True)


def cancel_spark_batch_job(cmd, job_id, workspace_name, spark_pool_name):
    client = cf_synapse_spark_batch(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.cancel_spark_batch_job(job_id)


def list_spark_batch_jobs(cmd, workspace_name, spark_pool_name, from_index=None, size=None):
    client = cf_synapse_spark_batch(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.get_spark_batch_jobs(from_index, size, detailed=True)


def create_spark_batch_job(cmd, workspace_name, spark_pool_name, job_name, main_definition_file,
                           executor_size, executors, language=SparkBatchLanguage.Scala, main_class_name=None,
                           command_line_arguments=None,
                           reference_files=None, archives=None, configuration=None,
                           tags=None):
    # pylint: disable-msg=too-many-locals
    client = cf_synapse_spark_batch(cmd.cli_ctx, workspace_name, spark_pool_name)
    file = main_definition_file
    class_name = main_class_name
    final_command_line_arguments = []
    if main_class_name is None:
        if language == SparkBatchLanguage.SparkDotNet or language == SparkBatchLanguage.Spark:
            raise CLIError('Cannot perform the requested operation because main class name'
                           ' is not provided. Please specify --main-class-name for Spark job or '
                           ' .NET Spark job')
    if command_line_arguments:
        for item in command_line_arguments:
            final_command_line_arguments.append(' '.join(item))
        # e.g --arguments a b; command_line_arguments =[['a', 'b']]
        if len(command_line_arguments) == 1 and len(command_line_arguments[0]) != 1:
            final_command_line_arguments = split(final_command_line_arguments[0])
    arguments = final_command_line_arguments
    # dotnet spark
    if language.upper() == SparkBatchLanguage.SparkDotNet.upper() or language.upper() == SparkBatchLanguage.CSharp.upper():
        file = DOTNET_FILE
        class_name = DOTNET_CLASS

        arguments = [main_definition_file, main_class_name]
        if command_line_arguments:
            arguments = arguments + command_line_arguments

        archives = ["{}#{}".format(main_definition_file, SPARK_DOTNET_UDFS_FOLDER_NAME)] + archives if archives \
            else ["{}#{}".format(main_definition_file, SPARK_DOTNET_UDFS_FOLDER_NAME)]

        if not configuration:
            configuration = {SPARK_DOTNET_ASSEMBLY_SEARCH_PATHS_KEY: './{}'.format(SPARK_DOTNET_UDFS_FOLDER_NAME)}
        else:
            check_udfs_folder(configuration)

    files = None
    jars = None
    if reference_files:
        files, jars = categorized_files(reference_files)
    driver_cores = EXECUTOR_SIZE[executor_size]['Cores']
    driver_memory = EXECUTOR_SIZE[executor_size]['Memory']
    executor_cores = EXECUTOR_SIZE[executor_size]['Cores']
    executor_memory = EXECUTOR_SIZE[executor_size]['Memory']

    spark_batch_job_options = SparkBatchJobOptions(
        tags=tags,
        name=job_name,
        file=file,
        class_name=class_name,
        arguments=arguments,
        jars=jars,
        files=files,
        archives=archives,
        configuration=configuration,
        driver_memory=driver_memory,
        driver_cores=driver_cores,
        executor_memory=executor_memory,
        executor_cores=executor_cores,
        executor_count=executors)

    return client.create_spark_batch_job(spark_batch_job_options, detailed=True)


# Spark Session
def list_spark_session_jobs(cmd, workspace_name, spark_pool_name, from_index=None, size=None):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.get_spark_sessions(from_index, size, detailed=True)


def create_spark_session_job(cmd, workspace_name, spark_pool_name, job_name, executor_size, executors,
                             reference_files=None, configuration=None, tags=None):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    files = None
    jars = None
    if reference_files:
        files, jars = categorized_files(reference_files)
    driver_cores = EXECUTOR_SIZE[executor_size]['Cores']
    driver_memory = EXECUTOR_SIZE[executor_size]['Memory']
    executor_cores = EXECUTOR_SIZE[executor_size]['Cores']
    executor_memory = EXECUTOR_SIZE[executor_size]['Memory']

    spark_session_options = SparkSessionOptions(
        tags=tags,
        name=job_name,
        jars=jars,
        files=files,
        conf=configuration,
        driver_memory=driver_memory,
        driver_cores=driver_cores,
        executor_memory=executor_memory,
        executor_cores=executor_cores,
        executor_count=executors)

    return client.create_spark_session(spark_session_options, detailed=True)


def get_spark_session_job(cmd, workspace_name, spark_pool_name, session_id):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.get_spark_session(session_id, detailed=True)


def cancel_spark_session_job(cmd, workspace_name, spark_pool_name, session_id):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.cancel_spark_session(session_id)


def reset_timeout(cmd, workspace_name, spark_pool_name, session_id):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.reset_spark_session_timeout(session_id)


# Spark Session Statement
def list_spark_session_statements(cmd, workspace_name, spark_pool_name, session_id):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.get_spark_statements(session_id)


def create_spark_session_statement(cmd, workspace_name, spark_pool_name, session_id, code, language):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    if not code:
        raise CLIError(
            'Could not read code content from the supplied --code parameter. It is either empty or an invalid file.')
    spark_statement_options = SparkStatementOptions(code=code, kind=language)
    return client.create_spark_statement(session_id, spark_statement_options)


def get_spark_session_statement(cmd, workspace_name, spark_pool_name, session_id, statement_id):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.get_spark_statement(session_id, statement_id)


def cancel_spark_session_statement(cmd, workspace_name, spark_pool_name, session_id, statement_id):
    client = cf_synapse_spark_session(cmd.cli_ctx, workspace_name, spark_pool_name)
    return client.cancel_spark_statement(session_id, statement_id)
