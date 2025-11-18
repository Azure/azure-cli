# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
# pylint: disable=line-too-long

import base64
import os
import zipfile
from io import BytesIO
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def deploy_edge_action_version(cmd, resource_group, edge_action_name, version,
                               file_path, deployment_type=None, no_wait=False):
    """Deploy edge action version code from a file.

    This is a custom command that provides file-based deployment for edge action versions.
    It processes JavaScript or zip files and deploys them to the specified version.

    Args:
        cmd: Command context
        resource_group: Resource group name
        edge_action_name: Edge action name
        version: Version name
        file_path: Path to JavaScript or zip file
        deployment_type: Deployment type ('file' for JS, 'zip' for zip archives), auto-detected if not specified
        no_wait: Don't wait for long-running operation
    """
    from .aaz.latest.edge_action.version._deploy_version_code import DeployVersionCode

    # Validate file exists
    if not os.path.isfile(file_path):
        raise CLIError(f"File not found: {file_path}")

    # Validate it's not a directory
    if os.path.isdir(file_path):
        raise CLIError(
            f"Directories are not supported. Please specify a file: {file_path}")

    # Determine deployment type from file extension if not specified
    if deployment_type is None:
        # Auto-detect from extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext == '.js':
            deployment_type = 'file'  # JS files use 'file' deployment type
        elif ext == '.zip':
            deployment_type = 'zip'   # Zip files use 'zip' deployment type
        else:
            raise CLIError(
                f"Cannot determine deployment type from extension '{ext}'. "
                "Please specify --deployment-type (file or zip).")

    # Get file extension for validation
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip('.')

    # Validate deployment type and file extension combinations
    if deployment_type == 'file':
        # 'file' deployment type: Only accept .js files
        if ext not in ['js']:
            raise CLIError(
                f"Deployment type 'file' requires a JavaScript (.js) file, but got '.{ext}'. "
                "Use --deployment-type zip for zip files or provide a .js file.")
    elif deployment_type == 'zip':
        # 'zip' deployment type: Accept both .js (will auto-zip) and .zip files
        if ext not in ['js', 'zip']:
            raise CLIError(
                f"Deployment type 'zip' requires a JavaScript (.js) or zip (.zip) file, but got '.{ext}'. "
                "Please provide a .js or .zip file.")
    else:
        raise CLIError(
            f"Invalid deployment type '{deployment_type}'. "
            "Valid values are 'file' (for .js) or 'zip' (for .zip or auto-zipped .js).")

    logger.info("Processing file: %s (deployment type: %s)", file_path, deployment_type)

    # Process file based on deployment type and file extension
    if deployment_type == 'file':
        # 'file' deployment type: JS file, encode as-is without zipping
        logger.info("Reading JavaScript file for 'file' deployment type (no zipping)")
        with open(file_path, 'rb') as f:
            file_content = f.read()
        encoded_content = base64.b64encode(file_content).decode('utf-8')
    elif deployment_type == 'zip':
        # 'zip' deployment type: Can be .js (auto-zip) or .zip (use as-is)
        if ext == 'zip':
            # Already a zip file, just encode it
            logger.info("Reading zip file for 'zip' deployment type")
            with open(file_path, 'rb') as f:
                zip_content = f.read()
            encoded_content = base64.b64encode(zip_content).decode('utf-8')
        else:  # ext == 'js'
            # JS file with zip deployment type - auto-zip it
            logger.info("Auto-zipping JavaScript file for 'zip' deployment type")
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(file_path, os.path.basename(file_path))
            zip_content = buffer.getvalue()
            encoded_content = base64.b64encode(zip_content).decode('utf-8')

    logger.info("Content encoded to base64 (length: %d)", len(encoded_content))

    # Use version name as deployment name
    name = version

    # Call the AAZ command with the processed content
    logger.info("Deploying to version %s with name %s", version, name)
    return DeployVersionCode(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group,
        'edge_action_name': edge_action_name,
        'version': version,
        'content': encoded_content,
        'name': name,
        'no_wait': no_wait
    })
