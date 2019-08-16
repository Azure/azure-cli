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

helps['sql vm group'] = """
type: group
short-summary: Manage SQL virtual machine groups.
"""

helps['sql vm group ag-listener'] = """
type: group
short-summary: Manage SQL availability group listeners.
"""

helps['sql vm group ag-listener update'] = """
type: command
short-summary: Updates an availability group listener.
examples:
  - name: Replace the SQL virtual machines that were in the availability group.
    text: >
        az sql vm group ag-listener update -n aglistenertest -g myresourcegroup --sqlvms sqlvm3 sqlvm4 --group-name mygroup
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
"""
