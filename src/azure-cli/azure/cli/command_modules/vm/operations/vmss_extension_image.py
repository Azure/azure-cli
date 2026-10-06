# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import register_command

from ..aaz.latest.vm.extension.image import ListVersions as _VMExtensionImageListVersions
from ..aaz.latest.vm.extension.image import Show as _VMExtensionImageShow


@register_command(
    "vmss extension image list-versions",
)
class VMSSExtensionImageListVersions(_VMExtensionImageListVersions):
    """List the versions for available extensions."""


@register_command(
    "vmss extension image show",
)
class VMSSExtensionImageShow(_VMExtensionImageShow):
    """Display information for an extension."""
