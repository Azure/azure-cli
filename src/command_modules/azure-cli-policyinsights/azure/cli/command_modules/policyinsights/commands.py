# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (policy_events_operations, policy_states_operations)
from ._exception_handler import policyinsights_exception_handler

def load_command_table(self, _):
    policy_events_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.policyinsights.operations.policy_events_operations#PolicyEventsOperations.{}',
        exception_handler=policyinsights_exception_handler
    )

    policy_states_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.policyinsights.operations.policy_states_operations#PolicyStatesOperations.{}',
        exception_handler=policyinsights_exception_handler
    )

    with self.command_group('policyinsights event', policy_events_sdk, client_factory=policy_events_operations) as g:
        g.custom_command('list', 'list_policy_events')

    with self.command_group('policyinsights state', policy_states_sdk, client_factory=policy_states_operations) as g:
        g.custom_command('list', 'list_policy_states')
        g.custom_command('summarize', 'summarize_policy_states')
