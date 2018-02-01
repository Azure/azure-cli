# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.decorators import Completer
from azure.mgmt.containerservice.models import ContainerServiceVMSizeTypes

from ._client_factory import cf_compute_service


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return the intersection of the VM sizes allowed by the ACS SDK with those returned by the Compute Service."""
    try:
        location = namespace.location
    except AttributeError:
        # TODO: try the resource group's default location before falling back to this
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return sorted(set(r.name for r in result) & set(c.value for c in ContainerServiceVMSizeTypes))


def get_vm_sizes(cli_ctx, location):
    return list(cf_compute_service(cli_ctx).virtual_machine_sizes.list(location))
