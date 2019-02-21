# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from argcomplete.completers import FilesCompleter
from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    tags_type,
    get_resource_name_completion_list,
    quotes,
    get_three_state_flag,
    get_enum_type
)
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from ._constants import (
    STORAGE_RESOURCE_TYPE,
    REGISTRY_RESOURCE_TYPE,
    WEBHOOK_RESOURCE_TYPE,
    REPLICATION_RESOURCE_TYPE,
    TASK_RESOURCE_TYPE
)
from ._validators import (
    validate_headers,
    validate_arg,
    validate_secret_arg,
    validate_set,
    validate_set_secret
)


image_by_tag_type = CLIArgumentType(
    options_list=['--image', '-t'],
    help="The name of the image. May include a tag in the format 'name:tag'."
)

image_by_tag_or_digest_type = CLIArgumentType(
    options_list=['--image', '-t'],
    help="The name of the image. May include a tag in the format 'name:tag' or digest in the format 'name@digest'."
)


def load_arguments(self, _):  # pylint: disable=too-many-statements
    SkuName, PasswordName, OsType, DefaultAction, PolicyStatus, WebhookAction, WebhookStatus, TaskStatus, BaseImageTriggerType, RunStatus = self.get_models('SkuName', 'PasswordName', 'OsType', 'DefaultAction', 'PolicyStatus', 'WebhookAction', 'WebhookStatus', 'TaskStatus', 'BaseImageTriggerType', 'RunStatus')
    with self.argument_context('acr') as c:
        c.argument('tags', arg_type=tags_type)
        c.argument('registry_name', options_list=['--name', '-n'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('tenant_suffix', options_list=['--suffix'], help="The tenant suffix in registry login server. You may specify '--suffix tenant' if your registry login server is in the format 'registry-tenant.azurecr.io'. Applicable if you\'re accessing the registry from a different subscription or you have permission to access images but not the permission to manage the registry resource.")
        c.argument('storage_account_name', help='Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account. Only applicable to Classic SKU.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
        c.argument('sku', help='The SKU of the container registry', arg_type=get_enum_type(SkuName))
        c.argument('admin_enabled', help='Indicates whether the admin user is enabled', arg_type=get_three_state_flag())
        c.argument('password_name', help='The name of password to regenerate', arg_type=get_enum_type(PasswordName))
        c.argument('username', options_list=['--username', '-u'], help='The username used to log into a container registry')
        c.argument('password', options_list=['--password', '-p'], help='The password used to log into a container registry')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')
        c.argument('image_names', arg_type=image_by_tag_type, action='append')
        c.argument('timeout', type=int, help='The timeout in seconds.')
        c.argument('docker_file_path', options_list=['--file', '-f'], help="The relative path of the the docker file to the source code root folder. Default to 'Dockerfile'.")
        c.argument('no_logs', help="Do not show logs after successfully queuing the build.", action='store_true')
        c.argument('no_wait', help="Do not wait for the run to complete and return immediately after queuing the run.", action='store_true')
        c.argument('no_format', help="Indicates whether the logs should be displayed in raw format", action='store_true')
        c.argument('os_type', options_list=['--os'], help='The operating system type required for the build.', arg_type=get_enum_type(OsType), deprecate_info=c.deprecate(redirect='platform', hide=True))
        c.argument('platform', help="The platform where build/task is run, Eg, 'windows' and 'linux'. When it's used in build commands, it also can be specified in 'os/arch/variant' format for the resulting image. Eg, linux/arm/v7. The 'arch' and 'variant' parts are optional.")
        c.argument('target', help='The name of the target build stage.')

    for scope in ['acr create', 'acr update']:
        with self.argument_context(scope, arg_group='Network Rule') as c:
            c.argument('default_action', arg_type=get_enum_type(DefaultAction),
                       help='Default action to apply when no rule matches. Only applicable to Premium SKU.')

    with self.argument_context('acr import') as c:
        c.argument('source', help="The source identifier in the format '[registry.azurecr.io/]repository[:tag]' or '[registry.azurecr.io/]repository@digest'.")
        c.argument('source_registry', options_list=['--registry', '-r'], help='The source container registry can be name, login server or resource ID of the source registry.')
        c.argument('source_registry_username', options_list=['--username', '-u'], help='The username of source container registry')
        c.argument('source_registry_password', options_list=['--password', '-p'], help='The password of source container registry')
        c.argument('target_tags', arg_type=image_by_tag_type, action='append')
        c.argument('repository', help='The repository name to do a manifest-only copy for images.', action='append')
        c.argument('force', help='Overwrite the existing tag of the image to be imported.', action='store_true')

    with self.argument_context('acr config content-trust') as c:
        c.argument('status', help="Indicates whether content-trust is enabled or disabled.", arg_type=get_enum_type(PolicyStatus))

    with self.argument_context('acr login') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(hide=True))

    with self.argument_context('acr repository') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(hide=True))
        c.argument('repository', help="The name of the repository.")
        c.argument('image', arg_type=image_by_tag_or_digest_type)
        c.argument('top', type=int, help='Limit the number of items in the results.')
        c.argument('orderby', help='Order the items in the results. Default to alphabetical order of names.', arg_type=get_enum_type(['time_asc', 'time_desc']))
        c.argument('detail', help='Show detailed information.', action='store_true')
        c.argument('delete_enabled', help='Indicates whether delete operation is allowed.', arg_type=get_three_state_flag())
        c.argument('list_enabled', help='Indicates whether this item shows in list operation results.', arg_type=get_three_state_flag())
        c.argument('read_enabled', help='Indicates whether read operation is allowed.', arg_type=get_three_state_flag())
        c.argument('write_enabled', help='Indicates whether write or delete operation is allowed.', arg_type=get_three_state_flag())

    with self.argument_context('acr repository untag') as c:
        c.argument('image', arg_type=image_by_tag_type)

    with self.argument_context('acr create') as c:
        c.argument('registry_name', completer=None)
        c.argument('deployment_name', validator=None)
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('acr check-name') as c:
        c.argument('registry_name', completer=None)

    with self.argument_context('acr webhook') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.argument('webhook_name', options_list=['--name', '-n'], help='The name of the webhook', completer=get_resource_name_completion_list(WEBHOOK_RESOURCE_TYPE))
        c.argument('uri', help='The service URI for the webhook to post notifications.')
        c.argument('headers', nargs='+', help="Space-separated custom headers in 'key[=value]' format that will be added to the webhook notifications. Use {} to clear existing headers.".format(quotes), validator=validate_headers)
        c.argument('actions', nargs='+', help='Space-separated list of actions that trigger the webhook to post notifications.', arg_type=get_enum_type(WebhookAction))
        c.argument('status', help='Indicates whether the webhook is enabled.', arg_type=get_enum_type(WebhookStatus))
        c.argument('scope', help="The scope of repositories where the event can be triggered. For example, 'foo:*' means events for all tags under repository 'foo'. 'foo:bar' means events for 'foo:bar' only. 'foo' is equivalent to 'foo:latest'. Empty means events for all repositories.")

    with self.argument_context('acr webhook create') as c:
        c.argument('webhook_name', completer=None)

    with self.argument_context('acr replication') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.argument('replication_name', options_list=['--name', '-n'], help='The name of the replication.', completer=get_resource_name_completion_list(REPLICATION_RESOURCE_TYPE))

    with self.argument_context('acr replication create') as c:
        c.argument('replication_name', help='The name of the replication. Default to the location name.', completer=None)

    with self.argument_context('acr run') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.positional('source_location', help="The local source code directory path (e.g., './src') or the URL to a git repository (e.g., 'https://github.com/Azure-Samples/acr-build-helloworld-node.git') or a remote tarball (e.g., 'http://server/context.tar.gz').", completer=FilesCompleter())
        c.argument('file', options_list=['--file', '-f'], help="The task template/definition file path relative to the source context.")
        c.argument('values', help="The task values file path relative to the source context.")
        c.argument('set_value', options_list=['--set'], help="Value in 'name[=value]' format.", action='append', validator=validate_set)
        c.argument('set_secret', help="Secret value in 'name[=value]' format.", action='append', validator=validate_set_secret)

    with self.argument_context('acr build') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.positional('source_location', help="The local source code directory path (e.g., './src') or the URL to a git repository (e.g., 'https://github.com/Azure-Samples/acr-build-helloworld-node.git') or a remote tarball (e.g., 'http://server/context.tar.gz').", completer=FilesCompleter())
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", action='store_true')
        c.argument('arg', options_list=['--build-arg'], help="Build argument in 'name[=value]' format.", action='append', validator=validate_arg)
        c.argument('secret_arg', options_list=['--secret-build-arg'], help="Secret build argument in 'name[=value]' format.", action='append', validator=validate_secret_arg)

    with self.argument_context('acr task') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.argument('task_name', options_list=['--name', '-n'], help='The name of the task.', completer=get_resource_name_completion_list(TASK_RESOURCE_TYPE))
        c.argument('status', help='The current status of task.', arg_type=get_enum_type(TaskStatus))
        c.argument('with_secure_properties', help="Indicates whether the secure properties of a task should be returned.", action='store_true')

        # DockerBuildStep, FileTaskStep parameters
        c.argument('file', options_list=['--file', '-f'], help="The relative path of the the task/docker file to the source code root folder. Task files must be suffixed with '.yaml'.")
        c.argument('image', arg_type=image_by_tag_or_digest_type)
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", arg_type=get_three_state_flag())
        c.argument('no_cache', help='Indicates whether the image cache is enabled.', arg_type=get_three_state_flag())
        c.argument('values', help="The task values/parameters file path relative to the source context.")

        # common to DockerBuildStep, FileTaskStep and RunTaskStep
        c.argument('context_path', options_list=['--context', '-c'], help="The full URL to the source code repository (Requires '.git' suffix for a github repo).")
        c.argument('arg', help="Build argument in 'name[=value]' format.", action='append', validator=validate_arg)
        c.argument('secret_arg', help="Secret build argument in 'name[=value]' format.", action='append', validator=validate_secret_arg)
        c.argument('set_value', options_list=['--set'], help="Task value in 'name[=value]' format.", action='append', validator=validate_set)
        c.argument('set_secret', help="Secret task value in 'name[=value]' format.", action='append', validator=validate_set_secret)

        # Source Trigger parameters
        c.argument('source_trigger_name', help="The name of the source trigger.")
        c.argument('commit_trigger_enabled', help="Indicates whether the source control commit trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('pull_request_trigger_enabled', help="Indicates whether the source control pull request trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('git_access_token', help="The access token used to access the source control provider.")
        c.argument('branch', help="The source control branch name.")
        c.argument('base_image_trigger_name', help="The name of the base image trigger.")
        c.argument('base_image_trigger_enabled', help="Indicates whether the base image trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('base_image_trigger_type', help="The type of the auto trigger for base image dependency updates.", arg_type=get_enum_type(BaseImageTriggerType))

        # Run related parameters
        c.argument('top', help='Limit the number of latest runs in the results.')
        c.argument('run_id', help='The unique run identifier.')
        c.argument('run_status', help='The current status of run.', arg_type=get_enum_type(RunStatus))
        c.argument('no_archive', help='Indicates whether the run should be archived.', arg_type=get_three_state_flag())

        # Run agent parameters
        c.argument('cpu', type=int, help='The CPU configuration in terms of number of cores required for the run.')

    with self.argument_context('acr task create') as c:
        c.argument('task_name', completer=None)

    with self.argument_context('acr helm') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(hide=True))
        c.argument('repository', help=argparse.SUPPRESS)
        c.argument('version', help='The helm chart version.')

    with self.argument_context('acr helm show') as c:
        c.positional('chart', help='The helm chart name.')

    with self.argument_context('acr helm delete') as c:
        c.positional('chart', help='The helm chart name.')
        c.argument('prov', help='Only delete the provenance file.', action='store_true')

    with self.argument_context('acr helm push') as c:
        c.positional('chart_package', help="The helm chart package.", completer=FilesCompleter())
        c.argument('force', help='Overwrite the existing chart package.', action='store_true')

    with self.argument_context('acr network-rule') as c:
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.')
        c.argument('ip_address', help='IPv4 address or CIDR range.')
