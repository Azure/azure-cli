# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter

from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.extension import get_extension_names


def extension_name_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    return get_extension_names()


with ParametersContext('extension') as c:
    c.register('extension_name', ('--name', '-n'), help='Name of extension', completer=extension_name_completion_list)


with ParametersContext('extension add') as c:
    c.argument('extension_name', completer=None)
    c.register('source', ('--source', '-s'), help='Filepath or URL to an extension', completer=FilesCompleter())
