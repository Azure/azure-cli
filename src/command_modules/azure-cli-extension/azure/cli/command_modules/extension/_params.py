# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse

from argcomplete.completers import FilesCompleter

from azure.cli.core.util import CLIError
from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.extension import get_extension_names
from ._index import get_index_extensions


def extension_name_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    return get_extension_names()


def extension_name_from_index_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    return get_index_extensions().keys()


def validate_extension_add(namespace):
    if (namespace.extension_name and namespace.source) or (not namespace.extension_name and not namespace.source):
        raise CLIError("usage error: --name NAME | --source SOURCE")


with ParametersContext('extension') as c:
    c.register('extension_name', ('--name', '-n'), help='Name of extension', completer=extension_name_completion_list)
    # This is a hidden parameter for now
    c.register('index_url', ('--index',), help=argparse.SUPPRESS)

with ParametersContext('extension add') as c:
    c.argument('extension_name', completer=extension_name_from_index_completion_list, validator=validate_extension_add)
    c.register('source', ('--source', '-s'), help='Filepath or URL to an extension', completer=FilesCompleter())
    c.register('yes', ('--yes', '-y'), action='store_true', help='Do not prompt for confirmation.')
