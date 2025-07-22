# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals, too-many-statements too-many-boolean-expressions too-many-branches protected-access

from azure.mgmt.cdn.models import (MinimumTlsVersion, ProtocolType, SkuName, UpdateRule, DeleteRule, CertificateType,
                                   ResourceType)
from azure.cli.core.aaz._base import has_value
from azure.cli.command_modules.cdn.aaz.latest.cdn.custom_domain import EnableHttps as _EnableHttps, \
    Delete as _CDNCustomDomainDelete
from azure.cli.command_modules.cdn.aaz.latest.afd.profile import Show as _AFDProfileShow, \
    Create as _AFDProfileCreate, Update as _AFDProfileUpdate, Delete as _AFDProfileDelete, \
    List as _AFDProfileList
from azure.cli.core.aaz import AAZStrArg, AAZBoolArg, AAZIntArg, AAZListArg, AAZTimeArg
from azure.cli.command_modules.cdn.aaz.latest.cdn.origin import Create as _CDNOriginCreate, \
    Update as _CDNOriginUpdate
from azure.cli.command_modules.cdn.aaz.latest.cdn.origin_group import Create as _CDNOriginGroupCreate, \
    Update as _CDNOriginGroupUpdate, Show as _CDNOriginGroupShow
from azure.cli.command_modules.cdn.aaz.latest.cdn.endpoint import Create as _CDNEndpointCreate, \
    Update as _CDNEndpointUpdate, Show as _CDNEndpointShow
from azure.cli.command_modules.cdn.aaz.latest.cdn.profile_migration import Migrate as _Migrate
from azure.cli.command_modules.cdn.aaz.latest.cdn._name_exists import NameExists
from .custom_rule_util import (create_condition, create_action, create_delivery_policy_from_existing)
import argparse

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def default_content_types():
    return ["text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/x-javascript",
            "application/javascript",
            "application/json",
            "application/xml"]


def _parse_ranges(ranges: str):
    if ranges is None:
        return []

    from azure.mgmt.cdn.models import HttpErrorRangeParameters

    def parse_range(error_range: str):
        split = error_range.split('-')
        if not split or len(split) > 2:
            raise CLIError(f'range "{error_range}" is invalid')

        try:
            begin = split[0]
            end = split[1] if len(split) == 2 else begin
        except ValueError:
            raise CLIError(f'range "{error_range}" is invalid')

        return HttpErrorRangeParameters(being=begin, end=end)

    return [parse_range(error_range) for error_range in ranges.split(',')]


class NameExistsWithType(NameExists):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.type = ResourceType.MICROSOFT_CDN_PROFILES_ENDPOINTS.value


class CDNProfileList(_AFDProfileList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema


class CDNProfileShow(_AFDProfileShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema


class CDNProfileCreate(_AFDProfileCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = 'global'


class CDNProfileUpdate(_AFDProfileUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.sku._registered = False
        return args_schema


class CDNProfileDelete(_AFDProfileDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema


class CDNEnableHttps(_EnableHttps):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.min_tls_version = AAZStrArg(
            options=['--min-tls-version'],
            help='The minimum TLS version required for the custom domain.',
        )
        args_schema.user_cert_group_name = AAZStrArg(
            options=['--user-cert-group-name'],
            help='The resource group of the KeyVault certificate.',
        )
        args_schema.user_cert_protocol_type = AAZStrArg(
            options=['--user-cert-protocol-type'],
            help='The protocol type of the certificate.',
        )
        args_schema.user_cert_secret_name = AAZStrArg(
            options=['--user-cert-secret-name'],
            help='The secret name of the KeyVault certificate.',
        )
        args_schema.user_cert_secret_version = AAZStrArg(
            options=['--user-cert-secret-version'],
            help='The secret version of the KeyVault certificate, '
            'If not specified, the "Latest" version will always been used and '
            'the deployed certificate will be automatically rotated to the latest version '
            'when a newer version of the certificate is available.',
        )
        args_schema.user_cert_subscription_id = AAZStrArg(
            options=['--user-cert-subscription-id'],
            help='The subscription id of the KeyVault certificate.',
        )
        args_schema.user_cert_vault_name = AAZStrArg(
            options=['--user-cert-vault-name'],
            help='The vault name of the KeyVault certificate.',
        )
        args_schema.minimum_tls_version._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        profile = CDNProfileShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name
        })

        if has_value(args.min_tls_version) and \
                args.min_tls_version.to_serialized_data().casefold() == 'none'.casefold():
            args.minimum_tls_version = MinimumTlsVersion.none
        elif args.min_tls_version == '1.0':
            args.minimum_tls_version = MinimumTlsVersion.tls10
        elif args.min_tls_version == '1.2':
            args.minimum_tls_version = MinimumTlsVersion.tls12

        # Are we using BYOC?
        if has_value(args.user_cert_group_name) or has_value(args.user_cert_protocol_type) or \
                has_value(args.user_cert_secret_name) or has_value(args.user_cert_secret_version) or \
                has_value(args.user_cert_subscription_id) or has_value(args.user_cert_vault_name):
            # If any BYOC flags are set, make sure they all are (except secret version).
            if not has_value(args.user_cert_group_name) or not has_value(args.user_cert_protocol_type) or \
                    not has_value(args.user_cert_secret_name) or \
                    not has_value(args.user_cert_vault_name):
                # BYOC is enabled, so make sure the secret version is set to None.
                raise CLIError("--user-cert-group-name, --user-cert-vault-name, --user-cert-secret-name, "
                               "and --user-cert-protocol-type are all required for user managed certificates.")
            if not has_value(args.user_cert_subscription_id):
                args.user_cert_subscription_id = self.ctx.subscription_id
            # All BYOC params are set, let's create the https parameters
            if not has_value(args.user_cert_protocol_type) or \
                    args.user_cert_protocol_type.to_serialized_data().lower() == 'sni':
                args.user_cert_protocol_type = ProtocolType.server_name_indication
            elif args.user_cert_protocol_type.to_serialized_data().lower() == 'ip':
                args.user_cert_protocol_type = ProtocolType.ip_based
            else:
                raise CLIError("--user-cert-protocol-type must be either 'sni' or 'ip'.")

            azure_key_vault = {
                'certificate_source_parameters': {
                    'delete_rule': DeleteRule.NO_ACTION,
                    'resource_group_name': args.user_cert_group_name,
                    'secret_name': args.user_cert_secret_name,
                    'subscription_id': args.user_cert_subscription_id,
                    'type_name': 'KeyVaultCertificateSourceParameters',
                    'update_rule': UpdateRule.NO_ACTION,
                    'vault_name': args.user_cert_vault_name,
                    'secret_version': args.user_cert_secret_version,
                }
            }

            args.azure_key_vault = azure_key_vault
            args.protocol_type = args.user_cert_protocol_type
        else:
            # We're using a CDN-managed certificate, let's create the right https
            # parameters for the profile SKU

            # Microsoft parameters
            if profile['sku']['name'] == SkuName.standard_microsoft:
                cdn = {
                    'certificate_source_parameters': {
                        'certificate_type': CertificateType.dedicated,
                        'type_name': 'CdnCertificateSourceParameters',
                    }
                }
                args.cdn = cdn
                args.protocol_type = ProtocolType.server_name_indication
            # Akamai parameters
            elif profile['sku']['name'] == SkuName.standard_akamai:
                cdn = {
                    'certificate_source_parameters': {
                        'certificate_type': CertificateType.shared,
                        'type_name': 'CdnCertificateSourceParameters',
                    }
                }
                args.cdn = cdn
                args.protocol_type = ProtocolType.server_name_indication
            # Verizon parameters
            else:
                cdn = {
                    'certificate_source_parameters': {
                        'certificate_type': CertificateType.shared,
                        'type_name': 'CdnCertificateSourceParameters',
                    }
                }
                args.cdn = cdn
                args.protocol_type = ProtocolType.ip_based


class CDNCustomDomainDelete(_CDNCustomDomainDelete):
    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_lro_poller(self._execute_operations, None)


class CDNOriginCreate(_CDNOriginCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.disabled = AAZBoolArg(
            options=['--disabled'],
            help='Don\'t use the origin for load balancing.',
            blank=True
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if not has_value(args.disabled):
            args.disabled = False
        args.enabled = not args.disabled
        if not has_value(args.http_port):
            args.http_port = 80
        if not has_value(args.https_port):
            args.https_port = 443
        if not has_value(args.priority):
            args.priority = 1
        elif int(args.priority.to_serialized_data()) < 1 or int(args.priority.to_serialized_data()) > 1000:
            raise CLIError('Priority must be between 1 and 1000')
        if not has_value(args.weight):
            args.weight = 1000


class CDNOriginUpdate(_CDNOriginUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.disabled = AAZBoolArg(
            options=['--disabled'],
            help='Don\'t use the origin for load balancing.',
            blank=True
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if not has_value(args.disabled):
            args.disabled = False
        args.enabled = not args.disabled


class CDNOriginGroupCreate(_CDNOriginGroupCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.probe_interval = AAZIntArg(
            options=['--probe-interval'],
            help='The frequency to perform health probes in seconds.',
            blank=240
        )
        args_schema.probe_method = AAZStrArg(
            options=['--probe-method'],
            help='The request method to use for health probes.',
            blank='HEAD'
        )
        args_schema.probe_path = AAZStrArg(
            options=['--probe-path'],
            help='The path relative to the origin that is used to determine the health of the origin.',
        )
        args_schema.probe_protocol = AAZStrArg(
            options=['--probe-protocol'],
            help='The protocol to use for health probes.',
            blank='Http'
        )
        args_schema.origins = AAZStrArg(
            options=['--origins'],
            help='The origins load balanced by this origin group, '
            'as a comma-separated list of origin names or origin resource IDs.',
        )
        args_schema.response_error_detection_status_code_ranges = AAZStrArg(
            options=['--response-error-detection-status-code-ranges'],
            help='Type of response errors for real user requests for which origin will be deemed unhealthy',
        )
        args_schema.response_error_detection_failover_threshold = AAZIntArg(
            options=['--response-error-detection-failover-threshold'],
            help='The percentage of failed requests in the sample where failover should trigger.',
        )
        args_schema.response_error_detection_error_types = AAZStrArg(
            options=['--response-error-detection-error-types'],
            help='The list of Http status code ranges '
            'that are considered as server errors for origin and it is marked as unhealthy.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        health_probe_settings = {
            'probe_interval_in_seconds': args.probe_interval,
            'probe_request_type': args.probe_method,
            'probe_path': args.probe_path,
            'probe_protocol': args.probe_protocol,
        }
        args.health_probe_settings = health_probe_settings

        formatted_origins = []
        if has_value(args.origins):
            for origin in args.origins.to_serialized_data().split(','):
                # If the origin is not an ID, assume it's a name and format it as an ID.
                if '/' not in origin:
                    origin = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                             f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/endpoints/{args.endpoint_name}' \
                             f'/origins/{origin}'
                formatted_origins.append({'id': origin})
        args.formatted_origins = formatted_origins

        response_based_origin_error_detection_settings = None
        if has_value(args.response_error_detection_error_types) or \
           has_value(args.response_error_detection_failover_threshold) or \
           has_value(args.response_error_detection_status_code_ranges):
            response_based_origin_error_detection_settings = {
                'http_error_ranges': _parse_ranges(args.response_error_detection_status_code_ranges),
                'response_based_detected_error_types': args.response_error_detection_error_types,
                'response_based_failover_threshold_percentage': args.response_error_detection_failover_threshold
            }
        args.response_based_origin_error_detection_settings = response_based_origin_error_detection_settings


class CDNOriginGroupUpdate(_CDNOriginGroupUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.probe_interval = AAZIntArg(
            options=['--probe-interval'],
            help='The frequency to perform health probes in seconds.',
        )
        args_schema.probe_method = AAZStrArg(
            options=['--probe-method'],
            help='The request method to use for health probes.',
        )
        args_schema.probe_path = AAZStrArg(
            options=['--probe-path'],
            help='The path relative to the origin that is used to determine the health of the origin.',
        )
        args_schema.probe_protocol = AAZStrArg(
            options=['--probe-protocol'],
            help='The protocol to use for health probes.',
        )
        args_schema.origins = AAZStrArg(
            options=['--origins'],
            help='The origins load balanced by this origin group, '
            'as a comma-separated list of origin names or origin resource IDs.',
        )
        args_schema.response_error_detection_status_code_ranges = AAZStrArg(
            options=['--response-error-detection-status-code-ranges'],
            help='Type of response errors for real user requests for which origin will be deemed unhealthy',
        )
        args_schema.response_error_detection_failover_threshold = AAZIntArg(
            options=['--response-error-detection-failover-threshold'],
            help='The percentage of failed requests in the sample where failover should trigger.',
        )
        args_schema.response_error_detection_error_types = AAZStrArg(
            options=['--response-error-detection-error-types'],
            help='The list of Http status code ranges '
            'that are considered as server errors for origin and it is marked as unhealthy.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _CDNOriginGroupShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name,
            'origin_group_name': args.origin_group_name
        })
        # Allow removing properties explicitly by specifying as empty string, or
        # update without modifying by not specifying (value is None).
        if not has_value(args.probe_path):
            args.probe_path = existing['healthProbeSettings']['probePath']
        elif args.probe_path.to_serialized_data() == '':
            args.probe_path = None
        if not has_value(args.probe_method):
            args.probe_method = existing['healthProbeSettings']['probeRequestType']
        elif args.probe_method.to_serialized_data() == '':
            args.probe_method = None
        if not has_value(args.probe_protocol):
            args.probe_protocol = existing['healthProbeSettings']['probeProtocol']
        elif args.probe_protocol.to_serialized_data() == '':
            args.probe_protocol = None
        if not has_value(args.probe_interval):
            args.probe_interval = existing['healthProbeSettings']['probeIntervalInSeconds']
        elif args.probe_interval.to_serialized_data() == '':
            args.probe_interval = None
        health_probe_settings = {
            'probe_interval_in_seconds': args.probe_interval,
            'probe_request_type': args.probe_method,
            'probe_path': args.probe_path,
            'probe_protocol': args.probe_protocol,
        }
        args.health_probe_settings = health_probe_settings

        formatted_origins = []
        if has_value(args.origins):
            args.origins = args.origins.to_serialized_data()
        else:
            args.origins = existing['origins']
        for origin in str(args.origins).split(','):
            # If the origin is not an ID, assume it's a name and format it as an ID.
            if '/' not in origin:
                origin = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                         f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/endpoints/{args.endpoint_name}' \
                         f'/origins/{origin}'
            formatted_origins.append({'id': origin})
        args.formatted_origins = formatted_origins

        response_based_origin_error_detection_settings = None
        if has_value(args.response_error_detection_error_types) or \
           has_value(args.response_error_detection_failover_threshold) or \
           has_value(args.response_error_detection_status_code_ranges):
            response_based_origin_error_detection_settings = {
                'http_error_ranges': _parse_ranges(args.response_error_detection_status_code_ranges),
                'response_based_detected_error_types': args.response_error_detection_error_types,
                'response_based_failover_threshold_percentage': args.response_error_detection_failover_threshold
            }
        args.response_based_origin_error_detection_settings = response_based_origin_error_detection_settings


class CDNEndpointCreate(_CDNEndpointCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.origin = AAZListArg(
            options=['--origin'],
            help='Endpoint origin specified by the following space-delimited 7 tuple: '
            'www.example.com http_port https_port private_link_resource_id '
            'private_link_location private_link_approval_message origin_name. '
            'The HTTP and HTTPS ports and the private link resource ID and location are optional. '
            'The HTTP and HTTPS ports default to 80 and 443, respectively. '
            'Private link fields are only valid for the sku Standard_Microsoft, '
            'and private_link_location is required if private_link_resource_id is set. '
            'the origin name is optional and defaults to origin.',
            required=True,
        )
        args_schema.origin.Element = AAZStrArg()
        args_schema.no_http = AAZBoolArg(
            options=['--no-http'],
            help='Disable HTTP traffic.Indicates whether HTTP traffic is not allowed on the endpoint. '
            'Default is to allow HTTP traffic.',
            blank=True
        )
        args_schema.no_https = AAZBoolArg(
            options=['--no-https'],
            help='Indicates whether HTTPS traffic is not allowed on the endpoint. '
            'Default is to allow HTTPS traffic.',
            blank=True
        )
        args_schema.enable_compression = AAZBoolArg(
            options=['--enable-compression'],
            help='If compression is enabled, content will be served as compressed '
            'if user requests for a compressed version. '
            'Content won\'t be compressed on CDN when requested content is smaller than 1 byte or larger than 1 MB.',
            blank=True
        )
        args_schema.origins._registered = False
        args_schema.is_http_allowed._registered = False
        args_schema.is_https_allowed._registered = False
        args_schema.is_compression_enabled._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if not 1 <= len(args.origin) <= 3 and not 5 <= len(args.origin) <= 6:
            msg = '%s takes 1, 2, 3, 5, or 6 values, %d given'
            raise argparse.ArgumentError(
                self, msg % (len(args.origin)))

        host_name = args.origin[0]
        http_port = 80
        https_port = 443
        private_link_resource_id = None
        private_link_location = None
        private_link_approval_message = None
        origin_name = host_name.to_serialized_data().replace('.', '-')

        if len(args.origin) > 1:
            http_port = int(args.origin[1].to_serialized_data())
        if len(args.origin) > 2:
            https_port = int(args.origin[2].to_serialized_data())
        if len(args.origin) > 4:
            private_link_resource_id = args.origin[3]
            private_link_location = args.origin[4]
        if len(args.origin) > 5:
            private_link_approval_message = args.origin[5]
        if len(args.origin) > 6:
            origin_name = args.origin[6]

        if http_port < 1 or http_port > 65535 or https_port < 1 or https_port > 65535:
            raise CLIError('Port number must be between 1 and 65535')

        args.origins = [{
            'name': origin_name,
            'host_name': host_name,
            'http_port': http_port,
            'https_port': https_port,
            'private_link_resource_id': private_link_resource_id,
            'private_link_location': private_link_location,
            'private_link_approval_message': private_link_approval_message
        }]

        if has_value(args.enable_compression):
            args.is_compression_enabled = args.enable_compression
        if has_value(args.no_http):
            args.is_http_allowed = not args.no_http
        if has_value(args.no_https):
            args.is_https_allowed = not args.no_https
        if args.enable_compression.to_serialized_data() and not has_value(args.content_types_to_compress):
            args.content_types_to_compress = default_content_types()


class CDNEndpointUpdate(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.no_http = AAZBoolArg(
            options=['--no-http'],
            help='Disable HTTP traffic.Indicates whether HTTP traffic is not allowed on the endpoint. '
            'Default is to allow HTTP traffic.',
            blank=True
        )
        args_schema.no_https = AAZBoolArg(
            options=['--no-https'],
            help='Indicates whether HTTPS traffic is not allowed on the endpoint. '
            'Default is to allow HTTPS traffic.',
            blank=True
        )
        args_schema.enable_compression = AAZBoolArg(
            options=['--enable-compression'],
            help='If compression is enabled, content will be served as compressed '
            'if user requests for a compressed version. '
            'Content won\'t be compressed on CDN when requested content is smaller than 1 byte or larger than 1 MB.',
            blank=True
        )
        args_schema.is_http_allowed._registered = False
        args_schema.is_https_allowed._registered = False
        args_schema.is_compression_enabled._registered = False
        args_schema.query_string_caching_behavior._default = None
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        existing = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })
        if has_value(args.default_origin_group):
            if '/' not in args.default_origin_group.to_serialized_data():
                args.default_origin_group = f'/subscriptions/{self.ctx.subscription_id}' \
                                            f'/resourceGroups/{args.resource_group}' \
                                            f'/providers/Microsoft.Cdn/profiles/{args.profile_name}' \
                                            f'/endpoints/{args.endpoint_name}' \
                                            f'/originGroups/{args.default_origin_group}'
        if has_value(args.enable_compression):
            args.is_compression_enabled = args.enable_compression
        if not has_value(args.enable_compression):
            args.is_compression_enabled = existing['isCompressionEnabled']
        if args.is_compression_enabled.to_serialized_data() and not has_value(args.content_types_to_compress):
            args.content_types_to_compress = existing['contentTypesToCompress']
            if not has_value(args.content_types_to_compress) is None:
                args.content_types_to_compress = default_content_types()
        if has_value(args.no_http):
            args.is_http_allowed = not args.no_http
        if has_value(args.no_https):
            args.is_https_allowed = not args.no_https


class CDNEndpointRuleAdd(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_name = AAZStrArg(
            options=['--action-name'],
            help='The name of the action for the delivery rule: '
            'https://learn.microsoft.com/en-us/azure/cdn/cdn-standard-rules-engine-actions.',
            required=True
        )
        args_schema.order = AAZIntArg(
            options=['--order'],
            help='The order in which the rules are applied for the endpoint. Possible values {0,1,2,3,………}. '
            'A rule with a lower order will be applied before one with a higher order. '
            'Rule with order 0 is a special rule. It does not require any condition and '
            'actions listed in it will always be applied.',
            required=True
        )
        args_schema.cache_behavior = AAZStrArg(
            options=['--cache-behavior'],
            help='Caching behavior for the requests.',
            enum=['BypassCache', 'Override', 'SetIfMissing']
        )
        args_schema.cache_duration = AAZTimeArg(
            options=['--cache-duration'],
            help='The duration for which the content needs to be cached. '
            'Allowed format is hh:mm:ss.xxxxxx',
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
            help='The full path to redirect. Path cannot be empty and must start with /. '
            'Leave empty to use the incoming path as destination path.',
        )
        args_schema.custom_querystring = AAZStrArg(
            options=['--custom-querystring'],
            help='The set of query strings to be placed in the redirect URL. '
            'leave empty to preserve the incoming query string.',
        )
        args_schema.destination = AAZStrArg(
            options=['--destination'],
            help='The destination path to be used in the rewrite.'
        )
        args_schema.header_action = AAZStrArg(
            options=['--header-action'],
            help='Header action for the requests.',
            enum=['Append', 'Overwrite', 'Delete']
        )
        args_schema.header_name = AAZStrArg(
            options=['--header-name'],
            help='Name of the header to modify.',
        )
        args_schema.header_value = AAZStrArg(
            options=['--header-value'],
            help='Value of the header.',
        )
        args_schema.match_values = AAZListArg(
            options=['--match-values'],
            help='Match values of the match condition. e.g, space separated values "GET" "HTTP".',
        )
        args_schema.match_values.Element = AAZStrArg()
        args_schema.match_variable = AAZStrArg(
            options=['--match-variable'],
            help='Name of the match condition: '
            'https://learn.microsoft.com/en-us/azure/cdn/cdn-standard-rules-engine-match-conditions.',
            enum=['ClientPort', 'Cookies', 'HostName', 'HttpVersion', 'IsDevice', 'PostArgs', 'QueryString',
                  'RemoteAddress', 'RequestBody', 'RequestHeader', 'RequestMethod', 'RequestScheme', 'RequestUri',
                  'ServerPort', 'SocketAddr', 'SslProtocol', 'UrlFileExtension', 'UrlFileName', 'UrlPath']
        )
        args_schema.negate_condition = AAZBoolArg(
            options=['--negate-condition'],
            help='If true, negates the condition.',
        )
        args_schema.operator = AAZStrArg(
            options=['--operator'],
            help='Operator of the match condition.'
        )
        args_schema.preserve_unmatched_path = AAZBoolArg(
            options=['--preserve-unmatched-path'],
            help='If True, the remaining path after the source pattern will be appended to the new destination path.',
        )
        args_schema.query_parameters = AAZStrArg(
            options=['--query-parameters'],
            help='Query parameters to include or exclude (comma separated).',
        )
        args_schema.query_string_behavior = AAZStrArg(
            options=['--query-string-behavior'],
            help='Query string behavior for the requests.',
            enum=['Include', 'IncludeAll', 'Exclude', 'ExcludeAll']
        )
        args_schema.redirect_protocol = AAZStrArg(
            options=['--redirect-protocol'],
            help='Protocol to use for the redirect.',
        )
        args_schema.redirect_type = AAZStrArg(
            options=['--redirect-type'],
            help='The redirect type the rule will use when redirecting traffic.',
            enum=['Moved', 'Found', 'TemporaryRedirect', 'PermanentRedirect']
        )
        args_schema.rule_name = AAZStrArg(
            options=['--rule-name'],
            help='Name of the rule, only required for Microsoft SKU.',
        )
        args_schema.selector = AAZStrArg(
            options=['--selector'],
            help='Selector of the match condition.',
        )
        args_schema.source_pattern = AAZStrArg(
            options=['--source-pattern'],
            help='A request URI pattern that identifies the type of requests that may be rewritten.',
        )
        args_schema.transform = AAZListArg(
            options=['--transform'],
            help='Transform to apply before matching.',
        )
        args_schema.transform.Element = AAZStrArg(
            enum=['Lowercase', 'Uppercase']
        )
        args_schema.origin_group = AAZStrArg(
            options=['--origin-group'],
            help='Name of the origin group to which this rule will be added.Name or ID of the OriginGroup '
            'that would override the default OriginGroup.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        partner_skus = [SkuName.PREMIUM_VERIZON, SkuName.CUSTOM_VERIZON, SkuName.STANDARD_VERIZON]
        profile = CDNProfileShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name
        })
        if not has_value(args.rule_name) and profile['sku']['name'] not in partner_skus:
            raise CLIError("--rule-name is required for Microsoft SKU")
        endpoint = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })

        delivery_policy = None
        if 'deliveryPolicy' in endpoint:
            delivery_policy = create_delivery_policy_from_existing(endpoint['deliveryPolicy'])
        else:
            delivery_policy = {
                'description': 'default_policy',
                'rules': []
            }

        conditions = []
        condition = create_condition(args.match_variable, args.operator, args.match_values,
                                     args.selector, args.negate_condition, args.transform)
        if condition is not None:
            conditions.append(condition)
        actions = []
        action = create_action(args.action_name, args.cache_behavior, args.cache_duration, args.header_action,
                               args.header_name, args.header_value, args.query_string_behavior, args.query_parameters,
                               args.redirect_type, args.redirect_protocol, args.custom_hostname, args.custom_path,
                               args.custom_querystring, args.custom_fragment, args.source_pattern, args.destination,
                               args.preserve_unmatched_path, self.ctx.subscription_id,
                               args.resource_group, args.profile_name, args.endpoint_name, args.origin_group)
        if action is not None:
            actions.append(action)
        rule = {
            'name': args.rule_name,
            'order': args.order,
            'conditions': conditions,
            'actions': actions
        }
        delivery_policy['rules'].append(rule)
        args.delivery_policy = delivery_policy


class CDNEndpointRuleRemove(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rule_name = AAZStrArg(
            options=['--rule-name'],
            help='Name of the rule.',
        )
        args_schema.order = AAZIntArg(
            options=['--order'],
            help='The order in which the rules are applied for the endpoint. Possible values {0,1,2,3,………}. '
            'A rule with a lower order will be applied before one with a higher order. '
            'Rule with order 0 is a special rule. It does not require any condition and '
            'actions listed in it will always be applied.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if not has_value(args.rule_name) and not has_value(args.order):
            raise CLIError("Either --rule-name or --order must be specified")

        if has_value(args.order) and args.order < 0:
            raise CLIError("Order should be non-negative.")
        endpoint = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })
        delivery_policy = create_delivery_policy_from_existing(endpoint['deliveryPolicy'])
        if delivery_policy is not None:
            pop_index = -1
            for idx, rule in enumerate(delivery_policy['rules']):
                if has_value(args.rule_name) and rule['name'] == args.rule_name:
                    pop_index = idx
                    break
                if args.order is not None and rule['order'] == args.order:
                    pop_index = idx
                    break

            # To guarantee the consecutive rule order,
            # we need to make sure the rule with order larger than the deleted one
            # to decrease its order by one. Rule with order 0 is special and no rule order adjustment is required.
            if pop_index != -1:
                pop_order = delivery_policy['rules'][pop_index]['order']
                delivery_policy['rules'].pop(pop_index)
                for rule in delivery_policy['rules']:
                    if rule['order'] > pop_order and pop_order != 0:
                        rule['order'] -= 1

        else:
            logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")
        args.delivery_policy = delivery_policy


class CDNEndpointRuleActionAdd(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_name = AAZStrArg(
            options=['--action-name'],
            help='The name of the action for the delivery rule: '
            'https://learn.microsoft.com/en-us/azure/cdn/cdn-standard-rules-engine-actions.',
            required=True
        )
        args_schema.cache_behavior = AAZStrArg(
            options=['--cache-behavior'],
            help='Caching behavior for the requests.',
            enum=['BypassCache', 'Override', 'SetIfMissing']
        )
        args_schema.cache_duration = AAZTimeArg(
            options=['--cache-duration'],
            help='The duration for which the content needs to be cached. '
            'Allowed format is hh:mm:ss.xxxxxx',
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
            help='The full path to redirect. Path cannot be empty and must start with /. '
            'Leave empty to use the incoming path as destination path.',
        )
        args_schema.custom_querystring = AAZStrArg(
            options=['--custom-querystring'],
            help='The set of query strings to be placed in the redirect URL. '
            'leave empty to preserve the incoming query string.',
        )
        args_schema.destination = AAZStrArg(
            options=['--destination'],
            help='The destination path to be used in the rewrite.'
        )
        args_schema.header_action = AAZStrArg(
            options=['--header-action'],
            help='Header action for the requests.',
            enum=['Append', 'Overwrite', 'Delete']
        )
        args_schema.header_name = AAZStrArg(
            options=['--header-name'],
            help='Name of the header to modify.',
        )
        args_schema.header_value = AAZStrArg(
            options=['--header-value'],
            help='Value of the header.',
        )
        args_schema.preserve_unmatched_path = AAZBoolArg(
            options=['--preserve-unmatched-path'],
            help='If True, the remaining path after the source pattern will be appended to the new destination path.',
        )
        args_schema.query_parameters = AAZStrArg(
            options=['--query-parameters'],
            help='Query parameters to include or exclude (comma separated).',
        )
        args_schema.query_string_behavior = AAZStrArg(
            options=['--query-string-behavior'],
            help='Query string behavior for the requests.',
            enum=['Include', 'IncludeAll', 'Exclude', 'ExcludeAll']
        )
        args_schema.redirect_protocol = AAZStrArg(
            options=['--redirect-protocol'],
            help='Protocol to use for the redirect.',
        )
        args_schema.redirect_type = AAZStrArg(
            options=['--redirect-type'],
            help='The redirect type the rule will use when redirecting traffic.',
            enum=['Moved', 'Found', 'TemporaryRedirect', 'PermanentRedirect']
        )
        args_schema.rule_name = AAZStrArg(
            options=['--rule-name'],
            help='Name of the rule, only required for Microsoft SKU.',
            required=True,
        )
        args_schema.source_pattern = AAZStrArg(
            options=['--source-pattern'],
            help='A request URI pattern that identifies the type of requests that may be rewritten.',
        )
        args_schema.origin_group = AAZStrArg(
            options=['--origin-group'],
            help='Name of the origin group to which this rule will be added.Name or ID of the OriginGroup '
            'that would override the default OriginGroup.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        endpoint = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })

        delivery_policy = create_delivery_policy_from_existing(endpoint['deliveryPolicy'])
        action = create_action(args.action_name, args.cache_behavior, args.cache_duration, args.header_action,
                               args.header_name, args.header_value, args.query_string_behavior, args.query_parameters,
                               args.redirect_type, args.redirect_protocol, args.custom_hostname, args.custom_path,
                               args.custom_querystring, args.custom_fragment, args.source_pattern, args.destination,
                               args.preserve_unmatched_path, self.ctx.subscription_id,
                               args.resource_group, args.profile_name, args.endpoint_name, args.origin_group)
        for i in range(0, len(delivery_policy['rules'])):
            if delivery_policy['rules'][i]['name'] == args.rule_name:
                delivery_policy['rules'][i]['actions'].append(action)
        args.delivery_policy = delivery_policy


class CDNEndpointRuleActionRemove(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.index = AAZIntArg(
            options=['--index'],
            help='The index of the condition/action.',
            required=True
        )
        args_schema.rule_name = AAZStrArg(
            options=['--rule-name'],
            help='Name of the rule.',
            required=True,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        endpoint = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })

        delivery_policy = create_delivery_policy_from_existing(endpoint['deliveryPolicy'])
        if delivery_policy is not None:
            for i in range(0, len(delivery_policy['rules'])):
                if delivery_policy['rules'][i]['name'] == args.rule_name:
                    delivery_policy['rules'][i]['actions'].pop(args.index.to_serialized_data())
        else:
            logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")
        args.delivery_policy = delivery_policy


class CDNEndpointRuleConditionAdd(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.match_values = AAZListArg(
            options=['--match-values'],
            help='Match values of the match condition. e.g, space separated values "GET" "HTTP".',
        )
        args_schema.match_values.Element = AAZStrArg()
        args_schema.match_variable = AAZStrArg(
            options=['--match-variable'],
            help='Name of the match condition: '
            'https://learn.microsoft.com/en-us/azure/cdn/cdn-standard-rules-engine-match-conditions.',
            enum=['ClientPort', 'Cookies', 'HostName', 'HttpVersion', 'IsDevice', 'PostArgs', 'QueryString',
                  'RemoteAddress', 'RequestBody', 'RequestHeader', 'RequestMethod', 'RequestScheme', 'RequestUri',
                  'ServerPort', 'SocketAddr', 'SslProtocol', 'UrlFileExtension', 'UrlFileName', 'UrlPath'],
            required=True
        )
        args_schema.negate_condition = AAZBoolArg(
            options=['--negate-condition'],
            help='If true, negates the condition.',
        )
        args_schema.operator = AAZStrArg(
            options=['--operator'],
            help='Operator of the match condition.',
            required=True
        )
        args_schema.rule_name = AAZStrArg(
            options=['--rule-name'],
            help='Name of the rule, only required for Microsoft SKU.',
            required=True,
        )
        args_schema.selector = AAZStrArg(
            options=['--selector'],
            help='Selector of the match condition.',
        )
        args_schema.transform = AAZListArg(
            options=['--transform'],
            help='Transform to apply before matching.',
        )
        args_schema.transform.Element = AAZStrArg(
            enum=['Lowercase', 'Uppercase']
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        endpoint = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })

        delivery_policy = create_delivery_policy_from_existing(endpoint['deliveryPolicy'])
        condition = create_condition(args.match_variable, args.operator, args.match_values,
                                     args.selector, args.negate_condition, args.transform)
        for i in range(0, len(delivery_policy['rules'])):
            if delivery_policy['rules'][i]['name'] == args.rule_name:
                delivery_policy['rules'][i]['conditions'].append(condition)

        args.delivery_policy = delivery_policy


class CDNEndpointRuleConditionRemove(_CDNEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.index = AAZIntArg(
            options=['--index'],
            help='The index of the condition/action.',
            required=True
        )
        args_schema.rule_name = AAZStrArg(
            options=['--rule-name'],
            help='Name of the rule.',
            required=True,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        endpoint = _CDNEndpointShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name
        })

        delivery_policy = create_delivery_policy_from_existing(endpoint['deliveryPolicy'])
        if delivery_policy is not None:
            for i in range(0, len(delivery_policy['rules'])):
                if delivery_policy['rules'][i]['name'] == args.rule_name:
                    delivery_policy['rules'][i]['conditions'].pop(args.index.to_serialized_data())
        else:
            logger.warning("rule cannot be found. This command will be skipped. Please check the rule name")
        args.delivery_policy = delivery_policy


class CdnMigrateToAfd(_Migrate):
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
        return args_schema

    def post_operations(self):
        args = self.ctx.args
        identity = None
        user_assigned_identities = {}
        for identity in args.user_assigned_identities:
            user_assigned_identities[identity.to_serialized_data()] = {}
        if args.identity_type == 'UserAssigned' or args.identity_type == 'SystemAssigned, UserAssigned':
            identity = {
                'type': args.identity_type,
                'userAssignedIdentities': user_assigned_identities
            }
        elif args.identity_type == 'SystemAssigned':
            identity = {
                'type': args.identity_type
            }

        existing = _AFDProfileShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name
        })
        location = None if 'location' not in existing else existing['location']
        _AFDProfileUpdate(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'location': location,
            'identity': identity
        })
