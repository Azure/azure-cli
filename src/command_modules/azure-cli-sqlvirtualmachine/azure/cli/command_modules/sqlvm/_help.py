# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['sqlvm'] = """
    type: group
    short-summary: Manage SQL virtual machines.
    """
helps['sqlvm group'] = """
    type: group
    short-summary: Manage SQL virtual machine groups.
    """
helps['sqlvm aglistener'] = """
    type: group
    short-summary: Manage SQL availability group listeners.
    """
helps['sqlvm op'] = """
    type: group
    short-summary: List all SQL available Rest API operations.
    """
helps['sqlvm group create'] = """
    type: command
    short-summary: Creates or updates a SQL virtual machine group.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine group.
    """
helps['sqlvm aglistener create'] = """
    type: command
    short-summary: Creates or updates an availability group listener.
    parameters:
        - name: --name -n
          short-summary: Name of the availability group listener.
        - name: --group-name, -gn
          short-summary: Name of the SQL virtual machine group.
        - name: --availability-group-name
          short-summary: Name of the availability group.
    """
helps['sqlvm create']="""
    type: command
    short-summary: Creates or updates a SQL virtual machine.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine. The name of the new SQL virtual machine must be equal to the underlying virtual machine created from SQL marketplace image.
        - name: --virtual-machine-resource-id
          short-summary: ARM Resource id of underlying virtual machine created from SQL marketplace image.
    examples:
        - name: Create a SQL virtual machine with AHUB billing tag.
          text: >
            az sqlvm create -n SqlVm -g MyResourceGroup -l eastus -sql_server_license_type AHUB
    """

