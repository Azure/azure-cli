# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger

from azure.cli.core.extension.operations import (
    add_extension, remove_extension, list_extensions, show_extension,
    list_available_extensions, update_extension)

logger = get_logger(__name__)


def add_extension_cmd(cmd, source=None, extension_name=None, index_url=None, yes=None,
                      pip_extra_index_urls=None, pip_proxy=None, system=None):
    return add_extension(cmd=cmd, source=source, extension_name=extension_name, index_url=index_url, yes=yes,
                         pip_extra_index_urls=pip_extra_index_urls, pip_proxy=pip_proxy, system=system)


def remove_extension_cmd(extension_name):
    return remove_extension(extension_name)


def list_extensions_cmd():
    return list_extensions()


def show_extension_cmd(extension_name):
    return show_extension(extension_name)


def update_extension_cmd(cmd, extension_name, index_url=None, pip_extra_index_urls=None, pip_proxy=None):
    return update_extension(cmd, extension_name, index_url=index_url, pip_extra_index_urls=pip_extra_index_urls,
                            pip_proxy=pip_proxy)


def list_available_extensions_cmd(index_url=None, show_details=False):
    return list_available_extensions(index_url=index_url, show_details=show_details)
