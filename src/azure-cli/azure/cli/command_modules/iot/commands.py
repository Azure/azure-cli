# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation, CliCommandType
from azure.cli.command_modules.iot._client_factory import (iot_hub_service_factory,
                                                           iot_central_service_factory,
                                                           iot_service_provisioning_factory)
from azure.cli.command_modules.iot._utils import _dps_certificate_response_transform

CS_DEPRECATION_INFO = 'IoT Extension (azure-iot) connection-string command (az iot hub connection-string show)'


class PolicyUpdateResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(PolicyUpdateResultTransform, self).__call__(poller)
        return result.properties.authorization_policies


class EndpointUpdateResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(EndpointUpdateResultTransform, self).__call__(poller)
        return result.properties.routing.endpoints


class RouteUpdateResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(RouteUpdateResultTransform, self).__call__(poller)
        return result.properties.routing.routes


# Deleting IoT Hub is a long-running operation. Due to API implementation issue, 404 error will be thrown during
# deletion of an IoT Hub.
# This is a work around to suppress the 404 error. It should be removed after API is fixed.
class HubDeleteResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        from azure.cli.core.util import CLIError
        try:
            super(HubDeleteResultTransform, self).__call__(poller)
        except CLIError as e:
            if 'not found' not in str(e):
                raise e


def load_command_table(self, _):  # pylint: disable=too-many-statements

    update_custom_util = CliCommandType(operations_tmpl='azure.cli.command_modules.iot.custom#{}')

    iot_central_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.iotcentral.operations#IoTCentralOperations.{}'
    )

    private_endpoint_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.iotcentral.operations#PrivateEndpointConnectionsOperations.{}',
        # client_factory=cf_private_endpoint,
    )

    private_link_resource_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.iotcentral.operations#PrivateLinksOperations.{}',
        # client_factory=cf_private_link,
    )

    # iot dps commands
    with self.command_group('iot dps', client_factory=iot_service_provisioning_factory) as g:
        g.custom_command('list', 'iot_dps_list')
        g.custom_show_command('show', 'iot_dps_get')
        g.custom_command('create', 'iot_dps_create')
        g.custom_command('delete', 'iot_dps_delete')
        g.generic_update_command('update', getter_name='iot_dps_get', setter_name='iot_dps_update',
                                 command_type=update_custom_util)

    # iot dps linked-hub commands
    with self.command_group('iot dps linked-hub', client_factory=iot_service_provisioning_factory) as g:
        g.custom_command('list', 'iot_dps_linked_hub_list')
        g.custom_show_command('show', 'iot_dps_linked_hub_get')
        g.custom_command('create', 'iot_dps_linked_hub_create', supports_no_wait=True)
        g.custom_command('update', 'iot_dps_linked_hub_update', supports_no_wait=True)
        g.custom_command('delete', 'iot_dps_linked_hub_delete', supports_no_wait=True)

    # iot dps certificate commands
    with self.command_group('iot dps certificate',
                            client_factory=iot_service_provisioning_factory,
                            transform=_dps_certificate_response_transform) as g:
        g.custom_command('list', 'iot_dps_certificate_list')
        g.custom_show_command('show', 'iot_dps_certificate_get')
        g.custom_command('create', 'iot_dps_certificate_create')
        g.custom_command('delete', 'iot_dps_certificate_delete')
        g.custom_command('generate-verification-code', 'iot_dps_certificate_gen_code')
        g.custom_command('verify', 'iot_dps_certificate_verify')
        g.custom_command('update', 'iot_dps_certificate_update')

    # iot dps policy commands
    with self.command_group('iot dps policy', client_factory=iot_service_provisioning_factory) as g:
        g.custom_command('list', 'iot_dps_policy_list')
        g.custom_show_command('show', 'iot_dps_policy_get')
        g.custom_command('create', 'iot_dps_policy_create', supports_no_wait=True)
        g.custom_command('update', 'iot_dps_policy_update', supports_no_wait=True)
        g.custom_command('delete', 'iot_dps_policy_delete', supports_no_wait=True)

    # iot hub certificate commands
    with self.command_group('iot hub certificate', client_factory=iot_hub_service_factory) as g:
        g.custom_command('list', 'iot_hub_certificate_list')
        g.custom_show_command('show', 'iot_hub_certificate_get')
        g.custom_command('create', 'iot_hub_certificate_create')
        g.custom_command('delete', 'iot_hub_certificate_delete')
        g.custom_command('generate-verification-code', 'iot_hub_certificate_gen_code')
        g.custom_command('verify', 'iot_hub_certificate_verify')
        g.custom_command('update', 'iot_hub_certificate_update')

    # iot hub commands
    with self.command_group('iot hub', client_factory=iot_hub_service_factory) as g:
        g.custom_command('create', 'iot_hub_create')
        g.custom_command('list', 'iot_hub_list')
        g.custom_command('show-connection-string', 'iot_hub_show_connection_string',
                         deprecate_info=self.deprecate(redirect=CS_DEPRECATION_INFO))
        g.custom_show_command('show', 'iot_hub_get')
        g.generic_update_command('update', getter_name='iot_hub_get', setter_name='iot_hub_update',
                                 command_type=update_custom_util, custom_func_name='update_iot_hub_custom')
        g.custom_command('delete', 'iot_hub_delete', transform=HubDeleteResultTransform(self.cli_ctx))
        g.custom_command('list-skus', 'iot_hub_sku_list')
        g.custom_command('show-quota-metrics', 'iot_hub_get_quota_metrics')
        g.custom_command('show-stats', 'iot_hub_get_stats')
        g.custom_command('manual-failover', 'iot_hub_manual_failover', supports_no_wait=True)

    # iot hub consumer group commands
    with self.command_group('iot hub consumer-group', client_factory=iot_hub_service_factory) as g:
        g.custom_command('create', 'iot_hub_consumer_group_create')
        g.custom_command('list', 'iot_hub_consumer_group_list')
        g.custom_show_command('show', 'iot_hub_consumer_group_get')
        g.custom_command('delete', 'iot_hub_consumer_group_delete')

    # iot hub identity commands
    with self.command_group('iot hub identity', client_factory=iot_hub_service_factory) as g:
        g.custom_command('assign', 'iot_hub_identity_assign')
        g.custom_show_command('show', 'iot_hub_identity_show')
        g.custom_command('remove', 'iot_hub_identity_remove')

    # iot hub policy commands
    with self.command_group('iot hub policy', client_factory=iot_hub_service_factory) as g:
        g.custom_command('list', 'iot_hub_policy_list')
        g.custom_show_command('show', 'iot_hub_policy_get')
        g.custom_command('create', 'iot_hub_policy_create', transform=PolicyUpdateResultTransform(self.cli_ctx))
        g.custom_command('delete', 'iot_hub_policy_delete', transform=PolicyUpdateResultTransform(self.cli_ctx))
        g.custom_command('renew-key', 'iot_hub_policy_key_renew', supports_no_wait=True)

    # iot hub routing endpoint commands
    with self.command_group('iot hub routing-endpoint', client_factory=iot_hub_service_factory) as g:
        g.custom_command('create', 'iot_hub_routing_endpoint_create',
                         transform=EndpointUpdateResultTransform(self.cli_ctx))
        g.custom_show_command('show', 'iot_hub_routing_endpoint_show')
        g.custom_command('list', 'iot_hub_routing_endpoint_list')
        g.custom_command('delete', 'iot_hub_routing_endpoint_delete',
                         transform=EndpointUpdateResultTransform(self.cli_ctx))

    # iot hub message enrichment commands
    with self.command_group('iot hub message-enrichment', client_factory=iot_hub_service_factory,
                            min_api="2019-07-01-preview") as g:
        g.custom_command('create', 'iot_message_enrichment_create')
        g.custom_command('list', 'iot_message_enrichment_list')
        g.custom_command('delete', 'iot_message_enrichment_delete')
        g.custom_command('update', 'iot_message_enrichment_update')

    # iot hub route commands
    with self.command_group('iot hub route', client_factory=iot_hub_service_factory) as g:
        g.custom_command('create', 'iot_hub_route_create', transform=RouteUpdateResultTransform(self.cli_ctx))
        g.custom_show_command('show', 'iot_hub_route_show')
        g.custom_command('list', 'iot_hub_route_list')
        g.custom_command('delete', 'iot_hub_route_delete', transform=RouteUpdateResultTransform(self.cli_ctx))
        g.custom_command('update', 'iot_hub_route_update', transform=RouteUpdateResultTransform(self.cli_ctx))
        g.custom_command('test', 'iot_hub_route_test')

    # iot hub device stream commands
    with self.command_group('iot hub devicestream', client_factory=iot_hub_service_factory,
                            min_api="2019-07-01-preview") as g:
        g.custom_show_command('show', 'iot_hub_devicestream_show')

    # iot central commands
    with self.command_group('iot central app', iot_central_sdk, client_factory=iot_central_service_factory) as g:
        g.custom_command('create', 'iot_central_app_create', supports_no_wait=True)
        g.custom_command('list', 'iot_central_app_list')
        g.custom_show_command('show', 'iot_central_app_get')
        g.generic_update_command('update', getter_name='iot_central_app_get',
                                 setter_name='iot_central_app_update', command_type=update_custom_util)
        g.custom_command('delete', 'iot_central_app_delete', confirmation=True, supports_no_wait=True)
        g.custom_command('identity assign', 'iot_central_app_assign_identity')
        g.custom_command('identity remove', 'iot_central_app_remove_identity')
        g.custom_show_command('identity show', 'iot_central_app_show_identity')

    with self.command_group('iot central app private-endpoint-connection',
                            private_endpoint_sdk,
                            client_factory=iot_central_service_factory) as g:
        from azure.cli.command_modules.iot._validators import validate_private_endpoint_connection_id
        g.custom_command('delete', 'delete_private_endpoint_connection', confirmation=True,
                         validator=validate_private_endpoint_connection_id)
        g.custom_show_command('show', 'show_private_endpoint_connection',
                              validator=validate_private_endpoint_connection_id)
        g.custom_command('approve', 'approve_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('list', 'list_private_endpoint_connection')

    with self.command_group('iot central app private-link-resource', private_link_resource_sdk,
                            client_factory=iot_central_service_factory) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.custom_command('list', 'list_private_link_resource',
                         transform=gen_dict_to_list_transform(key="value"))
        g.custom_show_command('show', 'get_private_link_resource')
