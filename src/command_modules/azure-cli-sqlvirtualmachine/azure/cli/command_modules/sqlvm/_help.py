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
    examples:
        - name: Create a SQL virtual machine group for SQL2016-WS2016 Enterprise virtual machines.
        - text: >
            az sqlvm group create -n sqlvmgroup -i SQL2016-WS2016 -s Enterprise -l eastus -g MyResourceGroup -f Domain.com -a testop@Domain.com -b testservice@Domain.com --sa-key '<PublicKey>' --sa-url 'https://storacc.blob.core.windows.net/'
    """
helps['sqlvm aglistener create'] = """
    type: command
    short-summary: Creates or updates an availability group listener.
    """
helps['sqlvm aglistener update'] = """
    type: command
    short-summary: Updates an availability group listener.
    """
helps['sqlvm create'] = """
    type: command
    short-summary: Creates or updates a SQL virtual machine.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine. The name of the new SQL virtual machine must be equal to the underlying virtual machine created from SQL marketplace image.
    examples:
        - name: Create a SQL virtual machine with AHUB billing tag.
          text: >
            az sqlvm create -n sqlvm -g MyResourceGroup -l eastus --sql-server-license-type AHUB
        - name: Create a SQL virtual machine and join it with an existing SQL virtual machine group.
          text: >
            $sqlvmgroup = az sqlvm group show -n sqlvmgroup -g MyResourceGroup | ConvertFrom-Json

            az sqlvm create -n sqlvm -g MyResourceGroup -l eastus --group-resource-id $sqlvmgroup.id --cluster-bootstrap-account-password
            '<boostrappassword>' --cluster-operator-account-password '<operatorpassword>' --sql-service-account-password '<servicepassword>'
        - name: Update SQL virtual machine auto backup settings.
          text: >
            az sqlvm create -n sqlvm -g MyResourceGroup -l eastus --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-time 2 --full-backup-window-hours 2
            --storage-access-key '<storageKey>' --storage-account-url 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
        - name: Update SQL virtual machine auto patching settings.
          text: >
            az sqlvm create -n sqlvm -g MyResourceGroup -l eastus --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-starting-hour 2
        - name: Enable R services in SQL2016 onwards.
          text: >
            az sqlvm create -n sqlvm -g MyResourceGroup -l eastus --enable-r-services true
    """
helps['sqlvm update'] = """
    type: command
    short-summary: Updates the properties of a SQL virtual machine.
    examples:
        - name: Add or update a tag.
          text: >
            az sqlvm update -n sqlvm -g MyResourceGroup --set tags.tagName=tagValue
        - name: Remove a tag.
          text: >
            az sqlvm update -n sqlvm -g MyResourceGroup --remove tags.tagName
    """
helps['sqlvm add-to-group'] = """
    type: command
    short-summary: Adds SQL virtual machine to a SQL virtual machine group.
    """
helps['sqlvm remove-from-group'] = """
    type: command
    short-summary: Remove SQL virtual machine from its current SQL virtual machine group.
    examples:
        - name: Remove SQL virtual machine from a group.
          text: >
            az sqlvm remove-from-group -n sqlvm -g MyResourceGroup
    """

