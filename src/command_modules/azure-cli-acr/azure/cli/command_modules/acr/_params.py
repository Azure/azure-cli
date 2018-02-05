# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_location_type,
    tags_type,
    deployment_name_type,
    get_resource_name_completion_list,
    quotes
)
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from ._constants import (
    STORAGE_RESOURCE_TYPE,
    REGISTRY_RESOURCE_TYPE,
    WEBHOOK_RESOURCE_TYPE,
    REPLICATION_RESOURCE_TYPE,
    CLASSIC_REGISTRY_SKU,
    MANAGED_REGISTRY_SKU
)
from ._validators import validate_registry_name, validate_headers


def load_arguments(self, _):
    with self.argument_context('acr') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('registry_name', options_list=['--name', '-n'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('storage_account_name', help='Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account. Only applicable to Classic SKU.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
        c.argument('sku', help='The SKU of the container registry', choices=MANAGED_REGISTRY_SKU + CLASSIC_REGISTRY_SKU)
        c.argument('password_name', help='The name of password to regenerate', choices=['password', 'password2'])
        c.argument('username', options_list=['--username', '-u'], help='The username used to log into a container registry')
        c.argument('password', options_list=['--password', '-p'], help='The password used to log into a container registry')

    with self.argument_context('acr create') as c:
        c.argument('admin_enabled', nargs='?', required=False, const='true', default='false', help='Indicates whether the admin user is enabled', choices=['true', 'false'])

    with self.argument_context('acr update') as c:
        c.argument('admin_enabled', help='Indicates whether the admin user is enabled', choices=['true', 'false'])

    with self.argument_context('acr repository delete') as c:
        c.argument('manifest', nargs='?', required=False, const='', default=None, help='The sha256 based digest of manifest to delete')
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation')
        c.argument('repository', help='The name of the repository to delete.')
        c.argument('tag', help='The name of tag to delete')

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
        c.argument('registry_name', options_list=['--registry', '-r'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('webhook_name', options_list=['--name', '-n'], help='The name of the webhook', completer=get_resource_name_completion_list(WEBHOOK_RESOURCE_TYPE))
        c.argument('uri', help='The service URI for the webhook to post notifications.')
        c.argument('headers', nargs='+', help="Space separated custom headers in 'key[=value]' format that will be added to the webhook notifications. Use {} to clear existing headers.".format(quotes), validator=validate_headers)
        c.argument('actions', nargs='+', help='Space separated list of actions that trigger the webhook to post notifications.', choices=['push', 'delete'])
        c.argument('status', help='Indicates whether the webhook is enabled.', choices=['enabled', 'disabled'])
        c.argument('scope', help="The scope of repositories where the event can be triggered. For example, 'foo:*' means events for all tags under repository 'foo'. 'foo:bar' means events for 'foo:bar' only. 'foo' is equivalent to 'foo:latest'. Empty means events for all repositories.")

    with self.argument_context('acr webhook create') as c:
        c.argument('webhook_name', completer=None)

    with self.argument_context('acr replication') as c:
        c.argument('registry_name', options_list=['--registry', '-r'], help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
        c.argument('replication_name', options_list=['--name', '-n'], help='The name of the replication.', completer=get_resource_name_completion_list(REPLICATION_RESOURCE_TYPE))

    with self.argument_context('acr replication create') as c:
        c.argument('replication_name', help='The name of the replication. Default to the location name.', completer=None)
