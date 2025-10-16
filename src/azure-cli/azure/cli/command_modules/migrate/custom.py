# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_mgmt_service_client
import json
import time

logger = get_logger(__name__)

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
    from azure.cli.command_modules.migrate._helpers import send_get_request, APIVersion

    # Validate required parameters
    if not project_name:
        raise CLIError("project_name is required.")

    if not resource_group_name:
        raise CLIError("resource_group_name is required.")
      
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
        response = send_get_request(cmd, request_uri)
        
        discovered_servers_data = response.json()
        values = discovered_servers_data.get('value', [])

        # Fetch all discovered servers
        while discovered_servers_data.get('nextLink'):
            nextLink = discovered_servers_data.get('nextLink')
            response = send_get_request(cmd, nextLink)

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
            os_disk_id = {}
            
            if discovery_data:
                latest_discovery = discovery_data[0]  # Most recent discovery data
                machine_name = latest_discovery.get('machineName', 'N/A')
                ip_addresses = latest_discovery.get('ipAddresses', [])
                os_name = latest_discovery.get('osName', 'N/A')
                disk_details = json.loads(latest_discovery.get('extendedInfo', {}).get('diskDetails', []))[0]
                os_disk_id = disk_details.get("InstanceId", "N/A")
                
                extended_info = latest_discovery.get('extendedInfo', {})
                boot_type = extended_info.get('bootType', 'N/A')
            
            ip_addresses_str = ', '.join(ip_addresses) if ip_addresses else 'N/A'
            
            server_info = {
                'index': index,
                'machine_name': machine_name,
                'ip_addresses': ip_addresses_str,
                'operating_system': os_name,
                'boot_type': boot_type,
                'os_disk_id': os_disk_id
            }
            formatted_output.append(server_info)
        
        # Print formatted output
        for server in formatted_output:
            index_str = f"[{server['index']}]"
            print(f"{index_str} Machine Name: {server['machine_name']}")
            print(f"{' ' * len(index_str)} IP Addresses: {server['ip_addresses']}")
            print(f"{' ' * len(index_str)} Operating System: {server['operating_system']}")
            print(f"{' ' * len(index_str)} Boot Type: {server['boot_type']}")
            print(f"{' ' * len(index_str)} OS Disk ID: {server['os_disk_id']}")
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
        send_get_request, 
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
    import json

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
        project_uri = f"{rg_uri}/providers/Microsoft.Migrate/migrateprojects/{project_name}"
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
        vault_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}"
        replication_vault = get_resource_by_id(cmd, vault_uri, APIVersion.Microsoft_DataReplication.value)
        if not replication_vault:
            raise CLIError(f"No Replication Vault '{replication_vault_name}' found.")
        
        # Check if vault has managed identity, if not, enable it
        vault_identity = replication_vault.get('identity') or replication_vault.get('properties', {}).get('identity')
        if not vault_identity or not vault_identity.get('principalId'):
            print(f"Replication vault '{replication_vault_name}' does not have a managed identity. Enabling system-assigned identity...")
            
            # Update vault to enable system-assigned managed identity
            vault_update_body = {
                "identity": {
                    "type": "SystemAssigned"
                }
            }
            
            replication_vault = create_or_update_resource(cmd, vault_uri, APIVersion.Microsoft_DataReplication.value, vault_update_body)
            
            # Wait for identity to be created
            print("Waiting 30 seconds for managed identity to be created...")
            time.sleep(30)
            
            # Refresh vault to get the identity
            replication_vault = get_resource_by_id(cmd, vault_uri, APIVersion.Microsoft_DataReplication.value)
            vault_identity = replication_vault.get('identity') or replication_vault.get('properties', {}).get('identity')
            
            if not vault_identity or not vault_identity.get('principalId'):
                raise CLIError(f"Failed to enable managed identity for replication vault '{replication_vault_name}'")
            
            print(f"✓ Enabled system-assigned managed identity for vault. Principal ID: {vault_identity.get('principalId')}")
        else:
            print(f"✓ Replication vault has managed identity. Principal ID: {vault_identity.get('principalId')}")
        
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
                            # Store both lowercase and original case
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
                            # Store both lowercase and original case
                            app_map[appliance_name_key.lower()] = site_info['SiteId']
                            app_map[appliance_name_key] = site_info['SiteId']
                        elif isinstance(site_info, str):
                            # Store both lowercase and original case
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
                
        # Validate SourceApplianceName & TargetApplianceName - try both original and lowercase
        source_site_id = app_map.get(source_appliance_name) or app_map.get(source_appliance_name.lower())
        target_site_id = app_map.get(target_appliance_name) or app_map.get(target_appliance_name.lower())
        
        if not source_site_id:
            # Provide helpful error message with available appliances (filter out duplicates)
            available_appliances = list(set(k for k in app_map.keys() if not k.islower()))
            if not available_appliances:
                # If all keys are lowercase, show them
                available_appliances = list(set(app_map.keys()))
            raise CLIError(f"Source appliance '{source_appliance_name}' not found in discovery solution. Available appliances: {', '.join(available_appliances)}")
        if not target_site_id:
            # Provide helpful error message with available appliances (filter out duplicates)
            available_appliances = list(set(k for k in app_map.keys() if not k.islower()))
            if not available_appliances:
                # If all keys are lowercase, show them
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
        replication_fabrics_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationFabrics"
        fabrics_uri = f"{replication_fabrics_uri}?api-version={APIVersion.Microsoft_DataReplication.value}"
        fabrics_response = send_get_request(cmd, fabrics_uri)
        all_fabrics = fabrics_response.json().get('value', [])
        
        for fabric in all_fabrics:
            props = fabric.get('properties', {})
            custom_props = props.get('customProperties', {})

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
            
            # Check if fabric name contains appliance name or vice versa
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
                
                if all_fabrics:
                    error_msg += f"\n\nAvailable fabrics in resource group:\n"
                    for fabric in all_fabrics:
                        props = fabric.get('properties', {})
                        custom_props = props.get('customProperties', {})
                        error_msg += f"  - {fabric.get('name')} (type: {custom_props.get('instanceType')})\n"
            
            raise CLIError(error_msg)
                
        # Get source fabric agent (DRA)
        source_fabric_name = source_fabric.get('name')
        dras_uri = f"{replication_fabrics_uri}/{source_fabric_name}/fabricAgents?api-version={APIVersion.Microsoft_DataReplication.value}"
        source_dras_response = send_get_request(cmd, dras_uri)
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
        target_dras_uri = f"{replication_fabrics_uri}/{target_fabric_name}/fabricAgents?api-version={APIVersion.Microsoft_DataReplication.value}"
        target_dras_response = send_get_request(cmd, target_dras_uri)
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
                
        # Setup Policy
        policy_name = f"{replication_vault_name}{instance_type}policy"
        policy_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationPolicies/{policy_name}"
        
        # Try to get existing policy, handle not found gracefully
        try:
            policy = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
        except Exception as e:
            error_str = str(e)
            if "ResourceNotFound" in error_str or "404" in error_str or "Not Found" in error_str:
                # Policy doesn't exist, this is expected for new setups
                print(f"Policy '{policy_name}' does not exist, will create it.")
                policy = None
            else:
                # Some other error occurred, re-raise it
                raise
        
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
        if not policy or (policy and policy.get('properties', {}).get('provisioningState') == ProvisioningState.Deleted.value):
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
                try:
                    policy = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
                except Exception as poll_error:
                    # During creation, it might still return 404 initially
                    if "ResourceNotFound" in str(poll_error) or "404" in str(poll_error):
                        print(f"Policy creation in progress... ({i+1}/20)")
                        continue
                    else:
                        raise
                
                if policy:
                    provisioning_state = policy.get('properties', {}).get('provisioningState')
                    print(f"Policy state: {provisioning_state}")
                    if provisioning_state in [ProvisioningState.Succeeded.value, ProvisioningState.Failed.value, 
                                             ProvisioningState.Canceled.value, ProvisioningState.Deleted.value]:
                        break
        
        if not policy or policy.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"Policy '{policy_name}' is not in Succeeded state.")
                
        # Setup Cache Storage Account
        amh_stored_storage_account_id = amh_solution.get('properties', {}).get('details', {}).get('extendedDetails', {}).get('replicationStorageAccountId')
        cache_storage_account = None
        
        if amh_stored_storage_account_id:
            # Check existing storage account
            storage_account_name = amh_stored_storage_account_id.split("/")[8]
            storage_uri = f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            storage_account = get_resource_by_id(cmd, storage_uri, APIVersion.Microsoft_Storage.value)
            
            if storage_account and storage_account.get('properties', {}).get('provisioningState') == StorageAccountProvisioningState.Succeeded.value:
                cache_storage_account = storage_account
                if cache_storage_account_id and cache_storage_account['id'] != cache_storage_account_id:
                    logger.warning(f"A Cache Storage Account '{storage_account_name}' is already linked. Ignoring provided -cache_storage_account_id.")
        
        # Use user-provided storage account if no existing one
        if not cache_storage_account and cache_storage_account_id:
            storage_account_name = cache_storage_account_id.split("/")[8].lower()
            storage_uri = f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
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
                    "allowBlobPublicAccess": False,
                    "allowCrossTenantReplication": True,
                    "minimumTlsVersion": "TLS1_2",
                    "networkAcls": {
                        "defaultAction": "Allow"
                    },
                    "encryption": {
                        "services": {
                            "blob": {"enabled": True},
                            "file": {"enabled": True}
                        },
                        "keySource": "Microsoft.Storage"
                    },
                    "accessTier": "Hot"
                }
            }
            
            storage_uri = f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            cache_storage_account = create_or_update_resource(cmd, storage_uri, APIVersion.Microsoft_Storage.value, storage_body)
            
            for i in range(20):
                time.sleep(30)
                cache_storage_account = get_resource_by_id(cmd, storage_uri, APIVersion.Microsoft_Storage.value)
                if cache_storage_account and cache_storage_account.get('properties', {}).get('provisioningState') == StorageAccountProvisioningState.Succeeded.value:
                    break
        
        if not cache_storage_account or cache_storage_account.get('properties', {}).get('provisioningState') != StorageAccountProvisioningState.Succeeded.value:
            raise CLIError("Failed to setup Cache Storage Account.")
        
        storage_account_id = cache_storage_account['id']
        
        # Verify storage account network settings
        print("Verifying storage account network configuration...")
        network_acls = cache_storage_account.get('properties', {}).get('networkAcls', {})
        default_action = network_acls.get('defaultAction', 'Allow')
        
        if default_action != 'Allow':
            print(f"WARNING: Storage account network defaultAction is '{default_action}'. This may cause permission issues.")
            print("Updating storage account to allow public network access...")
            
            # Update storage account to allow public access
            storage_account_name = storage_account_id.split("/")[-1]
            storage_uri = f"{rg_uri}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            
            update_body = {
                "properties": {
                    "networkAcls": {
                        "defaultAction": "Allow"
                    }
                }
            }
            
            create_or_update_resource(cmd, storage_uri, APIVersion.Microsoft_Storage.value, update_body)
            
            # Wait for network update to propagate
            print("Waiting 30 seconds for network configuration update...")
            time.sleep(30)
                
        # Grant permissions (Role Assignments)
        from azure.mgmt.authorization import AuthorizationManagementClient
        from azure.mgmt.authorization.models import RoleAssignmentCreateParameters, PrincipalType
        
        # Get role assignment client using the correct method for Azure CLI
        auth_client = get_mgmt_service_client(cmd.cli_ctx, AuthorizationManagementClient)
        
        source_dra_object_id = source_dra.get('properties', {}).get('resourceAccessIdentity', {}).get('objectId')
        target_dra_object_id = target_dra.get('properties', {}).get('resourceAccessIdentity', {}).get('objectId')
        
        # Get vault identity from either root level or properties level
        vault_identity = replication_vault.get('identity') or replication_vault.get('properties', {}).get('identity')
        vault_identity_id = vault_identity.get('principalId') if vault_identity else None
        
        print("Granting permissions to the storage account...")
        print(f"  Source DRA Principal ID: {source_dra_object_id}")
        print(f"  Target DRA Principal ID: {target_dra_object_id}")
        print(f"  Vault Identity Principal ID: {vault_identity_id}")
        
        # Track successful role assignments
        successful_assignments = []
        failed_assignments = []
        
        # Create role assignments for source and target DRAs
        for object_id in [source_dra_object_id, target_dra_object_id]:
            if object_id:
                for role_def_id in [RoleDefinitionIds.ContributorId, RoleDefinitionIds.StorageBlobDataContributorId]:
                    role_name = "Contributor" if role_def_id == RoleDefinitionIds.ContributorId else "Storage Blob Data Contributor"
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
                                principal_id=object_id,
                                principal_type=PrincipalType.SERVICE_PRINCIPAL
                            )
                            auth_client.role_assignments.create(
                                scope=storage_account_id,
                                role_assignment_name=str(uuid4()),
                                parameters=role_assignment_params
                            )
                            print(f"  ✓ Created {role_name} role for DRA {object_id[:8]}...")
                            successful_assignments.append(f"{object_id[:8]} - {role_name}")
                        else:
                            print(f"  ✓ {role_name} role already exists for DRA {object_id[:8]}")
                            successful_assignments.append(f"{object_id[:8]} - {role_name} (existing)")
                    except Exception as e:
                        error_msg = f"{object_id[:8]} - {role_name}: {str(e)}"
                        failed_assignments.append(error_msg)
                        logger.warning(f"Failed to create role assignment: {str(e)}")
        
        # Grant vault identity permissions if exists
        if vault_identity_id:
            for role_def_id in [RoleDefinitionIds.ContributorId, RoleDefinitionIds.StorageBlobDataContributorId]:
                role_name = "Contributor" if role_def_id == RoleDefinitionIds.ContributorId else "Storage Blob Data Contributor"
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
                            principal_id=vault_identity_id,
                            principal_type=PrincipalType.SERVICE_PRINCIPAL
                        )
                        auth_client.role_assignments.create(
                            scope=storage_account_id,
                            role_assignment_name=str(uuid4()),
                            parameters=role_assignment_params
                        )
                        print(f"  ✓ Created {role_name} role for vault {vault_identity_id[:8]}...")
                        successful_assignments.append(f"{vault_identity_id[:8]} - {role_name}")
                    else:
                        print(f"  ✓ {role_name} role already exists for vault {vault_identity_id[:8]}")
                        successful_assignments.append(f"{vault_identity_id[:8]} - {role_name} (existing)")
                except Exception as e:
                    error_msg = f"{vault_identity_id[:8]} - {role_name}: {str(e)}"
                    failed_assignments.append(error_msg)
                    logger.warning(f"Failed to create vault role assignment: {str(e)}")
        
        # Report role assignment status
        print(f"\nRole Assignment Summary:")
        print(f"  Successful: {len(successful_assignments)}")
        if failed_assignments:
            print(f"  Failed: {len(failed_assignments)}")
            for failure in failed_assignments:
                print(f"    - {failure}")
        
        # If there are failures, raise an error
        if failed_assignments:
            raise CLIError(f"Failed to create {len(failed_assignments)} role assignment(s). The storage account may not have proper permissions.")
        
        # Add a wait after role assignments to ensure propagation
        print("\nWaiting 120 seconds for role assignments to propagate...")
        time.sleep(120)
        
        # Verify role assignments were successful
        print("Verifying role assignments...")
        all_assignments = list(auth_client.role_assignments.list_for_scope(scope=storage_account_id))
        verified_principals = set()
        for assignment in all_assignments:
            principal_id = assignment.principal_id
            if principal_id in [source_dra_object_id, target_dra_object_id, vault_identity_id]:
                verified_principals.add(principal_id)
                role_id = assignment.role_definition_id.split('/')[-1]
                role_display = "Contributor" if role_id == RoleDefinitionIds.ContributorId else "Storage Blob Data Contributor"
                print(f"  ✓ Verified {role_display} for principal {principal_id[:8]}")
        
        expected_principals = {source_dra_object_id, target_dra_object_id, vault_identity_id}
        missing_principals = expected_principals - verified_principals
        if missing_principals:
            print(f"WARNING: {len(missing_principals)} principal(s) missing role assignments:")
            for principal in missing_principals:
                print(f"  - {principal}")
        
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
            
            # Wait for the AMH solution update to fully propagate
            print("Waiting 60 seconds for AMH solution update to propagate...")
            time.sleep(60)
        
        # Setup Replication Extension
        source_fabric_id = source_fabric['id']
        target_fabric_id = target_fabric['id']
        source_fabric_short_name = source_fabric_id.split('/')[-1]
        target_fabric_short_name = target_fabric_id.split('/')[-1]
        replication_extension_name = f"{source_fabric_short_name}-{target_fabric_short_name}-MigReplicationExtn"

        extension_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationExtensions/{replication_extension_name}"
        
        # Try to get existing extension, handle not found gracefully
        try:
            replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
        except Exception as e:
            error_str = str(e)
            if "ResourceNotFound" in error_str or "404" in error_str or "Not Found" in error_str:
                # Extension doesn't exist, this is expected for new setups
                print(f"Extension '{replication_extension_name}' does not exist, will create it.")
                replication_extension = None
            else:
                # Some other error occurred, re-raise it
                raise
        
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
        
        print("\nVerifying prerequisites before creating extension...")
        
        # 1. Verify policy is succeeded
        policy_check = get_resource_by_id(cmd, policy_uri, APIVersion.Microsoft_DataReplication.value)
        if policy_check.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"Policy is not in Succeeded state: {policy_check.get('properties', {}).get('provisioningState')}")
        
        # 2. Verify storage account is succeeded
        storage_check = get_resource_by_id(cmd, storage_uri, APIVersion.Microsoft_Storage.value)
        if storage_check.get('properties', {}).get('provisioningState') != StorageAccountProvisioningState.Succeeded.value:
            raise CLIError(f"Storage account is not in Succeeded state: {storage_check.get('properties', {}).get('provisioningState')}")
        
        # 3. Verify AMH solution has storage account
        solution_check = get_resource_by_id(cmd, amh_solution_uri, APIVersion.Microsoft_Migrate.value)
        if solution_check.get('properties', {}).get('details', {}).get('extendedDetails', {}).get('replicationStorageAccountId') != storage_account_id:
            raise CLIError("AMH solution doesn't have the correct storage account ID")
        
        # 4. Verify fabrics are responsive
        source_fabric_check = get_resource_by_id(cmd, source_fabric_id, APIVersion.Microsoft_DataReplication.value)
        if source_fabric_check.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"Source fabric is not in Succeeded state")
        
        target_fabric_check = get_resource_by_id(cmd, target_fabric_id, APIVersion.Microsoft_DataReplication.value)
        if target_fabric_check.get('properties', {}).get('provisioningState') != ProvisioningState.Succeeded.value:
            raise CLIError(f"Target fabric is not in Succeeded state")
        
        print("All prerequisites verified successfully!")
        time.sleep(30)

        # Create replication extension if needed
        if not replication_extension:
            print(f"Creating Replication Extension '{replication_extension_name}'...")
            existing_extensions_uri = f"{rg_uri}/providers/Microsoft.DataReplication/replicationVaults/{replication_vault_name}/replicationExtensions"
            try:
                existing_extensions_response = send_get_request(cmd, f"{existing_extensions_uri}?api-version={APIVersion.Microsoft_DataReplication.value}")
                existing_extensions = existing_extensions_response.json().get('value', [])
                if existing_extensions:
                    print(f"Found {len(existing_extensions)} existing extension(s):")
                    for ext in existing_extensions:
                        ext_name = ext.get('name')
                        ext_state = ext.get('properties', {}).get('provisioningState')
                        ext_type = ext.get('properties', {}).get('customProperties', {}).get('instanceType')
                        print(f"  - {ext_name}: state={ext_state}, type={ext_type}")
                else:
                    print("No existing extensions found")
            except Exception as list_error:
                # If listing fails, it might mean no extensions exist at all
                print(f"Could not list extensions (this is normal for new projects): {str(list_error)}")
            
            print("\n=== Creating extension for replication infrastructure ===")
            print(f"Instance Type: {instance_type}")
            print(f"Source Fabric ID: {source_fabric_id}")
            print(f"Target Fabric ID: {target_fabric_id}")
            print(f"Storage Account ID: {storage_account_id}")
            
            # Build the extension body with properties in the exact order from the working API call
            if instance_type == AzLocalInstanceTypes.VMwareToAzLocal.value:
                # Match exact property order from working call for VMware
                extension_body = {
                    "properties": {
                        "customProperties": {
                            "azStackHciFabricArmId": target_fabric_id,
                            "storageAccountId": storage_account_id,
                            "storageAccountSasSecretName": None,
                            "instanceType": instance_type,
                            "vmwareFabricArmId": source_fabric_id
                        }
                    }
                }
            elif instance_type == AzLocalInstanceTypes.HyperVToAzLocal.value:
                # For HyperV, use similar order but with hyperVFabricArmId
                extension_body = {
                    "properties": {
                        "customProperties": {
                            "azStackHciFabricArmId": target_fabric_id,
                            "storageAccountId": storage_account_id,
                            "storageAccountSasSecretName": None,
                            "instanceType": instance_type,
                            "hyperVFabricArmId": source_fabric_id
                        }
                    }
                }
            else:
                raise CLIError(f"Unsupported instance type: {instance_type}")
            
            # Debug: Print the exact body being sent
            import json
            print(f"Extension body being sent:\n{json.dumps(extension_body, indent=2)}")
            
            try:
                result = create_or_update_resource(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value, extension_body, no_wait=False)                
                if result:
                    print("Extension creation initiated successfully")
                    # Wait for the extension to be created
                    print("Waiting for extension creation to complete...")
                    for i in range(20):
                        time.sleep(30)
                        try:
                            replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
                            if replication_extension:
                                ext_state = replication_extension.get('properties', {}).get('provisioningState')
                                print(f"Extension state: {ext_state}")
                                if ext_state in [ProvisioningState.Succeeded.value, ProvisioningState.Failed.value, ProvisioningState.Canceled.value]:
                                    break
                        except:
                            print(f"Waiting for extension... ({i+1}/20)")
            except Exception as create_error:
                error_str = str(create_error)
                print(f"Error during extension creation: {error_str}")
                
                # Check if extension was created despite the error
                time.sleep(30)
                try:
                    replication_extension = get_resource_by_id(cmd, extension_uri, APIVersion.Microsoft_DataReplication.value)
                    if replication_extension:
                        print(f"Extension exists despite error, state: {replication_extension.get('properties', {}).get('provisioningState')}")
                except:
                    replication_extension = None
                
                if not replication_extension:
                    raise CLIError(f"Failed to create replication extension: {str(create_error)}")
        
        print("Successfully initialized replication infrastructure")
        
        if pass_thru:
            return True
            
    except Exception as e:
        logger.error(f"Error initializing replication infrastructure: {str(e)}")
        raise CLIError(f"Failed to initialize replication infrastructure: {str(e)}")
