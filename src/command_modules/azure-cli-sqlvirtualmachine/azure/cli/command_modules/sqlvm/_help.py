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
    short-summary: Creates or Updates a SQL virtual machine group.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine group.
        - name: --sql-image-offer
          short-summary: SQL image offer.
        - name: --sql-image-sku
          short-summary: SQL image sku.
    """
helps['sqlvm aglistener create'] = """
    type: command
    short-summary: Creates or Updates an availability group listener.
    parameters:
        - name: --name -n
          short-summary: Name of the availability group listener.
        - name: --group-name, -gn
          short-summary: Name of the SQL virtual machine group.
        - name: --availability-group-name
          short-summary: Name of the availability group.
        - name: --port
          short-summary: Listener port.
    """
helps['sqlvm create']="""
    type: command
    short-summary: Creates or Updates a SQL virtual machine.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine. Name must match the SQL marketplace image name.
        - name: --virtual-machine-resource-id
          short-summary: ARM Resource id of underlying virtual machine created from SQL marketplace image.
    """

