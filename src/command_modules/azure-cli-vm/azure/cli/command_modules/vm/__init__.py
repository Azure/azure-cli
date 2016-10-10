#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=unused-import

import azure.cli.command_modules.vm._help

def load_params(command):
    import azure.cli.command_modules.vm._params

def load_commands():
    import azure.cli.command_modules.vm.commands

