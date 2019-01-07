# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['sql vm'] = """
    type: group
    short-summary: Manage SQL virtual machines.
    """
helps['sql vm group'] = """
    type: group
    short-summary: Manage SQL virtual machine groups.
    """
helps['sql vm group aglistener'] = """
    type: group
    short-summary: Manage SQL availability group listeners.
    """
helps['sql vm group create'] = """
    type: command
    short-summary: Creates a SQL virtual machine group.
    examples:
        - name: Create a SQL virtual machine group for SQL2016-WS2016 Enterprise virtual machines.
          text: >
            az sql vm group create -n sqlvmgroup -l eastus -g myresourcegroup --image-offer SQL2016-WS2016 --image-sku Enterprise
            --domain-fqdn Domain.com --operator-acc testop --service-acc testservice --sa-key '{PublicKey}' --storage-acc 'https://storacc.blob.core.windows.net/'
    """
helps['sql vm group update'] = """
    type: command
    short-summary: Updates a SQL virtual machine group if there are not SQL virtual machines attached to the group.
    examples:
        - name: Update an empty SQL virtual machine group operator account.
          text: >
            az sql vm group update -n sqlvmgroup -g myresourcegroup --operator-acc testop
        - name: Update an empty SQL virtual machine group storage account and key.
          text: >
            az sql vm group update -n sqlvmgroup -g myresourcegroup --sa-key '{PublicKey}' --storage-acc 'https://newstoracc.blob.core.windows.net/'
    """
helps['sql vm group aglistener create'] = """
    type: command
    short-summary: Creates or updates an availability group listener.
    examples:
        - name: Create an availability group listener. Note the SQL virtual machines are in the same resource group as the SQL virtual machine group.
          text: >
            az sql vm group aglistener create -n aglistenertest -g myresourcegroup --ag-name agname --group-name sqlvmgroup --ip-address 10.0.0.11
            --lb-rid '/subscriptions/{yoursubscription}/resourceGroups/{yourrg}/providers/Microsoft.Network/loadBalancers/{lbname}' --probe-port 59999
            --subnet-rid '/subscriptions/{yoursubscription}/resourceGroups/{yourrg}/providers/Microsoft.Network/virtualNetworks/{vnname}/subnets/{subnetname}'
            --sqlvms sqlvm1 sqlvm2
    """
helps['sql vm create'] = """
    type: command
    short-summary: Creates a SQL virtual machine.
    parameters:
        - name: --name -n
          short-summary: Name of the SQL virtual machine. The name of the new SQL virtual machine must be equal to the underlying virtual machine created from SQL marketplace image.
    examples:
        - name: Create a SQL virtual machine with AHUB billing tag.
          text: >
            az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type AHUB
        - name: Create a SQL virtual machine and join it with an existing SQL virtual machine group in the same resource group.
          text: >
            az sql vm create -n sqlvm -g myresourcegroup -l eastus --sqlvm-group sqlvmgroup --boostrap-acc-pwd
            '{boostrappassword}' --operator-acc-pwd '{operatorpassword}' --service-acc-pwd '{servicepassword}'
        - name: Enable R services in SQL2016 onwards.
          text: >
            az sql vm create -n sqlvm -g myresourcegroup -l eastus --enable-r-services true
        - name: Create SQL virtual machine and configure auto backup settings.
          text: >
            az sql vm create -n sqlvm -g myresourcegroup -l eastus --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-time 2 --full-backup-window-hours 2
            --storage-access-key '{storageKey}' --storage-acc 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
        - name: Create SQL virtual machine and configure auto patching settings.
          text: >
            az sql vm create -n sqlvm -g myresourcegroup -l eastus --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-starting-hour 2
        - name: Create SQL virtual machine and configure SQL connectivity settings.
          text: >
            az sql vm create -n sqlvm -g myresourcegroup -l eastus --connectivity-type private --port 1433 --sql-auth-update-username '{newlogin}' --sql-auth-update-pwd '{sqlpassword}'
    """
helps['sql vm update'] = """
    type: command
    short-summary: Updates the properties of a SQL virtual machine.
    examples:
        - name: Add or update a tag.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --set tags.tagName=tagValue
        - name: Remove a tag.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --remove tags.tagName
        - name: Update SQL virtual machine auto backup settings.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-time 2 --full-backup-window-hours 2
            --storage-access-key '{storageKey}' --storage-acc 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
        - name: Disable SQL virtual machine auto backup settings.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --enable-auto-backup false
        - name: Update SQL virtual machine auto patching settings.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-starting-hour 2
        - name: Disable SQL virtual machine auto patching settings.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --enable-auto-patching false
        - name: Update a SQL virtual machine billing tag to AHUB.
          text: >
            az sql vm update -n sqlvm -g myresourcegroup --license-type AHUB
    """
helps['sql vm add-to-group'] = """
    type: command
    short-summary: Adds SQL virtual machine to a SQL virtual machine group.
    examples:
        - name: Add SQL virtual machine to a group.
          text: >
            az sql vm add-to-group -n sqlvm -g myresourcegroup --sqlvm-group sqlvmgroup --boostrap-acc-pwd
            '{boostrappassword}' --operator-acc-pwd '{operatorpassword}' --service-acc-pwd '{servicepassword}'
    """
helps['sql vm remove-from-group'] = """
    type: command
    short-summary: Remove SQL virtual machine from its current SQL virtual machine group.
    examples:
        - name: Remove SQL virtual machine from a group.
          text: >
            az sql vm remove-from-group -n sqlvm -g myresourcegroup
    """
helps['sql vm group aglistener update'] = """
    type: command
    short-summary: Updates an availability group listener.
    examples:
        - name: Add SQL virtual machine to an availavility group listener.
          text: >
            az sql vm group aglistener update -n aglistener -g myresourcegroup --group-name sqlvmgroup --add-sqlvm sqlvm1
        - name: Remove SQL virtual machine from an availability group listener.
          text: >
            az sql vm group aglistener update -n aglistener -g myresourcegroup --group-name sqlvmgroup --remove-sqlvm sqlvm1
    """
