# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file
# flake8: noqa

from azure.cli.core.aaz import register_command
from ._add import Add


@register_command(
    "security va sql baseline set",
    is_preview=True,
    redirect="security va sql baseline add",
)
class Set(Add):
    """Set a list of baseline rules. Will overwrite any previously existing results (for all rules).

    This is a deprecated alias of `az security va sql baseline add`, preserved for backwards
    compatibility with the legacy `az security va sql baseline set` command.

    :example: Set baseline for all rules on an Azure SQL database using the latest scan results.
        az security va sql baseline set --resource-id /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Sql/servers/{server}/databases/{db} --latest-scan true
    """


__all__ = ["Set"]
