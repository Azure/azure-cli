# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from argcomplete.completers import FilesCompleter

from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
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
    get_three_state_flag
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


def load_arguments(self, _):  # pylint: disable=too-many-statements
    with self.argument_context('acr') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('registry_name', options_list=['--name', '-n'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('storage_account_name', help='Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account. Only applicable to Classic SKU.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
        c.argument('sku', help='The SKU of the container registry', choices=MANAGED_REGISTRY_SKU + CLASSIC_REGISTRY_SKU)
        c.argument('admin_enabled', help='Indicates whether the admin user is enabled', arg_type=get_three_state_flag())
        c.argument('password_name', help='The name of password to regenerate', choices=['password', 'password2'])
        c.argument('username', options_list=['--username', '-u'], help='The username used to log into a container registry')
        c.argument('password', options_list=['--password', '-p'], help='The password used to log into a container registry')
        c.argument('image_names', options_list=['--image', '-t'], help="The image repository and optionally a tag in the 'repository:tag' format.", action='append')
        c.argument('docker_file_path', options_list=['--file', '-f'], help="The relative path of the the docker file to the source code root folder.")
        c.argument('build_arg', help="Build argument in 'name[=value]' format.", action='append', validator=validate_build_arg)
        c.argument('secret_build_arg', help="Secret build argument in 'name[=value]' format.", action='append', validator=validate_secret_build_arg)
        c.argument('no_push', help="Indicates whether the image built should be pushed to the registry.", arg_type=get_three_state_flag())
        c.argument('no_logs', help="Do not show logs after successfully queuing the build.", action='store_true')

    with self.argument_context('acr repository delete') as c:
        c.argument('manifest', nargs='?', required=False, const='', default=None, help=argparse.SUPPRESS)
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation')
        c.argument('repository', help="The name of the repository to delete")
        c.argument('tag', help=argparse.SUPPRESS)
        c.argument('image', help="The name of the image to delete. May include a tag in the format 'name:tag' or digest in the format 'name@digest'.")

    with self.argument_context('acr repository untag') as c:
        c.argument('image', help="The name of the image to untag. May include a tag in the format 'name:tag'.")

    with self.argument_context('acr repository show-manifests') as c:
        c.argument('repository', help='The repository to obtain manifests from.')

    with self.argument_context('acr repository show-tags') as c:
        c.argument('repository', help='The repository to obtain tags from.')

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
        c.argument('actions', nargs='+', help='Space-separated list of actions that trigger the webhook to post notifications.', choices=['push', 'delete'])
        c.argument('status', help='Indicates whether the webhook is enabled.', choices=['enabled', 'disabled'])
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
        c.argument('timeout', help='The build timeout in seconds.')

    with self.argument_context('acr build-task') as c:
        c.argument('registry_name', options_list=['--registry', '-r'])
        # build task parameters
        c.argument('build_task_name', options_list=['--name', '-n'], help='The name of the build task.', completer=get_resource_name_completion_list(BUILD_TASK_RESOURCE_TYPE))
        c.argument('alias', help='The alternative name for build task. Default to the build task name.')
        c.argument('status', help='The current status of build task.', choices=[BuildTaskStatus.enabled.value, BuildTaskStatus.disabled.value])
        c.argument('os_type', options_list=['--os'], help='The operating system type required for the build.', choices=[OsType.linux.value, OsType.windows.value])
        c.argument('cpu', type=int, help='The CPU configuration in terms of number of cores required for the build.')
        c.argument('timeout', type=int, help='Build timeout in seconds.')
        c.argument('repository_url', options_list=['--context', '-c'], help="The full URL to the source code respository.")
        c.argument('commit_trigger_enabled', help="Indicates whether the source control commit trigger is enabled.", arg_type=get_three_state_flag())
        c.argument('git_access_token', help="The access token used to access the source control provider.")
        # build step parameters
        c.argument('step_name', help='The name of the build step.', completer=get_resource_name_completion_list(BUILD_STEP_RESOURCE_TYPE))
        c.argument('branch', help="The source control branch name.")
        c.argument('no_cache', help='Indicates whether the image cache is enabled.', arg_type=get_three_state_flag())
        c.argument('base_image_trigger', help="The type of the auto trigger for base image dependency updates.", choices=[BaseImageTriggerType.all.value,
                                                                                                                          BaseImageTriggerType.runtime.value,
                                                                                                                          BaseImageTriggerType.none.value])
        # build parameters
        c.argument('top', help='Limit the number of latest builds in the results.')
        c.argument('build_id', help='The unique build identifier.')
        c.argument('build_status', help='The current status of build.', choices=[BuildStatus.queued.value,
                                                                                 BuildStatus.started.value,
                                                                                 BuildStatus.running.value,
                                                                                 BuildStatus.succeeded.value,
                                                                                 BuildStatus.failed.value,
                                                                                 BuildStatus.canceled.value,
                                                                                 BuildStatus.error.value,
                                                                                 BuildStatus.timeout.value])

    with self.argument_context('acr build-task create') as c:
        c.argument('build_task_name', completer=None)
