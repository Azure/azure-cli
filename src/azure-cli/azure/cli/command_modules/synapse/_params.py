# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------s

from azure.cli.core.commands.parameters import name_type, tags_type


# pylint: disable=too-many-statements
def load_arguments(self, _):
    # synapse spark
    with self.argument_context('synapse spark') as c:
        c.argument('workspace_name', help='The name of the workspace.')
        c.argument('spark_pool_name', help='The name of the spark pool.')
        c.argument('from_index', help='Optional parameter specifying which index the list should begin from.')
        c.argument('detailed',
                   help='Optional query parameter specifying whether detailed response is returned beyond plain livy.')
        c.argument('size',
                   help='The size of the returned list.By default it is 20 and that is the maximum.')
        c.argument('tags', arg_type=tags_type, help='The tag of spark batch job.')
        c.argument('artifact_id', help='The artifact id.')
        c.argument('job_name', arg_type=name_type, help='The spark batch or session job name.')
        c.argument('file', help='The URI of file.')
        c.argument('class_name', help='The class name.')
        c.argument('args', nargs='+', help='The arguments of the job.')
        c.argument('jars', nargs='+', help='The array of jar files.')
        c.argument('files', nargs='+', help='The array of files URI.')
        c.argument('archives', nargs='+', help='The array of archives.')
        c.argument('conf', help='The configuration of spark batch job.')
        c.argument('driver_memory', help='The memory of driver.')
        c.argument('driver_cores', help='The number of cores in driver.')
        c.argument('executor_memory', help='The memory of executor.')
        c.argument('executor_cores', help='The number of cores in each executor.')
        c.argument('executor_number', help='The number of executors.')

    with self.argument_context('synapse spark batch') as c:
        c.argument('batch_id', options_list=['--id'], arg_group='Spark Batch', help='The id of the spark batch job.')

    with self.argument_context('synapse spark session') as c:
        c.argument('session_id', options_list=['--id'], arg_group='Spark Session',
                   help='The id of the spark session job.')

    with self.argument_context("synapse spark session-statement") as c:
        c.argument('statement_id', options_list=['--id'], arg_group="Spark Session-statement",
                   help='The id of the statement.')
        c.argument('session_id', help='The id of spark session job.')
        c.argument('code', help='The code of spark statement.')
        c.argument('kind', help='The kind of spark statement.')

    # synapse workspace
    with self.argument_context('synapse workspace') as c:
        c.argument('resource_group_name', help='The resource group name.')
        c.argument('workspace_name', arg_type=name_type, help='The workspace name.')
        c.argument("account_url", help='The data lake storage account url.')
        c.argument('file_system', help='The file system of the data lake storage account.')
        c.argument('sql_admin_login_user', help='The sql administrator login user name.')
        c.argument('sql_admin_login_password', help='The sql administrator login password.')

    # synapse spark pool
    with self.argument_context('synapse spark pool') as c:
        c.argument('big_data_pool_name', arg_type=name_type, help='The spark pool name.')
        c.argument('spark_pool_name', arg_type=name_type, help='The spark pool name.')
        c.argument('workspace_name', help='The workspace name.')
