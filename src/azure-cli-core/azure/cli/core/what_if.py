# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Module for handling what-if functionality in Azure CLI.
This module provides the core logic for preview mode execution without actually running commands.

IMPORTANT: The what-if service requires client-side authentication to operate under the 
caller's subscription and permissions. Server-side authentication is not supported for 
what-if operations as it would not provide access to the caller's subscription.

This client now uses AzureCliCredential to obtain an access token for the caller's subscription.
    
The what-if service will use your configured credentials to access your subscription
and preview deployment changes under your permissions.
"""

import requests
from typing import Dict, Any, Optional
from azure.identity import AzureCliCredential
from datetime import datetime, timezone
from knack.log import get_logger

logger = get_logger(__name__)

# Configuration
FUNCTION_APP_URL = "https://azcli-script-insight.azurewebsites.net"


def get_azure_cli_access_token() -> Optional[str]:
    """
    Get access token for the caller's subscription using AzureCliCredential

    Returns:
        Access token string if successful, None if failed
    """
    token_info = get_azure_cli_token_info()
    return token_info.get("accessToken") if token_info else None


def get_azure_cli_token_info() -> Optional[Dict[str, Any]]:
    """
    Get complete token information using AzureCliCredential including expiration
    
    Returns:
        Dictionary with token info including accessToken, expiresOn, etc., or None if failed
    """
    try:
        # Use AzureCliCredential for Azure CLI authentication
        cli_credential = AzureCliCredential(process_timeout=30)

        # Get access token for Azure Resource Manager
        token = cli_credential.get_token("https://management.azure.com/.default")

        token_info = {
            "accessToken": token.token,
            "expiresOn": datetime.fromtimestamp(token.expires_on, tz=timezone.utc).isoformat(),
            "tokenType": "Bearer"
        }

        return token_info

    except Exception as e:
        logger.warning(f"Error getting access token with AzureCliCredential: {str(e)}")
        return None


def what_if_preview(azcli_script: str, subscription_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Preview deployment changes using Azure what-if functionality
    
    Args:
        function_app_url: Base URL of your Azure Function App
        azcli_script: Azure CLI script to analyze
        subscription_id: Optional fallback subscription ID if not in script
        
    Returns:
        Dictionary with what-if preview result
    """
    url = f"{FUNCTION_APP_URL.rstrip('/')}/api/what_if_preview"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Get access token from Azure CLI
    access_token = get_azure_cli_access_token()
    if not access_token:
        return {
            "error": "Failed to get access token from Azure CLI. Please ensure you are logged in with 'az login'",
            "details": "The what-if service requires client credentials to access your subscription. Please provide an access token.",
            "success": False
        }
    
    # Use Authorization header for access token
    headers['Authorization'] = f'Bearer {access_token}'
    
    payload = {"azcli_script": azcli_script}
    if subscription_id:
        payload["subscription_id"] = subscription_id
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        return response.json()
    except requests.RequestException as e:
        raise e
