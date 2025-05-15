# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for disconnected operations module."""

import os
import platform
import shutil
import subprocess
from typing import Any, Dict, Optional

import requests
from knack.log import get_logger

# Constants
PROVIDER_NAMESPACE = "Microsoft.Edge"
SUB_PROVIDER = "Microsoft.EdgeMarketplace"
API_VERSION = "2023-08-01-preview"
CATALOG_API_VERSION = "2021-06-01"

logger = get_logger(__name__)


# pylint: disable=too-few-public-methods
class OperationResult:
    """Standard result object for operations."""

    def __init__(self, success: bool, message: str = "", data: Any = None, error: str = ""):
        self.success = success
        self.message = message
        self.data = data or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        result = {
            "status": "succeeded" if self.success else "failed"
        }

        if self.message:
            result["message"] = self.message

        if self.error:
            result["error"] = self.error

        if self.data:
            result.update(self.data)

        return result


def get_management_endpoint(cli_ctx) -> str:
    """Get management endpoint based on cloud configuration."""
    cloud = cli_ctx.cloud

    # Remove ending slash if exists
    endpoint = cloud.endpoints.resource_manager
    if endpoint.endswith("/"):
        endpoint = endpoint[:-1]

    # Append https:// if not exists
    if not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint

    return endpoint


def handle_directory_cleanup(path: str) -> Optional[OperationResult]:
    """Clean up existing directory.

    Args:
        path: Directory path to clean up

    Returns:
        None if successful, OperationResult with error details if failed
    """
    if os.path.exists(path):
        try:
            # Remove directory and all its contents
            shutil.rmtree(path)
            logger.info("Cleaned up existing directory: %s", path)
            return None
        except OSError as e:
            error_message = f"Failed to clean up directory {path}: {str(e)}"
            logger.error(error_message)
            return OperationResult(
                success=False,
                error=error_message,
                data={"path": path}
            )
    return None


def download_file(url: str, file_path: str) -> bool:
    """Download a file from URL to specified path.

    Args:
        url: Source URL
        file_path: Destination file path

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            logger.info("Downloaded file to %s", file_path)
            return True

        logger.error("Failed to download file: %s", response.status_code)
        return False
    except requests.RequestException as e:
        logger.error("Error downloading file: %s", str(e))
        return False


def is_azcopy_available() -> bool:
    """Check if azcopy is available in the system path."""
    # First try using shutil.which which is the proper way to check for executables
    if shutil.which("azcopy"):
        return True

    # Fallback to trying the command directly
    try:
        result = subprocess.run(
            ["azcopy", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_azcopy_install_info() -> Dict[str, str]:
    """Get OS-specific AzCopy installation information."""
    system = platform.system().lower()

    if system == 'windows':
        return {
            "url": "https://aka.ms/downloadazcopy-v10-windows",
            "instructions": "Download, extract the ZIP file, and add the extracted folder to your PATH."
        }
    if system == 'linux':
        return {
            "url": "https://aka.ms/downloadazcopy-v10-linux",
            "instructions": "Download, extract the tar.gz file, and move the azcopy binary to a directory in your PATH."
        }
    if system == 'darwin':  # macOS
        return {
            "url": "https://aka.ms/downloadazcopy-v10-mac",
            "instructions": "Download, extract the .zip file, and move the azcopy binary to a directory in your PATH."
        }

    return {
        "url": "https://aka.ms/downloadazcopy",
        "instructions": "Download and install AzCopy for your platform."
    }


def construct_resource_uri(subscription_id: str, resource_group_name: str, resource_name: str) -> str:
    """Construct a resource URI for disconnected operations.

    Args:
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        resource_name: Resource name

    Returns:
        Resource URI string
    """
    return (
        f"/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group_name}"
        f"/providers/{PROVIDER_NAMESPACE}/disconnectedOperations/{resource_name}"
    )
