# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['vm repair'] = """
    type: group
    short-summary: Auto repair commands to fix VMs.
    long-summary: |
        VM repair scripts will enable Azure users to self-repair non-bootable VMs by copying the source VM's OS disk and attaching it to a newly created repair VM.
"""

helps['vm repair create'] = """
    type: command
    short-summary: Create a new repair VM and attach the source VM's copied OS disk as a data disk.
    examples:
        - name: Create a repair VM
          text: >
            az vm repair create -g MyResourceGroup -n myVM --verbose
        - name: Create a repair VM and set the VM authentication
          text: >
            az vm repair create -g MyResourceGroup -n myVM --repair-username username --repair-password password!234 --verbose
"""

helps['vm repair restore'] = """
    type: command
    short-summary: Replace source VM's OS disk with data disk from repair VM.
    examples:
        - name: Restore from the repair VM, command will auto-search for repair-vm
          text: >
            az vm repair restore -g MyResourceGroup -n MyVM --verbose
        - name: Restore from the repair VM, specify the disk to restore
          text: >
            az vm repair restore -g MyResourceGroup -n MyVM --disk-name MyDiskCopy --verbose
"""
