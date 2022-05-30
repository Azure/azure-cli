# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['sql vm'] = """
type: group
short-summary: Manage SQL virtual machines.
"""

helps['sql vm add-to-group'] = """
type: command
short-summary: Adds SQL virtual machine to a SQL virtual machine group.
examples:
  - name: Add SQL virtual machine to a group.
    text: >
        az sql vm add-to-group -n sqlvm -g myresourcegroup --sqlvm-group sqlvmgroup --bootstrap-acc-pwd {bootstrappassword} --operator-acc-pwd {operatorpassword} --service-acc-pwd {servicepassword}
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
  - name: Create a SQL virtual machine with DR billing tag.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type DR
  - name: Create a SQL virtual machine with specific sku type and license type.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --image-sku Enterprise --license-type AHUB
  - name: Create a SQL virtual machine with NoAgent type, only valid for EOS SQL 2008 and SQL 2008 R2.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type AHUB --sql-mgmt-type NoAgent --image-sku Enterprise --image-offer SQL2008-WS2008R2
  - name: Enable R services in SQL2016 onwards.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type PAYG --sql-mgmt-type Full --enable-r-services true
  - name: Create SQL virtual machine and configure auto backup settings.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type PAYG --sql-mgmt-type Full --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-hour 2 --full-backup-duration 2 --sa-key {storageKey} --storage-account 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
  - name: Create SQL virtual machine and configure auto patching settings.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type PAYG --sql-mgmt-type Full --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-start-hour 2
  - name: Create SQL virtual machine and configure SQL connectivity settings.
    text: >
        az sql vm create -n sqlvm -g myresourcegroup -l eastus --license-type PAYG --sql-mgmt-type Full --connectivity-type private --port 1433 --sql-auth-update-username {newlogin} --sql-auth-update-pwd {sqlpassword}
"""

helps['sql vm group'] = """
type: group
short-summary: Manage SQL virtual machine groups.
"""

helps['sql vm group ag-listener'] = """
type: group
short-summary: Manage SQL availability group listeners.
"""

helps['sql vm group ag-listener create'] = """
type: command
short-summary: Creates an availability group listener.
examples:
  - name: Create an availability group listener. Note the SQL virtual machines are in the same resource group as the SQL virtual machine group.
    text: >
        az sql vm group ag-listener create -n aglistenertest -g myresourcegroup --ag-name agname --group-name sqlvmgroup --ip-address 10.0.0.11 --load-balancer '/subscriptions/{yoursubscription}/resourceGroups/{yourrg}/providers/Microsoft.Network/loadBalancers/{lbname}' --probe-port 59999 --subnet '/subscriptions/{yoursubscription}/resourceGroups/{yourrg}/providers/Microsoft.Network/virtualNetworks/{vnname}/subnets/{subnetname}' --sqlvms sqlvm1 sqlvm2
  - name: Create an availability group listener. Note all resources are in the same resource group.
    text: >
        az sql vm group ag-listener create -n aglistenertest -g myresourcegroup --ag-name agname --group-name sqlvmgroup --ip-address 10.0.0.11 --load-balancer {lbname} --probe-port 59999 --subnet {subnetname} --vnet-name {vnname} --sqlvms sqlvm1 sqlvm2
"""

helps['sql vm group ag-listener update'] = """
type: command
short-summary: Updates an availability group listener.
examples:
  - name: Replace the SQL virtual machines that were in the availability group.
    text: >
        az sql vm group ag-listener update -n aglistenertest -g myresourcegroup --sqlvms sqlvm3 sqlvm4 --group-name mygroup
"""

helps['sql vm group create'] = """
type: command
short-summary: Creates a SQL virtual machine group.
examples:
  - name: Create a SQL virtual machine group for SQL2016-WS2016 Enterprise virtual machines.
    text: >
        az sql vm group create -n sqlvmgroup -l eastus -g myresourcegroup --image-offer SQL2016-WS2016 --image-sku Enterprise --domain-fqdn Domain.com --operator-acc testop --service-acc testservice --sa-key {PublicKey} --storage-account 'https://storacc.blob.core.windows.net/'
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
        az sql vm group update -n sqlvmgroup -g myresourcegroup --sa-key {PublicKey} --storage-account 'https://newstoracc.blob.core.windows.net/'
"""

helps['sql vm remove-from-group'] = """
type: command
short-summary: Remove SQL virtual machine from its current SQL virtual machine group.
examples:
  - name: Remove SQL virtual machine from a group.
    text: >
        az sql vm remove-from-group -n sqlvm -g myresourcegroup
"""

helps['sql vm start-assessment'] = """
type: command
short-summary: Starts SQL best practice assessment on SQL virtual machine
examples:
  - name: Starts SQL best practice assessment.
    text: >
        az sql vm start-assessment -n sqlvm -g myresourcegroup
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
  - name: Update a SQL virtual machine with specific sku type.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --image-sku Enterprise
  - name: Update a SQL virtual machine manageability from LightWeight to Full.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --sql-mgmt-type Full --yes
  - name: Update SQL virtual machine auto backup settings.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --backup-schedule-type manual --full-backup-frequency Weekly --full-backup-start-hour 2 --full-backup-duration 2 --sa-key {storageKey} --storage-account 'https://storageacc.blob.core.windows.net/' --retention-period 30 --log-backup-frequency 60
  - name: Disable SQL virtual machine auto backup settings.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --enable-auto-backup false
  - name: Update SQL virtual machine auto patching settings.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --day-of-week sunday --maintenance-window-duration 60 --maintenance-window-start-hour 2
  - name: Disable SQL virtual machine auto patching settings.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --enable-auto-patching false
  - name: Update a SQL virtual machine billing tag to AHUB.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --license-type AHUB
  - name: Update a SQL virtual machine billing tag to DR.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --license-type DR
  - name: Update a SQL virtual machine to disable SQL best practice assessment.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --enable-assessment false
  - name: Update a SQL virtual machine to disable schedule for SQL best practice assessment.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --enable-assessment-schedule false
  - name: Update a SQL virtual machine to enable schedule with weekly interval for SQL best practice assessment when VM is already associated with a Log Analytics workspace.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --assessment-weekly-interval 1 --assessment-day-of-week monday --assessment-start-time-local '19:30'
  - name: Update a SQL virtual machine to enable schedule with monthly occurrence for SQL best practice assessment while associating with a Log Analytics workspace.
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --workspace-name myLogAnalyticsWorkspace --workspace-rg myRg --assessment-monthly-occurrence 1 --assessment-day-of-week monday --assessment-start-time-local '19:30'
  - name: Update a SQL virtual machine to enable SQL best practices assessment without setting a schedule for running assessment on-demand
    text: >
        az sql vm update -n sqlvm -g myresourcegroup --enable-assessment true
"""
