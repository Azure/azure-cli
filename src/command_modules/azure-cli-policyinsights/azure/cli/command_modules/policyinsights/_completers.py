# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.command_modules.resource._client_factory import _resource_policy_client_factory

@Completer
def get_policy_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_definitions.list()
    return [i.name for i in result]

@Completer
def get_policy_set_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_set_definitions.list()
    return [i.name for i in result]

@Completer
def get_policy_assignment_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_assignments.list()
    return [i.name for i in result]
