# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals, too-many-statements too-many-boolean-expressions too-many-branches protected-access

from azure.mgmt.cdn.models import SkuName
from azure.cli.core.aaz._base import has_value
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.command_modules.cdn.aaz.latest.afd.custom_domain import Create as _AFDCustomDomainCreate, \
    Update as _AFDCustomDomainUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.origin import Create as _AFDOriginCreate, Update as _AFDOriginUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.route import Show as _AFDRouteShow, \
    Create as _AFDRouteCreate, Update as _AFDRouteUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.rule import Show as _RuleShow, \
    Create as _AFDRuleCreate, Update as _AFDRuleUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.secret import Show as _AFDSecretShow, \
    Create as _AFDSecretCreate, Update as _AFDSecretUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.security_policy import Show as _AFDSecurityPolicyShow, \
    Create as _AFDSecurityPolicyCreate, Update as _AFDSecurityPolicyUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.profile import Show as _AFDProfileShow, \
    Create as _AFDProfileCreate, Update as _AFDProfileUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.profile.log_scrubbing import Show as _AFDProfileLogScrubbingShow
from azure.cli.command_modules.cdn.aaz.latest.afd.endpoint import Show as _AFDEndpointShow, \
    Create as _AFDEndpointCreate, Update as _AFDEndpointUpdate
from azure.cli.command_modules.cdn.aaz.latest.afd.origin_group import Show as _AFDOriginGroupShow, \
    Create as _AFDOriginGroupCreate, Update as _AFDOriginGroupUpdate
from azure.cli.core.aaz import AAZStrArg, AAZBoolArg, AAZListArg, AAZTimeArg, AAZIntArg, AAZIntArgFormat
from knack.util import CLIError
from knack.log import get_logger
from .custom_rule_util import (create_condition, create_action,
                               create_conditions_from_existing, create_actions_from_existing)
logger = get_logger(__name__)


def default_content_types():
    return ['application/eot',
            'application/font',
            'application/font-sfnt',
            'application/javascript',
            'application/json',
            'application/opentype',
            'application/otf',
            'application/pkcs7-mime',
            'application/truetype',
            'application/ttf',
            'application/vnd.ms-fontobject',
            'application/xhtml+xml',
            'application/xml',
            'application/xml+rss',
            'application/x-font-opentype',
            'application/x-font-truetype',
            'application/x-font-ttf',
            'application/x-httpd-cgi',
            'application/x-javascript',
            'application/x-mpegurl',
            'application/x-opentype',
            'application/x-otf',
            'application/x-perl',
            'application/x-ttf',
            'font/eot',
            'font/ttf',
            'font/otf',
            'font/opentype',
            'image/svg+xml',
            'text/css',
            'text/csv',
            'text/html',
            'text/javascript',
            'text/js',
            'text/plain',
            'text/richtext',
            'text/tab-separated-values',
            'text/xml',
            'text/x-script',
            'text/x-component',
            'text/x-java-source']


class AFDCustomDomainCreate(_AFDCustomDomainCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.azure_dns_zone) and "/dnszones/" not in args.azure_dns_zone.to_serialized_data().lower():
            raise InvalidArgumentValueError('azure_dns_zone should be valid Azure dns zone ID.')
        if has_value(args.secret) and "/secrets/" not in args.secret.to_serialized_data().lower():
            args.secret = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                          f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/secrets/{args.secret}'


class AFDCustomDomainUpdate(_AFDCustomDomainUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.azure_dns_zone) and "/dnszones/" not in args.azure_dns_zone.to_serialized_data().lower():
            raise InvalidArgumentValueError('azure_dns_zone should be valid Azure dns zone ID.')
        if has_value(args.secret) and "/secrets/" not in args.secret.to_serialized_data().lower():
            args.secret = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                          f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/secrets/{args.secret}'


class AFDProfileShow(_AFDProfileShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        existing = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        if existing['sku']['name'] not in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
            logger.warning('Unexpected SKU type, only Standard_AzureFrontDoor and Premium_AzureFrontDoor are supported')
            raise ResourceNotFoundError("Operation returned an invalid status code 'Not Found'")
        return existing


class AFDProfileCreate(_AFDProfileCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.identity_type = AAZStrArg(
            options=['--identity-type'],
            help='Type of managed service identity (where both SystemAssigned and UserAssigned types are allowed).',
            enum=['SystemAssigned', 'None', 'UserAssigned', 'SystemAssigned, UserAssigned'],
        )
        args_schema.user_assigned_identities = AAZListArg(
            options=['--user-assigned-identities'],
            help='The set of user assigned identities associated with the resource. '
            'The userAssignedIdentities dictionary keys will be ARM resource ids in the form: '
            '\'/subscriptions/{{subscriptionId}}/resourceGroups/{{resourceGroupName}}'
            '/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{{identityName}}. '
            'The dictionary values can be empty objects ({{}}) in requests.',
        )
        args_schema.user_assigned_identities.Element = AAZStrArg()
        args_schema.location._registered = False
        args_schema.location._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = 'global'  # AFD profile location is always global
        user_assigned_identities = {}
        for identity in args.user_assigned_identities:
            user_assigned_identities[identity.to_serialized_data()] = {}
        if args.identity_type == 'UserAssigned' or args.identity_type == 'SystemAssigned, UserAssigned':
            args.identity = {
                'type': args.identity_type,
                'userAssignedIdentities': user_assigned_identities
            }
        elif args.identity_type == 'SystemAssigned':
            args.identity = {
                'type': args.identity_type
            }
        else:
            args.identity = None


class AFDProfileUpdate(_AFDProfileUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.identity_type = AAZStrArg(
            options=['--identity-type'],
            help='Type of managed service identity (where both SystemAssigned and UserAssigned types are allowed).',
            enum=['SystemAssigned', 'None', 'UserAssigned', 'SystemAssigned, UserAssigned'],
        )
        args_schema.user_assigned_identities = AAZListArg(
            options=['--user-assigned-identities'],
            help='The set of user assigned identities associated with the resource. '
            'The userAssignedIdentities dictionary keys will be ARM resource ids in the form: '
            '\'/subscriptions/{{subscriptionId}}/resourceGroups/{{resourceGroupName}}'
            '/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{{identityName}}. '
            'The dictionary values can be empty objects ({{}}) in requests.',
        )
        args_schema.user_assigned_identities.Element = AAZStrArg()
        args_schema.sku._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _AFDProfileShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name
        })
        if existing['sku']['name'] not in (SkuName.premium_azure_front_door, SkuName.standard_azure_front_door):
            logger.warning('Unexpected SKU type, only Standard_AzureFrontDoor and Premium_AzureFrontDoor are supported')
            raise ResourceNotFoundError("Operation returned an invalid status code 'Not Found'")

        if has_value(args.identity_type):
            user_assigned_identities = {}
            for identity in args.user_assigned_identities:
                user_assigned_identities[identity.to_serialized_data()] = {}
            if args.identity_type == 'UserAssigned' or args.identity_type == 'SystemAssigned, UserAssigned':
                args.identity = {
                    'type': args.identity_type,
                    'userAssignedIdentities': user_assigned_identities
                }
            elif args.identity_type == 'SystemAssigned':
                args.identity = {
                    'type': args.identity_type
                }
            else:
                args.identity = None


class AFDProfileLogScrubbingShow(_AFDProfileLogScrubbingShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        existing = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return existing['logScrubbing']


class AFDEndpointCreate(_AFDEndpointCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = 'global'


class AFDEndpointUpdate(_AFDEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name_reuse_scope._registered = False
        return args_schema


def get_health_probe_settings(enable_health_probe, probe_interval_in_seconds,
                              probe_path, probe_protocol, probe_request_type):
    params = [probe_interval_in_seconds, probe_path, probe_protocol, probe_request_type]
    if enable_health_probe is False:
        return None
    if enable_health_probe is True:
        if any(param is None for param in params):
            raise InvalidArgumentValueError(
                'When --enable-health-probe is set, all of --probe-interval-in-seconds, --probe-path, '
                '--probe-protocol and --probe-request-type must be specified.'
            )
    elif any(param is not None for param in params):
        enable_health_probe = True
        if any(param is None for param in params):
            raise InvalidArgumentValueError(
                'When --enable-health-probe is set, all of --probe-interval-in-seconds, --probe-path, '
                '--probe-protocol and --probe-request-type must be specified.'
            )
    else:
        enable_health_probe = False
        if any(param is not None for param in params):
            raise InvalidArgumentValueError(
                'When --enable-health-probe is not set, none of --probe-interval-in-seconds, --probe-path, '
                '--probe-protocol and --probe-request-type can be specified.'
            )
        return None

    return {
        'probeIntervalInSeconds': probe_interval_in_seconds,
        'probePath': probe_path,
        'probeProtocol': probe_protocol,
        'probeRequestType': probe_request_type
    }


class AFDOriginGroupCreate(_AFDOriginGroupCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enable_health_probe = AAZBoolArg(
            options=['--enable-health-probe'],
            help='Indicates whether to enable probe on the origin group.',
            blank=True,
        )
        args_schema.probe_interval_in_seconds = AAZIntArg(
            options=["--probe-interval-in-seconds"],
            arg_group="HealthProbeSettings",
            help="The number of seconds between health probes.Default is 240sec.",
            fmt=AAZIntArgFormat(
                maximum=255,
                minimum=1,
            ),
        )
        args_schema.probe_path = AAZStrArg(
            options=["--probe-path"],
            arg_group="HealthProbeSettings",
            help="The path relative to the origin that is used to determine the health of the origin.",
        )
        args_schema.probe_protocol = AAZStrArg(
            options=["--probe-protocol"],
            arg_group="HealthProbeSettings",
            help="Protocol to use for health probe.",
            enum={"Http": "Http", "Https": "Https", "NotSet": "NotSet"},
        )
        args_schema.probe_request_type = AAZStrArg(
            options=["--probe-request-type"],
            arg_group="HealthProbeSettings",
            help="The type of health probe request that is made.",
            enum={"GET": "GET", "HEAD": "HEAD", "NotSet": "NotSet"},
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        enable_health_probe = None
        probe_interval_in_seconds = None
        probe_path = None
        probe_protocol = None
        probe_request_type = None
        if has_value(args.enable_health_probe):
            enable_health_probe = args.enable_health_probe.to_serialized_data()
        if has_value(args.probe_interval_in_seconds):
            probe_interval_in_seconds = args.probe_interval_in_seconds.to_serialized_data()
        if has_value(args.probe_path):
            probe_path = args.probe_path.to_serialized_data()
        if has_value(args.probe_protocol):
            probe_protocol = args.probe_protocol.to_serialized_data()
        if has_value(args.probe_request_type):
            probe_request_type = args.probe_request_type.to_serialized_data()

        args.health_probe_settings = get_health_probe_settings(
            enable_health_probe,
            probe_interval_in_seconds,
            probe_path,
            probe_protocol,
            probe_request_type
        )


class AFDOriginGroupUpdate(_AFDOriginGroupUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enable_health_probe = AAZBoolArg(
            options=['--enable-health-probe'],
            help='Indicates whether to enable probe on the origin group.',
            blank=True,
        )
        args_schema.probe_interval_in_seconds = AAZIntArg(
            options=["--probe-interval-in-seconds"],
            arg_group="HealthProbeSettings",
            help="The number of seconds between health probes.Default is 240sec.",
            fmt=AAZIntArgFormat(
                maximum=255,
                minimum=1,
            ),
        )
        args_schema.probe_path = AAZStrArg(
            options=["--probe-path"],
            arg_group="HealthProbeSettings",
            help="The path relative to the origin that is used to determine the health of the origin.",
        )
        args_schema.probe_protocol = AAZStrArg(
            options=["--probe-protocol"],
            arg_group="HealthProbeSettings",
            help="Protocol to use for health probe.",
            enum={"Http": "Http", "Https": "Https", "NotSet": "NotSet"},
        )
        args_schema.probe_request_type = AAZStrArg(
            options=["--probe-request-type"],
            arg_group="HealthProbeSettings",
            help="The type of health probe request that is made.",
            enum={"GET": "GET", "HEAD": "HEAD", "NotSet": "NotSet"},
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _AFDOriginGroupShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'origin_group_name': args.origin_group_name
        })

        enable_health_probe = None
        probe_interval_in_seconds = None
        probe_path = None
        probe_protocol = None
        probe_request_type = None

        if not has_value(args.enable_health_probe):
            if 'healthProbeSettings' not in existing:
                enable_health_probe = False
            else:
                enable_health_probe = True
        else:
            enable_health_probe = args.enable_health_probe.to_serialized_data()

        if has_value(args.probe_path):
            enable_health_probe = True
            probe_path = args.probe_path.to_serialized_data()
        elif 'probePath' in existing['healthProbeSettings']:
            probe_path = existing['healthProbeSettings']['probePath']

        if has_value(args.probe_protocol):
            enable_health_probe = True
            probe_protocol = args.probe_protocol.to_serialized_data()
        elif 'probeProtocol' in existing['healthProbeSettings']:
            probe_protocol = existing['healthProbeSettings']['probeProtocol']

        if has_value(args.probe_interval_in_seconds):
            enable_health_probe = True
            probe_interval_in_seconds = args.probe_interval_in_seconds.to_serialized_data()
        elif 'probeIntervalInSeconds' in existing['healthProbeSettings']:
            probe_interval_in_seconds = existing['healthProbeSettings']['probeIntervalInSeconds']

        if has_value(args.probe_request_type):
            enable_health_probe = True
            probe_request_type = args.probe_request_type.to_serialized_data()
        elif 'probeRequestType' in existing['healthProbeSettings']:
            probe_request_type = existing['healthProbeSettings']['probeRequestType']

        args.health_probe_settings = get_health_probe_settings(
            enable_health_probe,
            probe_interval_in_seconds,
            probe_path,
            probe_protocol,
            probe_request_type
        )


class AFDOriginCreate(_AFDOriginCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enable_private_link = AAZBoolArg(
            options=['--enable-private-link'],
            help='Indicates whether private link is enabled on that origin.',
            blank=True,
            default=False
        )
        args_schema.private_link_location = AAZStrArg(
            options=['--private-link-location'],
            help='The location of origin that will be connected to using the private link.',
        )
        args_schema.private_link_resource = AAZStrArg(
            options=['--private-link-resource'],
            help='The resource ID of the origin that will be connected to using the private link.',
        )
        args_schema.private_link_request_message = AAZStrArg(
            options=['--private-link-request-message'],
            help='The message that is shown to the approver of the private link request.',
        )
        args_schema.private_link_sub_resource_type = AAZStrArg(
            options=['--private-link-sub-resource-type'],
            help='The sub-resource type of the origin that will be connected to using the private '
            'link.You can use "az network private-link-resource list" to obtain the supported sub-resource types.',
        )
        args_schema.shared_private_link_resource._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        shared_private_link_resource = None
        if has_value(args.enable_private_link) and args.enable_private_link.to_serialized_data() is True:
            shared_private_link_resource = {
                'private_link_location': args.private_link_location,
                'private_link': {'id': args.private_link_resource},
                'request_message': args.private_link_request_message,
                'group_id': args.private_link_sub_resource_type
            }
        args.shared_private_link_resource = shared_private_link_resource
        if not has_value(args.priority):
            args.priority = 1
        elif int(args.priority.to_serialized_data()) < 1 or int(args.priority.to_serialized_data()) > 1000:
            raise CLIError('Priority must be between 1 and 1000')


class AFDOriginUpdate(_AFDOriginUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enable_private_link = AAZBoolArg(
            options=['--enable-private-link'],
            help='Indicates whether private link is enabled on that origin.',
            blank=True
        )
        args_schema.private_link_location = AAZStrArg(
            options=['--private-link-location'],
            help='The location of origin that will be connected to using the private link.',
        )
        args_schema.private_link_resource = AAZStrArg(
            options=['--private-link-resource'],
            help='The resource ID of the origin that will be connected to using the private link.',
        )
        args_schema.private_link_request_message = AAZStrArg(
            options=['--private-link-request-message'],
            help='The message that is shown to the approver of the private link request.',
        )
        args_schema.private_link_sub_resource_type = AAZStrArg(
            options=['--private-link-sub-resource-type'],
            help='The sub-resource type of the origin that will be connected to using the private link.'
            'You can use "az network private-link-resource list" to obtain the supported sub-resource types.',
        )
        args_schema.shared_private_link_resource._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        from azure.cli.command_modules.cdn.aaz.latest.afd.origin import Show
        existing = Show(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'origin_group_name': args.origin_group_name,
            'origin_name': args.origin_name
        })

        shared_private_link_resource = None
        # if no enable_private_link is specified and origin doesn't have private link resource, then no change
        if (not has_value(args.enable_private_link) and 'sharedPrivateLinkResource' not in existing) or \
                (has_value(args.enable_private_link) and args.enable_private_link.to_serialized_data() is False):
            shared_private_link_resource = None
        # if any private link related parameter is specified, then update the private link resource
        elif ((has_value(args.private_link_location) or
              has_value(args.private_link_resource) or
              has_value(args.private_link_request_message) or
              has_value(args.private_link_sub_resource_type)) or
              args.enable_private_link.to_serialized_data() is True or
              'sharedPrivateLinkResource' in existing):
            # no specified private link related parameter, then use existing private link resource
            existing_private_link_location = None if 'sharedPrivateLinkResource' not in existing or \
                'privateLinkLocation' not in existing['sharedPrivateLinkResource'] \
                else existing['sharedPrivateLinkResource']['privateLinkLocation']
            existing_private_link_resource = None if 'sharedPrivateLinkResource' not in existing or \
                'privateLink' not in existing['sharedPrivateLinkResource'] \
                else existing['sharedPrivateLinkResource']['privateLink']['id']
            existing_private_link_request_message = None if 'sharedPrivateLinkResource' not in existing \
                or 'requestMessage' not in existing['sharedPrivateLinkResource'] else \
                existing['sharedPrivateLinkResource']['requestMessage']
            existing_private_link_sub_resource_type = None if 'sharedPrivateLinkResource' not in existing \
                or 'groupId' not in existing['sharedPrivateLinkResource'] else \
                existing['sharedPrivateLinkResource']['groupId']
            shared_private_link_resource = {
                'private_link_location': args.private_link_location if has_value(args.private_link_location)
                else existing_private_link_location,
                'private_link': {
                    'id': args.private_link_resource if has_value(args.private_link_resource)
                    else existing_private_link_resource
                },
                'request_message': args.private_link_request_message if has_value(args.private_link_request_message)
                else existing_private_link_request_message,
                'group_id': args.private_link_sub_resource_type if has_value(args.private_link_sub_resource_type)
                else existing_private_link_sub_resource_type
            }

        args.shared_private_link_resource = shared_private_link_resource
        args.host_name = args.host_name if args.host_name is not None else existing['hostName']
        args.http_port = args.http_port if args.http_port is not None else existing['httpPort']
        args.https_port = args.https_port if args.https_port is not None else existing['httpsPort']
        args.origin_host_header = args.origin_host_header if args.origin_host_header is not None \
            else existing['originHostHeader']
        if has_value(args.priority) \
                and (int(args.priority.to_serialized_data()) < 1 or int(args.priority.to_serialized_data()) > 1000):
            raise CLIError('Priority must be between 1 and 1000')
        args.priority = args.priority if has_value(args.priority) else existing['priority']
        args.weight = args.weight if args.weight is not None else existing['weight']
        args.enabled_state = args.enabled_state if args.enabled_state is not None else existing['enabledState']
        args.enforce_certificate_name_check = \
            args.enforce_certificate_name_check if args.enforce_certificate_name_check is not None \
            else existing['enforceCertificateNameCheck']


class AFDRouteCreate(_AFDRouteCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enable_caching = AAZBoolArg(
            options=['--enable-caching'],
            help='Indicates whether caching is enabled on that route.',
        )
        args_schema.custom_domains = AAZListArg(
            options=['--custom-domains'],
            help='Custom domains referenced by this endpoint.',
            nullable=True,
        )
        args_schema.custom_domains.Element = AAZStrArg()
        args_schema.rule_sets = AAZListArg(
            options=['--rule-sets'],
            help='Collection of ID or name of rule set referenced by the route.',
            nullable=True,
        )
        args_schema.rule_sets.Element = AAZStrArg()
        args_schema.query_string_caching_behavior = AAZStrArg(
            options=['--query-string-caching-behavior'],
            help='Defines how Frontdoor caches requests that include query strings.'
            'You can ignore any query strings when caching, ignore specific query strings,'
            'cache every request with a unique URL, or cache specific query strings',
        )
        args_schema.query_parameters = AAZListArg(
            options=['--query-parameters'],
            help='Query parameters to include or exclude.',
        )
        args_schema.query_parameters.Element = AAZStrArg()
        args_schema.content_types_to_compress = AAZListArg(
            options=['--content-types-to-compress'],
            help='List of content types on which compression applies.',
        )
        args_schema.content_types_to_compress.Element = AAZStrArg()
        args_schema.enable_compression = AAZBoolArg(
            options=['--enable-compression'],
            help='Indicates whether content compression is enabled on AzureFrontDoor. '
            'Default value is false. If compression is enabled,'
            'content will be served as compressed if user requests for a compressed version.'
            'Content won\'t be compressed on AzureFrontDoor'
            'when requested content is smaller than 8 MB or larger than 1 KB.',
        )
        args_schema.cache_configuration._registered = False
        args_schema.formatted_custom_domains._registered = False
        args_schema.formatted_rule_sets._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        custom_domains = []
        if has_value(args.custom_domains):
            for custom_domain in args.custom_domains:
                if '/customdomains/' not in custom_domain.to_serialized_data().lower():
                    custom_domain = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                        f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/customDomains/{custom_domain}'
                    item = {
                        'id': custom_domain,
                    }
                    custom_domains.append(item)
            args.formatted_custom_domains = custom_domains

        if has_value(args.origin_group) and '/origingroups/' not in args.origin_group.to_serialized_data().lower():
            args.origin_group = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/originGroups/{args.origin_group}'

        cache_configuration = {
            'query_string_caching_behavior': args.query_string_caching_behavior,
            'query_parameters': None if (not has_value(args.query_parameters) or
                                         args.query_parameters is None)
            else ",".join(args.query_parameters.to_serialized_data()),
            'compression_settings': {
                'is_compression_enabled': args.enable_compression,
                'content_types_to_compress': args.content_types_to_compress
            }
        }
        if not has_value(args.enable_caching) or args.enable_caching.to_serialized_data() is False:
            cache_configuration = None
        else:
            if not has_value(args.enable_compression) or args.enable_compression.to_serialized_data() is False:
                cache_configuration['compression_settings']['content_types_to_compress'] = []
            else:
                if not has_value(args.content_types_to_compress):
                    cache_configuration['compression_settings']['content_types_to_compress'] = default_content_types()

        args.cache_configuration = cache_configuration

        rule_sets = []
        if has_value(args.rule_sets):
            for rule_set in args.rule_sets:
                if '/rulesets/' not in rule_set.to_serialized_data().lower():
                    rule_set = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                        f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/ruleSets/{rule_set}'
                    item = {
                        'id': rule_set,
                    }
                    rule_sets.append(item)
            args.formatted_rule_sets = rule_sets


class AFDRouteUpdate(_AFDRouteUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enable_caching = AAZBoolArg(
            options=['--enable-caching'],
            help='Indicates whether caching is enabled on that route.',
        )
        args_schema.custom_domains = AAZListArg(
            options=['--custom-domains'],
            help='Custom domains referenced by this endpoint.',
            nullable=True,
        )
        args_schema.custom_domains.Element = AAZStrArg()
        args_schema.rule_sets = AAZListArg(
            options=['--rule-sets'],
            help='Collection of ID or name of rule set referenced by the route.',
            nullable=True,
        )
        args_schema.rule_sets.Element = AAZStrArg()
        args_schema.query_string_caching_behavior = AAZStrArg(
            options=['--query-string-caching-behavior'],
            help='Defines how Frontdoor caches requests that include query strings.'
            'You can ignore any query strings when caching, ignore specific query strings,'
            'cache every request with a unique URL, or cache specific query strings',
        )
        args_schema.query_parameters = AAZListArg(
            options=['--query-parameters'],
            help='Query parameters to include or exclude.',
        )
        args_schema.query_parameters.Element = AAZStrArg()
        args_schema.content_types_to_compress = AAZListArg(
            options=['--content-types-to-compress'],
            help='List of content types on which compression applies.',
        )
        args_schema.content_types_to_compress.Element = AAZStrArg()
        args_schema.enable_compression = AAZBoolArg(
            options=['--enable-compression'],
            help='Indicates whether content compression is enabled on AzureFrontDoor. Default value is false.'
            'If compression is enabled, content will be served as compressed if user requests for a compressed version.'
            'Content won\'t be compressed on AzureFrontDoor'
            'when requested content is smaller than 8 MB or larger than 1 KB.',
        )
        args_schema.cache_configuration._registered = False
        args_schema.formatted_custom_domains._registered = False
        args_schema.formatted_rule_sets._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        custom_domains = []
        if has_value(args.custom_domains):
            for custom_domain in args.custom_domains:
                if '/customdomains/' not in custom_domain.to_serialized_data().lower():
                    custom_domain = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                        f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/customDomains/{custom_domain}'
                    item = {
                        'id': custom_domain,
                    }
                    custom_domains.append(item)
            args.formatted_custom_domains = custom_domains

        if has_value(args.origin_group) and '/origingroups/' not in args.origin_group.to_serialized_data().lower():
            args.origin_group = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/originGroups/{args.origin_group}'

        existing = _AFDRouteShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name,
            'route_name': args.route_name
        })

        cache_configuration = {
            'query_string_caching_behavior': args.query_string_caching_behavior,
            'query_parameters': None if (not has_value(args.query_parameters) or
                                         args.query_parameters is None)
            else ",".join(args.query_parameters.to_serialized_data()),
            'compression_settings': {
                'is_compression_enabled': args.enable_compression,
                'content_types_to_compress': args.content_types_to_compress,
            }
        }

        # if not specified, then use existing cache configuration
        if not has_value(args.enable_caching):
            if 'cacheConfiguration' not in existing or existing['cacheConfiguration'] is None:
                cache_configuration = None
            else:
                # if already has cache configuration, then use existing cache configuration
                if not has_value(args.query_string_caching_behavior):
                    if ('cacheConfiguration' in existing and
                            'queryStringCachingBehavior' in existing['cacheConfiguration']):
                        cache_configuration['query_string_caching_behavior'] = \
                            existing['cacheConfiguration']['queryStringCachingBehavior']
                if not has_value(args.query_parameters):
                    if 'cacheConfiguration' in existing and 'queryParameters' in existing['cacheConfiguration']:
                        cache_configuration['query_parameters'] = existing['cacheConfiguration']['queryParameters']
                if not has_value(args.content_types_to_compress):
                    if ('cacheConfiguration' in existing and
                            'compressionSettings' in existing['cacheConfiguration'] and
                            'contentTypesToCompress' in existing['cacheConfiguration']['compressionSettings']):
                        cache_configuration['compression_settings']['content_types_to_compress'] = \
                            existing['cacheConfiguration']['compressionSettings']['contentTypesToCompress']
                if not has_value(args.enable_compression):
                    if ('cacheConfiguration' in existing and
                            'compressionSettings' in existing['cacheConfiguration'] and
                            'isCompressionEnabled' in existing['cacheConfiguration']['compressionSettings']):
                        cache_configuration['compression_settings']['is_compression_enabled'] = \
                            existing['cacheConfiguration']['compressionSettings']['isCompressionEnabled']
        elif args.enable_caching.to_serialized_data() is False:
            cache_configuration = None
        # if caching setting specified and set to true, check compression setting
        else:
            # if not specified, then use existing compression settings
            if (not has_value(args.enable_compression) and 'cacheConfiguration' in existing and
                    'compressionSettings' in existing['cacheConfiguration'] and
                    'contentTypesToCompress' in existing['cacheConfiguration']['compressionSettings']):
                cache_configuration['compression_settings']['content_types_to_compress'] = \
                    existing['cacheConfiguration']['compressionSettings']['contentTypesToCompress']
            elif args.enable_compression.to_serialized_data() is False:
                cache_configuration['compression_settings']['content_types_to_compress'] = []
            else:
                # if compression setting specified and set to true, check content types to compress
                if (not has_value(args.content_types_to_compress) or
                        args.content_types_to_compress.to_serialized_data() is None):
                    cache_configuration['compression_settings']['content_types_to_compress'] = default_content_types()
        args.cache_configuration = cache_configuration

        rule_sets = []
        if has_value(args.rule_sets):
            for rule_set in args.rule_sets:
                if '/rulesets/' not in rule_set.to_serialized_data().lower():
                    rule_set = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                        f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/ruleSets/{rule_set}'
                    item = {
                        'id': rule_set,
                    }
                    rule_sets.append(item)
            args.formatted_rule_sets = rule_sets


class AFDRuleCreate(_AFDRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_name = AAZStrArg(
            options=['--action-name'],
            help='The name of the action for the delivery rule: '
            'https://learn.microsoft.com/en-us/azure/frontdoor/front-door-rules-engine-actions.',
        )
        args_schema.cache_behavior = AAZStrArg(
            options=['--cache-behavior'],
            help='Caching behavior for the requests.',
        )
        args_schema.cache_duration = AAZTimeArg(
            options=['--cache-duration'],
            help='The duration for which the content needs to be cached. Allowed format is hh:mm:ss.xxxxxx',
        )
        args_schema.custom_fragment = AAZStrArg(
            options=['--custom-fragment'],
            help='Fragment to add to the redirect URL.',
        )
        args_schema.custom_hostname = AAZStrArg(
            options=['--custom-hostname'],
            help='Host to redirect. Leave empty to use the incoming host as the destination host.',
        )
        args_schema.custom_path = AAZStrArg(
            options=['--custom-path'],
            help='The full path to redirect. Path cannot be empty and must start with /.'
            'Leave empty to use the incoming path as destination pat',
        )
        args_schema.custom_querystring = AAZStrArg(
            options=['--custom-querystring'],
            help='The set of query strings to be placed in the redirect URL.'
            'leave empty to preserve the incoming query string.',
        )
        args_schema.destination = AAZStrArg(
            options=['--destination'],
            help='The destination path to be used in the rewrite.',
        )
        args_schema.enable_caching = AAZBoolArg(
            options=['--enable-caching'],
            help='Indicates whether to enable caching on the route.',
        )
        args_schema.enable_compression = AAZBoolArg(
            options=['--enable-compression'],
            help='Indicates whether content compression is enabled on AzureFrontDoor. Default value is false.'
            'If compression is enabled, content will be served as compressed if user requests for a compressed version.'
            'Content won\'t be compressed on AzureFrontDoor'
            'when requested content is smaller than 8 MB or larger than 1 KB.',
        )
        args_schema.forwarding_protocol = AAZStrArg(
            options=['--forwarding-protocol'],
            help='Protocol this rule will use when forwarding traffic to backends.',
        )
        args_schema.header_action = AAZStrArg(
            options=['--header-action'],
            help='Header action for the requests.'
        )
        args_schema.header_name = AAZStrArg(
            options=['--header-name'],
            help='Name of the header to modify.'
        )
        args_schema.header_value = AAZStrArg(
            options=['--header-value'],
            help='Value of the header.',
        )
        args_schema.match_values = AAZListArg(
            options=['--match-values'],
            help='Match values of the match condition. e.g, space separated values \'GET\' \'HTTP\'.',
        )
        args_schema.match_values.Element = AAZStrArg()
        args_schema.match_variable = AAZStrArg(
            options=['--match-variable'],
            help='Name of the match condition: '
            'https://learn.microsoft.com/en-us/azure/frontdoor/rules-match-conditions.',
        )
        args_schema.negate_condition = AAZBoolArg(
            options=['--negate-condition'],
            help='If true, negates the condition.',
        )
        args_schema.operator = AAZStrArg(
            options=['--operator'],
            help='Operator of the match condition.',
        )
        args_schema.origin_group = AAZStrArg(
            options=['--origin-group'],
            help='Name or ID of the OriginGroup that would override the default OriginGroup.',
        )
        args_schema.preserve_unmatched_path = AAZBoolArg(
            options=['--preserve-unmatched-path'],
            help='If True, the remaining path after the source pattern will be appended to the new destination path.',
        )
        args_schema.query_parameters = AAZListArg(
            options=['--query-parameters'],
            help='Query parameters to include or exclude.',
        )
        args_schema.query_parameters.Element = AAZStrArg()
        args_schema.query_string_caching_behavior = AAZStrArg(
            options=['--query-string-caching-behavior'],
            help='Defines how CDN caches requests that include query strings.'
            'You can ignore any query strings when caching,'
            'bypass caching to prevent requests that contain query strings from being cached,'
            'or cache every request with a unique URL.',
        )
        args_schema.redirect_protocol = AAZStrArg(
            options=['--redirect-protocol'],
            help='Protocol to use for the redirect.',
        )
        args_schema.redirect_type = AAZStrArg(
            options=['--redirect-type'],
            help='The redirect type the rule will use when redirecting traffic.',
        )
        args_schema.selector = AAZStrArg(
            options=['--selector'],
            help='Selector of the match condition.',
        )
        args_schema.source_pattern = AAZStrArg(
            options=['--source-pattern'],
            help='A request URI pattern that identifies the type of requests that may be rewritten.',
        )
        args_schema.transforms = AAZListArg(
            options=['--transforms'],
            help='Transform to apply before matching.',
        )
        args_schema.transforms.Element = AAZStrArg()
        args_schema.actions._registered = False
        args_schema.conditions._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # conditions
        conditions = []
        condition = create_condition(args.match_variable, args.operator,
                                     args.match_values, args.selector, args.negate_condition, args.transforms)
        if condition is not None:
            conditions.append(condition)
        args.conditions = conditions

        # actions
        actions = []
        action = create_action(
            args.action_name, args.cache_behavior, args.cache_duration, args.header_action,
            args.header_name, args.header_value, None,
            None if not has_value(args.query_parameters) else ','.join(args.query_parameters.to_serialized_data()),
            args.redirect_type, args.redirect_protocol, args.custom_hostname,
            args.custom_path, args.custom_querystring, args.custom_fragment, args.source_pattern,
            args.destination, args.preserve_unmatched_path,
            origin_group=args.origin_group,
            sub_id=self.ctx.subscription_id,
            enable_caching=args.enable_caching,
            resource_group=args.resource_group,
            profile_name=args.profile_name,
            enable_compression=args.enable_compression,
            query_string_caching_behavior=args.query_string_caching_behavior,
            forwarding_protocol=args.forwarding_protocol,
        )
        if action is not None:
            actions.append(action)
        args.actions = actions


# pylint: disable=line-too-long
class AFDRuleconditionAdd(_AFDRuleUpdate):
    """Add a match condition to the specified delivery rule.

    :example: Add a match condition to a delivery rule.
        az afd rule condition add --resource-group MyResourceGroup --profile-name MyFrontDoorProfile --rule-set-name MyRuleSet --rule-name MyRule --match-variable RequestMethod --operator Any --match-values GET HTTP --negate-condition false --transforms Lowercase
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.match_values = AAZListArg(
            options=['--match-values'],
            help='Match values of the match condition. e.g, space separated values \'GET\' \'HTTP\'.',
        )
        args_schema.match_values.Element = AAZStrArg()
        args_schema.match_variable = AAZStrArg(
            options=['--match-variable'],
            help='Name of the match condition: '
            'https://learn.microsoft.com/en-us/azure/frontdoor/rules-match-conditions.',
            required=True,
        )
        args_schema.negate_condition = AAZBoolArg(
            options=['--negate-condition'],
            help='If true, negates the condition.',
        )
        args_schema.operator = AAZStrArg(
            options=['--operator'],
            help='Operator of the match condition.',
            required=True,
        )
        args_schema.selector = AAZStrArg(
            options=['--selector'],
            help='Selector of the match condition.',
        )
        args_schema.transforms = AAZListArg(
            options=['--transforms'],
            help='Transform to apply before matching.',
        )
        args_schema.transforms.Element = AAZStrArg()
        args_schema.actions._registered = False
        args_schema.conditions._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        existing = _RuleShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'rule_set_name': args.rule_set_name,
            'rule_name': args.rule_name
        })
        conditions = create_conditions_from_existing(existing['conditions'])
        condition = create_condition(args.match_variable, args.operator,
                                     args.match_values, args.selector, args.negate_condition, args.transforms)
        if condition is not None:
            conditions.append(condition)
        args.conditions = conditions


# pylint: disable=line-too-long
class AFDRuleconditionRemove(_AFDRuleUpdate):
    """Remove a condition from the specified delivery rule.

    :example: Remove a condition from a delivery rule.
        az afd rule condition remove --resource-group MyResourceGroup --profile-name MyFrontDoorProfile --rule-set-name MyRuleSet --rule-name MyRule --index 0
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.index = AAZIntArg(
            options=['--index'],
            help='The index of the condition/action.',
            required=True
        )
        args_schema.actions._registered = False
        args_schema.conditions._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        existing = _RuleShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'rule_set_name': args.rule_set_name,
            'rule_name': args.rule_name
        })
        conditions = create_conditions_from_existing(existing['conditions'])

        if len(conditions) > 1 and args.index < len(conditions):
            conditions.pop(args.index.to_serialized_data())
        else:
            logger.warning('Invalid condition index found. This command will be skipped. Please check the rule.')
        args.conditions = conditions


# pylint: disable=line-too-long
class AFDRuleActionCreate(_AFDRuleUpdate):
    """Update a new delivery rule within the specified rule set.

    :example: Create a new delivery rule with a modify response header action.
        az afd rule action create --resource-group MyResourceGroup --profile-name MyFrontDoorProfile --rule-set-name MyRuleSet --rule-name MyRule --action-name Redirect --redirect-type "Found" --redirect-protocol "Https" --destination "www.example.com
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_name = AAZStrArg(
            options=['--action-name'],
            help='The name of the action for the delivery rule: '
            'https://learn.microsoft.com/en-us/azure/frontdoor/front-door-rules-engine-actions.',
            required=True,
        )
        args_schema.cache_behavior = AAZStrArg(
            options=['--cache-behavior'],
            help='Caching behavior for the requests.',
        )
        args_schema.cache_duration = AAZTimeArg(
            options=['--cache-duration'],
            help='The duration for which the content needs to be cached. Allowed format is hh:mm:ss.xxxxxx',
        )
        args_schema.custom_fragment = AAZStrArg(
            options=['--custom-fragment'],
            help='Fragment to add to the redirect URL.',
        )
        args_schema.custom_hostname = AAZStrArg(
            options=['--custom-hostname'],
            help='Host to redirect. Leave empty to use the incoming host as the destination host.',
        )
        args_schema.custom_path = AAZStrArg(
            options=['--custom-path'],
            help='The full path to redirect. Path cannot be empty and must start with /.'
            'Leave empty to use the incoming path as destination pat',
        )
        args_schema.custom_querystring = AAZStrArg(
            options=['--custom-querystring'],
            help='The set of query strings to be placed in the redirect URL.'
            'leave empty to preserve the incoming query string.',
        )
        args_schema.destination = AAZStrArg(
            options=['--destination'],
            help='The destination path to be used in the rewrite.',
        )
        args_schema.enable_caching = AAZBoolArg(
            options=['--enable-caching'],
            help='Indicates whether to enable caching on the route.',
        )
        args_schema.enable_compression = AAZBoolArg(
            options=['--enable-compression'],
            help='Indicates whether content compression is enabled on AzureFrontDoor. Default value is false.'
            'If compression is enabled, content will be served as compressed if user requests for a compressed version.'
            'Content won\'t be compressed on AzureFrontDoor'
            'when requested content is smaller than 8 MB or larger than 1 KB.',
        )
        args_schema.forwarding_protocol = AAZStrArg(
            options=['--forwarding-protocol'],
            help='Protocol this rule will use when forwarding traffic to backends.',
        )
        args_schema.header_action = AAZStrArg(
            options=['--header-action'],
            help='Header action for the requests.'
        )
        args_schema.header_name = AAZStrArg(
            options=['--header-name'],
            help='Name of the header to modify.'
        )
        args_schema.header_value = AAZStrArg(
            options=['--header-value'],
            help='Value of the header.',
        )
        args_schema.origin_group = AAZStrArg(
            options=['--origin-group'],
            help='Name or ID of the OriginGroup that would override the default OriginGroup.',
        )
        args_schema.preserve_unmatched_path = AAZBoolArg(
            options=['--preserve-unmatched-path'],
            help='If True, the remaining path after the source pattern will be appended to the new destination path.',
        )
        args_schema.query_parameters = AAZListArg(
            options=['--query-parameters'],
            help='Query parameters to include or exclude.',
        )
        args_schema.query_parameters.Element = AAZStrArg()
        args_schema.query_string_caching_behavior = AAZStrArg(
            options=['--query-string-caching-behavior'],
            help='Defines how CDN caches requests that include query strings.'
            'You can ignore any query strings when caching,'
            'bypass caching to prevent requests that contain query strings from being cached,'
            'or cache every request with a unique URL.',
        )
        args_schema.redirect_protocol = AAZStrArg(
            options=['--redirect-protocol'],
            help='Protocol to use for the redirect.',
        )
        args_schema.redirect_type = AAZStrArg(
            options=['--redirect-type'],
            help='The redirect type the rule will use when redirecting traffic.',
        )
        args_schema.source_pattern = AAZStrArg(
            options=['--source-pattern'],
            help='A request URI pattern that identifies the type of requests that may be rewritten.',
        )
        args_schema.actions._registered = False
        args_schema.conditions._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _RuleShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'rule_set_name': args.rule_set_name,
            'rule_name': args.rule_name
        })
        actions = create_actions_from_existing(existing['actions'])
        action = create_action(
            args.action_name, args.cache_behavior, args.cache_duration, args.header_action,
            args.header_name, args.header_value, None,
            None if not has_value(args.query_parameters) else ','.join(args.query_parameters.to_serialized_data()),
            args.redirect_type, args.redirect_protocol, args.custom_hostname,
            args.custom_path, args.custom_querystring, args.custom_fragment, args.source_pattern,
            args.destination, args.preserve_unmatched_path,
            origin_group=args.origin_group,
            sub_id=self.ctx.subscription_id,
            enable_caching=args.enable_caching,
            resource_group=args.resource_group,
            profile_name=args.profile_name,
            enable_compression=args.enable_compression,
            query_string_caching_behavior=args.query_string_caching_behavior,
            forwarding_protocol=args.forwarding_protocol,
        )
        if action is not None:
            actions.append(action)
        args.actions = actions


# pylint: disable=line-too-long
class AFDRuleActionRemove(_AFDRuleUpdate):
    """Remove an action from the specified delivery rule.

    :example: Remove an action from a delivery rule.
        az afd rule action remove --resource-group MyResourceGroup --profile-name MyFrontDoorProfile --rule-set-name MyRuleSet --rule-name MyRule --index 0
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.index = AAZIntArg(
            options=['--index'],
            help='The index of the condition/action.',
            required=True
        )
        args_schema.actions._registered = False
        args_schema.conditions._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _RuleShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'rule_set_name': args.rule_set_name,
            'rule_name': args.rule_name
        })
        actions = create_actions_from_existing(existing['actions'])
        if len(actions) > 1 and args.index < len(actions):
            actions.pop(args.index.to_serialized_data())
        else:
            logger.warning('Invalid condition index found. This command will be skipped. Please check the rule.')
        args.actions = actions


# pylint: disable=line-too-long
class AFDRuleActionShow(_RuleShow):
    """Show the actions of a delivery rule.

    :example: Show the actions of a delivery rule.
        az afd rule action show --resource-group MyResourceGroup --profile-name MyFrontDoorProfile --rule-set-name MyRuleSet --rule-name MyRule
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        existing = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return existing['actions']


# pylint: disable=line-too-long
class AFDRuleConditionShow(_RuleShow):
    """Show the conditions of a delivery rule.

    :example: Show the conditions of a delivery rule.
        az afd rule condition show --resource-group MyResourceGroup --profile-name MyFrontDoorProfile --rule-set-name MyRuleSet --rule-name MyRule
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        existing = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return existing['conditions']


class AFDSecretCreate(_AFDSecretCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.secret_source = AAZStrArg(
            options=['--secret-source'],
            help='Resource ID of the Azure Key Vault certificate, expected format is like'
            '/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.KeyVault/vaults/vault1/secrets/cert1.',
            required=True,
        )
        args_schema.secret_version = AAZStrArg(
            options=['--secret-version'],
            help='Version of the certificate to be used.',
        )
        args_schema.use_latest_version = AAZBoolArg(
            options=['--use-latest-version'],
            help='Whether to use the latest version for the certificate.',
        )
        args_schema.parameters._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if "/secrets/" not in args.secret_source.to_serialized_data().lower():
            raise InvalidArgumentValueError('secret_source should be valid Azure key vault certificate ID.')

        if not has_value(args.secret_version) and not args.use_latest_version.to_serialized_data():
            raise InvalidArgumentValueError('Either specify secret_version or enable use_latest_version.')
        parameters = None
        if has_value(args.use_latest_version) and args.use_latest_version.to_serialized_data() is True:
            parameters = {
                'customer-certificate': {
                    'secret-source': {'id': args.secret_source},
                    'secret-version': None,
                    'use-latest-version': True
                }
            }
        else:
            parameters = {
                'customer-certificate': {
                    'secret-source': {'id': args.secret_source},
                    'secret-version': args.secret_version,
                    'use-latest-version': False
                }
            }
        args.parameters = parameters


class AFDSecretUpdate(_AFDSecretUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.secret_source = AAZStrArg(
            options=['--secret-source'],
            help='Resource ID of the Azure Key Vault certificate, expected format is like'
            '/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.KeyVault/vaults/vault1/secrets/cert1.',
        )
        args_schema.secret_version = AAZStrArg(
            options=['--secret-version'],
            help='Version of the certificate to be used.',
        )
        args_schema.use_latest_version = AAZBoolArg(
            options=['--use-latest-version'],
            help='Whether to use the latest version for the certificate.',
        )
        args_schema.parameters._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _AFDSecretShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'secret_name': args.secret_name
        })

        para = existing['parameters']
        secret_source = args.secret_source.to_serialized_data() if has_value(args.secret_source) \
            else para['secretSource']['id']
        if 'secretVersion' in para and para['secretVersion'] in secret_source:
            existing_secret_version = para['secretVersion']
            version_start = secret_source.lower().rindex(f'/{existing_secret_version}')
            secret_source = secret_source[0:version_start]

        secret_version = args.secret_version \
            if has_value(args.secret_version) and args.secret_version is not None \
            else para['secretVersion']
        use_latest_version = args.use_latest_version \
            if has_value(args.use_latest_version) and args.use_latest_version is not None \
            else para['useLatestVersion']

        parameters = {
            'customer-certificate': {
                'secret-source': {'id': secret_source},
                'secret-version': secret_version,
                'use-latest-version': use_latest_version
            }
        }
        args.parameters = parameters


class AFDSecurityPolicyCreate(_AFDSecurityPolicyCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.domains = AAZListArg(
            options=['--domains'],
            help='The domains to associate with the WAF policy. Could either be the ID of an endpoint'
            '(default domain will be used in that case) or ID of a custom domain.',
            required=True,
        )
        args_schema.domains.Element = AAZStrArg()
        args_schema.waf_policy = AAZStrArg(
            options=['--waf-policy'],
            help='The ID of Front Door WAF policy.',
            required=True,
        )
        args_schema.web_application_firewall._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if any(("/afdendpoints/" not in domain.lower() and
                "/customdomains/" not in domain.lower()) for domain in args.domains.to_serialized_data()):
            raise InvalidArgumentValueError('Domain should either be endpoint ID or custom domain ID.')
        if (has_value(args.waf_policy) and
                "/frontdoorwebapplicationfirewallpolicies/" not in args.waf_policy.to_serialized_data().lower()):
            raise InvalidArgumentValueError('waf_policy should be Front Door WAF policy ID.')

        domains = []
        if has_value(args.domains):
            for domain in args.domains:
                domains.append({
                    'id': domain
                })

        associations = [{
            'domains': domains,
            'patterns_to_match': ['/*']
        }]

        args.web_application_firewall = {
            'waf_policy': args.waf_policy,
            'associations': associations
        }


class AFDSecurityPolicyUpdate(_AFDSecurityPolicyUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.domains = AAZListArg(
            options=['--domains'],
            help='The domains to associate with the WAF policy. Could either be the ID of an endpoint'
            '(default domain will be used in that case) or ID of a custom domain.',
        )
        args_schema.domains.Element = AAZStrArg()

        args_schema.waf_policy = AAZStrArg(
            options=['--waf-policy'],
            help='The ID of Front Door WAF policy.',
        )
        args_schema.web_application_firewall._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing_security_policy = _AFDSecurityPolicyShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'security_policy_name': args.security_policy_name
        })

        associations = existing_security_policy['parameters']['associations']

        domains = []
        if has_value(args.domains):
            for domain in args.domains:
                domains.append({
                    'id': domain
                })
            associations = [{
                'domains': domains,
                'patterns_to_match': ['/*'],
            }]

        args.web_application_firewall = {
            'waf_policy': args.waf_policy if has_value(args.waf_policy)
            else existing_security_policy['parameters']['wafPolicy']['id'],
            'associations': associations
        }
