# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.decorators import Completer

from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc, get_vm_sizes


@Completer
def get_urn_aliases_completion_list(cmd, prefix, namespace):  # pylint: disable=unused-argument
    images = load_images_from_aliases_doc(cmd.cli_ctx)
    return [i['urnAlias'] for i in images]


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace):  # pylint: disable=unused-argument
    location = namespace.location
    if not location:
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return [r.name for r in result]


@Completer
def get_vm_run_command_completion_list(cmd, prefix, namespace):  # pylint: disable=unused-argument
    from ._client_factory import _compute_client_factory
    try:
        location = namespace.location
    except AttributeError:
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    result = _compute_client_factory(cmd.cli_ctx).virtual_machine_run_commands.list(location)
    return [r.id for r in result]
