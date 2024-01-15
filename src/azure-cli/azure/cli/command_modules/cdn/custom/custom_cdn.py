# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals, too-many-statements too-many-boolean-expressions too-many-branches protected-access

from azure.mgmt.cdn.models import (MinimumTlsVersion, ProtocolType, SkuName, UpdateRule, DeleteRule, CertificateType)
from azure.cli.core.aaz._base import has_value
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.command_modules.cdn.aaz.latest.cdn.custom_domain import EnableCustomHttp as _CDNEnableCustomHttp
from azure.cli.command_modules.cdn.aaz.latest.afd.profile import Show as _AFDProfileShow, \
    Create as _AFDProfileCreate, Update as _AFDProfileUpdate, Delete as _AFDProfileDelete
from azure.cli.core.aaz import AAZStrArg, AAZBoolArg, AAZIntArg, AAZListArg, AAZDateArg, register_command
from azure.cli.command_modules.cdn.aaz.latest.cdn.origin import Create as _CDNOriginCreate, \
    Update as _CDNOriginUpdate
from azure.cli.command_modules.cdn.aaz.latest.cdn.origin_group import Create as _CDNOriginGroupCreate, \
    Update as _CDNOriginGroupUpdate, Show as _CDNOriginGroupShow

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


@register_command('cdn profile show')
class CDNProfileShow(_AFDProfileShow):
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


@register_command('cdn profile create')
class CDNProfileCreate(_AFDProfileCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._registered = False
        return args_schema
    # def pre_operations(self):
    #     args = self.ctx.args
    #     args.location = 'global'


@register_command('cdn profile update')
class CDNProfileUpdate(_AFDProfileUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._registered = False
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
        existing_location = None if 'location' not in existing else existing['location']
        args.location = existing_location


@register_command('cdn profile delete', _AFDProfileDelete)
class CDNProfileDelete(_AFDProfileDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema


class CDNEnableCustomHttp(_CDNEnableCustomHttp):
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
        args_schema.user_cert_secret_name = AAZStrArg(
            options=['--user-cert-subscription-id'],
            help='The subscription id of the KeyVault certificate.',
        )
        args_schema.user_cert_secret_name = AAZStrArg(
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

        if has_value(args.min_tls_version) and args.min_tls_version.to_serialized_data().casefold() == 'none'.casefold():
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
            if has_value(args.user_cert_group_name) or has_value(args.user_cert_protocol_type) or \
                    has_value(args.user_cert_secret_name) or \
                    has_value(args.user_cert_vault_name):
                # BYOC is enabled, so make sure the secret version is set to None.
                raise CLIError("--user-cert-group-name, --user-cert-vault-name, --user-cert-secret-name, "
                               "and --user-cert-protocol-type are all required for user managed certificates.")
            if not has_value(args.user_cert_subscription_id):
                args.user_cert_subscription_id = self.ctx.subscription_id
            # All BYOC params are set, let's create the https parameters
            if not has_value(args.user_cert_protocol_type) or args.user_cert_protocol_type.to_serialized_data().lower() == 'sni':
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


class CDNOriginCreate(_CDNOriginCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.disabled = AAZBoolArg(
            options=['--disabled'],
            help='Don\'t use the origin for load balancing.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.enable = not args.disabled
        if not has_value(args.http_port):
            args.http_port = 80
        if not has_value(args.https_port):
            args.https_port = 443
        if not has_value(args.priority):
            args.priority = 1
        if not has_value(args.weight):
            args.weight = 1000


class CDNOriginUpdate(_CDNOriginUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.disabled = AAZBoolArg(
            options=['--disabled'],
            help='Don\'t use the origin for load balancing.',
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.enable = not args.disabled


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


class CDNOriginGroupCreate(_CDNOriginCreate):
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
        args_schema.origin = AAZListArg(
            options=['--origin-name'],
            help='The origins load balanced by this origin group, '
            'as a comma-separated list of origin names or origin resource IDs.',
        )
        args_schema.origin.Element = AAZStrArg()
        args_schema.response_error_detection_error_types = AAZStrArg(
            options=['--response-error-detection-error-types'],
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
        if not has_value(args.probe_method):
            args.probe_method = 'HEAD'
        if not has_value(args.probe_protocol):
            args.probe_protocol = 'HTTP'
        if not has_value(args.probe_interval):
            args.probe_interval = 240
        health_probe_settings = {
            'probe_interval_in_seconds': args.probe_interval,
            'probe_method': args.probe_method,
            'probe_path': args.probe_path,
            'probe_protocol': args.probe_protocol,
        }
        args.health_probe_settings = health_probe_settings

        formatted_origins = []
        if has_value(args.origin):
            for origin in args.origins.to_serialized_data().split(','):
                # If the origin is not an ID, assume it's a name and format it as an ID.
                if '/' not in origin:
                    origin = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                             f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/endpoints/{args.endpoint_name}' \
                             f'/origins/{origin}'
                formatted_origins.append({'id': origin})
        args.formatted_origins = formatted_origins

        response_based_error_detection_settings = None
        if has_value(args.response_error_detection_error_types) or \
           has_value(args.response_error_detection_failover_threshold) or \
           has_value(args.response_error_detection_status_code_ranges):
            response_based_error_detection_settings = {
                'http_error_ranges': _parse_ranges(args.response_error_detection_status_code_ranges),
                'response_based_detected_error_types': args.response_error_detection_error_types,
                'response_based_failover_threshold_percentage': args.response_error_detection_failover_threshold
            }
        args.response_based_error_detection_settings = response_based_error_detection_settings


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
        args_schema.origin = AAZListArg(
            options=['--origin-name'],
            help='The origins load balanced by this origin group, '
            'as a comma-separated list of origin names or origin resource IDs.',
        )
        args_schema.origin.Element = AAZStrArg()
        args_schema.response_error_detection_error_types = AAZStrArg(
            options=['--response-error-detection-error-types'],
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
        if has_value(args.probe_method):
            args.probe_method = args.probe_method.to_serialized_data().upper()
        if has_value(args.probe_protocol):
            args.probe_protocol = args.probe_protocol.to_serialized_data().upper()

        existing = _CDNOriginGroupShow(cli_ctx=self.cli_ctx)(command_args={
            'resource_group': args.resource_group,
            'profile_name': args.profile_name,
            'endpoint_name': args.endpoint_name,
            'origin_group_name': args.origin_group_name
        })
        # Allow removing properties explicitly by specifying as empty string, or
        # update without modifying by not specifying (value is None).
        if not has_value(args.probe_path):
            args.probe_path = existing['health_probe_settings']['probe_path']
        elif args.probe_path.to_serialized_data() == '':
            args.probe_path = None
        if not has_value(args.probe_method):
            args.probe_method = existing['health_probe_settings']['probe_method']
        elif args.probe_method.to_serialized_data() == '':
            args.probe_method = None
        if not has_value(args.probe_protocol):
            args.probe_protocol = existing['health_probe_settings']['probe_protocol']
        elif args.probe_protocol.to_serialized_data() == '':
            args.probe_protocol = None
        if not has_value(args.probe_interval):
            args.probe_interval = existing['health_probe_settings']['probe_interval_in_seconds']
        elif args.probe_interval.to_serialized_data() == '':
            args.probe_interval = None
        health_probe_settings = {
            'probe_interval_in_seconds': args.probe_interval,
            'probe_method': args.probe_method,
            'probe_path': args.probe_path,
            'probe_protocol': args.probe_protocol,
        }
        args.health_probe_settings = health_probe_settings

        formatted_origins = []
        if has_value(args.origins):
            args.origins = args.origins.to_serialized_data()
        else:
            args.origins = existing['origins']
        for origin in args.origins.split(','):
            # If the origin is not an ID, assume it's a name and format it as an ID.
            if '/' not in origin:
                origin = f'/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}' \
                         f'/providers/Microsoft.Cdn/profiles/{args.profile_name}/endpoints/{args.endpoint_name}' \
                         f'/origins/{origin}'
            formatted_origins.append({'id': origin})
        args.formatted_origins = formatted_origins

        response_based_error_detection_settings = None
        if has_value(args.response_error_detection_error_types) or \
           has_value(args.response_error_detection_failover_threshold) or \
           has_value(args.response_error_detection_status_code_ranges):
            response_based_error_detection_settings = {
                'http_error_ranges': _parse_ranges(args.response_error_detection_status_code_ranges),
                'response_based_detected_error_types': args.response_error_detection_error_types,
                'response_based_failover_threshold_percentage': args.response_error_detection_failover_threshold
            }
        args.response_based_error_detection_settings = response_based_error_detection_settings