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
from .policy import RetentionType

from ._constants import (
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
    validate_set_secret,
    validate_retention_days
)

image_by_tag_or_digest_type = CLIArgumentType(
    options_list=['--image', '-t'],
    help="The name of the image. May include a tag in the format 'name:tag' or digest in the format 'name@digest'."
)


def load_arguments(self, _):  # pylint: disable=too-many-statements
    SkuName, PasswordName, DefaultAction, PolicyStatus, WebhookAction, WebhookStatus, TaskStatus, BaseImageTriggerType, RunStatus, SourceRegistryLoginMode, UpdateTriggerPayloadType = self.get_models('SkuName', 'PasswordName', 'DefaultAction', 'PolicyStatus', 'WebhookAction', 'WebhookStatus', 'TaskStatus', 'BaseImageTriggerType', 'RunStatus', 'SourceRegistryLoginMode', 'UpdateTriggerPayloadType')
    with self.argument_context('acr') as c:
        c.argument('tags', arg_type=tags_type)
        c.argument('registry_name', options_list=['--name', '-n'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('tenant_suffix', options_list=['--suffix'], help="The tenant suffix in registry login server. You may specify '--suffix tenant' if your registry login server is in the format 'registry-tenant.azurecr.io'. Applicable if you\'re accessing the registry from a different subscription or you have permission to access images but not the permission to manage the registry resource.")
        c.argument('sku', help='The SKU of the container registry', arg_type=get_enum_type(SkuName))
        c.argument('admin_enabled', help='Indicates whether the admin user is enabled', arg_type=get_three_state_flag())
        c.argument('password_name', help='The name of password to regenerate', arg_type=get_enum_type(PasswordName))
        c.argument('username', options_list=['--username', '-u'], help='The username used to log into a container registry')
        c.argument('password', options_list=['--password', '-p'], help='The password used to log into a container registry')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')
        c.argument('image_names', options_list=['--image', '-t'], help="The name and tag of the image using the format: '-t repo/image:tag'. Multiple tags are supported by passing -t multiple times.", action='append')
        c.argument('timeout', type=int, help='The timeout in seconds.')
        c.argument('docker_file_path', options_list=['--file', '-f'], help="The relative path of the the docker file to the source code root folder. Default to 'Dockerfile'.")
        c.argument('no_logs', help="Do not show logs after successfully queuing the build.", action='store_true')
        c.argument('no_wait', help="Do not wait for the run to complete and return immediately after queuing the run.", action='store_true')
        c.argument('no_format', help="Indicates whether the logs should be displayed in raw format", action='store_true')
        c.argument('platform', options_list=['--platform', c.deprecate(target='--os', redirect='--platform', hide=True)], help="The platform where build/task is run, Eg, 'windows' and 'linux'. When it's used in build commands, it also can be specified in 'os/arch/variant' format for the resulting image. Eg, linux/arm/v7. The 'arch' and 'variant' parts are optional.")
        c.argument('target', help='The name of the target build stage.')
        c.argument('auth_mode', help='Auth mode of the source registry.', arg_type=get_enum_type(SourceRegistryLoginMode))
        # Overwrite default shorthand of cmd to make availability for acr usage
        c.argument('cmd', options_list=['--__cmd__'])
        c.argument('cmd_value', help="Commands to execute.", options_list=['--cmd'])

    for scope in ['acr create', 'acr update']:
        with self.argument_context(scope, arg_group='Network Rule') as c:
            c.argument('default_action', arg_type=get_enum_type(DefaultAction),
                       help='Default action to apply when no rule matches. Only applicable to Premium SKU.')

    with self.argument_context('acr import') as c:
        c.argument('source_image', options_list=['--source'], help="The source identifier will be either a source image name or a fully qualified source.")
        c.argument('source_registry', options_list=['--registry', '-r'], help='The source container registry can be name, login server or resource ID of the source registry.')
        c.argument('source_registry_username', options_list=['--username', '-u'], help='The username of source container registry')
        c.argument('source_registry_password', options_list=['--password', '-p'], help='The password of source container registry')
        c.argument('target_tags', options_list=['--image', '-t'], help="The name and tag of the image using the format: '-t repo/image:tag'. Multiple tags are supported by passing -t multiple times.", action='append')
        c.argument('repository', help='The repository name for a manifest-only copy of images. Multiple copies supported by passing --repository multiple times.', action='append')
        c.argument('force', help='Overwrite the existing tag of the image to be imported.', action='store_true')

    with self.argument_context('acr config content-trust') as c:
        c.argument('registry_name', options_list=['--registry', '-r', c.deprecate(target='-n', redirect='-r', hide=True), c.deprecate(target='--name', redirect='--registry', hide=True)])
        c.argument('status', help="Indicates whether content-trust is enabled.", arg_type=get_enum_type(PolicyStatus))

    with self.argument_context('acr config retention') as c:
        c.argument('status', help="Indicates whether retention policy is enabled.", arg_type=get_enum_type(PolicyStatus))
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.argument('days', type=int, help='The number of days to retain an untagged manifest after which it gets purged (Range: 0 to 365). Value "0" will delete untagged manifests immediately.', validator=validate_retention_days, default=7)
        c.argument('policy_type', options_list=['--type'], help='The type of retention policy.', arg_type=get_enum_type(RetentionType))

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
        c.argument('image', options_list=['--image', '-t'], help="The name of the image. May include a tag in the format 'name:tag'.")

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
        c.positional('source_location', help="The local source code directory path (e.g., './src') or the URL to a git repository (e.g., 'https://github.com/Azure-Samples/acr-build-helloworld-node.git') or a remote tarball (e.g., 'http://server/context.tar.gz'). If '/dev/null' is specified, the value will be set to None and ignored.", completer=FilesCompleter())
        c.argument('file', options_list=['--file', '-f'], help="The task template/definition file path relative to the source context. It can be '-' to pipe a file from the standard input.")
        c.argument('values', help="The task values file path relative to the source context.")
        c.argument('set_value', options_list=['--set'], help="Value in 'name[=value]' format. Multiples supported by passing --set multiple times.", action='append', validator=validate_set)
        c.argument('set_secret', help="Secret value in '--set name[=value]' format. Multiples supported by passing --set multiple times.", action='append', validator=validate_set_secret)

    with self.argument_context('acr pack build') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.argument('image_name', options_list=['--image', '-t'], help="The name and tag of the image using the format: '-t repo/image:tag'.")
        c.argument('builder', options_list=['--builder', '-b'], help="The name and tag of a Buildpack builder image.")
        c.argument('pull', options_list=['--pull'], help="Pull the latest builder and run images before use.", action='store_true')
        c.positional('source_location', help="The local source code directory path (e.g., './src') or the URL to a git repository (e.g., 'https://github.com/Azure-Samples/acr-build-helloworld-node.git') or a remote tarball (e.g., 'http://server/context.tar.gz').", completer=FilesCompleter())

    with self.argument_context('acr build') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.positional('source_location', help="The local source code directory path (e.g., './src') or the URL to a git repository (e.g., 'https://github.com/Azure-Samples/acr-build-helloworld-node.git') or a remote tarball (e.g., 'http://server/context.tar.gz').", completer=FilesCompleter())
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", action='store_true')
        c.argument('no_wait', help="Do not wait for the build to complete and return immediately after queuing the build.", action='store_true')
        c.argument('arg', options_list=['--build-arg'], help="Build argument in '--build-arg name[=value]' format. Multiples supported by passing --build-arg multiple times.", action='append', validator=validate_arg)
        c.argument('secret_arg', options_list=['--secret-build-arg'], help="Secret build argument in '--secret-build-arg name[=value]' format. Multiples supported by passing '--secret-build-arg name[=value]' multiple times.", action='append', validator=validate_secret_arg)

    with self.argument_context('acr task') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.argument('task_name', options_list=['--name', '-n'], help='The name of the task.', completer=get_resource_name_completion_list(TASK_RESOURCE_TYPE))
        c.argument('status', help='The current status of task.', arg_type=get_enum_type(TaskStatus))
        c.argument('with_secure_properties', help="Indicates whether the secure properties of a task should be returned.", action='store_true')

        # DockerBuildStep, FileTaskStep parameters
        c.argument('file', options_list=['--file', '-f'], help="The relative path of the the task/docker file to the source code root folder. Task files must be suffixed with '.yaml' or piped from the standard input using '-'.")
        c.argument('image', arg_type=image_by_tag_or_digest_type)
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", arg_type=get_three_state_flag())
        c.argument('no_cache', help='Indicates whether the image cache is enabled.', arg_type=get_three_state_flag())
        c.argument('values', help="The task values/parameters file path relative to the source context.")

        # common to DockerBuildStep, FileTaskStep and RunTaskStep
        c.argument('context_path', options_list=['--context', '-c'], help="The full URL to the source code repository (Requires '.git' suffix for a github repo). If '/dev/null' is specified, the value will be set to None and ignored.")
        c.argument('arg', help="Build argument in '--arg name[=value]' format. Multiples supported by passing '--arg` multiple times.", action='append', validator=validate_arg)
        c.argument('secret_arg', help="Secret build argument in '--secret-arg name[=value]' format. Multiples supported by passing --secret-arg multiple times.", action='append', validator=validate_secret_arg)
        c.argument('set_value', options_list=['--set'], help="Task value in '--set name[=value]' format. Multiples supported by passing --set multiple times.", action='append', validator=validate_set)
        c.argument('set_secret', help="Secret task value in '--set-secret name[=value]' format. Multiples supported by passing --set-secret multiple times.", action='append', validator=validate_set_secret)

        # Trigger parameters
        c.argument('source_trigger_name', help="The name of the source trigger.")
        c.argument('commit_trigger_enabled', help="Indicates whether the source control commit trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('pull_request_trigger_enabled', help="Indicates whether the source control pull request trigger is enabled. The trigger is disabled by default.", arg_type=get_three_state_flag())
        c.argument('schedule', help="Schedule for a timer trigger represented as a cron expression. An optional trigger name can be specified using `--schedule name:schedule` format. Multiples supported by passing --schedule multiple times.", action='append')
        c.argument('git_access_token', help="The access token used to access the source control provider.")
        c.argument('branch', help="The source control branch name.")
        c.argument('base_image_trigger_name', help="The name of the base image trigger.")
        c.argument('base_image_trigger_enabled', help="Indicates whether the base image trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('base_image_trigger_type', help="The type of the auto trigger for base image dependency updates.", arg_type=get_enum_type(BaseImageTriggerType))
        c.argument('update_trigger_endpoint', help="The full URL of the endpoint to receive base image update trigger notifications.", is_preview=True)
        c.argument('update_trigger_payload_type', help="Indicates whether to include metadata about the base image trigger in the payload alongwith the update trigger token, when a notification is sent.", arg_type=get_enum_type(UpdateTriggerPayloadType), is_preview=True)

        # Run related parameters
        c.argument('top', help='Limit the number of latest runs in the results.')
        c.argument('run_id', help='The unique run identifier.')
        c.argument('run_status', help='The current status of run.', arg_type=get_enum_type(RunStatus))
        c.argument('no_archive', help='Indicates whether the run should be archived.', arg_type=get_three_state_flag())

        # Run agent parameters
        c.argument('cpu', type=int, help='The CPU configuration in terms of number of cores required for the run.')

        # MSI parameter
        c.argument('assign_identity', nargs='*', help="Assigns managed identities to the task. Use '[system]' to refer to the system-assigned identity or a resource ID to refer to a user-assigned identity. Please see https://aka.ms/acr/tasks/task-create-managed-identity for more information.")

        # Update trigger token parameters
        c.argument('update_trigger_token', help="The payload that will be passed back alongwith the base image trigger notification.", is_preview=True)

    with self.argument_context('acr task create') as c:
        c.argument('task_name', completer=None)

    with self.argument_context('acr task identity') as c:
        c.argument('identities', options_list=['--identities'], nargs='*', help="Assigns managed identities to the task. Use '[system]' to refer to the system-assigned identity or a resource ID to refer to a user-assigned identity.")

    with self.argument_context('acr task credential') as c:
        # Custom registry credentials
        c.argument('login_server', help="The login server of the custom registry. For instance, 'myregistry.azurecr.io'.", required=True)

    for scope in ['acr task credential add', 'acr task credential update']:
        with self.argument_context(scope) as c:
            c.argument('username', options_list=['--username', '-u'], help="The username to login to the custom registry. This can be plain text or a key vault secret URI.")
            c.argument('password', options_list=['--password', '-p'], help="The password to login to the custom registry. This can be plain text or a key vault secret URI.")
            c.argument('use_identity', help="The task managed identity used for the credential. Use '[system]' to refer to the system-assigned identity or a client id to refer to a user-assigned identity. Please see https://aka.ms/acr/tasks/cross-registry-authentication for more information.")

    with self.argument_context('acr task timer') as c:
        # Timer trigger parameters
        c.argument('timer_name', help="The name of the timer trigger.", required=True)
        c.argument('timer_schedule', options_list=['--schedule'], help="The schedule of the timer trigger represented as a cron expression.")
        c.argument('enabled', help="Indicates whether the timer trigger is enabled.", arg_type=get_three_state_flag())

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

    with self.argument_context('acr check-health') as c:
        c.argument('ignore_errors', options_list=['--ignore-errors'], help='Provide all health checks, even if errors are found', action='store_true', required=False)
