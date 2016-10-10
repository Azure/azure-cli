#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

def of_component_list():
    from azure.cli.command_modules.component.custom import list_components
    return list_components

def of_component_update():
    from azure.cli.command_modules.component.custom import update
    return update

def of_component_remove():
    from azure.cli.command_modules.component.custom import remove
    return remove
