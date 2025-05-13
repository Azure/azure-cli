# pylint: disable=line-too-long
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements


from knack.arguments import CLIArgumentType
from knack.log import get_logger
from azure.mgmt.signalr.models import SignalRRequestType
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_location_type,
    get_resource_name_completion_list,
    tags_type,
    get_enum_type,
    get_three_state_flag
)
from ._actions import (
    UpstreamTemplateAddAction,
    IPRuleTemplateUpdateAction
)
from ._constants import (
    SIGNALR_RESOURCE_TYPE,
    SIGNALR_KEY_TYPE,
    SIGNALR_SERVICE_MODE_TYPE
)
from ._validator import (
    validate_ip_rule
)

logger = get_logger(__name__)


def load_arguments(self, _):
    signalr_name_type = CLIArgumentType(options_list='--signalr-name', help='Name of the SignalR.', id_part='name')
    signalr_custom_domain_name_type = CLIArgumentType(help='Name of the custom domain.', id_part='child_name_1')
    signalr_custom_certificate_name_type = CLIArgumentType(
        help='Name of the custom certificate.', id_part='child_name_2')
    signalr_replica_name_type = CLIArgumentType(help='Name of the replica.', id_part='child_name_1')

    with self.argument_context('signalr') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location',
                   arg_type=get_location_type(self.cli_ctx),
                   validator=get_default_location_from_resource_group)
        c.argument('signalr_name', signalr_name_type, options_list=['--name', '-n'],
                   completer=get_resource_name_completion_list(SIGNALR_RESOURCE_TYPE),
                   help='Name of signalr service.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('signalr create') as c:
        c.argument('sku', help='The sku name of the signalr service. Allowed values: Premium_P1, Standard_S1, Free_F1')
        c.argument('unit_count', help='The number of signalr service unit count', type=int)
        c.argument('service_mode', help='The service mode which signalr service will be working on',
                   choices=SIGNALR_SERVICE_MODE_TYPE)
        c.argument('enable_message_logs', help='The switch for messaging logs which signalr service will generate or not',
                   arg_type=get_three_state_flag())
        c.argument('allowed_origins', options_list=['--allowed-origins', '-a'], nargs='*',
                   help='space separated origins that should be allowed to make cross-origin calls (for example: http://example.com:12345). To allow all, use "*"')

    with self.argument_context('signalr update') as c:
        c.argument('sku', help='The sku name of the signalr service. E.g. Standard_S1')
        c.argument('unit_count', help='The number of signalr service unit count', type=int)
        c.argument('service_mode', help='The service mode which signalr service will be working on',
                   choices=SIGNALR_SERVICE_MODE_TYPE)
        c.argument('enable_message_logs', help='The switch for messaging logs which signalr service will generate or not',
                   arg_type=get_three_state_flag())
        c.argument('allowed_origins', options_list=['--allowed-origins', '-a'], nargs='*',
                   help='space separated origins that should be allowed to make cross-origin calls (for example: http://example.com:12345). To allow all, use "*"')
        c.argument('client_cert_enabled',
                   help='Enable or disable client certificate authentication for a SignalR Service', arg_type=get_three_state_flag())
        c.argument('disable_local_auth',
                   help='Enable or disable local auth for a SignalR Service', arg_type=get_three_state_flag())
        c.argument('region_endpoint_enabled',
                   help='Enable or disable region endpoint for a SignalR Service', arg_type=get_three_state_flag())

    for scope in ['signalr create', 'signalr update']:
        with self.argument_context(scope, arg_group='Network Rule') as c:
            c.argument('default_action', arg_type=get_enum_type(
                ['Allow', 'Deny']), help='Default action to apply when no rule matches.', required=False)

    with self.argument_context('signalr key renew') as c:
        c.argument('key_type', help='The name of access key to regenerate', choices=SIGNALR_KEY_TYPE)

    with self.argument_context('signalr key list') as c:
        c.argument('signalr_name', id_part=None)

    with self.argument_context('signalr cors add') as c:
        c.argument('allowed_origins', options_list=['--allowed-origins', '-a'], nargs='*',
                   help='space separated origins that should be allowed to make cross-origin calls (for example: http://example.com:12345). To allow all, use "*"')

    with self.argument_context('signalr cors remove') as c:
        c.argument('allowed_origins', options_list=['--allowed-origins', '-a'], nargs='*',
                   help='space separated origins that should be allowed to make cross-origin calls (for example: http://example.com:12345). To allow all, use "*"')

    with self.argument_context('signalr cors update') as c:
        c.argument('allowed_origins', options_list=['--allowed-origins', '-a'], nargs='*',
                   help='space separated origins that should be allowed to make cross-origin calls (for example: http://example.com:12345). To allow all, use "*"')

    with self.argument_context('signalr cors list') as c:
        c.argument('signalr_name', id_part=None)

    # Network Rule
    with self.argument_context('signalr network-rule update') as c:
        c.argument('connection_name', nargs='*', help='Space-separeted list of private endpoint connection name.',
                   required=False, arg_group='Private Endpoint Connection')
        c.argument('public_network', arg_type=get_three_state_flag(),
                   help='Set rules for public network.', required=False, arg_group='Public Network')
        c.argument('allow', nargs='*', help='The allowed virtual network rule. Space-separeted list of scope to assign. Allowed values: ClientConnection, ServerConnection, RESTAPI',
                   type=SignalRRequestType, required=False)
        c.argument('deny', nargs='*', help='The denied virtual network rule. Space-separeted list of scope to assign. Allowed values: ClientConnection, ServerConnection, RESTAPI',
                   type=SignalRRequestType, required=False)

    for scope in ['signalr network-rule ip-rule add', 'signalr network-rule ip-rule remove']:
        with self.argument_context(scope, validator=validate_ip_rule) as c:
            c.argument('ip_rule', action=IPRuleTemplateUpdateAction, nargs='*',
                       help='The IP rule for the hub.', required=True)

    with self.argument_context('signalr network-rule list') as c:
        c.argument('signalr_name', id_part=None)

    # Upstream Settings
    with self.argument_context('signalr upstream update') as c:
        c.argument('template', action=UpstreamTemplateAddAction, nargs='+',
                   help='Template item for upstream settings. Use key=value pattern to set properties. Supported keys are "url-template", "hub-pattern", "event-pattern", "category-pattern".')

    with self.argument_context('signalr upstream list') as c:
        c.argument('signalr_name', id_part=None)

    # Managed Identity
    with self.argument_context('signalr identity assign') as c:
        c.argument(
            'identity', help="Assigns managed identities to the service. Use '[system]' to refer to the system-assigned identity or a resource ID to refer to a user-assigned identity. You can only assign either on of them.")

    # Custom Domain
    for scope in ['signalr custom-domain update',
                  'signalr custom-domain create',
                  'signalr custom-domain show',
                  'signalr custom-domain delete',
                  'signalr custom-domain list']:
        with self.argument_context(scope) as c:
            c.argument('signalr_name', signalr_name_type, id_part=None)
            c.argument('name', signalr_custom_domain_name_type)

    for scope in ['signalr custom-domain update',
                  'signalr custom-domain create']:
        with self.argument_context(scope) as c:
            c.argument('domain_name', help="Custom domain name. For example, `contoso.com`.")
            c.argument('certificate_resource_id', help="ResourceId of a previously created custom certificate.")

    # Custom Certificate
    for scope in ['signalr custom-certificate update',
                  'signalr custom-certificate create',
                  'signalr custom-certificate show',
                  'signalr custom-certificate delete',
                  'signalr custom-certificate list']:
        with self.argument_context(scope) as c:
            c.argument('signalr_name', signalr_name_type, id_part=None)
            c.argument('name', signalr_custom_certificate_name_type)

    for scope in ['signalr custom-certificate update',
                  'signalr custom-certificate create']:
        with self.argument_context(scope) as c:
            c.argument('keyvault_base_uri', help="Key vault base URI. For example, `https://contoso.vault.azure.net`.")
            c.argument('keyvault_secret_name', help="Key vault secret name where certificate is stored.")
            c.argument('keyvault_secret_version',
                       help="Key vault secret version where certificate is stored. If empty, will use latest version.")

    # Replica
    for scope in ['signalr replica create',
                  'signalr replica list',
                  'signalr replica delete',
                  'signalr replica show',
                  'signalr replica start',
                  'signalr replica stop',
                  'signalr replica restart']:
        with self.argument_context(scope) as c:
            c.argument('sku', help='The sku name of the replica. Currently allowed values: Premium_P1')
            c.argument('unit_count', help='The number of signalr service unit count', type=int)
            c.argument('replica_name', signalr_replica_name_type)

    for scope in ['signalr replica create',
                  'signalr replica list',
                  'signalr replica update']:
        with self.argument_context(scope) as c:
            c.argument('signalr_name', signalr_name_type, id_part=None)

    for scope in ['signalr replica show',
                  'signalr replica start',
                  'signalr replica stop',
                  'signalr replica restart',
                  'signalr replica delete']:
        with self.argument_context(scope) as c:
            c.argument('signalr_name', signalr_name_type)

    with self.argument_context('signalr replica update') as c:
        c.argument('replica_name', signalr_replica_name_type)
        c.argument('unit_count', help='The number of signalr service unit count', type=int)
        c.argument('region_endpoint_enabled',
                   help='Enable or disable region endpoint for a SignalR Service', arg_type=get_three_state_flag())
