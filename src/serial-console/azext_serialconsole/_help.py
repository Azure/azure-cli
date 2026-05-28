# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['serial-console'] = """
    type: group
    short-summary: Connect to the Serial Console of a Linux/Windows Virtual Machine or VMSS Instance.
"""

helps['serial-console send'] = """
    type: group
    short-summary: Send NMI/SysRq/Reset to a VM or VMSS Instance.
"""

helps['serial-console connect'] = """
    type: command
    short-summary: Connect to Serial Console VM or VMSS Instance
    long-summary: >
        This command provides access to a text-based console for Linux and Windows virtual machines (VMs) and virtual machine scale set instances. This serial connection connects to the ttys0 serial port of the VM or virtual machine scale set instance, providing access to it independent of the network or operating system state. To exit serial console type Ctrl + ] and then q. To send an NMI/SysRq/Reset type Ctrl + ] and then n/s/r respectively.
    parameters:
      - name: --name -n
        short-summary: Name of the Virtual Machine or Virtual Machine Scale Set.
      - name: --resource-group -g
        short-summary: Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.
      - name: --instance-id
        short-summary: ID of VMSS instance. Not needed when connecting to the serialport of a Virtual Machine.
      - name: --subscription
        short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
    examples:
      - name: Connect to Serial Console of a VM
        text: >
            az serial-console connect -n MyVM -g MyResourceGroup
      - name: Connect to Serial Console of a VMSS Instance with ID 2
        text: >
            az serial-console connect -n MyVMSS -g MyResourceGroup --instance-id 2
"""

helps['serial-console enable'] = """
    type: command
    short-summary: Enable the serial console service for an entire subscription.
    parameters:
      - name: --subscription
        short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
    examples:
      - name: Enable Serial Console for a subscription
        text: >
            az serial-console enable
"""

helps['serial-console disable'] = """
    type: command
    short-summary: Disable the serial console service for an entire subscription.
    parameters:
      - name: --subscription
        short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
    examples:
      - name: Disable Serial Console for a subscription
        text: >
            az serial-console disable
"""

helps['serial-console send nmi'] = """
    type: command
    short-summary: Send a Non-Maskable Interrupt (NMI) to a VM or VMSS Instance
    long-summary: >
        A Non-Maskable Interrupt (NMI) is used in debugging scenarios and is designed to crash your target Virtual Machine.
    parameters:
      - name: --name -n
        short-summary: Name of the Virtual Machine or Virtual Machine Scale Set.
      - name: --resource-group -g
        short-summary: Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.
      - name: --instance-id
        short-summary: ID of VMSS instance. Not needed when connecting to the serialport of a Virtual Machine.
      - name: --subscription
        short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
    examples:
      - name: Send NMI to VM
        text: >
            az serial-console send nmi -n MyVM -g MyResourceGroup
      - name: Send NMI to VMSS Instance with ID 2
        text: >
            az serial-console send nmi -n MyVMSS -g MyResourceGroup --instance-id 2
"""

helps['serial-console send sysrq'] = """
    type: command
    short-summary: Send SysRq sequence to a VM or VMSS Instance
    long-summary:
        A SysRq is a sequence of keys understood by the Linux operation system kernel, which can trigger a set of pre-defined actions. These commands are often used when virtual machine troubleshooting or recovery can't be performed through traditional administration (for example, if the VM is not responding).
    parameters:
      - name: --name -n
        short-summary: Name of the Virtual Machine or Virtual Machine Scale Set.
      - name: --resource-group -g
        short-summary: Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.
      - name: --instance-id
        short-summary: ID of VMSS instance. Not needed when connecting to the serialport of a Virtual Machine.
      - name: --subscription
        short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
      - name: --input
        short-summary: Input key to send over serial console. Must be one character.
    examples:
      - name: Send SysRq to VM to crash system
        text: >
            az serial-console send sysrq -n MyVM -g MyResourceGroup --input c
      - name: Send SysRq to VMSS Instance with ID 2 to crash system
        text: >
            az serial-console send sysrq -n MyVMSS -g MyResourceGroup --instance-id 2 --input c
"""

helps['serial-console send reset'] = """
    type: command
    short-summary: Perform a "hard" restart of the VM or VMSS Instance
    long-summary: >
        This results in a "hard" restart, like powering the computer down, then back up again. This can result in data loss in the virtual machine. You should only perform this operation if a graceful restart is not effective.
    parameters:
      - name: --name -n
        short-summary: Name of the Virtual Machine or Virtual Machine Scale Set.
      - name: --resource-group -g
        short-summary: Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.
      - name: --instance-id
        short-summary: ID of VMSS instance. Not needed when connecting to the serialport of a Virtual Machine.
      - name: --subscription
        short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
    examples:
      - name: Hard reset a VM
        text: >
            az serial-console send reset -n MyVM -g MyResourceGroup
      - name: Hard rest a VMSS Instance with ID 2
        text: >
            az serial-console send reset -n MyVMSS -g MyResourceGroup --instance-id 2
"""
