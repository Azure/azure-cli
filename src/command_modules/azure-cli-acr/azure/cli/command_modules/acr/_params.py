# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from argcomplete.completers import FilesCompleter
from knack.arguments import CLIArgumentType

from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    PasswordName,
    WebhookStatus,
    WebhookAction,
    BuildTaskStatus,
    OsType,
    BaseImageTriggerType,
    BuildStatus
)

from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_location_type,
    tags_type,
    deployment_name_type,
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
    BUILD_TASK_RESOURCE_TYPE,
    BUILD_STEP_RESOURCE_TYPE,
    CLASSIC_REGISTRY_SKU,
    MANAGED_REGISTRY_SKU
)
from ._validators import (
    validate_registry_name,
    validate_headers,
    validate_build_arg,
    validate_secret_build_arg
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
    with self.argument_context('acr') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('registry_name', options_list=['--name', '-n'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('storage_account_name', help='Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account. Only applicable to Classic SKU.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
        c.argument('sku', help='The SKU of the container registry', arg_type=get_enum_type(MANAGED_REGISTRY_SKU + CLASSIC_REGISTRY_SKU))
        c.argument('admin_enabled', help='Indicates whether the admin user is enabled', arg_type=get_three_state_flag())
        c.argument('password_name', help='The name of password to regenerate', arg_type=get_enum_type(PasswordName))
        c.argument('username', options_list=['--username', '-u'], help='The username used to log into a container registry')
        c.argument('password', options_list=['--password', '-p'], help='The password used to log into a container registry')
        c.argument('image_names', arg_type=image_by_tag_type, action='append')
        c.argument('timeout', type=int, help='The build timeout in seconds.')
        c.argument('docker_file_path', options_list=['--file', '-f'], help="The relative path of the the docker file to the source code root folder.")
        c.argument('build_arg', help="Build argument in 'name[=value]' format.", action='append', validator=validate_build_arg)
        c.argument('secret_build_arg', help="Secret build argument in 'name[=value]' format.", action='append', validator=validate_secret_build_arg)
        c.argument('no_logs', help="Do not show logs after successfully queuing the build.", action='store_true')
        c.argument('os_type', options_list=['--os'], help='The operating system type required for the build.', arg_type=get_enum_type(OsType))

    with self.argument_context('acr import') as c:
        c.argument('source', help="The source identifier in the format '[registry.azurecr.io/]repository[:tag]' or '[registry.azurecr.io/]repository@digest'.")
        c.argument('source_registry', options_list=['--registry', '-r'], help='The source container registry can be name, login server or resource ID of the source registry.')
        c.argument('target_tags', arg_type=image_by_tag_type, action='append')
        c.argument('repository', help='The repository name to do a manifest-only copy for images.', action='append')
        c.argument('force', help='Overwrite the existing tag of the image to be imported.', action='store_true')

    with self.argument_context('acr repository') as c:
        c.argument('repository', help="The name of the repository.")
        c.argument('image', arg_type=image_by_tag_or_digest_type)
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')
        c.argument('top', type=int, help='Limit the number of items in the results.')
        c.argument('orderby', help='Order the items in the results. Default to alphabetical order of names.', arg_type=get_enum_type(['time_asc', 'time_desc']))
        c.argument('detail', help='Show detailed information.', action='store_true')
        c.argument('delete_enabled', help='Indicates whether delete operation is allowed.', arg_type=get_three_state_flag())
        c.argument('list_enabled', help='Indicates whether this item shows in list operation results.', arg_type=get_three_state_flag())
        c.argument('read_enabled', help='Indicates whether read operation is allowed.', arg_type=get_three_state_flag())
        c.argument('write_enabled', help='Indicates whether write or delete operation is allowed.', arg_type=get_three_state_flag())

    with self.argument_context('acr repository delete') as c:
        c.argument('manifest', nargs='?', required=False, const='', default=None, help=argparse.SUPPRESS)
        c.argument('tag', help=argparse.SUPPRESS)

    with self.argument_context('acr repository untag') as c:
        c.argument('image', arg_type=image_by_tag_type)

    with self.argument_context('acr create') as c:
        c.argument('registry_name', completer=None, validator=validate_registry_name)
        c.argument('deployment_name', arg_type=deployment_name_type, validator=None)
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)

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

    with self.argument_context('acr build') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        c.positional('source_location', help="The local source code directory path (e.g., './src') or the URL to a git repository (e.g., 'https://github.com/Azure-Samples/acr-build-helloworld-node.git') or a remote tarball (e.g., 'http://server/context.tar.gz').", completer=FilesCompleter())
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", action='store_true')

    with self.argument_context('acr build-task') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        # build task parameters
        c.argument('build_task_name', options_list=['--name', '-n'], help='The name of the build task.', completer=get_resource_name_completion_list(BUILD_TASK_RESOURCE_TYPE))
        c.argument('alias', help='The alternative name for build task. Default to the build task name.')
        c.argument('status', help='The current status of build task.', arg_type=get_enum_type(BuildTaskStatus))
        c.argument('cpu', type=int, help='The CPU configuration in terms of number of cores required for the build.')
        c.argument('repository_url', options_list=['--context', '-c'], help="The full URL to the source code respository.")
        c.argument('commit_trigger_enabled', help="Indicates whether the source control commit trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('git_access_token', help="The access token used to access the source control provider.")
        # build step parameters
        c.argument('step_name', help='The name of the build step.', completer=get_resource_name_completion_list(BUILD_STEP_RESOURCE_TYPE))
        c.argument('branch', help="The source control branch name.")
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", arg_type=get_three_state_flag())
        c.argument('no_cache', help='Indicates whether the image cache is enabled.', arg_type=get_three_state_flag())
        c.argument('base_image_trigger', help="The type of the auto trigger for base image dependency updates.", arg_type=get_enum_type(BaseImageTriggerType))
        # build parameters
        c.argument('top', help='Limit the number of latest builds in the results.')
        c.argument('build_id', help='The unique build identifier.')
        c.argument('build_status', help='The current status of build.', arg_type=get_enum_type(BuildStatus))

    with self.argument_context('acr build-task create') as c:
        c.argument('build_task_name', completer=None)
