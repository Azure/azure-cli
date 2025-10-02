# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import platform
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.util import send_raw_request
from azure.cli.command_modules.migrate._powershell_utils import get_powershell_executor
from enum import Enum

logger = get_logger(__name__)

class APIVersion(Enum):
    Microsoft_Authorization = "2022-04-01"
    Microsoft_ResourceGraph = "2021-03-01"
    Microsoft_DataReplication = "2024-09-01"
    Microsoft_Resources = "2025-04-01"
    Microsoft_OffAzure = "2023-06-06"
    Microsoft_Storage = "2025-01-01"
    Microsoft_Migrate = "2020-05-01"
    Microsoft_HybridCompute = "2024-07-10"

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
    # Validate the protected item ID format
    if not protected_item_id or not protected_item_id.startswith('/'):
        raise CLIError("Invalid protected_item_id. Must be a full ARM resource ID starting with '/'.")
    
    # Construct the ARM URI with API version for Microsoft.DataReplication
    uri = f"{protected_item_id}?api-version=2024-09-01"
    request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + uri
    
    response = send_raw_request(
        cmd.cli_ctx,
        method='GET',
        url=request_uri,
    )
    
    # if response.status_code >= 400:
    #     error_message = f"Failed to retrieve protected item. Status: {response.status_code}"
        
    #     try:
    #         error_body = response.json()
    #         if 'error' in error_body:
    #             error_details = error_body['error']
    #             error_message += f", Code: {error_details.get('code', 'Unknown')}"
    #             error_message += f", Message: {error_details.get('message', 'No message provided')}"
    #     except (ValueError, KeyError):
    #         error_message += f", Response: {response.text}"
        
    #     raise CLIError(error_message)
    
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
        subscription_id = cmd.cli_ctx.data.get('subscription_id')
    
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
        response = send_raw_request(
            cmd.cli_ctx,
            method='GET',
            url=request_uri,
        )
        
        if response.status_code >= 400:
            error_message = f"Failed to retrieve discovered servers. Status: {response.status_code}"
            try:
                error_body = response.json()
                if 'error' in error_body:
                    error_details = error_body['error']
                    error_message += f", Code: {error_details.get('code', 'Unknown')}"
                    error_message += f", Message: {error_details.get('message', 'No message provided')}"
            except (ValueError, KeyError):
                error_message += f", Response: {response.text}"
            raise CLIError(error_message)
        
        discovered_servers_data = response.json()
        
        # Apply client-side filtering for display_name when using site endpoints
        if appliance_name and display_name and 'value' in discovered_servers_data:
            filtered_servers = []
            for server in discovered_servers_data['value']:
                properties = server.get('properties', {})
                server_display_name = properties.get('displayName', '')
                if server_display_name == display_name:
                    filtered_servers.append(server)
            discovered_servers_data['value'] = filtered_servers
        
        return discovered_servers_data
        
    except Exception as e:
        logger.error(f"Error retrieving discovered servers: {str(e)}")
        raise CLIError(f"Failed to retrieve discovered servers: {str(e)}")