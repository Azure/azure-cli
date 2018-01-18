# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long


def load_command_table(self, _):

    from azure.cli.core.commands import CliCommandType
    from azure.cli.command_modules.example._client_factory import cf_example

    example_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.example.operations#ExampleOperations.{}',
        client_factory=cf_example
    )

    with self.command_group('example', example_sdk) as g:
        g.custom_command('create', 'create_example')  # custom command
        g.command('show', 'get')  # reflected SDK command
        g.command('delete', 'delete')
