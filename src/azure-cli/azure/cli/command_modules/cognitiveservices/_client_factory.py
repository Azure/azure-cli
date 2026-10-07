# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re


_COGNITIVE_SERVICES_RESOURCE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,63}")


def _build_ai_project_endpoint(account_name, project_name):
    from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError

    for value, option_name, resource_type in (
            (account_name, "--account-name", "Cognitive Services account"),
            (project_name, "--project-name", "AI project")):
        if not value:
            raise RequiredArgumentMissingError(f"Please specify {option_name}.")
        if (not isinstance(value, str) or
                not _COGNITIVE_SERVICES_RESOURCE_NAME_PATTERN.fullmatch(value)):
            raise InvalidArgumentValueError(
                f"Invalid value for {option_name}. The {resource_type} name must be 2-64 characters, "
                "start with a letter or digit, and contain only letters, digits, periods, hyphens, or underscores."
            )

    return f"https://{account_name}.services.ai.azure.com/api/projects/{project_name}"


def get_cognitiveservices_management_client(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

    return get_mgmt_service_client(cli_ctx, CognitiveServicesManagementClient)


def cf_accounts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).accounts


def cf_deleted_accounts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).deleted_accounts


def cf_deployments(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).deployments


def cf_commitment_tiers(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).commitment_tiers


def cf_commitment_plans(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).commitment_plans


def cf_resource_skus(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).resource_skus


def cf_models(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).models


def cf_usages(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).usages


def cf_ai_projects(cli_ctx, command_args):
    """
    Create AI Projects client for data plane operations.
    Similar to keyvault's data plane client factory pattern.
    """
    from azure.ai.projects import AIProjectClient
    from azure.cli.core.commands.client_factory import prepare_client_kwargs_track2
    from azure.cli.core._profile import Profile

    # Get credentials using Azure CLI login
    profile = Profile(cli_ctx=cli_ctx)
    credential, _, _ = profile.get_login_credentials(
        subscription_id=cli_ctx.data.get("subscription_id")
    )

    # Get endpoint from command arguments (similar to keyvault's vault_url)
    account_name = command_args.get("account_name", None)
    endpoint = command_args.get("endpoint", None)
    project = command_args.get("project_name", None)

    # If no explicit endpoint provided, construct from account name
    if not endpoint and account_name:
        endpoint = _build_ai_project_endpoint(account_name, project)

    if not endpoint:
        from azure.cli.core.azclierror import RequiredArgumentMissingError

        raise RequiredArgumentMissingError("Please specify --account-name.")

    # Prepare client kwargs with proper logging and telemetry
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)

    # Create and return the AI Projects client
    return AIProjectClient(endpoint=endpoint, credential=credential, **client_kwargs)


def cf_projects(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).projects


def cf_account_connections(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).account_connections


def cf_managed_network_settings(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).managed_network_settings


def cf_managed_network_provisions(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).managed_network_provisions


def cf_outbound_rule(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).outbound_rule


def cf_account_capability_hosts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).account_capability_hosts


def cf_project_capability_hosts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).project_capability_hosts


def cf_managed_compute_deployments(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).managed_compute_deployments


def cf_computes(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).computes


def cf_project_connections(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).project_connections
