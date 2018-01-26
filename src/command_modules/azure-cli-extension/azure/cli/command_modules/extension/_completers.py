# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.core.extension import get_extension_names

from azure.cli.command_modules.extension.custom import get_index_extensions


@Completer
def extension_name_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    return get_extension_names()


@Completer
def extension_name_from_index_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    return get_index_extensions().keys()
