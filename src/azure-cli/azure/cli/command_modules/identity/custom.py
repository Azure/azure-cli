# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    MutuallyExclusiveArgumentError
)


def list_user_assigned_identities(cmd, resource_group_name=None):
    from azure.cli.command_modules.identity._client_factory import _msi_client_factory
    client = _msi_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.user_assigned_identities.list_by_resource_group(resource_group_name)
    return client.user_assigned_identities.list_by_subscription()


def create_identity(client, resource_group_name, resource_name, location, tags=None):
    parameters = {}
    parameters['location'] = location
    if tags is not None:
        parameters['tags'] = tags
    return client.create_or_update(resource_group_name=resource_group_name,
                                   resource_name=resource_name,
                                   parameters=parameters)


def list_identity_resources(cmd, resource_group_name, resource_name):
    from azure.cli.command_modules.identity._client_factory import _msi_list_resources_client
    client = _msi_list_resources_client(cmd.cli_ctx)
    return client.list_associated_resources(resource_group_name=resource_group_name,
                                            resource_name=resource_name)


def create_or_update_federated_credential(cmd, client, resource_group_name, identity_name, federated_credential_name,
                                          issuer=None, subject=None, audiences=None, claims_matching_expression_value=None, claims_matching_expression_version=None):
    _default_audiences = ['api://AzureADTokenExchange']
    audiences = _default_audiences if not audiences else audiences
    if not issuer:
        recommendation = "Please provide the issuer URL using --issuer parameter. For GitHub Actions, use 'https://token.actions.githubusercontent.com'"
        raise RequiredArgumentMissingError('Issuer URL is required for federated credential creation', recommendation)
    
    # When subject is present, CME should be null
    if subject:
        claims_matching_expression_value = None
        claims_matching_expression_version = None
    elif not claims_matching_expression_value:
        recommendation = [
            "Option 1: Provide --subject to create a federated credential with direct subject matching",
            "Option 2: Provide --claims-matching-expression-value and --claims-matching-expression-version to create a federated credential with claims matching expression"
        ]
        raise RequiredArgumentMissingError('Missing required authentication criteria for federated credential', recommendation)
    
    if subject and claims_matching_expression_value:
        recommendation = [
            "Option 1: Remove --subject to use claims matching expression",
            "Option 2: Remove --claims-matching-expression-value and --claims-matching-expression-version to use subject"
        ]
        raise MutuallyExclusiveArgumentError('Subject and claims matching expression cannot be used together', recommendation)

    FederatedIdentityCredential = cmd.get_models('FederatedIdentityCredential', resource_type=ResourceType.MGMT_MSI,
                                                 operation_group='federated_identity_credentials')
    parameters = FederatedIdentityCredential(issuer=issuer, subject=subject, audiences=audiences, 
                                           claims_matching_expression_value=claims_matching_expression_value,
                                           claims_matching_expression_version=claims_matching_expression_version)

    return client.create_or_update(resource_group_name=resource_group_name, resource_name=identity_name,
                                   federated_identity_credential_resource_name=federated_credential_name,
                                   parameters=parameters)


def delete_federated_credential(client, resource_group_name, identity_name, federated_credential_name):
    return client.delete(resource_group_name=resource_group_name, resource_name=identity_name,
                         federated_identity_credential_resource_name=federated_credential_name)


def show_federated_credential(client, resource_group_name, identity_name, federated_credential_name):
    return client.get(resource_group_name=resource_group_name, resource_name=identity_name,
                      federated_identity_credential_resource_name=federated_credential_name)


def list_federated_credential(client, resource_group_name, identity_name):
    return client.list(resource_group_name=resource_group_name, resource_name=identity_name)
