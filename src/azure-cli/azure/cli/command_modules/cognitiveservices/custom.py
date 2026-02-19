# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import urllib.parse
import os
import subprocess
import sys
import re
import datetime
from pathlib import Path

from knack.log import get_logger
from azure.cli.core.decorators import retry

import azure.core.rest

from azure.mgmt.cognitiveservices.models import Account as CognitiveServicesAccount, Sku, \
    VirtualNetworkRule, IpRule, NetworkRuleSet, NetworkRuleAction, \
    AccountProperties as CognitiveServicesAccountProperties, ApiProperties as CognitiveServicesAccountApiProperties, \
    Identity, ResourceIdentityType as IdentityType, \
    Deployment, DeploymentModel, DeploymentScaleSettings, DeploymentProperties, \
    CommitmentPlan, CommitmentPlanProperties, CommitmentPeriod, \
    ConnectionPropertiesV2BasicResource, ConnectionUpdateContent, \
    Project, ProjectProperties
from azure.cli.command_modules.cognitiveservices._client_factory import cf_accounts, cf_resource_skus
from azure.cli.core.azclierror import (
    BadRequestError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
    InvalidArgumentValueError,
    FileOperationError,
    AzureResponseError,
    ValidationError,
    DeploymentError,
    CLIInternalError,
    ResourceNotFoundError,
)
from azure.cli.command_modules.cognitiveservices._utils import load_connection_from_source, compose_identity

logger = get_logger(__name__)

# ACR Pack task YAML template for buildpack-based image builds
# Used when no Dockerfile exists - automatically detects Python, Node.js, .NET, etc.
PACK_TASK_YAML = """version: v1.1.0
steps:
  - cmd: mcr.microsoft.com/oryx/pack:stable build {image_name_full} --builder {builder} --env REGISTRY_NAME=$Registry -p .
    timeout: 28800
  - push: ["{image_name_full}"]
    timeout: 1800
"""


def list_resources(client, resource_group_name=None):
    """
    List all Azure Cognitive Services accounts.
    """
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def recover(client, location, resource_group_name, account_name):
    """
    Recover a deleted Azure Cognitive Services account.
    """
    properties = CognitiveServicesAccountProperties()
    properties.restore = True
    params = CognitiveServicesAccount(properties=properties)
    params.location = location

    return client.begin_create(resource_group_name, account_name, params)


def list_usages(client, resource_group_name, account_name):
    """
    List usages for Azure Cognitive Services account.
    """
    return client.list_usages(resource_group_name, account_name).value


def list_kinds(client):
    """
    List all valid kinds for Azure Cognitive Services account.

    :param client: the ResourceSkusOperations
    :return: a list
    """
    # The client should be ResourceSkusOperations, and list() should return a list of SKUs for all regions.
    # The sku will have "kind" and we use that to extract full list of kinds.
    kinds = {x.kind for x in client.list()}
    return sorted(list(kinds))


def list_skus(
    cmd, kind=None, location=None, resource_group_name=None, account_name=None
):
    """
    List skus for Azure Cognitive Services account.
    """
    if resource_group_name is not None or account_name is not None:
        logger.warning(
            "list-skus with an existing account has been deprecated and will be removed in a future release."
        )
        if resource_group_name is None:
            # account_name must not be None
            raise RequiredArgumentMissingError("--resource-group is required when --name is specified.")
        # keep the original behavior to avoid breaking changes
        return cf_accounts(cmd.cli_ctx).list_skus(resource_group_name, account_name)

    # in other cases, use kind and location to filter SKUs
    def _filter_sku(_sku):
        if kind is not None:
            if _sku.kind != kind:
                return False
        if location is not None:
            if location.lower() not in [x.lower() for x in _sku.locations]:
                return False
        return True

    return [x for x in cf_resource_skus(cmd.cli_ctx).list() if _filter_sku(x)]


def _is_valid_kind_change(current_kind, target_kind):
    valid_upgrades = {"AIServices": ["OpenAI"], "OpenAI": ["AIServices"]}
    return target_kind in valid_upgrades.get(current_kind, [])


def _kind_uses_project_management(kind):
    return kind in ["AIServices"]


def create(
    client,
    resource_group_name,
    account_name,
    sku_name,
    kind,
    location,
    custom_domain=None,
    tags=None,
    api_properties=None,
    assign_identity=False,
    storage=None,
    encryption=None,
    allow_project_management=None,
    yes=None,
):  # pylint: disable=unused-argument
    """
    Create an Azure Cognitive Services account.
    """

    sku = Sku(name=sku_name)

    if _kind_uses_project_management(kind) and allow_project_management is None:
        allow_project_management = True

    properties = CognitiveServicesAccountProperties()
    if api_properties is not None:
        api_properties = CognitiveServicesAccountApiProperties.deserialize(
            api_properties
        )
        properties.api_properties = api_properties
    if custom_domain:
        properties.custom_sub_domain_name = custom_domain

    if storage is not None:
        properties.user_owned_storage = json.loads(storage)

    if encryption is not None:
        properties.encryption = json.loads(encryption)

    properties.allow_project_management = allow_project_management
    params = CognitiveServicesAccount(sku=sku, kind=kind, location=location,
                                      properties=properties, tags=tags)
    if assign_identity or allow_project_management:
        params.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)

    return client.begin_create(resource_group_name, account_name, params)


def update(
    client,
    resource_group_name,
    account_name,
    sku_name=None,
    custom_domain=None,
    tags=None,
    api_properties=None,
    storage=None,
    encryption=None,
    allow_project_management=None,
    kind=None,
):
    """
    Update an Azure Cognitive Services account.
    """
    sa = None
    if sku_name is None:
        sa = client.get(resource_group_name, account_name)
        sku_name = sa.sku.name

    sku = Sku(name=sku_name)

    properties = CognitiveServicesAccountProperties()
    if api_properties is not None:
        api_properties = CognitiveServicesAccountApiProperties.deserialize(
            api_properties
        )
        properties.api_properties = api_properties
    if custom_domain:
        properties.custom_sub_domain_name = custom_domain
    if allow_project_management is not None:
        properties.allow_project_management = allow_project_management
    if storage is not None:
        properties.user_owned_storage = json.loads(storage)
    if encryption is not None:
        properties.encryption = json.loads(encryption)

    if kind is not None:
        if sa is None:
            sa = client.get(resource_group_name, account_name)
        if kind != sa.kind and not _is_valid_kind_change(sa.kind, kind):
            raise BadRequestError("Changing the account kind from '{}' to '{}' is not supported.".format(sa.kind, kind))
        if _kind_uses_project_management(kind) and allow_project_management is None:
            properties.allow_project_management = True

    params = CognitiveServicesAccount(kind=kind, sku=sku, properties=properties, tags=tags)

    return client.begin_update(resource_group_name, account_name, params)


def default_network_acls():
    rules = NetworkRuleSet()
    rules.default_action = NetworkRuleAction.deny
    rules.ip_rules = []
    rules.virtual_network_rules = []
    return rules


def list_network_rules(client, resource_group_name, account_name):
    """
    List network rules for Azure Cognitive Services account.
    """
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        rules = default_network_acls()
    return rules


def add_network_rule(
    client,
    resource_group_name,
    account_name,
    subnet=None,
    vnet_name=None,
    ip_address=None,
):  # pylint: disable=unused-argument
    """
    Add a network rule for Azure Cognitive Services account.
    """
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        rules = default_network_acls()

    if subnet:
        from azure.mgmt.core.tools import is_valid_resource_id

        if not is_valid_resource_id(subnet):
            raise InvalidArgumentValueError(
                f"Expected fully qualified resource ID: got '{subnet}'"
            )

        if not rules.virtual_network_rules:
            rules.virtual_network_rules = []
        rules.virtual_network_rules.append(
            VirtualNetworkRule(id=subnet, ignore_missing_vnet_service_endpoint=True)
        )
    if ip_address:
        if not rules.ip_rules:
            rules.ip_rules = []
        rules.ip_rules.append(IpRule(value=ip_address))

    properties = CognitiveServicesAccountProperties()
    properties.network_acls = rules
    params = CognitiveServicesAccount(properties=properties)

    return client.begin_update(resource_group_name, account_name, params)


def remove_network_rule(
    client,
    resource_group_name,
    account_name,
    ip_address=None,
    subnet=None,
    vnet_name=None,
):  # pylint: disable=unused-argument
    """
    Remove a network rule for Azure Cognitive Services account.
    """
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        # nothing to update, but return the object
        return client.update(resource_group_name, account_name)

    if subnet:
        rules.virtual_network_rules = [
            x for x in rules.virtual_network_rules if not x.id.endswith(subnet)
        ]
    if ip_address:
        rules.ip_rules = [x for x in rules.ip_rules if x.value != ip_address]

    properties = CognitiveServicesAccountProperties()
    properties.network_acls = rules
    params = CognitiveServicesAccount(properties=properties)

    return client.begin_update(resource_group_name, account_name, params)


def identity_assign(client, resource_group_name, account_name):
    """
    Assign the identity for Azure Cognitive Services account.
    """
    params = CognitiveServicesAccount()
    params.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)
    sa = client.begin_update(resource_group_name, account_name, params).result()
    return sa.identity if sa.identity else {}


def identity_remove(client, resource_group_name, account_name):
    """
    Remove the identity for Azure Cognitive Services account.
    """
    params = CognitiveServicesAccount()
    params.identity = Identity(type=IdentityType.NONE)
    return client.begin_update(resource_group_name, account_name, params)


def identity_show(client, resource_group_name, account_name):
    """
    Show the identity for Azure Cognitive Services account.
    """
    sa = client.get(resource_group_name, account_name)
    return sa.identity if sa.identity else {}


def deployment_begin_create_or_update(
        client, resource_group_name, account_name, deployment_name,
        model_format, model_name, model_version, model_source=None,
        sku_name=None, sku_capacity=None,
        scale_settings_scale_type=None, scale_settings_capacity=None,
        spillover_deployment_name=None):
    """
    Create a deployment for Azure Cognitive Services account.
    """
    dpy = Deployment()
    dpy.properties = DeploymentProperties()
    dpy.properties.model = DeploymentModel()
    dpy.properties.model.format = model_format
    dpy.properties.model.name = model_name
    dpy.properties.model.version = model_version
    if model_source is not None:
        dpy.properties.model.source = model_source
    if sku_name is not None:
        dpy.sku = Sku(name=sku_name)
        dpy.sku.capacity = sku_capacity
    if scale_settings_scale_type is not None:
        dpy.properties.scale_settings = DeploymentScaleSettings()
        dpy.properties.scale_settings.scale_type = scale_settings_scale_type
        dpy.properties.scale_settings.capacity = scale_settings_capacity
    if spillover_deployment_name is not None:
        dpy.properties.spillover_deployment_name = spillover_deployment_name
    return client.begin_create_or_update(resource_group_name, account_name, deployment_name, dpy, polling=False)


def commitment_plan_create_or_update(
    client,
    resource_group_name,
    account_name,
    commitment_plan_name,
    hosting_model,
    plan_type,
    auto_renew,
    current_tier=None,
    current_count=None,
    next_tier=None,
    next_count=None,
):
    """
    Create a commitment plan for Azure Cognitive Services account.
    """
    plan = CommitmentPlan()
    plan.properties = CommitmentPlanProperties()
    plan.properties.hosting_model = hosting_model
    plan.properties.plan_type = plan_type
    if current_tier is not None or current_count is not None:
        plan.properties.current = CommitmentPeriod()
        plan.properties.current.tier = current_tier
        plan.properties.current.count = current_count
    if next_tier is not None or next_count is not None:
        plan.properties.next = CommitmentPeriod()
        plan.properties.next.tier = next_tier
        plan.properties.next.count = next_count
    plan.properties.auto_renew = auto_renew
    return client.create_or_update(
        resource_group_name, account_name, commitment_plan_name, plan
    )


AGENT_API_VERSION_PARAMS = {"api-version": "2025-11-15-preview"}


def _validate_image_tag(image_uri):
    """
    Validate and extract the tag from a Docker image URI.

    This function ensures the image URI includes a tag, which becomes the agent
    version in Azure AI Foundry. It also warns about tags that may cause issues
    in production environments.

    Args:
        image_uri: Full or partial image URI (e.g., 'myregistry.azurecr.io/myagent:v1')

    Returns:
        str: The image tag (version)

    Raises:
        InvalidArgumentValueError: If image URI does not contain a tag

    Examples:
        >>> _validate_image_tag('myregistry.azurecr.io/myagent:v1')
        'v1'
        >>> _validate_image_tag('myagent:latest')  # Warns but succeeds
        'latest'
    """
    if ':' not in image_uri:
        raise InvalidArgumentValueError(
            "Image URI must include a tag (e.g., 'myagent:v1'). "
            "The image tag becomes the agent version in Azure AI Foundry."
        )

    # Split on last colon to handle registry URLs with ports
    parts = image_uri.rsplit(':', 1)
    if len(parts) != 2 or not parts[1].strip():
        raise InvalidArgumentValueError(
            "Image URI must include a non-empty tag (e.g., 'myagent:v1'). "
            "The image tag becomes the agent version in Azure AI Foundry."
        )

    tag = parts[1]

    # Warn about 'latest' tag usage
    if tag.lower() == 'latest':
        logger.warning(
            "Using 'latest' tag is not recommended for production deployments. "
            "Consider using explicit version tags (e.g., 'v1.0', '2024.11.14') "
            "for better version control and reproducibility."
        )

    return tag


def _validate_path_for_subprocess(path, path_description="path"):
    """
    Validate a file system path for safe use in subprocess calls.

    Checks for dangerous shell metacharacters, null bytes, and suspicious patterns
    that could be used for command injection attacks.

    Args:
        path: The file system path to validate
        path_description: Description of the path for error messages (e.g., "source directory")

    Raises:
        InvalidArgumentValueError: If the path contains dangerous characters or patterns

    Examples:
        >>> _validate_path_for_subprocess('/home/user/project')  # OK
        >>> _validate_path_for_subprocess('/tmp; rm -rf /')  # Raises error
    """
    if not path:
        raise InvalidArgumentValueError(f"The {path_description} cannot be empty")

    # Check for null bytes (can cause issues in C-based subprocess calls)
    if '\0' in path:
        raise InvalidArgumentValueError(
            f"The {path_description} contains null bytes, which is not allowed"
        )

    # Check for dangerous shell metacharacters
    # These could be used for command injection if the path is used in shell=True contexts
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    found_chars = [char for char in dangerous_chars if char in path]

    if found_chars:
        chars_list = ', '.join(repr(c) for c in found_chars)
        raise InvalidArgumentValueError(
            f"The {path_description} contains dangerous shell metacharacters: {chars_list}. "
            f"Please use a path without special shell characters."
        )

    # Check for shell expansion patterns that could be dangerous
    # Note: Relative paths (../) are legitimate and common, so only check for shell expansions
    dangerous_patterns = ['${', '$(']
    found_patterns = [pattern for pattern in dangerous_patterns if pattern in path]

    if found_patterns:
        raise InvalidArgumentValueError(
            f"The {path_description} contains shell expansion patterns: {', '.join(found_patterns)}. "
            f"These could be used for command injection and are not allowed."
        )


def _has_dockerfile(source_dir, dockerfile_name='Dockerfile'):
    """
    Check if a Dockerfile exists in the source directory.

    Args:
        source_dir: Path to source directory
        dockerfile_name: Name of the Dockerfile (default: 'Dockerfile')

    Returns:
        bool: True if Dockerfile exists, False otherwise
    """
    if not source_dir or not os.path.isdir(source_dir):
        return False

    dockerfile_path = os.path.join(source_dir, dockerfile_name)
    return os.path.isfile(dockerfile_path)


def _is_docker_running():
    """
    Check if Docker daemon is accessible.

    Returns:
        bool: True if Docker is running, False otherwise
    """
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
        return False
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Unexpected error checking Docker status: %s", str(e))
        return False


@retry(retry_times=3, interval=5, exceptions=(subprocess.CalledProcessError, OSError, CLIInternalError))
def _build_image_locally(cmd, source_dir, image_name, dockerfile_name='Dockerfile'):  # pylint: disable=unused-argument
    """
    Build Docker image locally using docker build command.

    Retries up to 3 times on transient failures (Docker daemon issues, network errors).

    Args:
        cmd: CLI command context
        source_dir: Path to source directory containing Dockerfile
        image_name: Full image name with tag (e.g., 'myregistry.azurecr.io/myagent:v1')
        dockerfile_name: Name of the Dockerfile (default: 'Dockerfile')

    Returns:
        str: The built image name

    Raises:
        FileOperationError: If Dockerfile cannot be located
        InvalidArgumentValueError: If paths contain dangerous characters
        CLIInternalError: If docker invocation fails
    """
    logger.info("Building Docker image locally: %s", image_name)

    # Validate paths for security (prevent command injection)
    _validate_path_for_subprocess(source_dir, "source directory")
    _validate_path_for_subprocess(dockerfile_name, "dockerfile name")

    dockerfile_path = os.path.join(source_dir, dockerfile_name)
    if not os.path.isfile(dockerfile_path):
        raise FileOperationError(f"Dockerfile not found at: {dockerfile_path}")

    # Get timeout from environment variable or use default (30 minutes)
    build_timeout = int(os.environ.get('AZURE_CLI_DOCKER_BUILD_TIMEOUT', 1800))

    try:
        # Build the image
        # Docker expects forward slashes even on Windows - use pathlib for cross-platform compatibility
        docker_file_arg = Path(dockerfile_path).as_posix()

        # Force AMD64/x86_64 platform for Azure compatibility
        # Azure Container Apps/Foundry runs on AMD64, not ARM64
        # This ensures images built on Apple Silicon Macs work in Azure
        build_cmd = [
            'docker', 'build',
            '--platform', 'linux/amd64',
            '-t', image_name,
            '-f', docker_file_arg,
            source_dir
        ]

        logger.info("Running: %s", ' '.join(build_cmd))
        logger.info("Build timeout: %d seconds", build_timeout)
        logger.warning("Building Docker image locally for linux/amd64 platform...")

        # Stream output to show build progress
        # Output goes directly to terminal for user visibility
        result = subprocess.run(
            build_cmd,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=build_timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # Log the output for debugging
        if result.stdout:
            logger.debug("Docker build output:\n%s", result.stdout)
            # Print to console for user visibility
            print(result.stdout)

        logger.warning("Docker build completed successfully")

        return image_name

    except subprocess.TimeoutExpired as e:
        raise CLIInternalError(
            f"Docker build timed out after {build_timeout} seconds. "
            f"You can increase the timeout by setting AZURE_CLI_DOCKER_BUILD_TIMEOUT environment variable."
        ) from e
    except subprocess.CalledProcessError as e:
        error_msg = f"Docker build failed with exit code {e.returncode}."
        if e.stdout:
            logger.error("Docker build output:\n%s", e.stdout)
            error_msg += f"\n\nOutput:\n{e.stdout}"
        raise CLIInternalError(error_msg) from e
    except Exception as e:
        raise CLIInternalError(f"Failed to build Docker image: {str(e)}") from e


@retry(retry_times=3, interval=5, exceptions=(subprocess.CalledProcessError, OSError, CLIInternalError))
def _push_image_to_registry(_cmd, image_name, registry_name):  # pylint: disable=unused-argument
    """
    Push built image to Azure Container Registry with authentication.

    Retries up to 3 times on transient failures (ACR auth, network errors, rate limiting).

    Args:
        cmd: CLI command context
        image_name: Full image name with tag (e.g., 'myregistry.azurecr.io/myagent:v1')
        registry_name: Short name of ACR (without .azurecr.io)

    Raises:
        InvalidArgumentValueError: If paths contain dangerous characters
        CLIInternalError: If push fails
    """
    logger.info("Pushing image to registry: %s", image_name)

    # Validate inputs for security
    _validate_path_for_subprocess(registry_name, "registry name")

    registry_uri = f"{registry_name}.azurecr.io"

    # Get timeout from environment variable or use default (30 minutes)
    push_timeout = int(os.environ.get('AZURE_CLI_DOCKER_PUSH_TIMEOUT', 1800))

    try:
        # Login to ACR using Azure CLI credentials
        # We use sys.executable + '-m azure.cli' instead of 'az' command to ensure
        # compatibility when developing/testing the CLI from source. In development
        # environments, 'az' may not be in PATH or may point to a different installation.
        # In production, sys.executable will still correctly invoke the installed CLI.
        az_cmd = [sys.executable, '-m', 'azure.cli', 'acr', 'login', '--name', registry_name]
        logger.info("Logging into ACR: %s", registry_name)

        result = subprocess.run(
            az_cmd,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=60  # ACR login should be fast
        )

        if result.stdout:
            logger.debug("ACR login output: %s", result.stdout)
        if result.stderr:
            logger.debug("ACR login stderr: %s", result.stderr)

        logger.info("ACR login successful")

        # Push the image
        push_cmd = ['docker', 'push', image_name]
        logger.warning("Pushing image to ACR: %s", registry_uri)
        logger.info("Running: %s", ' '.join(push_cmd))
        logger.info("Push timeout: %d seconds", push_timeout)

        # Stream output to show push progress
        # Output goes directly to terminal for user visibility
        result = subprocess.run(
            push_cmd,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=push_timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # Log the output for debugging
        if result.stdout:
            logger.debug("Docker push output:\n%s", result.stdout)
            # Print to console for user visibility
            print(result.stdout)

        logger.warning("Successfully pushed image to %s", registry_uri)

    except subprocess.TimeoutExpired as e:
        timeout_msg = "ACR login" if 'login' in str(e.cmd) else "Docker push"
        raise CLIInternalError(
            f"{timeout_msg} timed out. Check your network connection and try again. "
            f"You can increase the timeout by setting AZURE_CLI_DOCKER_PUSH_TIMEOUT environment variable."
        ) from e
    except subprocess.CalledProcessError as e:
        error_parts = ["Failed to push image to registry."]
        error_parts.append(f"Command: {' '.join(e.cmd)}")
        error_parts.append(f"Exit code: {e.returncode}")
        if e.stdout:
            logger.error("Command output: %s", e.stdout)
            error_parts.append(f"Output: {e.stdout}")
        if e.stderr:
            logger.error("Command stderr: %s", e.stderr)
            error_parts.append(f"Error: {e.stderr}")
        raise CLIInternalError('\n'.join(error_parts)) from e
    except Exception as e:
        raise CLIInternalError(f"Failed to push image: {str(e)}") from e


@retry(retry_times=3, interval=5, exceptions=(CLIInternalError,))
def _build_image_remotely(cmd, source_dir, image_name,  # pylint: disable=too-many-locals
                          registry_name, dockerfile_name='Dockerfile'):
    """
    Build Docker image using Azure Container Registry Task.
    Uses buildpacks (az acr pack build) if no Dockerfile exists,
    otherwise uses traditional Docker build (az acr build).

    Retries up to 3 times on transient failures (ACR API throttling, network errors).

    Args:
        cmd: CLI command context
        source_dir: Path to source directory
        image_name: Full image name with tag
        registry_name: Short name of ACR (without .azurecr.io)
        dockerfile_name: Name of the Dockerfile

    Returns:
        str: The built image name

    Raises:
        CLIInternalError: If remote build fails
    """
    # Use ACR module client factories and utility functions for build operations.
    # These private APIs are pinned to specific preview API versions and handle complex
    # operations like source upload, task scheduling, and log streaming.
    from azure.cli.command_modules.acr._client_factory import cf_acr_registries_tasks, cf_acr_runs
    from azure.cli.command_modules.acr._stream_utils import stream_logs
    from azure.cli.command_modules.acr._utils import prepare_source_location, get_resource_group_name_by_registry_name
    import base64

    logger.warning("Building image remotely using ACR Task: %s", image_name)

    # Get ACR clients - these use preview API versions with build task support
    client_registries = cf_acr_registries_tasks(cmd.cli_ctx)
    client_runs = cf_acr_runs(cmd.cli_ctx)

    # Get resource group from registry name
    resource_group_name = get_resource_group_name_by_registry_name(
        cmd.cli_ctx, registry_name)

    try:
        # Extract just the image name and tag (without registry)
        if '/' in image_name:
            image_without_registry = image_name.split('/', 1)[1]
        else:
            image_without_registry = image_name

        # Prepare source location (uploads source and returns URL)
        logger.warning("Uploading source code to ACR...")
        source_location = prepare_source_location(
            cmd, source_dir, client_registries, registry_name, resource_group_name)

        # Check if Dockerfile exists
        has_dockerfile = _has_dockerfile(source_dir, dockerfile_name)

        if has_dockerfile:
            # Traditional Docker build
            logger.warning("Dockerfile found - using Docker build")
            logger.warning("Queueing build task...")

            from azure.mgmt.containerregistry.models import (
                DockerBuildRequest, PlatformProperties
            )

            docker_build_request = DockerBuildRequest(
                image_names=[image_without_registry],
                is_push_enabled=True,
                source_location=source_location,
                platform=PlatformProperties(os='Linux', architecture='amd64'),
                docker_file_path=dockerfile_name,
                timeout=3600
            )

            queued = client_registries.schedule_run(
                resource_group_name=resource_group_name,
                registry_name=registry_name,
                run_request=docker_build_request)
        else:
            # Buildpacks for auto-detection
            logger.warning("No Dockerfile - using Cloud Native Buildpacks (auto-detect)")
            logger.warning("Buildpacks will detect Python, Node.js, .NET, etc.")
            logger.warning("Queueing build task...")

            from azure.mgmt.containerregistry.models import (
                EncodedTaskRunRequest, PlatformProperties
            )

            # Use module-level PACK_TASK_YAML constant
            yaml_body = PACK_TASK_YAML.format(
                image_name_full=image_name,
                builder='paketobuildpacks/builder:base')

            request = EncodedTaskRunRequest(
                encoded_task_content=base64.b64encode(yaml_body.encode()).decode(),
                source_location=source_location,
                timeout=3600,
                platform=PlatformProperties(os='Linux', architecture='amd64')
            )

            queued = client_registries.schedule_run(
                resource_group_name=resource_group_name,
                registry_name=registry_name,
                run_request=request)

        run_id = queued.run_id
        logger.warning("Queued build with ID: %s", run_id)
        logger.warning("Waiting for agent and streaming build logs...")

        # Stream logs for real-time progress
        stream_logs(cmd, client_runs, run_id, registry_name,
                    resource_group_name, timeout=3600, no_format=False,
                    raise_error_on_failure=True)

        logger.warning("Build completed successfully")
        return image_name

    except Exception as e:
        # Log full traceback for debugging
        logger.exception("ACR build failed")
        raise CLIInternalError(f"ACR build failed: {str(e)}") from e


def _create_agent_request(
    method: str,
    agent_name: str,
    agent_version: str = None,
    *,
    container: bool = False,
    action: str = None,
    body: dict = None,
):
    if container and not agent_version:
        raise ValueError("container=True requires agent_version to be specified")

    if agent_version:
        url = f"/agents/{urllib.parse.quote(agent_name)}/versions/{urllib.parse.quote(agent_version)}"
        if container:
            url += "/containers/default"
    else:
        url = f"/agents/{urllib.parse.quote(agent_name)}"

    if action:
        url += f":{action}"
    return azure.core.rest.HttpRequest(
        method, url, json=body, params=AGENT_API_VERSION_PARAMS
    )


def _get_agent_container_status(client, agent_name, agent_version):
    """Get the status of an agent container deployment."""
    request = _create_agent_request(
        "GET",
        agent_name,
        agent_version,
        container=True,
    )
    response = client.send_request(request)
    response.raise_for_status()
    return response.json()


# Constants for log streaming
LOG_STREAM_CONNECT_TIMEOUT = 10  # seconds
LOG_STREAM_READ_TIMEOUT = 5  # seconds for non-follow mode
LOG_STREAM_RETRY_INTERVAL = 5  # seconds between retries
LOG_STREAM_MAX_RETRIES = 30  # max retry attempts (~2.5 minutes)
LOG_STREAM_POST_DEPLOY_WAIT = 15  # seconds to stream after deployment ready


def _get_log_stream_auth_header(cmd):
    """
    Get authorization header for log stream API.

    Args:
        cmd: CLI command context

    Returns:
        dict: Authorization header with Bearer token
    """
    from azure.cli.core._profile import Profile

    profile = Profile(cli_ctx=cmd.cli_ctx)
    credential, _, _ = profile.get_login_credentials(
        subscription_id=cmd.cli_ctx.data.get("subscription_id")
    )
    token = credential.get_token("https://ai.azure.com/.default")
    return {"Authorization": f"Bearer {token.token}"}


def _build_log_stream_url(client, agent_name, agent_version, container_name="default"):
    """
    Build the log stream URL for an agent container.

    Args:
        client: Service client with endpoint configuration
        agent_name: Name of the agent
        agent_version: Version of the agent
        container_name: Container name (default: 'default')

    Returns:
        str: Full URL for the log stream endpoint
    """
    endpoint = client._config.endpoint  # pylint: disable=protected-access
    return (
        f"{endpoint}/agents/{urllib.parse.quote(agent_name)}"
        f"/versions/{urllib.parse.quote(str(agent_version))}"
        f"/containers/{urllib.parse.quote(container_name)}:logstream"
    )


def _stream_agent_logs(
    cmd,
    client,
    agent_name,
    agent_version,
    kind="console",
    tail=50,
    follow=True,
):
    """
    Stream logs from an agent container.

    Args:
        cmd: CLI command context
        client: Service client (AIProjectClient)
        agent_name: Name of the agent
        agent_version: Version of the agent
        kind: Type of logs - 'console' (stdout/stderr) or 'system' (container events)
        tail: Number of trailing lines to fetch (1-300)
        follow: Whether to stream logs in real-time

    Yields:
        str: Log lines as they arrive

    Raises:
        InvalidArgumentValueError: If tail or kind parameters are invalid
        AzureResponseError: If connection to log stream fails
    """
    import requests as http_requests

    # Validate parameters
    if tail is not None and not 1 <= tail <= 300:
        raise InvalidArgumentValueError("--tail must be between 1 and 300")
    if kind not in ("console", "system"):
        raise InvalidArgumentValueError("--type must be 'console' or 'system'")

    log_url = _build_log_stream_url(client, agent_name, agent_version)
    params = {
        "api-version": AGENT_API_VERSION_PARAMS["api-version"],
        "kind": kind,
        "tail": tail,
    }
    headers = _get_log_stream_auth_header(cmd)

    logger.info("Connecting to log stream: %s", log_url)

    timeout = None if follow else (LOG_STREAM_CONNECT_TIMEOUT, LOG_STREAM_READ_TIMEOUT)

    try:
        response = http_requests.get(
            log_url, params=params, headers=headers, stream=True, timeout=timeout
        )

        if not response.ok:
            error_detail = response.text or f"HTTP {response.status_code}"
            raise AzureResponseError(f"Failed to connect to log stream: {error_detail}")

        for line in response.iter_lines():
            if line:
                yield line.decode("utf-8", errors="replace")

    except http_requests.exceptions.Timeout:
        pass  # Expected when follow=False - read timeout after fetching available logs
    except http_requests.exceptions.ConnectionError as e:
        if "timed out" in str(e).lower():
            pass  # Timeout wrapped in ConnectionError
        else:
            raise AzureResponseError(f"Failed to connect to log stream: {e}") from e
    except KeyboardInterrupt:
        logger.warning("Log streaming interrupted by user")
        raise


def agent_logs_show(
    cmd,
    client,
    account_name,
    project_name,
    agent_name,
    agent_version,
    kind="console",
    tail=50,
    follow=False,
):  # pylint: disable=unused-argument
    """
    Show logs from a hosted agent container.

    Args:
        cmd: CLI command context
        client: Service client
        account_name: Cognitive Services account name (unused, for CLI routing)
        project_name: AI Foundry project name (unused, for CLI routing)
        agent_name: Name of the agent
        agent_version: Version of the agent
        kind: Type of logs - 'console' or 'system'
        tail: Number of trailing lines (1-300)
        follow: Stream logs in real-time if True
    """
    try:
        for log_line in _stream_agent_logs(
            cmd, client, agent_name, agent_version, kind=kind, tail=tail, follow=follow
        ):
            print(log_line)
    except KeyboardInterrupt:
        pass  # Clean exit on Ctrl+C


def _wait_for_agent_deployment_ready(
        cmd, client, agent_name, agent_version, timeout=600, poll_interval=5):
    """
    Wait for agent deployment to be ready with progress indicator.

    Args:
        cmd: CLI command context (for progress controller)
        client: Service client
        agent_name: Name of the agent
        agent_version: Version of the agent
        timeout: Maximum time to wait in seconds (default 600 seconds / 10 minutes)
        poll_interval: Time between status checks in seconds (default 5)

    Returns:
        dict: The final deployment status

    Raises:
        DeploymentError: If deployment fails or times out
    """
    import time
    from azure.cli.core.commands.progress import IndeterminateProgressBar

    # Environment variable to customize poll interval for testing/debugging
    poll_interval = int(os.environ.get('AZURE_CLI_AGENT_POLL_INTERVAL', poll_interval))

    start_time = time.time()
    last_status = None

    # Create progress indicator
    progress = IndeterminateProgressBar(cmd.cli_ctx, message="Waiting for deployment to be ready")
    progress.begin()

    try:
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)

            try:
                status = _get_agent_container_status(client, agent_name, agent_version)
                current_state = status.get("status", "unknown")
                last_status = status

                logger.debug("Deployment status: %s (elapsed: %ds)", current_state, elapsed)

                # Map API status to user-friendly messages
                status_messages = {
                    "creating": "Creating deployment resources",
                    "pending": "Pending deployment start",
                    "pulling": "Pulling container image",
                    "starting": "Starting deployment",
                    "running": "Deployment ready",
                    "failed": "Deployment failed",
                    "error": "Deployment error",
                    "unknown": "Checking deployment status"
                }

                friendly_message = status_messages.get(current_state.lower(), f"Status: {current_state}")
                progress.update_progress_with_msg(f"{friendly_message} (elapsed: {elapsed}s)")

                # Success case
                if current_state.lower() == "running":
                    progress.end()
                    logger.info("Deployment is ready (total time: %ds)", elapsed)
                    return status

                # Fatal error cases - fail fast
                if current_state.lower() in ["failed", "error"]:
                    progress.stop()
                    error_details = status.get("error", {})
                    error_message = error_details.get("message", "No error details available")
                    raise DeploymentError(
                        f"Deployment failed with status '{current_state}': {error_message}",
                        recommendation="Check container image exists and is accessible. Review agent logs for details."
                    )

            except DeploymentError:
                # Re-raise deployment errors immediately
                raise
            except Exception as e:  # pylint: disable=broad-except
                # For other exceptions, log but continue polling (might be transient)
                logger.debug("Transient error checking deployment status: %s", str(e))
                progress.update_progress_with_msg(f"Retrying status check (elapsed: {elapsed}s)")

            time.sleep(poll_interval)

        # Timeout case
        progress.stop()
        timeout_msg = f"Deployment did not become ready within {timeout} seconds"
        if last_status:
            final_state = last_status.get("status", "unknown")
            timeout_msg += f". Last status: {final_state}"

        raise DeploymentError(
            timeout_msg,
            recommendation=(
                f"Increase timeout with --timeout parameter (current: {timeout}s). "
                "For large images, consider using --timeout 1200 or higher."
            )
        )
    except KeyboardInterrupt:
        progress.stop()
        logger.warning("Deployment wait interrupted by user")
        raise
    finally:
        # Ensure progress indicator is cleaned up
        try:
            progress.end()
        except Exception:  # pylint: disable=broad-except
            pass


def _invoke_agent_container_operation(
    client,
    agent_name,
    agent_version,
    *,
    action: str,
    min_replicas=None,
    max_replicas=None,
):
    request_body = {}
    if min_replicas is not None:
        request_body["min_replicas"] = min_replicas
    if max_replicas is not None:
        request_body["max_replicas"] = max_replicas
    request = _create_agent_request(
        "POST",
        agent_name,
        agent_version,
        action=action,
        container=True,
        body=request_body,
    )
    response = client.send_request(request)
    response.raise_for_status()
    return response.json()


def _normalize_registry_name_input(registry_name):
    """Normalize registry input to short name without .azurecr.io suffix."""
    if not registry_name:
        return None

    registry = registry_name.strip()
    if registry.endswith('.azurecr.io'):
        registry = registry[: -len('.azurecr.io')]
    return registry


def _is_fully_qualified_image(image):
    """Heuristic to detect if an image already includes a registry hostname."""
    if not image:
        return False

    if '/' not in image:
        return False

    first_segment = image.split('/')[0]
    return '.' in first_segment or ':' in first_segment or first_segment == 'localhost'


def _determine_registry_for_access_check(image, registry, source):
    """Determine which registry (if any) should be checked for AcrPull permissions."""
    normalized_registry = _normalize_registry_name_input(registry)

    if normalized_registry:
        return normalized_registry

    if source:
        return None

    if image and '.azurecr.io' in image:
        return image.split('.azurecr.io')[0].split('/')[-1]

    return None


def _validate_scaling_options(no_start, min_replicas, max_replicas):
    if no_start and (min_replicas is not None or max_replicas is not None):
        raise InvalidArgumentValueError(
            "Cannot use --no-start with --min-replicas or --max-replicas. "
            "Replica configuration requires the agent to be deployed. "
            "Either remove --no-start to deploy with scaling, or remove replica parameters."
        )


def _validate_memory_value(memory):
    if memory and not re.match(r'^\d+(\.\d+)?(Gi|Mi)$', memory):
        raise InvalidArgumentValueError(
            f"Invalid memory value '{memory}'. "
            "Memory must be a positive number with units 'Gi' or 'Mi' (e.g., '2Gi', '512Mi', '1.5Gi')"
        )


def _validate_cpu_value(cpu):
    try:
        cpu_float = float(cpu)
    except (ValueError, TypeError) as exc:
        raise InvalidArgumentValueError(
            f"Invalid CPU value '{cpu}'. "
            "CPU must be a number (e.g., '1', '2', '0.5')"
        ) from exc

    if cpu_float <= 0:
        raise InvalidArgumentValueError(
            f"CPU must be positive. Got: '{cpu}'"
        )


def _convert_environment_variables(environment_variables):
    env_vars = {}
    if environment_variables:
        for env_var in environment_variables:
            env_vars[env_var['key']] = env_var['value']
    return env_vars


def _create_agent_definition(cpu, memory, protocol, protocol_version, image_uri, env_vars):
    protocol_record = {
        "protocol": protocol.upper(),
        "version": protocol_version
    }

    definition = {
        "kind": "hosted",
        "container_protocol_versions": [protocol_record],
        "cpu": cpu,
        "memory": memory,
        "image": image_uri,
    }

    if env_vars:
        definition["environment_variables"] = env_vars

    return definition


def _resolve_agent_image_uri(
    cmd,
    source,
    agent_name,
    registry,
    dockerfile,
    build_remote,
    image,
):
    if source:
        source_path = os.path.abspath(source)
        if not os.path.isdir(source_path):
            raise FileOperationError(f"Source directory not found: {source}")

        normalized_registry = _normalize_registry_name_input(registry)
        if not normalized_registry:
            raise RequiredArgumentMissingError(
                "Parameter --registry is required when using --source. "
                "Specify the Azure Container Registry where the built image will be stored."
            )

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        image_tag = f"v{timestamp}"
        image_uri = f"{normalized_registry}.azurecr.io/{agent_name}:{image_tag}"

        logger.info("Building container image from source: %s", source)
        logger.info("Target image: %s", image_uri)

        def _build_and_push_locally():
            _build_image_locally(cmd, source_path, image_uri, dockerfile)
            _push_image_to_registry(cmd, image_uri, normalized_registry)

        if build_remote:
            logger.info("Using remote build (forced via --build-remote)")
            _build_image_remotely(cmd, source_path, image_uri, normalized_registry, dockerfile)
            return image_uri

        docker_running = _is_docker_running()
        if docker_running:
            try:
                _build_and_push_locally()
                return image_uri
            except CLIInternalError as build_err:
                logger.warning(
                    "Local build or push failed (%s). Falling back to remote build.",
                    str(build_err)
                )

        logger.info("Building image remotely using ACR Task")
        _build_image_remotely(cmd, source_path, image_uri, normalized_registry, dockerfile)
        return image_uri

    if registry:
        normalized_registry = _normalize_registry_name_input(registry)
        if _is_fully_qualified_image(image):
            raise InvalidArgumentValueError(
                "When --image already contains a registry hostname, omit --registry."
            )
        registry_uri = f"{normalized_registry}.azurecr.io"
        return f"{registry_uri}/{image}"

    return image


class _BackgroundLogStreamer:
    """
    Context manager for streaming logs in a background thread during deployment.

    Usage:
        with _BackgroundLogStreamer(cmd, client, agent_name, version) as streamer:
            # deployment operations...
            streamer.wait_after_ready()  # optional: stream logs after deployment ready
    """

    def __init__(self, cmd, client, agent_name, agent_version, enabled=True):
        self.cmd = cmd
        self.client = client
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.enabled = enabled
        self._thread = None
        self._stop_event = None

    def __enter__(self):
        if not self.enabled:
            return self

        import threading
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._stream_with_retry, daemon=True)
        self._thread.start()
        logger.warning("Streaming container logs (Ctrl+C to stop)...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._thread and self._stop_event:
            self._stop_event.set()
            self._thread.join(timeout=2)
        return False  # Don't suppress exceptions

    def _stream_with_retry(self):
        """Stream logs with retry logic for container startup."""
        import time
        from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout

        last_error = None
        for attempt in range(LOG_STREAM_MAX_RETRIES):
            if self._stop_event.is_set():
                return

            try:
                # Check if container is in a streamable state
                if not self._is_container_ready():
                    time.sleep(LOG_STREAM_RETRY_INTERVAL)
                    continue

                # Stream logs
                for log_line in _stream_agent_logs(
                    self.cmd, self.client, self.agent_name, self.agent_version,
                    kind="console", tail=100, follow=True
                ):
                    if self._stop_event.is_set():
                        return
                    print(log_line)
                return  # Successfully streamed

            except (RequestsConnectionError, Timeout) as e:
                # Expected transient errors during container startup
                if self._stop_event.is_set():
                    return
                last_error = e
                logger.debug("Log stream attempt %d failed (transient): %s", attempt + 1, e)
                if attempt < LOG_STREAM_MAX_RETRIES - 1:
                    time.sleep(LOG_STREAM_RETRY_INTERVAL)

            except Exception as e:  # pylint: disable=broad-except
                # Unexpected errors - log and continue retrying
                if self._stop_event.is_set():
                    return
                last_error = e
                logger.debug("Log stream attempt %d failed: %s", attempt + 1, e)
                if attempt < LOG_STREAM_MAX_RETRIES - 1:
                    time.sleep(LOG_STREAM_RETRY_INTERVAL)

        # All retries exhausted - warn user
        if last_error and not self._stop_event.is_set():
            logger.warning(
                "Unable to establish log stream after %d attempts. "
                "The agent may still be starting. Last error: %s",
                LOG_STREAM_MAX_RETRIES, last_error
            )

    def _is_container_ready(self):
        """Check if container is in a state where logs can be streamed."""
        try:
            status = _get_agent_container_status(self.client, self.agent_name, self.agent_version)
            return status.get("status", "").lower() in ("running", "starting", "pending")
        except Exception:  # pylint: disable=broad-except
            return True  # Try streaming anyway if status check fails

    def wait_after_ready(self, seconds=LOG_STREAM_POST_DEPLOY_WAIT):
        """Wait for additional log streaming after deployment is ready."""
        import time

        if not self.enabled or not self._thread or not self._thread.is_alive():
            return

        logger.warning("Deployment ready. Streaming logs for %d more seconds (Ctrl+C to stop)...", seconds)
        for _ in range(seconds):
            if not self._thread.is_alive():
                break
            time.sleep(1)


def _deploy_agent_version(
    cmd, client, agent_name, created_version, min_replicas, max_replicas, timeout=600, show_logs=False
):
    """
    Deploy an agent version with horizontal scaling configuration.

    Args:
        cmd: CLI command context
        client: Service client
        agent_name: Name of the agent
        created_version: Version to deploy
        min_replicas: Minimum number of replicas (default 0)
        max_replicas: Maximum number of replicas (default 3)
        timeout: Maximum time to wait for deployment (default 600 seconds)
        show_logs: Stream container logs during deployment (default False)
    """
    effective_min_replicas = min_replicas if min_replicas is not None else 0
    effective_max_replicas = max_replicas if max_replicas is not None else 3

    logger.info(
        "Starting agent deployment (min_replicas=%s, max_replicas=%s)...",
        effective_min_replicas,
        effective_max_replicas,
    )

    with _BackgroundLogStreamer(cmd, client, agent_name, created_version, enabled=show_logs) as streamer:
        try:
            _invoke_agent_container_operation(client, agent_name, created_version, action="start")
            _wait_for_agent_deployment_ready(cmd, client, agent_name, created_version, timeout=timeout)

            if min_replicas is not None or max_replicas is not None:
                _invoke_agent_container_operation(
                    client, agent_name, created_version, action="update",
                    min_replicas=effective_min_replicas, max_replicas=effective_max_replicas
                )

            logger.info("Agent deployment started successfully")
            streamer.wait_after_ready()

        except Exception as deploy_err:
            raise DeploymentError(
                f"Agent version '{created_version}' was created but deployment failed: {deploy_err}",
                recommendation="Use 'az cognitiveservices agent start' to retry deployment."
            ) from deploy_err


def agent_update(
    client,
    account_name,
    project_name,
    agent_name,
    agent_version,
    min_replicas=None,
    max_replicas=None,
    description=None,
    tags=None,
):  # pylint: disable=unused-argument
    """
    Update hosted agent deployment configuration.
    Updates horizontal scale configuration (min and max replica), agent meta-data such as description and tags.
    New version is not created for this update.
    """
    return _invoke_agent_container_operation(
        client,
        agent_name,
        agent_version,
        action="update",
        min_replicas=min_replicas,
        max_replicas=max_replicas,
    )


def agent_stop(
    client, account_name, project_name, agent_name, agent_version
):  # pylint: disable=unused-argument
    """
    Stop hosted agent deployment.
    """
    return _invoke_agent_container_operation(
        client, agent_name, agent_version, action="stop"
    )


def agent_start(
    cmd, client, account_name, project_name, agent_name, agent_version, show_logs=False, timeout=600
):  # pylint: disable=unused-argument
    """
    Start hosted agent deployment.

    Args:
        cmd: CLI command context
        client: Service client
        account_name: Cognitive Services account name (unused, for CLI routing)
        project_name: AI Foundry project name (unused, for CLI routing)
        agent_name: Name of the agent
        agent_version: Version of the agent to start
        show_logs: Stream container logs during startup (default False)
        timeout: Maximum time to wait for deployment to be ready (default 600 seconds)
    """
    result = _invoke_agent_container_operation(client, agent_name, agent_version, action="start")

    if show_logs:
        with _BackgroundLogStreamer(cmd, client, agent_name, agent_version) as streamer:
            try:
                _wait_for_agent_deployment_ready(cmd, client, agent_name, agent_version, timeout=timeout)
                logger.warning("Agent deployment is now running")
                streamer.wait_after_ready()
            except KeyboardInterrupt:
                logger.warning("Log streaming interrupted")

    return result


def agent_delete_deployment(
    client, account_name, project_name, agent_name, agent_version
):  # pylint: disable=unused-argument
    """
    Delete hosted agent deployment.
    Deletes the agent deployment only, agent version associated with the deployment remains.
    """
    request = _create_agent_request(
        "POST", agent_name, agent_version, action="delete", container=True
    )
    response = client.send_request(request)
    response.raise_for_status()
    return response.json()


def agent_delete(
    client, account_name, project_name, agent_name, agent_version=None
):  # pylint: disable=unused-argument
    """
    Delete hosted agent version or all versions.
    If agent_version is provided, deletes the agent instance and agent definition associated with that version.
    If agent_version is not provided, deletes all agent instances and agent definitions associated with the agent name.
    """
    request = _create_agent_request("DELETE", agent_name, agent_version)
    response = client.send_request(request)
    response.raise_for_status()
    return response.json()


def agent_list(client, account_name, project_name):  # pylint: disable=unused-argument
    """
    List agents.
    """
    agents = []
    params = AGENT_API_VERSION_PARAMS.copy()
    while True:
        request = azure.core.rest.HttpRequest("GET", "/agents", params=params)
        response = client.send_request(request)
        response.raise_for_status()
        body = response.json()
        agents.extend(body.get("data", []))
        if body.get("has_more"):
            params["after"] = body.get("last_id")
        else:
            return agents


def agent_versions_list(
    client, account_name, project_name, agent_name
):  # pylint: disable=unused-argument
    """
    List all versions of a hosted agent.
    """
    versions = []
    params = AGENT_API_VERSION_PARAMS.copy()
    while True:
        request = azure.core.rest.HttpRequest(
            "GET", f"/agents/{urllib.parse.quote(agent_name)}/versions", params=params
        )
        response = client.send_request(request)
        response.raise_for_status()
        body = response.json()
        versions.extend(body.get("data", []))
        if body.get("has_more"):
            params["after"] = body.get("last_id")
        else:
            return versions


def agent_show(
    client, account_name, project_name, agent_name
):  # pylint: disable=unused-argument
    """
    Show details of a hosted agent.
    """
    request = azure.core.rest.HttpRequest(
        "GET",
        f"/agents/{urllib.parse.quote(agent_name)}",
        params=AGENT_API_VERSION_PARAMS,
    )
    response = client.send_request(request)
    response.raise_for_status()
    return response.json()


def agent_status(
    client,
    account_name,
    project_name,
    agent_name,
    agent_version,
):  # pylint: disable=unused-argument
    """Get the status of a hosted agent deployment (default container)."""
    return _get_agent_container_status(client, agent_name, agent_version)


def _get_resource_group_by_account_name(cmd, account_name):
    """
    Get resource group name for a Cognitive Services account by querying ARM.

    Args:
        cmd: CLI command context
        account_name: Cognitive Services account name

    Returns:
        str: Resource group name
    """
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource import ResourceManagementClient

    subscription_id = get_subscription_id(cmd.cli_ctx)
    resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceManagementClient)

    # Query for the Cognitive Services account
    resource_type = "Microsoft.CognitiveServices/accounts"
    filter_str = f"resourceType eq '{resource_type}' and name eq '{account_name}'"

    resources = list(resource_client.resources.list(filter=filter_str))

    if not resources:
        raise ResourceNotFoundError(
            f"Cognitive Services account '{account_name}' not found in subscription '{subscription_id}'."
        )

    if len(resources) > 1:
        raise CLIInternalError(
            f"Multiple Cognitive Services accounts found with name '{account_name}'. "
            "This should not happen."
        )

    # Extract resource group from resource ID
    resource_id = resources[0].id
    parts = resource_id.split('/')
    rg_index = parts.index('resourceGroups') + 1
    return parts[rg_index]


def _check_project_acr_access(cmd, client, account_name, project_name, registry_name):  # pylint: disable=unused-argument
    """
    Check if AI Foundry project's managed identity has AcrPull access to container registry.

    Args:
        cmd: CLI command context
        client: Service client
        account_name: Cognitive Services account name
        project_name: AI Foundry project name
        registry_name: ACR registry name (without .azurecr.io)

    Returns:
        tuple: (has_access: bool, principal_id: str, error_message: str)

    Limitations:
        - Only validates well-known role names (AcrPull, AcrPush, Reader, Contributor, Owner, etc.)
        - Custom roles with pull permissions may not be detected
        - Inherited permissions from parent scopes (resource group, subscription) are not checked
        - Only validates direct role assignments on the ACR resource
    """
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.command_modules.role.custom import list_role_assignments

    try:
        # Get resource group from account name
        resource_group_name = _get_resource_group_by_account_name(cmd, account_name)

        # Get project to find its managed identity
        from azure.cli.command_modules.cognitiveservices._client_factory import cf_projects
        projects_client = cf_projects(cmd.cli_ctx)

        # Get project resource (project-level identity, not account-level)
        project = projects_client.get(
            resource_group_name=resource_group_name,
            account_name=account_name,
            project_name=project_name
        )

        # Check if project has system-assigned managed identity
        if not project.identity or not project.identity.principal_id:
            return (False, None,
                    f"Project '{project_name}' does not have a system-assigned managed identity enabled. "
                    f"A project identity is automatically created when the project is created.")

        principal_id = project.identity.principal_id

        # Get ACR resource ID
        from azure.cli.command_modules.acr._utils import get_resource_group_name_by_registry_name
        subscription_id = get_subscription_id(cmd.cli_ctx)
        acr_resource_group = get_resource_group_name_by_registry_name(
            cmd.cli_ctx, registry_name)
        acr_resource_id = (
            f"/subscriptions/{subscription_id}/resourceGroups/{acr_resource_group}/"
            f"providers/Microsoft.ContainerRegistry/registries/{registry_name}"
        )

        # Check role assignments for AcrPull or higher permissions
        #
        # KNOWN LIMITATION: This checks for well-known role names rather than checking
        # the actual permissions (actions) of assigned roles. This means:
        # - Custom roles with pull permissions may not be detected
        # - Inherited permissions from parent scopes (resource group, subscription) are not checked
        #
        # A more robust approach would be to:
        # 1. Fetch the role definition for each assigned role
        # 2. Check if it includes Microsoft.ContainerRegistry/registries/pull/read action
        # 3. Check parent scopes for inherited permissions
        #
        # However, this is significantly more complex and slower. The current approach
        # follows the pattern used by AKS (see acs/_roleassignments.py) and covers
        # the most common scenarios. Users with custom roles can use --skip-acr-check.
        #
        # Acceptable roles include:
        # Standard ACR roles:
        # - AcrPull: Can pull images
        # - AcrPush: Can pull and push images
        # Repository-scoped roles:
        # - Container Registry Repository Reader: Read access (includes pull)
        # - Container Registry Repository Writer: Read/write access (includes pull)
        # - Container Registry Repository Contributor: Full repository access (includes pull)
        # General Azure roles:
        # - Reader: Can view resources (includes pull)
        # - Contributor, Owner: Full access
        acceptable_roles = [
            'AcrPull',
            'AcrPush',
            'Container Registry Repository Reader',
            'Container Registry Repository Writer',
            'Container Registry Repository Contributor',
            'Reader',
            'Contributor',
            'Owner'
        ]

        # Get role assignments for the principal on the ACR
        assignments = list_role_assignments(cmd, assignee=principal_id, scope=acr_resource_id)

        # Check if any assignment has acceptable role
        for assignment in assignments:
            role_name = assignment.get('roleDefinitionName', '')
            if role_name in acceptable_roles:
                logger.info(
                    "Found %s role for project identity on ACR %s",
                    role_name, registry_name)
                return (True, principal_id, None)

        # No suitable role found
        return (
            False, principal_id,
            f"Project managed identity does not have AcrPull access to '{registry_name}'"
        )

    except Exception as e:  # pylint: disable=broad-except
        error_msg = (
            f"Unable to verify ACR access: {str(e)}. "
            "If you have configured ACR access through other means, "
            "use --skip-acr-check to bypass this validation."
        )
        logger.error("ACR access check failed: %s", str(e))
        return (False, None, error_msg)


def _validate_agent_create_parameters(image, source, build_remote, no_start, min_replicas, max_replicas):
    """
    Validate agent create parameter combinations.

    Ensures mutually exclusive parameters are not used together and required
    parameters are provided.

    Args:
        image: Container image URI
        source: Source directory path
        build_remote: Whether to build remotely
        no_start: Whether to skip deployment
        min_replicas: Minimum replicas for scaling
        max_replicas: Maximum replicas for scaling

    Raises:
        MutuallyExclusiveArgumentError: If both image and source are provided
        RequiredArgumentMissingError: If neither image nor source is provided
        InvalidArgumentValueError: If build_remote is used without source
    """
    if image and source:
        raise MutuallyExclusiveArgumentError(
            "Parameters --image and --source are mutually exclusive. "
            "Provide either --image for an existing container image, or --source to build from source code."
        )

    if not image and not source:
        raise RequiredArgumentMissingError(
            "Either --image or --source must be provided. "
            "Use --image for an existing container image, or --source to build from source code."
        )

    if build_remote and not source:
        raise InvalidArgumentValueError(
            "Parameter --build-remote can only be used with --source. "
            "When using --image, the container image already exists and doesn't need to be built."
        )

    _validate_scaling_options(no_start, min_replicas, max_replicas)


def agent_create(  # pylint: disable=too-many-locals
    cmd,
    client,
    account_name,
    project_name,
    agent_name,
    image=None,
    source=None,
    dockerfile='Dockerfile',
    build_remote=False,
    registry=None,
    skip_acr_check=False,
    cpu="1",
    memory="2Gi",
    environment_variables=None,
    protocol="responses",
    protocol_version="v1",
    description=None,
    min_replicas=None,
    max_replicas=None,
    no_wait=False,
    no_start=False,
    timeout=600,
    show_logs=False,
):
    """
    Create a new hosted agent from a container image or source code.

    Creates an agent version with the specified configuration and optionally
    deploys it with horizontal scaling parameters. Can either use an existing
    container image or build one from source code.

    Args:
        cmd: CLI command context
        client: Service client
        account_name: Cognitive Services account name
        project_name: AI Foundry project name
        agent_name: Name for the new agent
        image: Container image URI with tag (mutually exclusive with source)
        source: Path to source directory (mutually exclusive with image)
        dockerfile: Name of Dockerfile in source directory (default 'Dockerfile')
        build_remote: Force remote build using ACR Task (default False)
        registry: Optional ACR registry name for image storage
        skip_acr_check: Skip validation that project has ACR access (default False)
        cpu: CPU cores allocation (default "1")
        memory: Memory allocation with units (default "2Gi")
        environment_variables: List of environment variable dicts (default None)
        protocol: Agent communication protocol (default "responses")
        protocol_version: Protocol version (default "v1")
        description: Agent description (default None)
        min_replicas: Minimum replicas for horizontal scaling (default None)
        max_replicas: Maximum replicas for horizontal scaling (default None)
        no_wait: Don't wait for operation completion (default False)
        no_start: Skip automatic deployment after version creation (default False)
        timeout: Maximum time in seconds to wait for deployment (default 600)
        show_logs: Stream container logs during deployment (default False)

    Returns:
        dict: Created agent version details including status, version, and configuration
    """
    _validate_agent_create_parameters(image, source, build_remote, no_start, min_replicas, max_replicas)

    registry_name = _determine_registry_for_access_check(image, registry, source)

    if registry_name and not skip_acr_check:
        logger.info("Checking if project has access to ACR %s...", registry_name)

        has_access, principal_id, error_msg = _check_project_acr_access(
            cmd, client, account_name, project_name, registry_name
        )

        if not has_access:
            from azure.cli.core.commands.client_factory import get_subscription_id
            subscription_id = get_subscription_id(cmd.cli_ctx)

            # Get ACR resource group for the command
            from azure.cli.command_modules.acr._utils import (
                get_resource_group_name_by_registry_name
            )
            try:
                acr_rg = get_resource_group_name_by_registry_name(
                    cmd.cli_ctx, registry_name)
            except Exception:  # pylint: disable=broad-except
                acr_rg = '<acr-resource-group>'

            error_message = (
                f"{error_msg}\n\n"
                f"AI Foundry needs permission to pull the container image from ACR.\n"
                f"Grant AcrPull role to the project's managed identity:\n\n"
                f"  az role assignment create --assignee {principal_id} "
                f"--role AcrPull "
                f"--scope /subscriptions/{subscription_id}/resourceGroups/{acr_rg}/"
                f"providers/Microsoft.ContainerRegistry/registries/{registry_name}\n\n"
                f"Or use Azure Portal:\n"
                f"  1. Open ACR '{registry_name}' → Access Control (IAM)\n"
                f"  2. Add role assignment → AcrPull\n"
                f"  3. Assign access to: Managed Identity\n"
                f"  4. Select the project's managed identity\n\n"
                f"To skip this check (not recommended), use: --skip-acr-check"
            )
            raise ValidationError(error_message)

    image_uri = _resolve_agent_image_uri(
        cmd,
        source,
        agent_name,
        registry,
        dockerfile,
        build_remote,
        image,
    )

    _validate_image_tag(image_uri)
    _validate_memory_value(memory)
    _validate_cpu_value(cpu)

    env_vars = _convert_environment_variables(environment_variables)
    definition = _create_agent_definition(cpu, memory, protocol, protocol_version, image_uri, env_vars)

    request_body = {"definition": definition}
    if description:
        request_body["description"] = description

    request = azure.core.rest.HttpRequest(
        "POST",
        f"/agents/{urllib.parse.quote(agent_name)}/versions",
        json=request_body,
        params=AGENT_API_VERSION_PARAMS
    )

    response = None
    try:
        response = client.send_request(request)
        response.raise_for_status()
    except Exception as e:
        error_parts = [f"Failed to create agent version: {str(e)}"]

        if response:
            if hasattr(response, 'status_code'):
                error_parts.append(f"Status Code: {response.status_code}")
                if response.status_code == 405:
                    error_parts.append(
                        "Hint: Method Not Allowed - The API endpoint may not support this HTTP method."
                    )

            try:
                body = response.text() if callable(response.text) else str(response.text)
                error_parts.append(f"Response: {body}")
            except Exception as body_err:  # pylint: disable=broad-except
                logger.debug("Could not read response body: %s", body_err)

        error_parts.append(f"Request URL: {request.url}")
        error_parts.append(f"Request Method: {request.method}")
        raise AzureResponseError('\n'.join(error_parts)) from e

    if no_wait:
        logger.warning(
            "Agent creation initiated. Use "
            "'az cognitiveservices agent show -a %s --project-name %s -n %s' "
            "to check status.",
            account_name, project_name, agent_name
        )
        return {
            "status": "InProgress",
            "agentName": agent_name,
            "message": "Agent creation is in progress"
        }

    version_response = response.json()
    created_version = version_response.get("version")

    logger.debug("Version response: %s", json.dumps(version_response, indent=2))
    logger.debug("Extracted version: %s", created_version)

    if created_version and not no_start:
        _deploy_agent_version(
            cmd,
            client,
            agent_name,
            created_version,
            min_replicas,
            max_replicas,
            timeout=timeout,
            show_logs=show_logs,
        )
    elif created_version and no_start:
        logger.info("Agent version created but not deployed (--no-start specified). "
                    "Use 'az cognitiveservices agent start' to deploy the agent.")

    return version_response


def project_create(
        client,
        resource_group_name,
        account_name,
        project_name,
        location,
        assign_identity=False,
        user_assigned_identity=None,
        description=None,
        display_name=None,
        no_wait=False,
):
    """
    Create a project for Azure Cognitive Services account.
    """
    project = Project(properties=ProjectProperties(display_name=display_name, description=description))
    project.location = location
    if user_assigned_identity is None:
        assign_identity = True
    project.identity = compose_identity(system_assigned=assign_identity, user_assigned_identity=user_assigned_identity)
    return client.begin_create(resource_group_name, account_name, project_name, project, polling=no_wait)


def project_update(
    client,
    resource_group_name,
    account_name,
    project_name,
    description=None,
    display_name=None,
):
    """
    Update a project for Azure Cognitive Services account.
    """
    project_props = ProjectProperties()
    if description is not None:
        project_props.description = description
    if display_name is not None:
        project_props.display_name = display_name
    project = Project(properties=project_props)
    return client.begin_update(resource_group_name, account_name, project_name, project)


def account_connection_create(
    client,
    resource_group_name,
    account_name,
    connection_name,
    file,
):
    """
    Create a connection for Azure Cognitive Services account.
    """
    account_connection_properties = load_connection_from_source(source=file)
    account_connection = ConnectionPropertiesV2BasicResource(properties=account_connection_properties)

    return client.create(
        resource_group_name,
        account_name,
        connection_name,
        account_connection)


# This function is intended to be used with the 'generic_update_command' per
# https://github.com/Azure/azure-cli/blob/0b06b4f295766bcadaebdb7cf8fc05c7d6c9a5a8/doc/authoring_command_modules/authoring_commands.md#generic-update-commands
def account_connection_update(
    instance,
):
    """
    Update a connection for Azure Cognitive Services account.
    """
    account_connection = ConnectionUpdateContent(properties=instance.properties)
    return account_connection


def project_connection_create(
    client,
    resource_group_name,
    account_name,
    project_name,
    connection_name,
    file,
):
    """
    Create a connection for Azure Cognitive Services account.
    """
    project_connection_properties = load_connection_from_source(source=file)
    project_connection = ConnectionPropertiesV2BasicResource(properties=project_connection_properties)
    return client.create(
        resource_group_name,
        account_name,
        project_name,
        connection_name,
        project_connection)


# This function is intended to be used with the 'generic_update_command' per
# https://github.com/Azure/azure-cli/blob/0b06b4f295766bcadaebdb7cf8fc05c7d6c9a5a8/doc/authoring_command_modules/authoring_commands.md#generic-update-commands
def project_connection_update(
    instance,
):
    """
    Update a connection for Azure Cognitive Services account.
    """
    project_connection = ConnectionUpdateContent(properties=instance.properties)
    return project_connection
