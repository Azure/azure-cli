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

class ProvisioningState(Enum):
    Succeeded = "Succeeded"
    Creating = "Creating"
    Updating = "Updating"
    Deleting = "Deleting"
    Deleted = "Deleted"
    Failed = "Failed"
    Canceled = "Canceled"

class StorageAccountProvisioningState(Enum):
    Succeeded = "Succeeded"
    Creating = "Creating"
    ResolvingDNS = "ResolvingDNS"

class AzLocalInstanceTypes(Enum):
    HyperVToAzLocal = "HyperVToAzStackHci"
    VMwareToAzLocal = "VMwareToAzStackHci"

class FabricInstanceTypes(Enum):
    HyperVInstance = "HyperVInstance"
    VMwareInstance = "VMwareInstance"
    AzLocalInstance = "AzStackHciInstance"

class RoleDefinitionIds:
    ContributorId = "b24988ac-6180-42a0-ab88-20f7382dd24c"
    StorageBlobDataContributorId = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"

class ReplicationDetails:
    class PolicyDetails:
        DefaultRecoveryPointHistoryInMinutes = 4320  # 72 hours
        DefaultCrashConsistentFrequencyInMinutes = 60  # 1 hour
        DefaultAppConsistentFrequencyInMinutes = 240  # 4 hours

def batch_call(cmd, request_uri):
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
    return response

def generate_hash_for_artifact(artifact):
    """Generate a hash for the given artifact string."""
    hash_object = hashlib.sha256(artifact.encode())
    hex_dig = hash_object.hexdigest()
    # Convert to numeric hash similar to PowerShell GetHashCode
    numeric_hash = int(hex_dig[:8], 16)
    return str(numeric_hash)

def get_resource_by_id(cmd, resource_id, api_version):
    """Get an Azure resource by its ARM ID."""
    uri = f"{resource_id}?api-version={api_version}"
    request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + uri
    
    response = send_raw_request(
        cmd.cli_ctx,
        method='GET',
        url=request_uri,
    )
    
    if response.status_code >= 400:
        return None
    
    return response.json()

def create_or_update_resource(cmd, resource_id, api_version, properties, no_wait=False):
    """Create or update an Azure resource."""
    uri = f"{resource_id}?api-version={api_version}"
    request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + uri
    
    response = send_raw_request(
        cmd.cli_ctx,
        method='PUT',
        url=request_uri,
        json=properties
    )
    
    if response.status_code >= 400 and response.status_code != 200:
        error_message = f"Failed to create/update resource. Status: {response.status_code}"
        try:
            error_body = response.json()
            if 'error' in error_body:
                error_details = error_body['error']
                error_message += f", Code: {error_details.get('code', 'Unknown')}"
                error_message += f", Message: {error_details.get('message', 'No message provided')}"
        except (ValueError, KeyError):
            error_message += f", Response: {response.text}"
        raise CLIError(error_message)
    
    return response.json() if response.text else None

def delete_resource(cmd, resource_id, api_version):
    """Delete an Azure resource."""
    uri = f"{resource_id}?api-version={api_version}"
    request_uri = cmd.cli_ctx.cloud.endpoints.resource_manager + uri
    
    response = send_raw_request(
        cmd.cli_ctx,
        method='DELETE',
        url=request_uri,
    )
    
    return response.status_code < 400
