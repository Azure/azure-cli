# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['migrate'] = """
    type: group
    short-summary: Manage Azure Migrate resources and operations.
    long-summary: |
        Commands to manage Azure Migrate projects,
        discover servers, and perform migrations
        to Azure and Azure Local/Stack HCI environments.
"""

helps['migrate local'] = """
    type: group
    short-summary: Manage Azure Local/Stack HCI migration operations.
    long-summary: |
        Commands to manage server discovery
        and replication for migrations to Azure Local
        and Azure Stack HCI environments.
        These commands support VMware and Hyper-V source
        environments.
"""

helps['migrate local get-discovered-server'] = """
    type: command
    short-summary: Retrieve discovered servers from an Azure Migrate project.
    long-summary: |
        Get information about servers discovered by Azure Migrate appliances.
        You can list all discovered servers in a project,
        filter by display name or machine type,
        or get a specific server by name.
        This command supports both VMware and Hyper-V environments.
    parameters:
        - name: --project-name
          short-summary: Name of the Azure Migrate project.
          long-summary: >
            The Azure Migrate project that contains
            the discovered servers.
        - name: --display-name
          short-summary: Display name of the source machine to filter by.
          long-summary: >
            Filter discovered servers by their display name
            (partial match supported).
        - name: --source-machine-type
          short-summary: Type of the source machine.
          long-summary: >
            Filter by source machine type. Valid values are
            'VMware' or 'HyperV'.
        - name: --subscription-id
          short-summary: Azure subscription ID.
          long-summary: >
            The subscription containing the Azure Migrate project.
            Uses the default subscription if not specified.
        - name: --name
          short-summary: Internal name of the specific source machine.
          long-summary: >
            The internal machine name assigned by Azure Migrate
            (different from display name).
        - name: --appliance-name
          short-summary: Name of the appliance (site) containing the machines.
          long-summary: >
            Filter servers discovered by
            a specific Azure Migrate appliance.
    examples:
        - name: List all discovered servers in a project
          text: |
            az migrate local get-discovered-server \\
                --project-name myMigrateProject \\
                --resource-group-name myRG
        - name: Get a specific discovered server by name
          text: |
            az migrate local get-discovered-server \\
                --project-name myMigrateProject \\
                --resource-group-name myRG \\
                --name machine-12345
        - name: Filter discovered servers by display name
          text: |
            az migrate local get-discovered-server \\
                --project-name myMigrateProject \\
                --resource-group-name myRG \\
                --display-name "web-server"
        - name: List VMware servers discovered by a specific appliance
          text: |
            az migrate local get-discovered-server \\
                --project-name myMigrateProject \\
                --resource-group-name myRG \\
                --appliance-name myVMwareAppliance \\
                --source-machine-type VMware
        - name: Get a specific server from a specific appliance
          text: |
            az migrate local get-discovered-server \\
                --project-name myMigrateProject \\
                --resource-group-name myRG \\
                --appliance-name myAppliance \\
                --name machine-12345 \\
                --source-machine-type HyperV
"""

helps['migrate local replication'] = """
    type: group
    short-summary: Manage replication for Azure Local/Stack HCI migrations.
    long-summary: |
        Commands to initialize replication infrastructure
        and create new server replications
        for migrations to Azure Local and Azure Stack HCI environments.
"""

helps['migrate local replication init'] = """
    type: command
    short-summary: Initialize Azure Migrate local replication infrastructure.
    long-summary: |
        Initialize the replication infrastructure required for
        migrating servers to Azure Local or Azure Stack HCI.
        This command sets up the necessary fabrics, policies, and mappings
        between source and target appliances.
        This is a prerequisite before creating any server replications.

        Note: This command uses a preview API version and
        may experience breaking changes in future releases.
    parameters:
        - name: --project-name
          short-summary: Name of the Azure Migrate project.
          long-summary: >
            The Azure Migrate project to be used
            for server migration.
        - name: --source-appliance-name
          short-summary: Source appliance name.
          long-summary: >
            Name of the Azure Migrate appliance that
            discovered the source servers.
        - name: --target-appliance-name
          short-summary: Target appliance name.
          long-summary: >
            Name of the Azure Local appliance that
            will host the migrated servers.
        - name: --subscription-id
          short-summary: Azure subscription ID.
          long-summary: >
            The subscription containing the Azure Migrate project.
            Uses the current subscription if not specified.
        - name: --pass-thru
          short-summary: Return true when the command succeeds.
          long-summary: >
            When enabled, returns a boolean value
            indicating successful completion.
    examples:
        - name: Initialize replication infrastructure
          text: |
            az migrate local replication init \\
                --resource-group-name myRG \\
                --project-name myMigrateProject \\
                --source-appliance-name myVMwareAppliance \\
                --target-appliance-name myAzStackHCIAppliance
        - name: Initialize and return success status
          text: |
            az migrate local replication init \\
                --resource-group-name myRG \\
                --project-name myMigrateProject \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --pass-thru
"""

helps['migrate local replication new'] = """
    type: command
    short-summary: Create a new replication for an Azure Local server.
    long-summary: |
        Create a new replication to migrate a discovered server to Azure Local.
        You can specify the source machine either
        by its ARM resource ID or by selecting it from
        a numbered list of discovered servers.

        The command supports two modes:
        - Default User Mode: Specify os-disk-id and target-virtual-switch-id
        - Power User Mode: Specify disk-to-include and nic-to-include

        Note: This command uses a preview API version
        and may experience breaking changes in
        future releases.
    parameters:
        - name: --machine-id
          short-summary: ARM resource ID of the discovered server to migrate.
          long-summary: >
            Full ARM resource ID of the discovered machine.
            Required if --machine-index is not provided.
        - name: --machine-index
          short-summary: Index of the discovered server from the list
          long-summary: >
            Select a server by its position
            in the discovered servers list.
            Required if --machine-id is not provided.
        - name: --project-name
          short-summary: Name of the Azure Migrate project.
          long-summary: >
            Required when using --machine-index
            to identify which project to query.
        - name: --target-storage-path-id
          short-summary: Storage path ARM ID where VMs will be stored.
          long-summary: >
            Full ARM resource ID of the storage path
            on the target Azure Local cluster.
        - name: --target-vm-cpu-core
          short-summary: Number of CPU cores for the target VM.
          long-summary: >
            Specify the number of CPU cores
            to allocate to the migrated VM.
        - name: --target-vm-ram
          short-summary: Target RAM size in MB.
          long-summary: >
            Specify the amount of RAM to
            allocate to the target VM in megabytes.
        - name: --disk-to-include
          short-summary: Disks to include for replication (power user mode).
          long-summary: >
            Space-separated list of disk IDs
            to replicate from the source server.
            Use this for power user mode.
        - name: --nic-to-include
          short-summary: NICs to include for replication (power user mode).
          long-summary: >
            Space-separated list of NIC IDs
            to replicate from the source server.
            Use this for power user mode.
        - name: --vm-name
          short-summary: Name of the VM to be created.
          long-summary: >
            The name for the virtual machine
            that will be created on the target environment.
        - name: --os-disk-id
          short-summary: Operating system disk ID.
          long-summary: >
            ID of the operating system disk for
            the source server. Required for default user mode.
        - name: --source-appliance-name
          short-summary: Source appliance name.
          long-summary: >
            Name of the Azure Migrate appliance
            that discovered the source server.
        - name: --target-appliance-name
          short-summary: Target appliance name.
          long-summary: >
            Name of the Azure Local appliance
            that will host the migrated server.
        - name: --subscription-id
          short-summary: Azure subscription ID.
          long-summary: >
            The subscription to use.
            Uses the current subscription if not specified.
    examples:
        - name: Create replication using machine ARM ID (default user mode)
          text: |
            az migrate local replication new \\
                --machine-id "XXXX" \\
                --target-storage-path-id "YYYY" \\
                --target-resource-group-id "ZZZZ" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name myVMwareAppliance \\
                --target-appliance-name myAzStackHCIAppliance \\
                --target-virtual-switch-id "XYXY" \\
                --os-disk-id "disk-0"
        - name: Create replication using machine index (power user mode)
          text: |
            az migrate local replication new \\
                --machine-index 1 \\
                --project-name myMigrateProject \\
                --resource-group-name myRG \\
                --target-storage-path-id "XZXZ" \\
                --target-resource-group-id "YZYZ" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --disk-to-include "disk-0" "disk-1" \\
                --nic-to-include "nic-0"
        - name: Create replication with custom CPU and RAM settings
          text: |
            az migrate local replication new \\
                --machine-id "XXXX" \\
                --target-storage-path-id "YYYY" \\
                --target-resource-group-id "ZZZZ" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --target-virtual-switch-id "XYXY" \\
                --os-disk-id "disk-0" \\
                --target-vm-cpu-core 4 \\
                --target-vm-ram 8192 \\
                --is-dynamic-memory-enabled false
        - name: Create replication with test virtual switch
          text: |
            az migrate local replication new \\
                --machine-id "XXXX" \\
                --target-storage-path-id "YYYY" \\
                --target-resource-group-id "ZZZZ" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --target-virtual-switch-id "XYXY" \\
                --target-test-virtual-switch-id "XYXY" \\
                --os-disk-id "disk-0"
"""
