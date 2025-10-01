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
    try:
        # Validate the protected item ID format
        if not protected_item_id or not protected_item_id.startswith('/'):
            raise CLIError("Invalid protected_item_id. Must be a full ARM resource ID starting with '/'.")
        
        # Construct the ARM URI with API version for Microsoft.DataReplication
        api_version = "2021-02-16-preview"  # Microsoft.DataReplication API version
        uri = f"https://management.azure.com{protected_item_id}?api-version={api_version}"
        
        response = send_raw_request(
            cmd.cli_ctx,
            method='GET',
            url=uri,
        )
        
        if response.status_code >= 400:
            error_message = f"Failed to retrieve protected item. Status: {response.status_code}"
            
            try:
                error_body = response.json()
                if 'error' in error_body:
                    error_details = error_body['error']
                    error_message += f", Code: {error_details.get('code', 'Unknown')}"
                    error_message += f", Message: {error_details.get('message', 'No message provided')}"
            except (ValueError, KeyError):
                error_message += f", Response: {response.text}"
            
            raise CLIError(error_message)
        
        protected_item_data = response.json()
        
        return protected_item_data
    
    except Exception as e:
        raise CLIError(error_message)