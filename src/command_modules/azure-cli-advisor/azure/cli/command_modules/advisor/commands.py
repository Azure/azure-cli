# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.advisor._client_factory import \
    (advisor_mgmt_client_factory,
     recommendations_mgmt_client_factory,
     suppressions_mgmt_client_factory,
     configurations_mgmt_client_factory)


def load_command_table(self, _):
    with self.command_group('advisor recommendation') as g:
        g.custom_command('list', 'cli_advisor_list_recommendations',
                         client_factory=recommendations_mgmt_client_factory)
        g.custom_command('disable', 'cli_advisor_disable_recommendations',
                         client_factory=suppressions_mgmt_client_factory)
        g.custom_command('enable', 'cli_advisor_enable_recommendations',
                         client_factory=advisor_mgmt_client_factory)

    with self.command_group('advisor configuration', client_factory=configurations_mgmt_client_factory) as g:
        g.custom_command('list', 'cli_advisor_list_configurations')
        g.custom_command('update', 'cli_advisor_update_configurations')
