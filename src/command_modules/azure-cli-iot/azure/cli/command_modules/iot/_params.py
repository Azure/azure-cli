# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import (location_type, enum_choice_list,
                                                get_resource_name_completion_list, CliArgumentType)
from azure.cli.core.commands import register_cli_argument
from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku
from ._factory import iot_hub_service_factory
from .custom import iot_device_list, KeyType, SimpleAccessRights
from ._validators import validate_policy_permissions


def get_device_id_completion_list(prefix, action, parsed_args,
                                  **kwargs):  # pylint: disable=unused-argument
    client = iot_hub_service_factory(kwargs)
    return [d.device_id for d in
            iot_device_list(client, parsed_args.hub_name, top=100)] if parsed_args.hub_name else []


hub_name_type = CliArgumentType(
    completer=get_resource_name_completion_list('Microsoft.Devices/IotHubs'),
    help='IoT Hub name.')

register_cli_argument('iot hub', 'hub_name', hub_name_type, options_list=('--name', '-n'),
                      id_part='name')
for subgroup in ['consumer-group', 'policy', 'job']:
    register_cli_argument('iot hub {}'.format(subgroup), 'hub_name', options_list=('--hub-name',))

register_cli_argument('iot device', 'hub_name', hub_name_type)

register_cli_argument('iot', 'device_id', options_list=('--device-id', '-d'), help='Device Id.',
                      completer=get_device_id_completion_list)

# Arguments for 'iot hub consumer-group' group
register_cli_argument('iot hub consumer-group', 'consumer_group_name',
                      options_list=('--name', '-n'),
                      id_part='grandchild_name', help='Event hub consumer group name.')
register_cli_argument('iot hub consumer-group', 'event_hub_name', id_part='child_name',
                      help='Event hub endpoint name.')

# Arguments for 'iot hub policy' group
register_cli_argument('iot hub policy', 'policy_name', options_list=('--name', '-n'),
                      id_part='child_name',
                      help='Shared access policy name.')

permission_values = ', '.join([x.value for x in SimpleAccessRights])
register_cli_argument('iot hub policy', 'permissions', nargs='*',
                      validator=validate_policy_permissions, type=str.lower,
                      help='Permissions of shared access policy. Use space separated list for '
                           'multiple permissions. Possible values: {}'.format(permission_values))

# Arguments for 'iot hub job' group
register_cli_argument('iot hub job', 'job_id', id_part='child_name', help='Job Id.')

# Arguments for 'iot hub create'
register_cli_argument('iot hub create', 'hub_name', completer=None)
register_cli_argument('iot hub create', 'location', location_type,
                      help='Location of your IoT Hub. Default is the location of target resource '
                           'group.')
register_cli_argument('iot hub create', 'sku',
                      help='Pricing tier for Azure IoT Hub. Default value is F1, which is free. '
                           'Note that only one free IoT Hub instance is allowed in each '
                           'subscription. Exception will be thrown if free instances exceed one.',
                      **enum_choice_list(IotHubSku))
register_cli_argument('iot hub create', 'unit', help='Units in your IoT Hub.', type=int)

# Arguments for 'iot hub show-connection-string'
register_cli_argument('iot hub show-connection-string', 'policy_name',
                      help='Shared access policy to use.')
register_cli_argument('iot hub show-connection-string', 'key_type', options_list=('--key',),
                      help='The key to use.',
                      **enum_choice_list(KeyType))

# Arguments for 'iot device create'
register_cli_argument('iot device create', 'device_id', completer=None)
register_cli_argument('iot device create', 'x509', action='store_true',
                      arg_group='X.509 Certificate',
                      help='Use X.509 certificate for device authentication.')
register_cli_argument('iot device create', 'primary_thumbprint', arg_group='X.509 Certificate',
                      help='Primary X.509 certificate thumbprint to authenticate device.')
register_cli_argument('iot device create', 'secondary_thumbprint', arg_group='X.509 Certificate',
                      help='Secondary X.509 certificate thumbprint to authenticate device.')
register_cli_argument('iot device create', 'valid_days', type=int, arg_group='X.509 Certificate',
                      help='Number of days the generated self-signed X.509 certificate should be '
                           'valid for. Default validity is 365 days.')
register_cli_argument('iot device create', 'output_dir', arg_group='X.509 Certificate',
                      help='Output directory for generated self-signed X.509 certificate. '
                           'Default is current working directory.')

# Arguments for 'iot device list'
register_cli_argument('iot device list', 'top',
                      help='Maximum number of device identities to return.', type=int)

# Arguments for 'iot device delete'
register_cli_argument('iot device delete', 'etag',
                      help='ETag of the target device. It is used for the purpose of optimistic '
                           'concurrency. Delete operation will be performed only if the specified '
                           'ETag matches the value maintained by the server, indicating that the '
                           'device identity has not been modified since it was retrieved. Default '
                           'value is set to wildcard character (*) to force an unconditional '
                           'delete.')

# Arguments for 'iot device show-connection-string'
register_cli_argument('iot device show-connection-string', 'top', type=int,
                      help='Maximum number of connection strings to return.')
register_cli_argument('iot device show-connection-string', 'key_type', options_list=('--key',),
                      help='The key to use.',
                      **enum_choice_list(KeyType))

# Arguments for 'iot device message' group
register_cli_argument('iot device message', 'lock_token', help='Message lock token.')

# Arguments for 'iot device message send'
register_cli_argument('iot device message send', 'data', help='Device-to-cloud message body.',
                      arg_group='Messaging')
register_cli_argument('iot device message send', 'message_id', help='Device-to-cloud message Id.',
                      arg_group='Messaging')
register_cli_argument('iot device message send', 'correlation_id',
                      help='Device-to-cloud message correlation Id.',
                      arg_group='Messaging')
register_cli_argument('iot device message send', 'user_id', help='Device-to-cloud message user Id.',
                      arg_group='Messaging')

# Arguments for 'iot device message receive'
register_cli_argument('iot device message receive', 'lock_timeout', type=int,
                      help='In case a message returned to this call, this specifies the amount of '
                           'time in seconds, the message will be invisible to other receive calls.')

# Arguments for 'iot device export'
register_cli_argument('iot device export', 'blob_container_uri',
                      help='Blob Shared Access Signature URI with write access to a blob container.'
                           'This is used to output the status of the job and the results.')
register_cli_argument('iot device export', 'include_keys', action='store_true',
                      help='If set, keys are exported normally. Otherwise, keys are set to null in '
                           'export output.')

# Arguments for 'iot device import'
register_cli_argument('iot device import', 'input_blob_container_uri',
                      help='Blob Shared Access Signature URI with read access to a blob container.'
                           'This blob contains the operations to be performed on the identity '
                           'registry ')
register_cli_argument('iot device import', 'output_blob_container_uri',
                      help='Blob Shared Access Signature URI with write access to a blob container.'
                           'This is used to output the status of the job and the results.')
