# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation, CliCommandType
from ._client_factory import iot_hub_service_factory


class PolicyUpdateResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(PolicyUpdateResultTransform, self).__call__(poller)
        return result.properties.authorization_policies


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
        return None


def load_command_table(self, _):

    update_custom_util = CliCommandType(operations_tmpl='azure.cli.command_modules.iot.custom#{}')

    # iot hub certificate commands
    with self.command_group('iot hub certificate', client_factory=iot_hub_service_factory) as g:
        g.custom_command('list', 'iot_hub_certificate_list')
        g.custom_command('show', 'iot_hub_certificate_get')
        g.custom_command('create', 'iot_hub_certificate_create')
        g.custom_command('delete', 'iot_hub_certificate_delete')
        g.custom_command('generate-verification-code', 'iot_hub_certificate_gen_code')
        g.custom_command('verify', 'iot_hub_certificate_verify')
        g.custom_command('update', 'iot_hub_certificate_update')

    # iot hub commands
    with self.command_group('iot hub', client_factory=iot_hub_service_factory) as g:
        g.custom_command('create', 'iot_hub_create')
        g.custom_command('list', 'iot_hub_list')
        g.custom_command('show-connection-string', 'iot_hub_show_connection_string')
        g.custom_command('show', 'iot_hub_get')
        g.generic_update_command('update', getter_name='iot_hub_get', setter_name='iot_hub_update',
                                 command_type=update_custom_util)
        g.custom_command('delete', 'iot_hub_delete', transform=HubDeleteResultTransform(self.cli_ctx))
        g.custom_command('list-skus', 'iot_hub_sku_list')
        g.custom_command('consumer-group create', 'iot_hub_consumer_group_create')
        g.custom_command('consumer-group list', 'iot_hub_consumer_group_list')
        g.custom_command('consumer-group show', 'iot_hub_consumer_group_get')
        g.custom_command('consumer-group delete', 'iot_hub_consumer_group_delete')
        g.custom_command('policy list', 'iot_hub_policy_list')
        g.custom_command('policy show', 'iot_hub_policy_get')
        g.custom_command('policy create', 'iot_hub_policy_create', transform=PolicyUpdateResultTransform(self.cli_ctx))
        g.custom_command('policy delete', 'iot_hub_policy_delete', transform=PolicyUpdateResultTransform(self.cli_ctx))
        g.custom_command('job list', 'iot_hub_job_list')
        g.custom_command('job show', 'iot_hub_job_get')
        g.custom_command('job cancel', 'iot_hub_job_cancel')
        g.custom_command('show-quota-metrics', 'iot_hub_get_quota_metrics')
        g.custom_command('show-stats', 'iot_hub_get_stats')

    # iot device commands
    with self.command_group('iot device', client_factory=iot_hub_service_factory) as g:
        g.custom_command('create', 'iot_device_create')
        g.custom_command('list', 'iot_device_list')
        g.custom_command('show-connection-string', 'iot_device_show_connection_string')
        g.custom_command('show', 'iot_device_get')
        g.generic_update_command('update', getter_name='iot_device_get', setter_name='iot_device_update',
                                 command_type=update_custom_util)
        g.custom_command('delete', 'iot_device_delete')
        g.custom_command('message send', 'iot_device_send_message')
        g.custom_command('message receive', 'iot_device_receive_message')
        g.custom_command('message complete', 'iot_device_complete_message')
        g.custom_command('message reject', 'iot_device_reject_message')
        g.custom_command('message abandon', 'iot_device_abandon_message')
        g.custom_command('export', 'iot_device_export')
        g.custom_command('import', 'iot_device_import')
