# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from azure.cli.command_modules.loganalytics._client_factory import loganalytics_data_plane_client

    loganalytics_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.loganalytics.custom#{}',
        client_factory=loganalytics_data_plane_client
    )

    with self.command_group('loganalytics', loganalytics_sdk) as g:
        g.command('query', 'execute_query')
