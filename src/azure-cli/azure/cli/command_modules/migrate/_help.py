# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['migrate'] = """
    type: group
    short-summary: Manage Azure Migrate resources and operations.
    long-summary: |
        Commands to manage Azure Migrate projects, discover servers, and perform migrations
        to Azure and Azure Local/Stack HCI environments.
"""

helps['migrate local'] = """
    type: group
    short-summary: Manage Azure Local/Stack HCI migration operations.
    long-summary: |
        Commands to manage server discovery and replication for migrations to Azure Local
        and Azure Stack HCI environments. These commands support VMware and Hyper-V source
        environments.
"""

helps['migrate local get-discovered-server'] = """
    type: command
    short-summary: Retrieve discovered servers from an Azure Migrate project.
    long-summary: |
        Get information about servers discovered by Azure Migrate appliances. You can list all
        discovered servers in a project, filter by display name or machine type, or get a
        specific server by name. This command supports both VMware and Hyper-V environments.
    parameters:
        - name: --project-name
          short-summary: Name of the Azure Migrate project.
          long-summary: The Azure Migrate project that contains the discovered servers.
        - name: --resource-group-name --resource-group -g
          short-summary: Name of the resource group containing the Azure Migrate project.
        - name: --display-name
          short-summary: Display name of the source machine to filter by.
          long-summary: Filter discovered servers by their display name (partial match supported).
        - name: --source-machine-type
          short-summary: Type of the source machine.
          long-summary: Filter by source machine type. Valid values are 'VMware' or 'HyperV'.
        - name: --subscription-id
          short-summary: Azure subscription ID.
          long-summary: The subscription containing the Azure Migrate project. Uses the default subscription if not specified.
        - name: --name
          short-summary: Internal name of the specific source machine to retrieve.
          long-summary: The internal machine name assigned by Azure Migrate (different from display name).
        - name: --appliance-name
          short-summary: Name of the appliance (site) containing the machines.
          long-summary: Filter servers discovered by a specific Azure Migrate appliance.
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
        Commands to initialize replication infrastructure and create new server replications
        for migrations to Azure Local and Azure Stack HCI environments.
"""

helps['migrate local replication init'] = """
    type: command
    short-summary: Initialize Azure Migrate local replication infrastructure.
    long-summary: |
        Initialize the replication infrastructure required for migrating servers to Azure Local
        or Azure Stack HCI. This command sets up the necessary fabrics, policies, and mappings
        between source and target appliances. This is a prerequisite before creating any server
        replications.
        
        Note: This command uses a preview API version and may experience breaking changes in
        future releases.
    parameters:
        - name: --resource-group-name --resource-group -g
          short-summary: Resource group of the Azure Migrate project.
          long-summary: The resource group containing the Azure Migrate project and related resources.
        - name: --project-name
          short-summary: Name of the Azure Migrate project.
          long-summary: The Azure Migrate project to be used for server migration.
        - name: --source-appliance-name
          short-summary: Source appliance name.
          long-summary: Name of the Azure Migrate appliance that discovered the source servers.
        - name: --target-appliance-name
          short-summary: Target appliance name.
          long-summary: Name of the Azure Local or Azure Stack HCI appliance that will host the migrated servers.
        - name: --cache-storage-account-id
          short-summary: Storage account ARM ID for private endpoint scenario.
          long-summary: Full ARM resource ID of the storage account to use for caching replication data in private endpoint scenarios.
        - name: --subscription-id
          short-summary: Azure subscription ID.
          long-summary: The subscription containing the Azure Migrate project. Uses the current subscription if not specified.
        - name: --pass-thru
          short-summary: Return true when the command succeeds.
          long-summary: When enabled, returns a boolean value indicating successful completion.
    examples:
        - name: Initialize replication infrastructure for VMware to Azure Stack HCI migration
          text: |
            az migrate local replication init \\
                --resource-group-name myRG \\
                --project-name myMigrateProject \\
                --source-appliance-name myVMwareAppliance \\
                --target-appliance-name myAzStackHCIAppliance
        - name: Initialize with a specific storage account for private endpoint
          text: |
            az migrate local replication init \\
                --resource-group-name myRG \\
                --project-name myMigrateProject \\
                --source-appliance-name myVMwareAppliance \\
                --target-appliance-name myAzStackHCIAppliance \\
                --cache-storage-account-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.Storage/storageAccounts/mycachestorage"
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
        Create a new replication to migrate a discovered server to Azure Local or Azure Stack HCI.
        You can specify the source machine either by its ARM resource ID or by selecting it from
        a numbered list of discovered servers.
        
        The command supports two modes:
        - Default User Mode: Specify os-disk-id and target-virtual-switch-id for simplified configuration
        - Power User Mode: Specify disk-to-include and nic-to-include for advanced control over which resources to replicate
        
        Note: This command uses a preview API version and may experience breaking changes in
        future releases.
    parameters:
        - name: --machine-id
          short-summary: ARM resource ID of the discovered server to migrate.
          long-summary: Full ARM resource ID of the discovered machine. Required if --machine-index is not provided.
        - name: --machine-index
          short-summary: Index of the discovered server from the list (1-based).
          long-summary: Select a server by its position in the discovered servers list. Required if --machine-id is not provided.
        - name: --project-name
          short-summary: Name of the Azure Migrate project.
          long-summary: Required when using --machine-index to identify which project to query.
        - name: --resource-group-name --resource-group -g
          short-summary: Resource group containing the Azure Migrate project.
          long-summary: Required when using --machine-index.
        - name: --target-storage-path-id
          short-summary: Storage path ARM ID where VMs will be stored.
          long-summary: Full ARM resource ID of the storage path on the target Azure Local or Azure Stack HCI cluster.
        - name: --target-vm-cpu-core
          short-summary: Number of CPU cores for the target VM.
          long-summary: Specify the number of CPU cores to allocate to the migrated VM.
        - name: --target-virtual-switch-id
          short-summary: Logical network ARM ID for VM connectivity.
          long-summary: Full ARM resource ID of the logical network (virtual switch) that the migrated VM will use. Required for default user mode.
        - name: --target-test-virtual-switch-id
          short-summary: Test logical network ARM ID.
          long-summary: Full ARM resource ID of the test logical network for test failover scenarios.
        - name: --is-dynamic-memory-enabled
          short-summary: Enable or disable dynamic memory.
          long-summary: Specify 'true' to enable dynamic memory or 'false' for static memory allocation.
        - name: --target-vm-ram
          short-summary: Target RAM size in MB.
          long-summary: Specify the amount of RAM to allocate to the target VM in megabytes.
        - name: --disk-to-include
          short-summary: Disks to include for replication (power user mode).
          long-summary: Space-separated list of disk IDs to replicate from the source server. Use this for power user mode.
        - name: --nic-to-include
          short-summary: NICs to include for replication (power user mode).
          long-summary: Space-separated list of NIC IDs to replicate from the source server. Use this for power user mode.
        - name: --target-resource-group-id
          short-summary: Target resource group ARM ID.
          long-summary: Full ARM resource ID of the resource group where migrated VM resources will be created.
        - name: --target-vm-name
          short-summary: Name of the VM to be created.
          long-summary: The name for the virtual machine that will be created on the target environment.
        - name: --os-disk-id
          short-summary: Operating system disk ID.
          long-summary: ID of the operating system disk for the source server. Required for default user mode.
        - name: --source-appliance-name
          short-summary: Source appliance name.
          long-summary: Name of the Azure Migrate appliance that discovered the source server.
        - name: --target-appliance-name
          short-summary: Target appliance name.
          long-summary: Name of the Azure Local or Azure Stack HCI appliance that will host the migrated server.
        - name: --subscription-id
          short-summary: Azure subscription ID.
          long-summary: The subscription to use. Uses the current subscription if not specified.
    examples:
        - name: Create replication using machine ARM ID (default user mode)
          text: |
            az migrate local replication new \\
                --machine-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.Migrate/migrateprojects/myProject/machines/machine-12345" \\
                --target-storage-path-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/storageContainers/myStorage" \\
                --target-resource-group-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myTargetRG" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name myVMwareAppliance \\
                --target-appliance-name myAzStackHCIAppliance \\
                --target-virtual-switch-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/logicalNetworks/myNetwork" \\
                --os-disk-id "disk-0"
        - name: Create replication using machine index (power user mode)
          text: |
            az migrate local replication new \\
                --machine-index 1 \\
                --project-name myMigrateProject \\
                --resource-group-name myRG \\
                --target-storage-path-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/storageContainers/myStorage" \\
                --target-resource-group-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myTargetRG" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --disk-to-include "disk-0" "disk-1" \\
                --nic-to-include "nic-0"
        - name: Create replication with custom CPU and RAM settings
          text: |
            az migrate local replication new \\
                --machine-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.Migrate/migrateprojects/myProject/machines/machine-12345" \\
                --target-storage-path-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/storageContainers/myStorage" \\
                --target-resource-group-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myTargetRG" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --target-virtual-switch-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/logicalNetworks/myNetwork" \\
                --os-disk-id "disk-0" \\
                --target-vm-cpu-core 4 \\
                --target-vm-ram 8192 \\
                --is-dynamic-memory-enabled false
        - name: Create replication with test virtual switch
          text: |
            az migrate local replication new \\
                --machine-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.Migrate/migrateprojects/myProject/machines/machine-12345" \\
                --target-storage-path-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/storageContainers/myStorage" \\
                --target-resource-group-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myTargetRG" \\
                --target-vm-name migratedVM01 \\
                --source-appliance-name mySourceAppliance \\
                --target-appliance-name myTargetAppliance \\
                --target-virtual-switch-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/logicalNetworks/myProdNetwork" \\
                --target-test-virtual-switch-id "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/myRG/providers/Microsoft.AzureStackHCI/logicalNetworks/myTestNetwork" \\
                --os-disk-id "disk-0"
"""

def new_local_server_replication(cmd,
                                 target_storage_path_id,
                                 target_resource_group_id,
                                 target_vm_name,
                                 source_appliance_name,
                                 target_appliance_name,
                                 machine_id=None,
                                 machine_index=None,
                                 project_name=None,
                                 resource_group_name=None,
                                 target_vm_cpu_core=None,
                                 target_virtual_switch_id=None,
                                 target_test_virtual_switch_id=None,
                                 is_dynamic_memory_enabled=None,
                                 target_vm_ram=None,
                                 disk_to_include=None,
                                 nic_to_include=None,
                                 os_disk_id=None,
                                 subscription_id=None):
    """
    Create a new replication for an Azure Local server.
    
    This cmdlet is based on a preview API version and may experience breaking changes in future releases.
    
    Args:
        cmd: The CLI command context
        target_storage_path_id (str): Specifies the storage path ARM ID where the VMs will be stored (required)
        target_resource_group_id (str): Specifies the target resource group ARM ID where the migrated VM resources will reside (required)
        target_vm_name (str): Specifies the name of the VM to be created (required)
        source_appliance_name (str): Specifies the source appliance name for the AzLocal scenario (required)
        target_appliance_name (str): Specifies the target appliance name for the AzLocal scenario (required)
        machine_id (str, optional): Specifies the machine ARM ID of the discovered server to be migrated (required if machine_index not provided)
        machine_index (int, optional): Specifies the index of the discovered server from the list (1-based, required if machine_id not provided)
        project_name (str, optional): Specifies the migrate project name (required when using machine_index)
        resource_group_name (str, optional): Specifies the resource group name (required when using machine_index)
        target_vm_cpu_core (int, optional): Specifies the number of CPU cores
        target_virtual_switch_id (str, optional): Specifies the logical network ARM ID that the VMs will use (required for default user mode)
        target_test_virtual_switch_id (str, optional): Specifies the test logical network ARM ID that the VMs will use
        is_dynamic_memory_enabled (str, optional): Specifies if RAM is dynamic or not. Valid values: 'true', 'false'
        target_vm_ram (int, optional): Specifies the target RAM size in MB
        disk_to_include (list, optional): Specifies the disks on the source server to be included for replication (power user mode)
        nic_to_include (list, optional): Specifies the NICs on the source server to be included for replication (power user mode)
        os_disk_id (str, optional): Specifies the operating system disk for the source server to be migrated (required for default user mode)
        subscription_id (str, optional): Azure Subscription ID. Uses current subscription if not provided
    
    Returns:
        dict: The job model from the API response
    
    Raises:
        CLIError: If required parameters are missing or validation fails
    """
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.command_modules.migrate._helpers import (
        send_get_request,
        get_resource_by_id,
        create_or_update_resource,
        APIVersion,
        ProvisioningState,
        AzLocalInstanceTypes,
        FabricInstanceTypes,
        SiteTypes,
        VMNicSelection,
        validate_arm_id_format,
        IdFormats
    )
    import re
    
    # Validate that either machine_id or machine_index is provided, but not both
    if not machine_id and not machine_index:
        raise CLIError("Either machine_id or machine_index must be provided.")
    if machine_id and machine_index:
        raise CLIError("Only one of machine_id or machine_index should be provided, not both.")
    
    if not subscription_id:
        subscription_id = get_subscription_id(cmd.cli_ctx)
    
    if machine_index:
        if not project_name:
            raise CLIError("project_name is required when using machine_index.")
        if not resource_group_name:
            raise CLIError("resource_group_name is required when using machine_index.")
        
        if not isinstance(machine_index, int) or machine_index < 1:
            raise CLIError("machine_index must be a positive integer (1-based index).")
                
        rg_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
        discovery_solution_name = "Servers-Discovery-ServerDiscovery"
        discovery_solution_uri = f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/{project_name}/solutions/{discovery_solution_name}"
        discovery_solution = get_resource_by_id(cmd, discovery_solution_uri, APIVersion.Microsoft_Migrate.value)
        
        if not discovery_solution:
            raise CLIError(f"Server Discovery Solution '{discovery_solution_name}' not found in project '{project_name}'.")
        
        # Get appliance mapping to determine site type
        app_map = {}
        extended_details = discovery_solution.get('properties', {}).get('details', {}).get('extendedDetails', {})
        
        # Process applianceNameToSiteIdMapV2 and V3
        if 'applianceNameToSiteIdMapV2' in extended_details:
            try:
                app_map_v2 = json.loads(extended_details['applianceNameToSiteIdMapV2'])
                if isinstance(app_map_v2, list):
                    for item in app_map_v2:
                        if isinstance(item, dict) and 'ApplianceName' in item and 'SiteId' in item:
                            # Store both lowercase and original case
                            app_map[item['ApplianceName'].lower()] = item['SiteId']
                            app_map[item['ApplianceName']] = item['SiteId']
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        if 'applianceNameToSiteIdMapV3' in extended_details:
            try:
                app_map_v3 = json.loads(extended_details['applianceNameToSiteIdMapV3'])
                if isinstance(app_map_v3, dict):
                    for appliance_name_key, site_info in app_map_v3.items():
                        if isinstance(site_info, dict) and 'SiteId' in site_info:
                            app_map[appliance_name_key.lower()] = site_info['SiteId']
                            app_map[appliance_name_key] = site_info['SiteId']
                        elif isinstance(site_info, str):
                            app_map[appliance_name_key.lower()] = site_info
                            app_map[appliance_name_key] = site_info
                elif isinstance(app_map_v3, list):
                    # V3 might also be in list format
                    for item in app_map_v3:
                        if isinstance(item, dict):
                            # Check if it has ApplianceName/SiteId structure
                            if 'ApplianceName' in item and 'SiteId' in item:
                                app_map[item['ApplianceName'].lower()] = item['SiteId']
                                app_map[item['ApplianceName']] = item['SiteId']
                            else:
                                # Or it might be a single key-value pair
                                for key, value in item.items():
                                    if isinstance(value, dict) and 'SiteId' in value:
                                        app_map[key.lower()] = value['SiteId']
                                        app_map[key] = value['SiteId']
                                    elif isinstance(value, str):
                                        app_map[key.lower()] = value
                                        app_map[key] = value
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                pass
        
        # Get source site ID - try both original and lowercase
        source_site_id = app_map.get(source_appliance_name) or app_map.get(source_appliance_name.lower())
        if not source_site_id:
            raise CLIError(f"Source appliance '{source_appliance_name}' not found in discovery solution.")
        
        # Determine site type from source site ID
        hyperv_site_pattern = "/Microsoft.OffAzure/HyperVSites/"
        vmware_site_pattern = "/Microsoft.OffAzure/VMwareSites/"
        
        if hyperv_site_pattern in source_site_id:
            site_name = source_site_id.split('/')[-1]
            machines_uri = f"{rg_uri}/providers/Microsoft.OffAzure/HyperVSites/{site_name}/machines"
        elif vmware_site_pattern in source_site_id:
            site_name = source_site_id.split('/')[-1]
            machines_uri = f"{rg_uri}/providers/Microsoft.OffAzure/VMwareSites/{site_name}/machines"
        else:
            raise CLIError(f"Unable to determine site type for source appliance '{source_appliance_name}'.")
        
        # Get all machines from the site
        request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + f"{machines_uri}?api-version={APIVersion.Microsoft_OffAzure.value}"
        
        response = send_get_request(cmd, request_uri)
        machines_data = response.json()
        machines = machines_data.get('value', [])
        
        # Fetch all pages if there are more
        while machines_data.get('nextLink'):
            response = send_get_request(cmd, machines_data.get('nextLink'))
            machines_data = response.json()
            machines.extend(machines_data.get('value', []))
        
        # Check if the index is valid
        if machine_index > len(machines):
            raise CLIError(f"Invalid machine_index {machine_index}. Only {len(machines)} machines found in site '{site_name}'.")
        
        # Get the machine at the specified index (convert 1-based to 0-based)
        selected_machine = machines[machine_index - 1]
        machine_id = selected_machine.get('id')
                
        # Extract machine name for logging
        machine_name_from_index = selected_machine.get('name', 'Unknown')
        properties = selected_machine.get('properties', {})
        display_name = properties.get('displayName', machine_name_from_index)
        
    
    # Validate required parameters
    if not machine_id:
        raise CLIError("machine_id could not be determined.")
    if not target_storage_path_id:
        raise CLIError("target_storage_path_id is required.")
    if not target_resource_group_id:
        raise CLIError("target_resource_group_id is required.")
    if not target_vm_name:
        raise CLIError("target_vm_name is required.")
    if not source_appliance_name:
        raise CLIError("source_appliance_name is required.")
    if not target_appliance_name:
        raise CLIError("target_appliance_name is required.")
    
    # Validate parameter set requirements
    is_power_user_mode = disk_to_include is not None or nic_to_include is not None
    is_default_user_mode = target_virtual_switch_id is not None or os_disk_id is not None
    
    if is_power_user_mode and is_default_user_mode:
        raise CLIError("Cannot mix default user mode parameters (target_virtual_switch_id, os_disk_id) with power user mode parameters (disk_to_include, nic_to_include).")
    
    if is_power_user_mode:
        # Power user mode validation
        if not disk_to_include:
            raise CLIError("disk_to_include is required when using power user mode.")
        if not nic_to_include:
            raise CLIError("nic_to_include is required when using power user mode.")
    else:
        # Default user mode validation
        if not target_virtual_switch_id:
            raise CLIError("target_virtual_switch_id is required when using default user mode.")
        if not os_disk_id:
            raise CLIError("os_disk_id is required when using default user mode.")
    
    is_dynamic_ram_enabled = None
    if is_dynamic_memory_enabled:
        if is_dynamic_memory_enabled not in ['true', 'false']:
            raise CLIError("is_dynamic_memory_enabled must be either 'true' or 'false'.")
        is_dynamic_ram_enabled = is_dynamic_memory_enabled == 'true'
    
    try:
        # Validate ARM ID formats
        if not validate_arm_id_format(machine_id, IdFormats.MachineArmIdTemplate):
            raise CLIError(f"Invalid -machine_id '{machine_id}'. A valid machine ARM ID should follow the format '{IdFormats.MachineArmIdTemplate}'.")
        
        if not validate_arm_id_format(target_storage_path_id, IdFormats.StoragePathArmIdTemplate):
            raise CLIError(f"Invalid -target_storage_path_id '{target_storage_path_id}'. A valid storage path ARM ID should follow the format '{IdFormats.StoragePathArmIdTemplate}'.")
        
        if not validate_arm_id_format(target_resource_group_id, IdFormats.ResourceGroupArmIdTemplate):
            raise CLIError(f"Invalid -target_resource_group_id '{target_resource_group_id}'. A valid resource group ARM ID should follow the format '{IdFormats.ResourceGroupArmIdTemplate}'.")
        
        if target_virtual_switch_id and not validate_arm_id_format(target_virtual_switch_id, IdFormats.LogicalNetworkArmIdTemplate):
            raise CLIError(f"Invalid -target_virtual_switch_id '{target_virtual_switch_id}'. A valid logical network ARM ID should follow the format '{IdFormats.LogicalNetworkArmIdTemplate}'.")
        
        if target_test_virtual_switch_id and not validate_arm_id_format(target_test_virtual_switch_id, IdFormats.LogicalNetworkArmIdTemplate):
            raise CLIError(f"Invalid -target_test_virtual_switch_id '{target_test_virtual_switch_id}'. A valid logical network ARM ID should follow the format '{IdFormats.LogicalNetworkArmIdTemplate}'.")
        
        machine_id_parts = machine_id.split("/")
        if len(machine_id_parts) < 11:
            raise CLIError(f"Invalid machine ARM ID format: '{machine_id}'")
        
        if not resource_group_name:
            resource_group_name = machine_id_parts[4]
        site_type = machine_id_parts[7]
        site_name = machine_id_parts[8]
        machine_name = machine_id_parts[10]
        
        run_as_account_id = None
        instance_type = None
        
        if site_type == SiteTypes.HyperVSites.value:
            instance_type = AzLocalInstanceTypes.HyperVToAzLocal.value
            
            # Get HyperV machine
            machine_uri = f"{rg_uri}/providers/Microsoft.OffAzure/HyperVSites/{site_name}/machines/{machine_name}"
            machine = get_resource_by_id(cmd, machine_uri, APIVersion.Microsoft_OffAzure.value)
            if not machine:
                raise CLIError(f"Machine '{machine_name}' not found in resource group '{resource_group_name}' and site '{site_name}'.")
            
            # Get HyperV site
            site_uri = f"{rg_uri}/providers/Microsoft.OffAzure/HyperVSites/{site_name}"
            site_object = get_resource_by_id(cmd, site_uri, APIVersion.Microsoft_OffAzure.value)
            if not site_object:
                raise CLIError(f"Machine site '{site_name}' with Type '{site_type}' not found.")
            
            # Get RunAsAccount
            properties = machine.get('properties', {})
            if properties.get('hostId'):
                # Machine is on a single HyperV host
                host_id_parts = properties['hostId'].split("/")
                if len(host_id_parts) < 11:
                    raise CLIError(f"Invalid Hyper-V Host ARM ID '{properties['hostId']}'")
                
                host_resource_group = host_id_parts[4]
                host_site_name = host_id_parts[8]
                host_name = host_id_parts[10]
                
                host_uri = f"/subscriptions/{subscription_id}/resourceGroups/{host_resource_group}/providers/Microsoft.OffAzure/HyperVSites/{host_site_name}/hosts/{host_name}"
                hyperv_host = get_resource_by_id(cmd, host_uri, APIVersion.Microsoft_OffAzure.value)
                if not hyperv_host:
                    raise CLIError(f"Hyper-V host '{host_name}' not found in resource group '{host_resource_group}' and site '{host_site_name}'.")
                
                run_as_account_id = hyperv_host.get('properties', {}).get('runAsAccountId')
            
            elif properties.get('clusterId'):
                # Machine is on a HyperV cluster
                cluster_id_parts = properties['clusterId'].split("/")
                if len(cluster_id_parts) < 11:
                    raise CLIError(f"Invalid Hyper-V Cluster ARM ID '{properties['clusterId']}'")
                
                cluster_resource_group = cluster_id_parts[4]
                cluster_site_name = cluster_id_parts[8]
                cluster_name = cluster_id_parts[10]
                
                cluster_uri = f"/subscriptions/{subscription_id}/resourceGroups/{cluster_resource_group}/providers/Microsoft.OffAzure/HyperVSites/{cluster_site_name}/clusters/{cluster_name}"
                hyperv_cluster = get_resource_by_id(cmd, cluster_uri, APIVersion.Microsoft_OffAzure.value)
                if not hyperv_cluster:
                    raise CLIError(f"Hyper-V cluster '{cluster_name}' not found in resource group '{cluster_resource_group}' and site '{cluster_site_name}'.")
                
                run_as_account_id = hyperv_cluster.get('properties', {}).get('runAsAccountId')
        
        elif site_type == SiteTypes.VMwareSites.value:
            instance_type = AzLocalInstanceTypes.VMwareToAzLocal.value
            
            # Get VMware machine
            machine_uri = f"{rg_uri}/providers/Microsoft.OffAzure/VMwareSites/{site_name}/machines/{machine_name}"
            machine = get_resource_by_id(cmd, machine_uri, APIVersion.Microsoft_OffAzure.value)
            if not machine:
                raise CLIError(f"Machine '{machine_name}' not found in resource group '{resource_group_name}' and site '{site_name}'.")
            
            # Get VMware site
            site_uri = f"{rg_uri}/providers/Microsoft.OffAzure/VMwareSites/{site_name}"
            site_object = get_resource_by_id(cmd, site_uri, APIVersion.Microsoft_OffAzure.value)
            if not site_object:
                raise CLIError(f"Machine site '{site_name}' with Type '{site_type}' not found.")
            
            # Get RunAsAccount
            properties = machine.get('properties', {})
            if properties.get('vCenterId'):
                vcenter_id_parts = properties['vCenterId'].split("/")
                if len(vcenter_id_parts) < 11:
                    raise CLIError(f"Invalid VMware vCenter ARM ID '{properties['vCenterId']}'")
                
                vcenter_resource_group = vcenter_id_parts[4]
                vcenter_site_name = vcenter_id_parts[8]
                vcenter_name = vcenter_id_parts[10]
                
                vcenter_uri = f"/subscriptions/{subscription_id}/resourceGroups/{vcenter_resource_group}/providers/Microsoft.OffAzure/VMwareSites/{vcenter_site_name}/vCenters/{vcenter_name}"
                vmware_vcenter = get_resource_by_id(cmd, vcenter_uri, APIVersion.Microsoft_OffAzure.value)
                if not vmware_vcenter:
                    raise CLIError(f"VMware vCenter '{vcenter_name}' not found in resource group '{vcenter_resource_group}' and site '{vcenter_site_name}'.")
                
                run_as_account_id = vmware_vcenter.get('properties', {}).get('runAsAccountId')
        
        else:
            raise CLIError(f"Site type of '{site_type}' in -machine_id is not supported. Only '{SiteTypes.HyperVSites.value}' and '{SiteTypes.VMwareSites.value}' are supported.")
        
        if not run_as_account_id:
            raise CLIError(f"Unable to determine RunAsAccount for site '{site_name}' from machine '{machine_name}'. Please verify your appliance setup and provided -machine_id.")
        
        # Validate the VM for replication
        machine_props = machine.get('properties', {})
        if machine_props.get('isDeleted'):
            raise CLIError(f"Cannot migrate machine '{machine_name}' as it is marked as deleted.")
        
        # Get project name from site
        discovery_solution_id = site_object.get('properties', {}).get('discoverySolutionId', '')
        if not discovery_solution_id:
            raise CLIError("Unable to determine project from site. Invalid site configuration.")
        
        if not project_name:
            project_name = discovery_solution_id.split("/")[8]
        
        # Get the migrate project resource
        migrate_project_uri = f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/{project_name}"
        migrate_project = get_resource_by_id(cmd, migrate_project_uri, APIVersion.Microsoft_Migrate.value)
        if not migrate_project:
            raise CLIError(f"Migrate project '{project_name}' not found.")
        
        # Get Data Replication Service (AMH solution)
        amh_solution_name = "Servers-Migration-ServerMigration_DataReplication"
        amh_solution_uri = f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/{project_name}/solutions/{amh_solution_name}"
        amh_solution = get_resource_by_id(cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value)
        if not amh_solution:
            raise CLIError(f"No Data Replication Service Solution '{amh_solution_name}' found in resource group '{resource_group_name}' and project '{project_name}'. Please verify your appliance setup.")
        
        # Validate replication vault
        vault_id = amh_solution.get('properties', {}).get('details', {}).get('extendedDetails', {}).get('vaultId')
        if not vault_id:
            raise CLIError("No Replication Vault found. Please verify your Azure Migrate project setup.")
        
        replication_vault_name = vault_id.split("/")[8]
        replication_vault = get_resource_by_id(cmd, vault_id, APIVersion.Microsoft_DataReplication.value)
        if not replication_vault:
            raise CLIError(f"No Replication Vault '{replication_vault_name}' found in Resource Group '{resource_group_name}'. Please verify your Azure Migrate project setup.")
        
        if replication_vault.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"The Replication Vault '{replication_vault_name}' is not in a valid state. The provisioning state is '{replication_vault.get('properties', {}).get('provisioningState')}'. Please verify your Azure Migrate project setup.")
        
        # Validate Policy
        policy_name = f"{replication_vault_name}{instance_type}policy"
        policy_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationPolicies/{policy_name}"
        policy = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
        
        if not policy:
            raise CLIError(f"The replication policy '{policy_name}' not found. The replication infrastructure is not initialized. Run the 'az migrate local-replication-infrastructure initialize' command.")
        if policy.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"The replication policy '{policy_name}' is not in a valid state. The provisioning state is '{policy.get('properties', {}).get('provisioningState')}'. Re-run the 'az migrate local-replication-infrastructure initialize' command.")
        
        # Access Discovery Solution to get appliance mapping
        discovery_solution_name = "Servers-Discovery-ServerDiscovery"
        discovery_solution_uri = f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/{project_name}/solutions/{discovery_solution_name}"
        discovery_solution = get_resource_by_id(cmd, discovery_solution_uri, APIVersion.Microsoft_Migrate.value)
        
        if not discovery_solution:
            raise CLIError(f"Server Discovery Solution '{discovery_solution_name}' not found.")
        
        # Get Appliances Mapping
        app_map = {}
        extended_details = discovery_solution.get('properties', {}).get('details', {}).get('extendedDetails', {})
        
        # Process applianceNameToSiteIdMapV2
        if 'applianceNameToSiteIdMapV2' in extended_details:
            try:
                app_map_v2 = json.loads(extended_details['applianceNameToSiteIdMapV2'])
                if isinstance(app_map_v2, list):
                    for item in app_map_v2:
                        if isinstance(item, dict) and 'ApplianceName' in item and 'SiteId' in item:
                            app_map[item['ApplianceName'].lower()] = item['SiteId']
                            app_map[item['ApplianceName']] = item['SiteId']
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse applianceNameToSiteIdMapV2: {str(e)}")
        
        # Process applianceNameToSiteIdMapV3
        if 'applianceNameToSiteIdMapV3' in extended_details:
            try:
                app_map_v3 = json.loads(extended_details['applianceNameToSiteIdMapV3'])
                if isinstance(app_map_v3, dict):
                    for appliance_name_key, site_info in app_map_v3.items():
                        if isinstance(site_info, dict) and 'SiteId' in site_info:
                            app_map[appliance_name_key.lower()] = site_info['SiteId']
                            app_map[appliance_name_key] = site_info['SiteId']
                        elif isinstance(site_info, str):
                            app_map[appliance_name_key.lower()] = site_info
                            app_map[appliance_name_key] = site_info
                elif isinstance(app_map_v3, list):
                    # V3 might also be in list format
                    for item in app_map_v3:
                        if isinstance(item, dict):
                            # Check if it has ApplianceName/SiteId structure
                            if 'ApplianceName' in item and 'SiteId' in item:
                                app_map[item['ApplianceName'].lower()] = item['SiteId']
                                app_map[item['ApplianceName']] = item['SiteId']
                            else:
                                # Or it might be a single key-value pair
                                for key, value in item.items():
                                    if isinstance(value, dict) and 'SiteId' in value:
                                        app_map[key.lower()] = value['SiteId']
                                        app_map[key] = value['SiteId']
                                    elif isinstance(value, str):
                                        app_map[key.lower()] = value
                                        app_map[key] = value
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse applianceNameToSiteIdMapV3: {str(e)}")
        
        if not app_map:
            raise CLIError("Server Discovery Solution missing Appliance Details. Invalid Solution.")
        
        source_site_id = app_map.get(source_appliance_name) or app_map.get(source_appliance_name.lower())
        target_site_id = app_map.get(target_appliance_name) or app_map.get(target_appliance_name.lower())
        
        if not source_site_id:
            available_appliances = list(set(k for k in app_map.keys() if not k.islower()))
            if not available_appliances:
                available_appliances = list(set(app_map.keys()))
            raise CLIError(f"Source appliance '{source_appliance_name}' not found in discovery solution. Available appliances: {', '.join(available_appliances)}")
        
        if not target_site_id:
            available_appliances = list(set(k for k in app_map.keys() if not k.islower()))
            if not available_appliances:
                available_appliances = list(set(app_map.keys()))
            raise CLIError(f"Target appliance '{target_appliance_name}' not found in discovery solution. Available appliances: {', '.join(available_appliances)}")
        
        # Determine instance types based on site IDs
        hyperv_site_pattern = "/Microsoft.OffAzure/HyperVSites/"
        vmware_site_pattern = "/Microsoft.OffAzure/VMwareSites/"
        
        if hyperv_site_pattern in source_site_id and hyperv_site_pattern in target_site_id:
            instance_type = AzLocalInstanceTypes.HyperVToAzLocal.value
            fabric_instance_type = FabricInstanceTypes.HyperVInstance.value
        elif vmware_site_pattern in source_site_id and hyperv_site_pattern in target_site_id:
            instance_type = AzLocalInstanceTypes.VMwareToAzLocal.value
            fabric_instance_type = FabricInstanceTypes.VMwareInstance.value
        else:
            raise CLIError(f"Error matching source '{source_appliance_name}' and target '{target_appliance_name}' appliances. Source is {'VMware' if vmware_site_pattern in source_site_id else 'HyperV' if hyperv_site_pattern in source_site_id else 'Unknown'}, Target is {'VMware' if vmware_site_pattern in target_site_id else 'HyperV' if hyperv_site_pattern in target_site_id else 'Unknown'}")
                
        # Get healthy fabrics in the resource group
        fabrics_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationFabrics"
        fabrics_response = send_get_request(cmd, f"{fabrics_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
        all_fabrics = fabrics_response.json().get('value', [])   

        if not all_fabrics:
            raise CLIError(
                f"No replication fabrics found in resource group '{resource_group_name}'. "
                f"Please ensure that:\n"
                f"1. The source appliance '{source_appliance_name}' is deployed and connected\n"
                f"2. The target appliance '{target_appliance_name}' is deployed and connected\n"
                f"3. Both appliances are registered with the Azure Migrate project '{project_name}'"
            )
        
        source_fabric = None
        source_fabric_candidates = []
        
        for fabric in all_fabrics:
            props = fabric.get('properties', {})
            custom_props = props.get('customProperties', {})
            fabric_name = fabric.get('name', '')            
            is_succeeded = props.get('provisioningState') == ProvisioningState.Succeeded.value
            
            fabric_solution_id = custom_props.get('migrationSolutionId', '').rstrip('/')
            expected_solution_id = amh_solution.get('id', '').rstrip('/')
            is_correct_solution = fabric_solution_id.lower() == expected_solution_id.lower()
            is_correct_instance = custom_props.get('instanceType') == fabric_instance_type
            
            name_matches = (
                fabric_name.lower().startswith(source_appliance_name.lower()) or
                source_appliance_name.lower() in fabric_name.lower() or
                fabric_name.lower() in source_appliance_name.lower() or
                f"{source_appliance_name.lower()}-" in fabric_name.lower()
            )
            
            # Collect potential candidates even if they don't fully match
            if custom_props.get('instanceType') == fabric_instance_type:
                source_fabric_candidates.append({
                    'name': fabric_name,
                    'state': props.get('provisioningState'),
                    'solution_match': is_correct_solution,
                    'name_match': name_matches
                })
            
            if is_succeeded and is_correct_instance and name_matches:
                # If solution doesn't match, log warning but still consider it
                if not is_correct_solution:
                    logger.warning(f"Fabric '{fabric_name}' matches name and type but has different solution ID")
                source_fabric = fabric
                break
        
        if not source_fabric:
            # Provide more detailed error message
            error_msg = f"Couldn't find connected source appliance '{source_appliance_name}'.\n"
            
            if source_fabric_candidates:
                error_msg += f"Found {len(source_fabric_candidates)} fabric(s) with matching type '{fabric_instance_type}':\n"
                for candidate in source_fabric_candidates:
                    error_msg += f"  - {candidate['name']} (state: {candidate['state']}, "
                    error_msg += f"solution_match: {candidate['solution_match']}, "
                    error_msg += f"name_match: {candidate['name_match']})\n"
                error_msg += "\nPlease verify:\n"
                error_msg += "1. The appliance name matches exactly\n"
                error_msg += "2. The fabric is in 'Succeeded' state\n"
                error_msg += "3. The fabric belongs to the correct migration solution"
            else:
                error_msg += f"No fabrics found with instance type '{fabric_instance_type}'.\n"
                error_msg += "\nThis usually means:\n"
                error_msg += f"1. The source appliance '{source_appliance_name}' is not properly configured\n"
                error_msg += f"2. The appliance type doesn't match (expecting {'VMware' if fabric_instance_type == FabricInstanceTypes.VMwareInstance.value else 'HyperV'})\n"
                error_msg += "3. The fabric creation is still in progress - wait a few minutes and retry"
                
                # List all available fabrics for debugging
                if all_fabrics:
                    error_msg += f"\n\nAvailable fabrics in resource group:\n"
                    for fabric in all_fabrics:
                        props = fabric.get('properties', {})
                        custom_props = props.get('customProperties', {})
                        error_msg += f"  - {fabric.get('name')} (type: {custom_props.get('instanceType')})\n"
            
            raise CLIError(error_msg)
                
        # Get source fabric agent (DRA)
        source_fabric_name = source_fabric.get('name')
        dras_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationFabrics/{source_fabric_name}/fabricAgents"
        source_dras_response = send_get_request(cmd, f"{dras_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
        source_dras = source_dras_response.json().get('value', [])
        
        source_dra = None
        for dra in source_dras:
            props = dra.get('properties', {})
            custom_props = props.get('customProperties', {})
            if (props.get('machineName') == source_appliance_name and
                custom_props.get('instanceType') == fabric_instance_type and
                props.get('isResponsive') == True):
                source_dra = dra
                break
        
        if not source_dra:
            raise CLIError(f"The source appliance '{source_appliance_name}' is in a disconnected state.")
                
        # Filter for target fabric - make matching more flexible and diagnostic
        target_fabric_instance_type = FabricInstanceTypes.AzLocalInstance.value
        target_fabric = None
        target_fabric_candidates = []
        
        for fabric in all_fabrics:
            props = fabric.get('properties', {})
            custom_props = props.get('customProperties', {})
            fabric_name = fabric.get('name', '')            
            is_succeeded = props.get('provisioningState') == ProvisioningState.Succeeded.value
            
            fabric_solution_id = custom_props.get('migrationSolutionId', '').rstrip('/')
            expected_solution_id = amh_solution.get('id', '').rstrip('/')
            is_correct_solution = fabric_solution_id.lower() == expected_solution_id.lower()
            is_correct_instance = custom_props.get('instanceType') == target_fabric_instance_type
            
            name_matches = (
                fabric_name.lower().startswith(target_appliance_name.lower()) or
                target_appliance_name.lower() in fabric_name.lower() or
                fabric_name.lower() in target_appliance_name.lower() or
                f"{target_appliance_name.lower()}-" in fabric_name.lower()
            )
            
            # Collect potential candidates
            if custom_props.get('instanceType') == target_fabric_instance_type:
                target_fabric_candidates.append({
                    'name': fabric_name,
                    'state': props.get('provisioningState'),
                    'solution_match': is_correct_solution,
                    'name_match': name_matches
                })
            
            if is_succeeded and is_correct_instance and name_matches:
                if not is_correct_solution:
                    logger.warning(f"Fabric '{fabric_name}' matches name and type but has different solution ID")
                target_fabric = fabric
                break
        
        if not target_fabric:
            # Provide more detailed error message
            error_msg = f"Couldn't find connected target appliance '{target_appliance_name}'.\n"
            
            if target_fabric_candidates:
                error_msg += f"Found {len(target_fabric_candidates)} fabric(s) with matching type '{target_fabric_instance_type}':\n"
                for candidate in target_fabric_candidates:
                    error_msg += f"  - {candidate['name']} (state: {candidate['state']}, "
                    error_msg += f"solution_match: {candidate['solution_match']}, "
                    error_msg += f"name_match: {candidate['name_match']})\n"
            else:
                error_msg += f"No fabrics found with instance type '{target_fabric_instance_type}'.\n"
                error_msg += "\nThis usually means:\n"
                error_msg += f"1. The target appliance '{target_appliance_name}' is not properly configured for Azure Local\n"
                error_msg += "2. The fabric creation is still in progress - wait a few minutes and retry\n"
                error_msg += "3. The target appliance is not connected to the Azure Local cluster"
            
            raise CLIError(error_msg)
                
        # Get target fabric agent (DRA)
        target_fabric_name = target_fabric.get('name')
        target_dras_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationFabrics/{target_fabric_name}/fabricAgents"
        target_dras_response = send_get_request(cmd, f"{target_dras_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
        target_dras = target_dras_response.json().get('value', [])
        
        target_dra = None
        for dra in target_dras:
            props = dra.get('properties', {})
            custom_props = props.get('customProperties', {})
            if (props.get('machineName') == target_appliance_name and
                custom_props.get('instanceType') == target_fabric_instance_type and
                props.get('isResponsive') == True):
                target_dra = dra
                break
        
        if not target_dra:
            raise CLIError(f"The target appliance '{target_appliance_name}' is in a disconnected state.")
                
        # 2. Validate Replication Extension
        source_fabric_id = source_fabric['id']
        target_fabric_id = target_fabric['id']
        source_fabric_short_name = source_fabric_id.split('/')[-1]
        target_fabric_short_name = target_fabric_id.split('/')[-1]
        replication_extension_name = f"{source_fabric_short_name}-{target_fabric_short_name}-MigReplicationExtn"
        extension_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationExtensions/{replication_extension_name}"        
        replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
        
        if not replication_extension:
            raise CLIError(f"The replication extension '{replication_extension_name}' not found. Run 'az migrate local-replication-infrastructure initialize' first.")
        
        extension_state = replication_extension.get('properties', {}).get('provisioningState')
        
        if extension_state != ProvisioningState.Succeeded.value:
            raise CLIError(f"The replication extension '{replication_extension_name}' is not ready. State: '{extension_state}'")
                
        # 3. Get ARC Resource Bridge info
        target_fabric_custom_props = target_fabric.get('properties', {}).get('customProperties', {})        
        target_cluster_id = target_fabric_custom_props.get('cluster', {}).get('resourceName', '')
        
        if not target_cluster_id:
            target_cluster_id = target_fabric_custom_props.get('azStackHciClusterName', '')
        
        if not target_cluster_id:
            target_cluster_id = target_fabric_custom_props.get('clusterName', '')
        
        # Extract custom location from target fabric
        custom_location_id = target_fabric_custom_props.get('customLocationRegion', '')
        
        if not custom_location_id:
            custom_location_id = target_fabric_custom_props.get('customLocationId', '')
        
        if not custom_location_id:
            if target_cluster_id:
                cluster_parts = target_cluster_id.split('/')
                if len(cluster_parts) >= 5:
                    custom_location_region = migrate_project.get('location', 'eastus')
                    custom_location_id = f"/subscriptions/{cluster_parts[2]}/resourceGroups/{cluster_parts[4]}/providers/Microsoft.ExtendedLocation/customLocations/{cluster_parts[-1]}-customLocation"
                else:
                    custom_location_region = migrate_project.get('location', 'eastus')
            else:
                custom_location_region = migrate_project.get('location', 'eastus')
        else:
            custom_location_region = migrate_project.get('location', 'eastus')
        
        # 4. Validate target VM name                
        if len(target_vm_name) == 0 or len(target_vm_name) > 64:
            raise CLIError("The target virtual machine name must be between 1 and 64 characters long.")
        
        vm_name_pattern = r"^[^_\W][a-zA-Z0-9\-]{0,63}(?<![-._])$"
        
        if not re.match(vm_name_pattern, target_vm_name):
            raise CLIError("The target VM name must begin with a letter or number, contain only letters, numbers, or hyphens, and not end with '.' or '-'.")
                
        # 5. Construct disk and NIC mappings
        disks = []
        nics = []
                
        if is_power_user_mode:
            if not disk_to_include or len(disk_to_include) == 0:
                raise CLIError("At least one disk must be included for replication.")
            
            # Validate that exactly one disk is marked as OS disk
            os_disks = [d for d in disk_to_include if d.get('isOSDisk', False)]
            for i, os_disk in enumerate(os_disks):
                if len(os_disks) != 1:
                    raise CLIError("Exactly one disk must be designated as the OS disk.")
                
            # Process disks
            for i, disk in enumerate(disk_to_include):
                disk_obj = {
                    'diskId': disk.get('diskId'),
                    'diskSizeGb': disk.get('diskSizeGb'),
                    'diskFileFormat': disk.get('diskFileFormat', 'VHDX'),
                    'isDynamic': disk.get('isDynamic', True),
                    'isOSDisk': disk.get('isOSDisk', False)
                }
                disks.append(disk_obj)
            
            # Process NICs
            print(f"DEBUG: Processing {len(nic_to_include)} NICs in power user mode")
            for i, nic in enumerate(nic_to_include):
                print(f"DEBUG: Processing NIC {i+1}: ID={nic.get('nicId')}, Target={nic.get('targetNetworkId')}")
                nic_obj = {
                    'nicId': nic.get('nicId'),
                    'targetNetworkId': nic.get('targetNetworkId'),
                    'testNetworkId': nic.get('testNetworkId', nic.get('targetNetworkId')),
                    'selectionTypeForFailover': nic.get('selectionTypeForFailover', VMNicSelection.SelectedByUser.value)
                }
                nics.append(nic_obj)
        else:
            machine_disks = machine_props.get('disks', [])
            machine_nics = machine_props.get('networkAdapters', [])
            
            # Find OS disk
            os_disk_found = False
            for i, disk in enumerate(machine_disks):
                if site_type == SiteTypes.HyperVSites.value:
                    disk_id = disk.get('instanceId')
                    disk_size = disk.get('maxSizeInBytes', 0)
                else:  # VMware
                    disk_id = disk.get('uuid')
                    disk_size = disk.get('maxSizeInBytes', 0)
            
                is_os_disk = disk_id == os_disk_id
                
                if is_os_disk:
                    os_disk_found = True
                
                disk_size_gb = (disk_size + (1024**3 - 1)) // (1024**3)  # Round up to GB
                
                disk_obj = {
                    'diskId': disk_id,
                    'diskSizeGb': disk_size_gb,
                    'diskFileFormat': 'VHDX',
                    'isDynamic': True,
                    'isOSDisk': is_os_disk
                }
                disks.append(disk_obj)
            
            for i, nic in enumerate(machine_nics):
                nic_id = nic.get('nicId')                
                test_network_id = target_test_virtual_switch_id or target_virtual_switch_id
                
                nic_obj = {
                    'nicId': nic_id,
                    'targetNetworkId': target_virtual_switch_id,
                    'testNetworkId': test_network_id,
                    'selectionTypeForFailover': VMNicSelection.SelectedByUser.value
                }
                nics.append(nic_obj)
        
        # 6. Create the protected item
        protected_item_name = machine_name        
        protected_item_uri = f"subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/protectedItems/{protected_item_name}"

        try:
            existing_item = get_resource_by_id(cmd, protected_item_uri, APIVersion.Microsoft_DataReplication.value)
            if existing_item:
                raise CLIError(f"A replication already exists for machine '{machine_name}'. Remove it first before creating a new one.")
        except Exception as e:
            # Check if it's a 404 Not Found error - that's expected and fine
            error_str = str(e)
            if "ResourceNotFound" in error_str or "404" in error_str or "Not Found" in error_str:
                existing_item = None
            else:
                # Some other error occurred, re-raise it
                raise
        
        # Determine Hyper-V generation
        if site_type == SiteTypes.HyperVSites.value:
            hyperv_generation = machine_props.get('generation', '1')
            is_source_dynamic_memory = machine_props.get('isDynamicMemoryEnabled', False)
        else:  # VMware
            firmware = machine_props.get('firmware', 'BIOS')
            hyperv_generation = '2' if firmware != 'BIOS' else '1'
            is_source_dynamic_memory = False
        
        # Determine target CPU and RAM
        source_cpu_cores = machine_props.get('numberOfProcessorCore', 2)
        source_memory_mb = machine_props.get('allocatedMemoryInMB', 4096)
        
        if not target_vm_cpu_core:
            target_vm_cpu_core = source_cpu_cores
        
        if not target_vm_ram:
            target_vm_ram = max(source_memory_mb, 512)  # Minimum 512MB
        
        if target_vm_cpu_core < 1 or target_vm_cpu_core > 240:
            raise CLIError("Target VM CPU cores must be between 1 and 240.")
        
        if hyperv_generation == '1':
            if target_vm_ram < 512 or target_vm_ram > 1048576:  # 1TB
                raise CLIError("Target VM RAM must be between 512 MB and 1048576 MB (1 TB) for Generation 1 VMs.")
        else:
            if target_vm_ram < 32 or target_vm_ram > 12582912:  # 12TB
                raise CLIError("Target VM RAM must be between 32 MB and 12582912 MB (12 TB) for Generation 2 VMs.")
        
        # Construct protected item properties with only the essential properties
        # The API schema varies by instance type, so we'll use a minimal approach
        custom_properties = {
            "instanceType": instance_type,
            "targetArcClusterCustomLocationId": custom_location_id or "",
            "customLocationRegion": custom_location_region,
            "fabricDiscoveryMachineId": machine_id,
            "disksToInclude": [
                {
                    "diskId": disk["diskId"],
                    "diskSizeGB": disk["diskSizeGb"],
                    "diskFileFormat": disk["diskFileFormat"],
                    "isOsDisk": disk["isOSDisk"],
                    "isDynamic": disk["isDynamic"],
                    "diskPhysicalSectorSize": 512
                }
                for disk in disks
            ],
            "targetVmName": target_vm_name,
            "targetResourceGroupId": target_resource_group_id,
            "storageContainerId": target_storage_path_id,
            "hyperVGeneration": hyperv_generation,
            "targetCpuCores": target_vm_cpu_core,
            "sourceCpuCores": source_cpu_cores,
            "isDynamicRam": is_dynamic_ram_enabled if is_dynamic_ram_enabled is not None else is_source_dynamic_memory,
            "sourceMemoryInMegaBytes": float(source_memory_mb),
            "targetMemoryInMegaBytes": int(target_vm_ram),
            "nicsToInclude": [
                {
                    "nicId": nic["nicId"],
                    "selectionTypeForFailover": nic["selectionTypeForFailover"],
                    "targetNetworkId": nic["targetNetworkId"],
                    "testNetworkId": nic.get("testNetworkId", "")
                }
                for nic in nics
            ],
            "dynamicMemoryConfig": {
                "maximumMemoryInMegaBytes": 1048576,  # Max for Gen 1
                "minimumMemoryInMegaBytes": 512,       # Min for Gen 1
                "targetMemoryBufferPercentage": 20
            },
            "sourceFabricAgentName": source_dra.get('name'),
            "targetFabricAgentName": target_dra.get('name'),
            "runAsAccountId": run_as_account_id,
            "targetHCIClusterId": target_cluster_id
        }
        
        protected_item_body = {
            "properties": {
                "policyName": policy_name,
                "replicationExtensionName": replication_extension_name,
                "customProperties": custom_properties
            }
        }
        
        result = create_or_update_resource(cmd, protected_item_uri, APIVersion.Microsoft_DataReplication.value, protected_item_body, no_wait=True)
        
        print(f"Successfully initiated replication for machine '{machine_name}'.")
        print("The replication setup is in progress. Use 'az migrate local-server-replication show' to check the status.")
        
        return {
            "message": f"Replication initiated for machine '{machine_name}'",
            "protectedItemId": protected_item_uri,
            "protectedItemName": protected_item_name,
            "status": "InProgress"
        }
            
    except Exception as e:
        logger.error(f"Error creating replication: {str(e)}")
        raise