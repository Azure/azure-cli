# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.util import CLIError
from knack.log import get_logger
from azure.mgmt.core.tools import is_valid_resource_id


def validate_storage_account(namespace):
    from azure.mgmt.core.tools import parse_resource_id
    if is_valid_resource_id(namespace.storage_account):
        parsed_storage = parse_resource_id(namespace.storage_account)
        storage_name = parsed_storage['resource_name']
        namespace.storage_account = storage_name


def example_name_or_id_validator(cmd, namespace):
    # Example of a storage account name or ID validator.
    # See: https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#supporting-name-or-id-parameters
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import resource_id
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


def validate_repository_type(namespace):
    logger = get_logger(__name__)
    repository_config_args = ['--host-name', '--account-name', '--collaboration-branch', '--repository-name', '--root-folder'
                              '--project-name', '--tenant-id']
    if namespace.repository_type is None:
        logger.warning('Parameter --repository-type is missing, the following arguments are ignored: %s. Repository configuration will not work.',
                       ' ,'.join(repository_config_args))


def add_progress_callback(cmd, namespace):
    def _update_progress(current, total):
        message = getattr(_update_progress, 'message', 'Alive')
        reuse = getattr(_update_progress, 'reuse', False)

        if total:
            hook.add(message=message, value=current, total_val=total)
            if total == current and not reuse:
                hook.end()

    hook = cmd.cli_ctx.get_progress_controller(det=True)
    _update_progress.hook = hook

    if not namespace.no_progress:
        namespace.progress_callback = _update_progress
    del namespace.no_progress
