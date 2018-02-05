# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.role.custom import list_role_definitions


@Completer
def get_role_definition_name_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    definitions = list_role_definitions(cmd)
    return [x.properties.role_name for x in list(definitions)]
