# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (
    policy_events_operations, policy_states_operations, policy_remediations_operations, policy_metadata_operations)
from ._exception_handler import policy_insights_exception_handler


def load_command_table(self, _):
    policy_events_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.policyinsights.operations#PolicyEventsOperations.{}',
        exception_handler=policy_insights_exception_handler
    )

    policy_states_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.policyinsights.operations#PolicyStatesOperations.{}',
        exception_handler=policy_insights_exception_handler
    )

    policy_remediations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.policyinsights.operations#RemediationsOperations.{}',
        exception_handler=policy_insights_exception_handler
    )

    policy_metadata_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.policyinsights.operations#PolicyMetadataOperations.{}',
        exception_handler=policy_insights_exception_handler
    )

    with self.command_group('policy event', policy_events_sdk, client_factory=policy_events_operations) as g:
        g.custom_command('list', 'list_policy_events')

    with self.command_group('policy state', policy_states_sdk, client_factory=policy_states_operations) as g:
        g.custom_command('list', 'list_policy_states')
        g.custom_command('summarize', 'summarize_policy_states')
        g.custom_command('trigger-scan', 'trigger_policy_scan',
                         supports_no_wait=True)

    with self.command_group('policy remediation', policy_remediations_sdk,
                            client_factory=policy_remediations_operations) as g:
        g.custom_show_command('show', 'get_policy_remediation')
        g.custom_command('list', 'list_policy_remediations')
        g.custom_command('delete', 'delete_policy_remediation')
        g.custom_command('cancel', 'cancel_policy_remediation')
        g.custom_command('create', 'create_policy_remediation')

    with self.command_group('policy remediation deployment', policy_remediations_sdk,
                            client_factory=policy_remediations_operations) as g:
        g.custom_command('list', 'list_policy_remediation_deployments')

    with self.command_group('policy metadata', policy_metadata_sdk, client_factory=policy_metadata_operations) as g:
        g.custom_command('list', 'list_policy_metadata')
        g.custom_show_command('show', 'show_policy_metadata')

    with self.command_group('policy attestation') as g:
        # Note(slakhotia): The recommended way to generate cli now is through using aaz-dev-tools.
        # As of 1/25/2023, this tool (aaz) does not support different scopes (Ex. Sub, RG, and Resource)
        # for an individual command and is instead divided into different commands based on the scope.
        # (Ex. create, create-by-rg, create-by-subscription).Only the 'list' command supports combining them.
        # Until that scenario is supported for other commands like create, update, delete, etc,
        # we will need to continue using custom commands to call those individual commands
        # based on the scope.
        g.custom_command('create', 'create_policy_attestation')
        g.custom_command('update', 'update_policy_attestation')
        g.custom_command('delete', 'delete_policy_attestation')
        g.custom_show_command('show', 'show_policy_attestation')

        from .operations.AttestationList import List
        self.command_table['policy attestation list'] = List(loader=self)
