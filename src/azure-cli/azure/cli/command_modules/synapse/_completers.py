# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.command_modules.synapse.operations.accesscontrol import list_role_definitions


@Completer
def get_role_definition_name_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    if namespace.workspace_name:
        definitions = list_role_definitions(cmd, namespace.workspace_name)
        return [x.name for x in definitions]
    return []
