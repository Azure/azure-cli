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
helps['sqlvm group create'] = """
    type: command
    short-summary: Creates a SQL virtual machine group.
    examples:
        - name: Create a SQL virtual machine group for SQL2016-WS2016 Enterprise virtual machines.
          text: >
            az sqlvm group create -n sqlvmgroup -l eastus -g myresourcegroup --image-offer SQL2016-WS2016 --image-sku Enterprise
            --domain-fqdn Domain.com --operator-acc testop@Domain.com --service-acc testservice@Domain.com --sa-key '<PublicKey>' --sa-url 'https://storacc.blob.core.windows.net/'
    """
helps['sqlvm group update'] = """
    type: command
    short-summary: Updates a SQL virtual machine group.
    examples:
        - name: Update an empty SQL virtual machine group image sku to Developer.
          text: >
            az sqlvm group update -n sqlvmgroup -g myresourcegroup -s Developer
    """
helps['sqlvm aglistener create'] = """
    type: command
    short-summary: Creates or updates an availability group listener.
    examples:
        - name: Create an availability group listener.
          text: >
            $sqlvm1 = az sqlvm show -g myresourcegroup -n sqlvm1 | ConvertFrom-Json

            $sqlvm2 = az sqlvm show -g myresourcegroup -n sqlvm2 | ConvertFrom-Json

            az sqlvm aglistener create -n aglistenertest -g myresourcegroup --ag-name agname --group-name sqlvmgroup --ip-address 10.0.0.11
            --lb-rid '/subscriptions/<yoursubscription>/resourceGroups/<yourrg>/providers/Microsoft.Network/loadBalancers/<lbname>' --probe-port 59999
            --subnet-rid '/subscriptions/<yoursubscription>/resourceGroups/<yourrg>/providers/Microsoft.Network/virtualNetworks/<vnname>/subnets/<subnetname>'
            --sqlvm-rids $sqlvm1.id $sqlvm2.id
    """
helps['sqlvm create'] = """
    type: command
    short-summary: Creates a SQL virtual machine.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine. The name of the new SQL virtual machine must be equal to the underlying virtual machine created from SQL marketplace image.
    examples:
        - name: Create a SQL virtual machine with AHUB billing tag.
          text: >
            az sqlvm create -n sqlvm -g myresourcegroup -l eastus --license-type AHUB
        - name: Create a SQL virtual machine and join it with an existing SQL virtual machine group.
          text: >
            $sqlvmgroup = az sqlvm group show -n sqlvmgroup -g myresourcegroup | ConvertFrom-Json

            az sqlvm create -n sqlvm -g myresourcegroup -l eastus --sqlvm-group-rid $sqlvmgroup.id --boostrap-acc-pwd
            '<boostrappassword>' --operator-acc-pwd '<operatorpassword>' --service-acc-pwd '<servicepassword>'
        - name: Enable R services in SQL2016 onwards.
          text: >
            az sqlvm create -n sqlvm -g myresourcegroup -l eastus --enable-r-services true
        - name: Create SQL virtual machine and configure auto backup settings.
          text: >
            az sqlvm create -n sqlvm -g myresourcegroup -l eastus --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-time 2 --full-backup-window-hours 2
            --storage-access-key '<storageKey>' --storage-account-url 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
        - name: Create SQL virtual machine and configure auto patching settings.
          text: >
            az sqlvm create -n sqlvm -g myresourcegroup -l eastus --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-starting-hour 2
    """
helps['sqlvm update'] = """
    type: command
    short-summary: Updates the properties of a SQL virtual machine.
    examples:
        - name: Add or update a tag.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --set tags.tagName=tagValue
        - name: Remove a tag.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --remove tags.tagName
        - name: Update SQL virtual machine auto backup settings.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-time 2 --full-backup-window-hours 2
            --storage-access-key '<storageKey>' --storage-account-url 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
        - name: Disable SQL virtual machine auto backup settings.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --enable-auto-backup false
        - name: Update SQL virtual machine auto patching settings.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-starting-hour 2
        - name: Disable SQL virtual machine auto patching settings.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --enable-auto-patching false
        - name: Update a SQL virtual machine billing tag to AHUB.
          text: >
            az sqlvm update -n sqlvm -g myresourcegroup --license-type AHUB
    """
helps['sqlvm add-to-group'] = """
    type: command
    short-summary: Adds SQL virtual machine to a SQL virtual machine group.
    examples:
        - name: Add SQL virtual machine to a group.
          text: >
            $sqlvmgroup = az sqlvm group show -n sqlvmgroup -g myresourcegroup | ConvertFrom-Json

            az sqlvm add-to-group -n sqlvm -g myresourcegroup --sqlvm-group-rid $sqlvmgroup.id --boostrap-acc-pwd
            '<boostrappassword>' --operator-acc-pwd '<operatorpassword>' --service-acc-pwd '<servicepassword>'
    """
helps['sqlvm remove-from-group'] = """
    type: command
    short-summary: Remove SQL virtual machine from its current SQL virtual machine group.
    examples:
        - name: Remove SQL virtual machine from a group.
          text: >
            az sqlvm remove-from-group -n sqlvm -g myresourcegroup
    """
helps['sqlvm aglistener add-sqlvm'] = """
    type: command
    short-summary: Add SQL virtual machine to an availability group listener.
    examples:
        - name: Add SQL virtual machine to a group.
          text: >
            $sqlvm = az sqlvm show -n sqlvm -g myresourcegroup | ConvertFrom-Json

            az sqlvm aglistener add-sqlvm -n aglistener -g myresourcegroup --group-name sqlvmgroup --sqlvm-rid $sqlvm.id
    """
helps['sqlvm aglistener remove-sqlvm'] = """
    type: command
    short-summary: Remove SQL virtual machine from an availability group listener.
    examples:
        - name: Remove SQL virtual machine from an availability group listener.
          text: >
            $sqlvm = az sqlvm show -n sqlvm -g myresourcegroup | ConvertFrom-Json

            az sqlvm aglistener remove-sqlvm -n aglistener -g myresourcegroup --group-name sqlvmgroup --sqlvm-rid $sqlvm.id
    """
