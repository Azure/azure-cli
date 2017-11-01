# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import register_cli_argument
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

register_cli_argument('acr', 'registry_name', options_list=('--name', '-n'), help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
register_cli_argument('acr', 'storage_account_name', help='Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account. Only applicable to Classic SKU.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
register_cli_argument('acr', 'sku', help='The SKU of the container registry', choices=MANAGED_REGISTRY_SKU + CLASSIC_REGISTRY_SKU)
register_cli_argument('acr', 'password_name', help='The name of password to regenerate', choices=['password', 'password2'])

register_cli_argument('acr', 'resource_group_name', resource_group_name_type)
register_cli_argument('acr', 'location', get_location_type)
register_cli_argument('acr', 'tags', tags_type)
register_cli_argument('acr create', 'admin_enabled', nargs='?', required=False, const='true', default='false', help='Indicates whether the admin user is enabled', choices=['true', 'false'])
register_cli_argument('acr update', 'admin_enabled', help='Indicates whether the admin user is enabled', choices=['true', 'false'])

register_cli_argument('acr', 'username', options_list=('--username', '-u'), help='The username used to log into a container registry')
register_cli_argument('acr', 'password', options_list=('--password', '-p'), help='The password used to log into a container registry')

register_cli_argument('acr repository delete', 'manifest', nargs='?', required=False, const='', default=None, help='The sha256 based digest of manifest to delete')
register_cli_argument('acr repository delete', 'yes', options_list=('--yes', '-y'), action='store_true', help='Do not prompt for confirmation')

register_cli_argument('acr create', 'registry_name', completer=None, validator=validate_registry_name)
register_cli_argument('acr create', 'deployment_name', deployment_name_type, validator=None)
register_cli_argument('acr create', 'location', get_location_type, validator=get_default_location_from_resource_group)
register_cli_argument('acr check-name', 'registry_name', completer=None)

register_cli_argument('acr webhook', 'registry_name', options_list=('--registry', '-r'), help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
register_cli_argument('acr webhook', 'webhook_name', options_list=('--name', '-n'), help='The name of the webhook', completer=get_resource_name_completion_list(WEBHOOK_RESOURCE_TYPE))
register_cli_argument('acr webhook', 'uri', help='The service URI for the webhook to post notifications.')
register_cli_argument('acr webhook', 'headers', nargs='+', help="Space separated custom headers in 'key[=value]' format that will be added to the webhook notifications. Use {} to clear existing headers.".format(quotes), validator=validate_headers)
register_cli_argument('acr webhook', 'actions', nargs='+', help='Space separated list of actions that trigger the webhook to post notifications.', choices=['push', 'delete'])
register_cli_argument('acr webhook', 'status', help='Indicates whether the webhook is enabled.', choices=['enabled', 'disabled'])
register_cli_argument('acr webhook', 'scope', help="The scope of repositories where the event can be triggered. For example, 'foo:*' means events for all tags under repository 'foo'. 'foo:bar' means events for 'foo:bar' only. 'foo' is equivalent to 'foo:latest'. Empty means events for all repositories.")
register_cli_argument('acr webhook create', 'webhook_name', completer=None)

register_cli_argument('acr replication', 'registry_name', options_list=('--registry', '-r'), help='The name of the container registry. You can configure the default registry name using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
register_cli_argument('acr replication', 'replication_name', options_list=('--name', '-n'), help='The name of the replication.', completer=get_resource_name_completion_list(REPLICATION_RESOURCE_TYPE))
register_cli_argument('acr replication create', 'replication_name', help='The name of the replication. Default to the location name.', completer=None)
