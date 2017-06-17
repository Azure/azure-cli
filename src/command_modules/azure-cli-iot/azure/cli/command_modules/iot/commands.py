# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.commands import LongRunningOperation
from ._factory import iot_hub_service_factory as factory

custom_path = 'azure.cli.command_modules.iot.custom#{0}'


class PolicyUpdateResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    def __call__(self, poller):
        result = super(PolicyUpdateResultTransform, self).__call__(poller)
        return result.properties.authorization_policies


# Deleting IoT Hub is a long running operation. Due to API implementation issue, 404 error will be thrown during
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


# iot hub commands
cli_command(__name__, 'iot hub create', custom_path.format('iot_hub_create'), factory)
cli_command(__name__, 'iot hub list', custom_path.format('iot_hub_list'), factory)
cli_command(__name__, 'iot hub show-connection-string',
            custom_path.format('iot_hub_show_connection_string'), factory)
cli_command(__name__, 'iot hub show', custom_path.format('iot_hub_get'), factory)
cli_generic_update_command(__name__, 'iot hub update', custom_path.format('iot_hub_get'),
                           custom_path.format('iot_hub_update'), factory)
cli_command(__name__, 'iot hub delete', custom_path.format('iot_hub_delete'), factory,
            transform=HubDeleteResultTransform())
cli_command(__name__, 'iot hub list-skus', custom_path.format('iot_hub_sku_list'), factory)
cli_command(__name__, 'iot hub consumer-group create',
            custom_path.format('iot_hub_consumer_group_create'), factory)
cli_command(__name__, 'iot hub consumer-group list',
            custom_path.format('iot_hub_consumer_group_list'), factory)
cli_command(__name__, 'iot hub consumer-group show',
            custom_path.format('iot_hub_consumer_group_get'), factory)
cli_command(__name__, 'iot hub consumer-group delete',
            custom_path.format('iot_hub_consumer_group_delete'), factory)
cli_command(__name__, 'iot hub policy list', custom_path.format('iot_hub_policy_list'), factory)
cli_command(__name__, 'iot hub policy show', custom_path.format('iot_hub_policy_get'), factory)
cli_command(__name__, 'iot hub policy create', custom_path.format('iot_hub_policy_create'), factory,
            transform=PolicyUpdateResultTransform())
cli_command(__name__, 'iot hub policy delete', custom_path.format('iot_hub_policy_delete'), factory,
            transform=PolicyUpdateResultTransform())
cli_command(__name__, 'iot hub job list', custom_path.format('iot_hub_job_list'), factory)
cli_command(__name__, 'iot hub job show', custom_path.format('iot_hub_job_get'), factory)
cli_command(__name__, 'iot hub job cancel', custom_path.format('iot_hub_job_cancel'), factory)
cli_command(__name__, 'iot hub show-quota-metrics', custom_path.format('iot_hub_get_quota_metrics'),
            factory)
cli_command(__name__, 'iot hub show-stats', custom_path.format('iot_hub_get_stats'), factory)

# iot device commands
cli_command(__name__, 'iot device create', custom_path.format('iot_device_create'), factory)
cli_command(__name__, 'iot device list', custom_path.format('iot_device_list'), factory)
cli_command(__name__, 'iot device show-connection-string',
            custom_path.format('iot_device_show_connection_string'), factory)
cli_command(__name__, 'iot device show', custom_path.format('iot_device_get'), factory)
cli_generic_update_command(__name__, 'iot device update', custom_path.format('iot_device_get'),
                           custom_path.format('iot_device_update'), factory)
cli_command(__name__, 'iot device delete', custom_path.format('iot_device_delete'), factory)
cli_command(__name__, 'iot device message send', custom_path.format('iot_device_send_message'),
            factory)
cli_command(__name__, 'iot device message receive',
            custom_path.format('iot_device_receive_message'), factory)
cli_command(__name__, 'iot device message complete',
            custom_path.format('iot_device_complete_message'), factory)
cli_command(__name__, 'iot device message reject', custom_path.format('iot_device_reject_message'),
            factory)
cli_command(__name__, 'iot device message abandon',
            custom_path.format('iot_device_abandon_message'), factory)
cli_command(__name__, 'iot device export', custom_path.format('iot_device_export'), factory)
cli_command(__name__, 'iot device import', custom_path.format('iot_device_import'), factory)
