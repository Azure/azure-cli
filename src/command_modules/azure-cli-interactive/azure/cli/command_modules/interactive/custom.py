# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from azure.cli.core.extension import ExtensionNotInstalledException, get_extension_modname, get_extension
from azure.cli.core.extension.operations import (reload_extension, update_extension,
                                                 add_extension, add_extension_to_path)

logger = get_logger(__name__)
INTERACTIVE_EXTENSION_NAME = 'interactive'


def start_shell(cmd, update=None, style=None):
    from importlib import import_module
    try:
        get_extension(INTERACTIVE_EXTENSION_NAME)
        if update:
            logger.warning("Updating the Interactive extension to the latest available..")
            update_extension(INTERACTIVE_EXTENSION_NAME)
            reload_extension(INTERACTIVE_EXTENSION_NAME)
    except ExtensionNotInstalledException:
        logger.warning("Installing the Interactive extension..")
        add_extension(extension_name=INTERACTIVE_EXTENSION_NAME)

    add_extension_to_path(INTERACTIVE_EXTENSION_NAME)
    interactive_module = get_extension_modname(ext_name=INTERACTIVE_EXTENSION_NAME)
    azext_interactive = import_module(interactive_module)
    azext_interactive.start_shell(cmd, style=style)
