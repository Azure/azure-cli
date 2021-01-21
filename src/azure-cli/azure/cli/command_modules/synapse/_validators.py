# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.util import CLIError
from msrestazure.tools import is_valid_resource_id


def validate_storage_account(namespace):
    from msrestazure.tools import parse_resource_id
    if is_valid_resource_id(namespace.storage_account):
        parsed_storage = parse_resource_id(namespace.storage_account)
        storage_name = parsed_storage['resource_name']
        namespace.storage_account = storage_name


def example_name_or_id_validator(cmd, namespace):
    # Example of a storage account name or ID validator.
    # See: https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#supporting-name-or-id-parameters
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import resource_id
    if namespace.storage_account:
        if not is_valid_resource_id(namespace.RESOURCE):
            namespace.storage_account = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage',
                type='storageAccounts',
                name=namespace.storage_account
            )


def validate_statement_language(namespace):
    statement_language = {
        'spark': 'spark',
        'scala': 'spark',
        'pyspark': 'pyspark',
        'python': 'pyspark',
        'sparkdotnet': 'sparkdotnet',
        'csharp': 'sparkdotnet',
        'sql': 'sql'
    }
    namespace.language = statement_language.get(namespace.language.lower())


def validate_audit_policy_arguments(namespace):
    blob_storage_arguments_provided = any(
        [namespace.storage_account, namespace.storage_endpoint, namespace.storage_account_access_key,
         namespace.retention_days])
    if not namespace.state and not blob_storage_arguments_provided:
        raise CLIError('Either state or blob storage arguments are missing')
