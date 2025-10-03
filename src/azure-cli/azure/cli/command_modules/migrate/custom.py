# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import platform
import hashlib
import time
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.util import send_raw_request
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.migrate._powershell_utils import get_powershell_executor
from enum import Enum

logger = get_logger(__name__)

# --------------------------------------------------------------------------------------------
# Protected Item Commands
# --------------------------------------------------------------------------------------------

def get_protected_item(cmd, protected_item_id):
    """
    Retrieve a protected item from the Data Replication service.
    
    Args:
        cmd: The CLI command context
        protected_item_id (str): Full ARM resource ID of the protected item
    
    Returns:
        dict: The protected item content from the API response
    
    Raises:
        CLIError: If the API request fails or returns an error response
    """
    from azure.cli.core.commands.arm import get_arm_resource_by_id
    from azure.cli.command_modules.migrate._helpers import batch_call
    # Validate the protected item ID format
    if not protected_item_id or not protected_item_id.startswith('/'):
        raise CLIError("Invalid protected_item_id. Must be a full ARM resource ID starting with '/'.")
    
    # Construct the ARM URI with API version for Microsoft.DataReplication
    uri = f"{protected_item_id}?api-version=2024-09-01"
    request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + uri
    
    response = batch_call(cmd, request_uri)
    
    protected_item_data = response.json()
    
    return protected_item_data

def get_discovered_server(cmd, 
                          project_name, 
                          resource_group_name, 
                          display_name=None, 
                          source_machine_type=None,
                          subscription_id=None,
                          name=None,
                          appliance_name=None):
    """
    Retrieve discovered servers from the Azure Migrate project.
    
    Args:
        cmd: The CLI command context
        project_name (str): Specifies the migrate project name (required)
        resource_group_name (str): Specifies the resource group name (required)
        display_name (str, optional): Specifies the source machine display name
        source_machine_type (str, optional): Specifies the source machine type (VMware, HyperV)
        subscription_id (str, optional): Specifies the subscription id
        name (str, optional): Specifies the source machine name (internal name)
        appliance_name (str, optional): Specifies the appliance name (maps to site)
    
    Returns:
        dict: The discovered server data from the API response
    
    Raises:
        CLIError: If required parameters are missing or the API request fails
    """
    from azure.cli.command_modules.migrate._helpers import batch_call, APIVersion

    # Validate required parameters
    if not project_name:
        raise CLIError("project_name is required.")
    if not resource_group_name:
        raise CLIError("resource_group_name is required.")
    
    # Validate source_machine_type if provided
    if source_machine_type and source_machine_type not in ["VMware", "HyperV"]:
        raise CLIError("source_machine_type must be either 'VMware' or 'HyperV'.")
    
    # Use current subscription if not provided
    if not subscription_id:
        from azure.cli.core.commands.client_factory import get_subscription_id
        subscription_id = get_subscription_id(cmd.cli_ctx)
    
    # Determine the correct endpoint based on machine type and parameters
    if appliance_name and name:
        # GetInSite: Get specific machine in specific site
        if source_machine_type == "HyperV":
            base_uri = (f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/"
                       f"providers/Microsoft.OffAzure/HyperVSites/{appliance_name}/machines/{name}")
        else:  # VMware or default
            base_uri = (f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/"
                       f"providers/Microsoft.OffAzure/VMwareSites/{appliance_name}/machines/{name}")
    elif appliance_name:
        # ListInSite: List machines in specific site
        if source_machine_type == "HyperV":
            base_uri = (f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/"
                       f"providers/Microsoft.OffAzure/HyperVSites/{appliance_name}/machines")
        else:  # VMware or default
            base_uri = (f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/"
                       f"providers/Microsoft.OffAzure/VMwareSites/{appliance_name}/machines")
    elif name:
        # Get: Get specific machine from project (need to determine type)
        base_uri = (f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/"
                   f"providers/Microsoft.Migrate/migrateprojects/{project_name}/machines/{name}")
    else:
        # List: List all machines in project
        base_uri = (f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/"
                   f"providers/Microsoft.Migrate/migrateprojects/{project_name}/machines")
    
    # Use the correct API version for Microsoft.OffAzure
    api_version = APIVersion.Microsoft_OffAzure.value if appliance_name else APIVersion.Microsoft_Migrate.value
    
    # Prepare query parameters
    query_params = [f"api-version={api_version}"]
    
    # Add optional filters for project-level queries
    if not appliance_name and display_name:
        query_params.append(f"$filter=displayName eq '{display_name}'")
    
    # Construct the full URI
    query_string = "&".join(query_params)
    uri = f"{base_uri}?{query_string}"
    request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + uri
    
    try:
        response = batch_call(cmd, request_uri)
        
        discovered_servers_data = response.json()
        values = discovered_servers_data.get('value', [])

        # Fetch all discovered servers
        while discovered_servers_data.get('nextLink'):
            nextLink = discovered_servers_data.get('nextLink')
            response = batch_call(cmd, nextLink)

            discovered_servers_data = response.json()
            values += discovered_servers_data.get('value', [])
            

        # Apply client-side filtering for display_name when using site endpoints
        if appliance_name and display_name and 'value' in discovered_servers_data:
            filtered_servers = []
            for server in discovered_servers_data['value']:
                properties = server.get('properties', {})
                server_display_name = properties.get('displayName', '')
                if server_display_name == display_name:
                    filtered_servers.append(server)
            discovered_servers_data['value'] = filtered_servers
        
        # Format and display the discovered servers information
        formatted_output = []
        for index, server in enumerate(values, 1):
            properties = server.get('properties', {})
            discovery_data = properties.get('discoveryData', [])
            
            # Extract information from the latest discovery data
            machine_name = "N/A"
            ip_addresses = []
            os_name = "N/A"
            boot_type = "N/A"
            
            if discovery_data:
                latest_discovery = discovery_data[0]  # Most recent discovery data
                machine_name = latest_discovery.get('machineName', 'N/A')
                ip_addresses = latest_discovery.get('ipAddresses', [])
                os_name = latest_discovery.get('osName', 'N/A')
                
                extended_info = latest_discovery.get('extendedInfo', {})
                boot_type = extended_info.get('bootType', 'N/A')
            
            ip_addresses_str = ', '.join(ip_addresses) if ip_addresses else 'N/A'
            
            server_info = {
                'index': index,
                'machine_name': machine_name,
                'ip_addresses': ip_addresses_str,
                'operating_system': os_name,
                'boot_type': boot_type
            }
            formatted_output.append(server_info)
        
        # Print formatted output
        for server in formatted_output:
            index_str = f"[{server['index']}]"
            print(f"{index_str} Machine Name: {server['machine_name']}")
            print(f"{' ' * len(index_str)} IP Addresses: {server['ip_addresses']}")
            print(f"{' ' * len(index_str)} Operating System: {server['operating_system']}")
            print(f"{' ' * len(index_str)} Boot Type: {server['boot_type']}")
            print()
            
    except Exception as e:
        logger.error(f"Error retrieving discovered servers: {str(e)}")
        raise CLIError(f"Failed to retrieve discovered servers: {str(e)}")

def initialize_replication_infrastructure(cmd,
                                        resource_group_name,
                                        project_name,
                                        source_appliance_name,
                                        target_appliance_name,
                                        cache_storage_account_id=None,
                                        subscription_id=None,
                                        pass_thru=False):
    """
    Initialize Azure Migrate local replication infrastructure.
    
    This function is based on a preview API version and may experience breaking changes in future releases.
    
    Args:
        cmd: The CLI command context
        resource_group_name (str): Specifies the Resource Group of the Azure Migrate Project (required)
        project_name (str): Specifies the name of the Azure Migrate project to be used for server migration (required)
        source_appliance_name (str): Specifies the source appliance name for the AzLocal scenario (required)
        target_appliance_name (str): Specifies the target appliance name for the AzLocal scenario (required)
        cache_storage_account_id (str, optional): Specifies the Storage Account ARM Id to be used for private endpoint scenario
        subscription_id (str, optional): Azure Subscription ID. Uses current subscription if not provided
        pass_thru (bool, optional): Returns True when the command succeeds
    
    Returns:
        bool: True if the operation succeeds (when pass_thru is True), otherwise None
    
    Raises:
        CLIError: If required parameters are missing or the API request fails
    """
    from azure.cli.command_modules.migrate._helpers import (
        batch_call, 
        get_resource_by_id, 
        delete_resource,
        create_or_update_resource,
        generate_hash_for_artifact,
        APIVersion, 
        ProvisioningState, 
        AzLocalInstanceTypes, 
        FabricInstanceTypes,
        ReplicationDetails,
        RoleDefinitionIds,
        StorageAccountProvisioningState
    )
    from azure.cli.core.commands.client_factory import get_subscription_id

    # Validate required parameters
    if not resource_group_name:
        raise CLIError("resource_group_name is required.")
    if not project_name:
        raise CLIError("project_name is required.")
    if not source_appliance_name:
        raise CLIError("source_appliance_name is required.")
    if not target_appliance_name:
        raise CLIError("target_appliance_name is required.")
    
    try:
        # Use current subscription if not provided
        if not subscription_id:
            subscription_id = get_subscription_id(cmd.cli_ctx)
        print(f"Selected Subscription Id: '{subscription_id}'")

        # Get resource group
        rg_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
        resource_group = get_resource_by_id(cmd, rg_uri, APIVersion.Microsoft_Resources.value)
        if not resource_group:
            raise CLIError(f"Resource group '{resource_group_name}' does not exist in the subscription.")
        print(f"Selected Resource Group: '{resource_group_name}'")
        
        # Get Migrate Project
        project_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Migrate/migrateprojects/{project_name}"
        migrate_project = get_resource_by_id(cmd, project_uri, APIVersion.Microsoft_Migrate.value)
        if not migrate_project:
            raise CLIError(f"Migrate project '{project_name}' not found.")
        
        if migrate_project.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"Migrate project '{project_name}' is not in a valid state.")
        
        # Get Data Replication Service Solution
        amh_solution_name = "Servers-Migration-ServerMigration_DataReplication"
        amh_solution_uri = f"{project_uri}/solutions/{amh_solution_name}"
        amh_solution = get_resource_by_id(cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value)
        if not amh_solution:
            raise CLIError(f"No Data Replication Service Solution '{amh_solution_name}' found.")
        
        # Validate Replication Vault
        vault_id = amh_solution.get('properties', {}).get('details', {}).get('extendedDetails', {}).get('vaultId')
        if not vault_id:
            raise CLIError("No Replication Vault found. Please verify your Azure Migrate project setup.")
        
        replication_vault_name = vault_id.split("/")[8]
        vault_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}"
        replication_vault = get_resource_by_id(cmd, vault_uri, APIVersion.Microsoft_DataReplication.value)
        if not replication_vault:
            raise CLIError(f"No Replication Vault '{replication_vault_name}' found.")
        
        # Get Discovery Solution
        discovery_solution_name = "Servers-Discovery-ServerDiscovery"
        discovery_solution_uri = f"{project_uri}/solutions/{discovery_solution_name}"
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
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse applianceNameToSiteIdMapV2: {str(e)}")
        
        # Process applianceNameToSiteIdMapV3
        if 'applianceNameToSiteIdMapV3' in extended_details:
            try:
                app_map_v3 = json.loads(extended_details['applianceNameToSiteIdMapV3'])
                if isinstance(app_map_v3, dict):
                    # V3 is a dictionary format
                    for appliance_name, site_info in app_map_v3.items():
                        if isinstance(site_info, dict) and 'SiteId' in site_info:
                            app_map[appliance_name.lower()] = site_info['SiteId']
                        elif isinstance(site_info, str):
                            # Sometimes the value might be the SiteId directly
                            app_map[appliance_name.lower()] = site_info
                elif isinstance(app_map_v3, list):
                    # V3 might also be in list format
                    for item in app_map_v3:
                        if isinstance(item, dict):
                            # Check if it has ApplianceName/SiteId structure
                            if 'ApplianceName' in item and 'SiteId' in item:
                                app_map[item['ApplianceName'].lower()] = item['SiteId']
                            else:
                                # Or it might be a single key-value pair
                                for key, value in item.items():
                                    if isinstance(value, dict) and 'SiteId' in value:
                                        app_map[key.lower()] = value['SiteId']
                                    elif isinstance(value, str):
                                        app_map[key.lower()] = value
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse applianceNameToSiteIdMapV3: {str(e)}")
        
        if not app_map:
            raise CLIError("Server Discovery Solution missing Appliance Details. Invalid Solution.")
        

        # Validate Source and Target Appliances
        source_site_id = app_map.get(source_appliance_name.lower())
        target_site_id = app_map.get(target_appliance_name.lower())
        
        if not source_site_id:
            available_appliances = ', '.join(app_map.keys())
            raise CLIError(f"Source appliance '{source_appliance_name}' not found in discovery solution. Available appliances: {available_appliances}")
        if not target_site_id:
            available_appliances = ', '.join(app_map.keys())
            raise CLIError(f"Target appliance '{target_appliance_name}' not found in discovery solution. Available appliances: {available_appliances}")
        
        print(f"Source site ID for '{source_appliance_name}': {source_site_id}")
        print(f"Target site ID for '{target_appliance_name}': {target_site_id}")
        
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
        
        print(f"Instance type: {instance_type}, Fabric instance type: {fabric_instance_type}")
        
        # Get healthy fabrics in the resource group
        fabrics_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationFabrics"
        fabrics_response = batch_call(cmd, f"{fabrics_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
        all_fabrics = fabrics_response.json().get('value', [])
        
        for fabric in all_fabrics:
            props = fabric.get('properties', {})
            custom_props = props.get('customProperties', {})
            print(f"Fabric: {fabric.get('name')}")
            print(f"  - State: {props.get('provisioningState')}")
            print(f"  - Type: {custom_props.get('instanceType')}")
            print(f"  - Solution ID: {custom_props.get('migrationSolutionId')}")
            print(f"  - Custom Properties: {json.dumps(custom_props, indent=2)}")

        # If no fabrics exist at all, provide helpful message
        if not all_fabrics:
            raise CLIError(
                f"No replication fabrics found in resource group '{resource_group_name}'. "
                f"Please ensure that:\n"
                f"1. The source appliance '{source_appliance_name}' is deployed and connected\n"
                f"2. The target appliance '{target_appliance_name}' is deployed and connected\n"
                f"3. Both appliances are registered with the Azure Migrate project '{project_name}'"
            )
        
        # Filter for source fabric - make matching more flexible and diagnostic
        source_fabric = None
        source_fabric_candidates = []
        
        for fabric in all_fabrics:
            props = fabric.get('properties', {})
            custom_props = props.get('customProperties', {})
            fabric_name = fabric.get('name', '')
            
            # Check if this fabric matches our criteria
            is_succeeded = props.get('provisioningState') == ProvisioningState.Succeeded.value
            
            # Check solution ID match - handle case differences and trailing slashes
            fabric_solution_id = custom_props.get('migrationSolutionId', '').rstrip('/')
            expected_solution_id = amh_solution.get('id', '').rstrip('/')
            is_correct_solution = fabric_solution_id.lower() == expected_solution_id.lower()
            
            is_correct_instance = custom_props.get('instanceType') == fabric_instance_type
            
            # More flexible name matching - check if fabric name contains appliance name or vice versa
            name_matches = (
                fabric_name.lower().startswith(source_appliance_name.lower()) or
                source_appliance_name.lower() in fabric_name.lower() or
                fabric_name.lower() in source_appliance_name.lower() or
                # Also check if the fabric name matches the site name pattern
                f"{source_appliance_name.lower()}-" in fabric_name.lower()
            )
            
            print(f"Checking source fabric '{fabric_name}':")
            print(f"  - succeeded={is_succeeded}")
            print(f"  - solution_match={is_correct_solution} (fabric: '{fabric_solution_id}' vs expected: '{expected_solution_id}')")
            print(f"  - instance_match={is_correct_instance} (fabric: '{custom_props.get('instanceType')}' vs expected: '{fabric_instance_type}')")
            print(f"  - name_match={name_matches}")
            
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
        
        print(f"Selected Source Fabric: '{source_fabric.get('name')}'")
        
        # Get source fabric agent (DRA)
        source_fabric_name = source_fabric.get('name')
        dras_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationFabrics/{source_fabric_name}/fabricAgents"
        source_dras_response = batch_call(cmd, f"{dras_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
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
        
        print(f"Selected Source Fabric Agent: '{source_dra.get('name')}'")
        
        # Filter for target fabric - make matching more flexible and diagnostic
        target_fabric_instance_type = FabricInstanceTypes.AzLocalInstance.value
        target_fabric = None
        target_fabric_candidates = []
        
        for fabric in all_fabrics:
            props = fabric.get('properties', {})
            custom_props = props.get('customProperties', {})
            fabric_name = fabric.get('name', '')
            
            # Check if this fabric matches our criteria
            is_succeeded = props.get('provisioningState') == ProvisioningState.Succeeded.value
            
            # Check solution ID match - handle case differences and trailing slashes
            fabric_solution_id = custom_props.get('migrationSolutionId', '').rstrip('/')
            expected_solution_id = amh_solution.get('id', '').rstrip('/')
            is_correct_solution = fabric_solution_id.lower() == expected_solution_id.lower()
            
            is_correct_instance = custom_props.get('instanceType') == target_fabric_instance_type
            
            # More flexible name matching
            name_matches = (
                fabric_name.lower().startswith(target_appliance_name.lower()) or
                target_appliance_name.lower() in fabric_name.lower() or
                fabric_name.lower() in target_appliance_name.lower() or
                f"{target_appliance_name.lower()}-" in fabric_name.lower()
            )
            
            print(f"Checking target fabric '{fabric_name}':")
            print(f"  - succeeded={is_succeeded}")
            print(f"  - solution_match={is_correct_solution}")
            print(f"  - instance_match={is_correct_instance} (fabric: '{custom_props.get('instanceType')}' vs expected: '{target_fabric_instance_type}')")
            print(f"  - name_match={name_matches}")
            
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
        
        print(f"Selected Target Fabric: '{target_fabric.get('name')}'")
        
        # Get target fabric agent (DRA)
        target_fabric_name = target_fabric.get('name')
        target_dras_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationFabrics/{target_fabric_name}/fabricAgents"
        target_dras_response = batch_call(cmd, f"{target_dras_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
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
        
        print(f"Selected Target Fabric Agent: '{target_dra.get('name')}'")
        
        # Setup Policy
        policy_name = f"{replication_vault_name}{instance_type}policy"
        policy_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationPolicies/{policy_name}"
        
        policy = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
        
        # Handle existing policy states
        if policy:
            provisioning_state = policy.get('properties', {}).get('provisioningState')
            
            # Wait for creating/updating to complete
            if provisioning_state in [ProvisioningState.Creating.value, ProvisioningState.Updating.value]:
                print(f"Policy '{policy_name}' found in Provisioning State '{provisioning_state}'.")
                for i in range(20):
                    time.sleep(30)
                    policy = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
                    if policy:
                        provisioning_state = policy.get('properties', {}).get('provisioningState')
                        if provisioning_state not in [ProvisioningState.Creating.value, ProvisioningState.Updating.value]:
                            break
            
            # Remove policy if in bad state
            if provisioning_state in [ProvisioningState.Canceled.value, ProvisioningState.Failed.value]:
                print(f"Policy '{policy_name}' found in unusable state '{provisioning_state}'. Removing...")
                delete_resource(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
                time.sleep(30)
                policy = None
        
        # Create policy if needed
        if not policy or policy.get('properties', {}).get('provisioningState') == ProvisioningState.Deleted.value:
            print(f"Creating Policy '{policy_name}'...")
            
            policy_body = {
                "properties": {
                    "customProperties": {
                        "instanceType": instance_type,
                        "recoveryPointHistoryInMinutes": ReplicationDetails.PolicyDetails.DefaultRecoveryPointHistoryInMinutes,
                        "crashConsistentFrequencyInMinutes": ReplicationDetails.PolicyDetails.DefaultCrashConsistentFrequencyInMinutes,
                        "appConsistentFrequencyInMinutes": ReplicationDetails.PolicyDetails.DefaultAppConsistentFrequencyInMinutes
                    }
                }
            }
            
            create_or_update_resource(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value, policy_body, no_wait=True)
            
            # Wait for policy creation
            for i in range(20):
                time.sleep(30)
                policy = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
                if policy:
                    provisioning_state = policy.get('properties', {}).get('provisioningState')
                    if provisioning_state in [ProvisioningState.Succeeded.value, ProvisioningState.Failed.value, 
                                             ProvisioningState.Canceled.value, ProvisioningState.Deleted.value]:
                        break
        
        if not policy or policy.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"Policy '{policy_name}' is not in Succeeded state.")
        
        print(f"Selected Policy: '{policy_name}'")
        
        # Setup Cache Storage Account
        amh_stored_storage_account_id = amh_solution.get('properties', {}).get('details', {}).get('extendedDetails', {}).get('replicationStorageAccountId')
        cache_storage_account = None
        
        if amh_stored_storage_account_id:
            # Check existing storage account
            storage_account_name = amh_stored_storage_account_id.split("/")[8]
            storage_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            storage_account = get_resource_by_id(cmd, storage_uri, APIVersion.Microsoft_Storage.value)
            
            if storage_account and storage_account.get('properties', {}).get('provisioningState') == StorageAccountProvisioningState.Succeeded.value:
                cache_storage_account = storage_account
                if cache_storage_account_id and cache_storage_account['id'] != cache_storage_account_id:
                    logger.warning(f"A Cache Storage Account '{storage_account_name}' is already linked. Ignoring provided -cache_storage_account_id.")
        
        # Use user-provided storage account if no existing one
        if not cache_storage_account and cache_storage_account_id:
            storage_account_name = cache_storage_account_id.split("/")[8].lower()
            storage_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            user_storage_account = get_resource_by_id(cmd, storage_uri, APIVersion.Microsoft_Storage.value)
            
            if user_storage_account and user_storage_account.get('properties', {}).get('provisioningState') == StorageAccountProvisioningState.Succeeded.value:
                cache_storage_account = user_storage_account
            else:
                raise CLIError(f"Cache Storage Account with Id '{cache_storage_account_id}' not found or not in valid state.")
        
        # Create new storage account if needed
        if not cache_storage_account:
            suffix_hash = generate_hash_for_artifact(f"{source_site_id}/{source_appliance_name}")
            if len(suffix_hash) > 14:
                suffix_hash = suffix_hash[:14]
            storage_account_name = f"migratersa{suffix_hash}"
            
            print(f"Creating Cache Storage Account '{storage_account_name}'...")
            
            storage_body = {
                "location": migrate_project.get('location'),
                "tags": {"Migrate Project": project_name},
                "sku": {"name": "Standard_LRS"},
                "kind": "StorageV2",
                "properties": {
                    "allowBlobPublicAccess": True,
                    "encryption": {
                        "services": {
                            "blob": {"enabled": True},
                            "file": {"enabled": True}
                        }
                    }
                }
            }
            
            storage_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            cache_storage_account = create_or_update_resource(cmd, storage_uri, APIVersion.Microsoft_Storage.value, storage_body)
            
            # Wait for storage account creation
            for i in range(20):
                time.sleep(30)
                cache_storage_account = get_resource_by_id(cmd, storage_uri, APIVersion.Microsoft_Storage.value)
                if cache_storage_account and cache_storage_account.get('properties', {}).get('provisioningState') == StorageAccountProvisioningState.Succeeded.value:
                    break
        
        if not cache_storage_account or cache_storage_account.get('properties', {}).get('provisioningState') != StorageAccountProvisioningState.Succeeded.value:
            raise CLIError("Failed to setup Cache Storage Account.")
        
        print(f"Selected Cache Storage Account: '{cache_storage_account.get('name')}'")
        
        # Grant permissions (Role Assignments)
        from azure.mgmt.authorization import AuthorizationManagementClient
        from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
        
        # Get role assignment client using the correct method for Azure CLI
        auth_client = get_mgmt_service_client(cmd.cli_ctx, AuthorizationManagementClient)
        
        source_dra_object_id = source_dra.get('properties', {}).get('resourceAccessIdentity', {}).get('objectId')
        target_dra_object_id = target_dra.get('properties', {}).get('resourceAccessIdentity', {}).get('objectId')
        vault_identity_id = replication_vault.get('properties', {}).get('identity', {}).get('principalId')
        
        storage_account_id = cache_storage_account['id']
        
        # Create role assignments for source and target DRAs
        for object_id in [source_dra_object_id, target_dra_object_id]:
            if object_id:
                for role_def_id in [RoleDefinitionIds.ContributorId, RoleDefinitionIds.StorageBlobDataContributorId]:
                    try:
                        # Check if assignment exists
                        assignments = auth_client.role_assignments.list_for_scope(
                            scope=storage_account_id,
                            filter=f"principalId eq '{object_id}'"
                        )
                        
                        has_role = any(a.role_definition_id.endswith(role_def_id) for a in assignments)
                        
                        if not has_role:
                            from uuid import uuid4
                            role_assignment_params = RoleAssignmentCreateParameters(
                                role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{role_def_id}",
                                principal_id=object_id
                            )
                            auth_client.role_assignments.create(
                                scope=storage_account_id,
                                role_assignment_name=str(uuid4()),
                                parameters=role_assignment_params
                            )
                    except Exception as e:
                        logger.warning(f"Failed to create role assignment: {str(e)}")
        
        # Grant vault identity permissions if exists
        if vault_identity_id:
            for role_def_id in [RoleDefinitionIds.ContributorId, RoleDefinitionIds.StorageBlobDataContributorId]:
                try:
                    assignments = auth_client.role_assignments.list_for_scope(
                        scope=storage_account_id,
                        filter=f"principalId eq '{vault_identity_id}'"
                    )
                    
                    has_role = any(a.role_definition_id.endswith(role_def_id) for a in assignments)
                    
                    if not has_role:
                        from uuid import uuid4
                        role_assignment_params = RoleAssignmentCreateParameters(
                            role_definition_id=f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{role_def_id}",
                            principal_id=vault_identity_id
                        )
                        auth_client.role_assignments.create(
                            scope=storage_account_id,
                            role_assignment_name=str(uuid4()),
                            parameters=role_assignment_params
                        )
                except Exception as e:
                    logger.warning(f"Failed to create vault role assignment: {str(e)}")
        
        # Update AMH solution with storage account ID
        if amh_solution.get('properties', {}).get('details', {}).get('extendedDetails', {}).get('replicationStorageAccountId') != storage_account_id:
            extended_details = amh_solution.get('properties', {}).get('details', {}).get('extendedDetails', {})
            extended_details['replicationStorageAccountId'] = storage_account_id
            
            solution_body = {
                "properties": {
                    "details": {
                        "extendedDetails": extended_details
                    }
                }
            }
            
            create_or_update_resource(cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value, solution_body)
        
        # Setup Replication Extension
        source_fabric_id = source_fabric['id']
        target_fabric_id = target_fabric['id']
        source_fabric_short_name = source_fabric_id.split('/')[-1]
        target_fabric_short_name = target_fabric_id.split('/')[-1]
        replication_extension_name = f"{source_fabric_short_name}-{target_fabric_short_name}-MigReplicationExtn"
        
        # Fix: Add leading slash to extension_uri
        extension_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationExtensions/{replication_extension_name}"
        replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
        
        # Check if extension exists and is in good state
        if replication_extension:
            existing_state = replication_extension.get('properties', {}).get('provisioningState')
            existing_storage_id = replication_extension.get('properties', {}).get('customProperties', {}).get('storageAccountId')
            
            print(f"Found existing extension '{replication_extension_name}' in state: {existing_state}")
            
            # If it's succeeded with the correct storage account, we're done
            if existing_state == ProvisioningState.Succeeded.value and existing_storage_id == storage_account_id:
                print(f"Replication Extension already exists with correct configuration.")
                print("Successfully initialized replication infrastructure")
                if pass_thru:
                    return True
                return
            
            # If it's in a bad state or has wrong storage account, delete it
            if existing_state in [ProvisioningState.Failed.value, ProvisioningState.Canceled.value] or existing_storage_id != storage_account_id:
                print(f"Removing existing extension (state: {existing_state}, storage mismatch: {existing_storage_id != storage_account_id})")
                delete_resource(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
                print("Waiting 120 seconds for deletion to complete...")
                time.sleep(120)
                replication_extension = None
        
        # Create replication extension if needed
        if not replication_extension:
            print(f"Creating Replication Extension '{replication_extension_name}'...")
            print(f"Waiting 120 seconds for permissions to sync...")
            time.sleep(120)  # Wait for permissions to sync
            
            # First, let's check what extensions already exist to understand the pattern
            print("\n=== Checking existing extensions for patterns ===")
            existing_extensions_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationExtensions"
            try:
                existing_extensions_response = batch_call(cmd, f"{existing_extensions_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
                existing_extensions = existing_extensions_response.json().get('value', [])
                if existing_extensions:
                    print(f"Found {len(existing_extensions)} existing extension(s):")
                    for ext in existing_extensions:
                        ext_name = ext.get('name')
                        ext_state = ext.get('properties', {}).get('provisioningState')
                        ext_type = ext.get('properties', {}).get('customProperties', {}).get('instanceType')
                        print(f"  - {ext_name}: state={ext_state}, type={ext_type}")
                        
                        # If we find one with our instance type, let's see its structure
                        if ext_type == instance_type:
                            print(f"\nFound matching extension type. Full structure:")
                            print(json.dumps(ext.get('properties', {}).get('customProperties', {}), indent=2))
                else:
                    print("No existing extensions found")
            except Exception as list_error:
                print(f"Error listing extensions: {str(list_error)}")
            
            # Try creating with minimal properties first
            print("\n=== Attempting to create extension ===")
            
            extension_body = {
                "properties": {
                    "customProperties": {
                        "instanceType": instance_type
                    }
                }
            }
            
            print(f"Extension body (minimal): {json.dumps(extension_body, indent=2)}")
            print(f"Extension URI: {extension_uri}")
            
            try:
                # Use the built-in helper function that handles auth properly
                print("Creating extension using built-in helper...")
                result = create_or_update_resource(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value, extension_body, no_wait=False)
                print(f"Creation result: {result}")
                
                # If minimal creation succeeded, wait a bit then check status
                if result:
                    print("Initial creation succeeded. Waiting for provisioning...")
                    time.sleep(30)
                    
            except Exception as create_error:
                print(f"Error during extension creation: {str(create_error)}")
                error_str = str(create_error)
                
                # Check for specific error patterns
                if "Internal Server Error" in error_str or "InternalServerError" in error_str:
                    print("\n=== Internal Server Error detected, trying with full properties ===")
                    
                    # Try with more properties based on what we saw in existing extensions
                    full_extension_body = {
                        "properties": {
                            "customProperties": {
                                "instanceType": instance_type
                            }
                        }
                    }
                    
                    # Add fabric-specific properties based on instance type
                    if instance_type == AzLocalInstanceTypes.VMwareToAzLocal.value:
                        full_extension_body["properties"]["customProperties"]["vmwareFabricArmId"] = source_fabric_id
                        full_extension_body["properties"]["customProperties"]["vmwareSiteId"] = source_site_id  
                        full_extension_body["properties"]["customProperties"]["azStackHciFabricArmId"] = target_fabric_id
                        full_extension_body["properties"]["customProperties"]["azStackHciSiteId"] = target_fabric_id
                    elif instance_type == AzLocalInstanceTypes.HyperVToAzLocal.value:
                        full_extension_body["properties"]["customProperties"]["hyperVFabricArmId"] = source_fabric_id
                        full_extension_body["properties"]["customProperties"]["hyperVSiteId"] = source_site_id
                        full_extension_body["properties"]["customProperties"]["azStackHciFabricArmId"] = target_fabric_id
                        full_extension_body["properties"]["customProperties"]["azStackHciSiteId"] = target_fabric_id
                    
                    # Add common properties seen in existing extensions
                    full_extension_body["properties"]["customProperties"]["storageAccountId"] = storage_account_id
                    full_extension_body["properties"]["customProperties"]["storageAccountSasSecretName"] = None
                    full_extension_body["properties"]["customProperties"]["resourceLocation"] = migrate_project.get('location')
                    full_extension_body["properties"]["customProperties"]["subscriptionId"] = subscription_id
                    full_extension_body["properties"]["customProperties"]["resourceGroup"] = resource_group_name
                    
                    print(f"Full extension body: {json.dumps(full_extension_body, indent=2)}")
                    
                    try:
                        result = create_or_update_resource(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value, full_extension_body, no_wait=False)
                        print(f"Full creation result: {result}")
                    except Exception as full_error:
                        print(f"Full creation also failed: {str(full_error)}")
                        
                        # Last resort: Check if extension was actually created despite the error
                        print("\nChecking if extension exists despite errors...")
                        replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
                        if replication_extension:
                            print(f"Extension exists with state: {replication_extension.get('properties', {}).get('provisioningState')}")
                        else:
                            raise CLIError(f"Failed to create extension after multiple attempts. Last error: {str(full_error)}")
                
                elif "InvalidProperty" in error_str or "unknown property" in error_str.lower():
                    print("\n=== Invalid property error, trying without storage properties ===")
                    
                    # Try without storage account properties that might be causing issues
                    simple_extension_body = {
                        "properties": {
                            "customProperties": {
                                "instanceType": instance_type
                            }
                        }
                    }
                    
                    # Only add fabric IDs, not storage
                    if instance_type == AzLocalInstanceTypes.VMwareToAzLocal.value:
                        simple_extension_body["properties"]["customProperties"]["vmwareFabricArmId"] = source_fabric_id
                        simple_extension_body["properties"]["customProperties"]["azStackHciFabricArmId"] = target_fabric_id
                    elif instance_type == AzLocalInstanceTypes.HyperVToAzLocal.value:
                        simple_extension_body["properties"]["customProperties"]["hyperVFabricArmId"] = source_fabric_id
                        simple_extension_body["properties"]["customProperties"]["azStackHciFabricArmId"] = target_fabric_id
                    
                    print(f"Simple extension body: {json.dumps(simple_extension_body, indent=2)}")
                    
                    try:
                        result = create_or_update_resource(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value, simple_extension_body, no_wait=False)
                        print(f"Simple creation result: {result}")
                    except Exception as simple_error:
                        print(f"Simple creation also failed: {str(simple_error)}")
                        raise
                else:
                    # Unknown error, re-raise
                    raise
            
            # Wait for extension creation to complete
            print("\nWaiting for extension operation to complete...")
            for i in range(20):
                print(f"Polling attempt {i+1}/20...")
                time.sleep(30)
                replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
                if replication_extension:
                    provisioning_state = replication_extension.get('properties', {}).get('provisioningState')
                    print(f"Current provisioning state: {provisioning_state}")
                    if provisioning_state in [ProvisioningState.Succeeded.value, ProvisioningState.Failed.value,
                                             ProvisioningState.Canceled.value]:
                        print(f"Extension operation finished with state: {provisioning_state}")
                        break
        
        # Final check
        if not replication_extension:
            replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
            
        if not replication_extension or replication_extension.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            current_state = replication_extension.get('properties', {}).get('provisioningState') if replication_extension else "None"
            print(f"Extension final state: {current_state}")
            if replication_extension:
                print(f"Extension details: {json.dumps(replication_extension, indent=2)}")
            raise CLIError(f"Replication Extension '{replication_extension_name}' is not in Succeeded state. Current state: {current_state}")
        
        print("Successfully initialized replication infrastructure")
        
        if pass_thru:
            return True
            
    except Exception as e:
        logger.error(f"Error initializing replication infrastructure: {str(e)}")
        raise CLIError(f"Failed to initialize replication infrastructure: {str(e)}")
            
