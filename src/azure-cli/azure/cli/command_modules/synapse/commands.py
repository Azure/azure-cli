# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import synapse_data_plane_factory
    from ._client_factory import cf_synapse_spark_batch
    from ._client_factory import cf_synapse_spark_session

    synapse_spark_batch_sdk = CliCommandType(
        operation_tmpl='azure.synapse.operations#SparkBatchOperations.{}',
        client_factory=cf_synapse_spark_batch
    )

    synapse_spark_session_sdk= CliCommandType(
        operations_tmpl='azure.synapse.operations#SparkSessionOperations.{}',
        client_factory=cf_synapse_spark_session
    )

    #spark batch opertions
    with self.command_group('synapse spark-batch', synapse_spark_batch_sdk, client_factory=cf_synapse_spark_batch) as g:
        g.custom_command('list', 'list_spark_batch_jobs')