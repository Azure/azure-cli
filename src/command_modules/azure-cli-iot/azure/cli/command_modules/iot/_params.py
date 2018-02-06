# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter
from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (get_location_type,
                                                file_type,
                                                get_resource_name_completion_list,
                                                get_enum_type,
                                                get_three_state_flag)
from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku
from azure.mgmt.iothubprovisioningservices.models.iot_dps_client_enums import (IotDpsSku,
                                                                               AllocationPolicy,
                                                                               AccessRightsDescription)

from .custom import KeyType, SimpleAccessRights
from ._validators import validate_policy_permissions
from ._completers import get_device_id_completion_list


hub_name_type = CLIArgumentType(
    completer=get_resource_name_completion_list('Microsoft.Devices/IotHubs'),
    help='IoT Hub name.')

dps_name_type = CLIArgumentType(
    options_list=['--dps-name'],
    completer=get_resource_name_completion_list('Microsoft.Devices/ProvisioningServices'),
    help='IoT Provisioning Service name')


def load_arguments(self, _):  # pylint: disable=too-many-statements
    # Arguments for IoT DPS
    with self.argument_context('iot dps') as c:
        c.argument('dps_name', dps_name_type, options_list=['--name', '-n'], id_part='name')

    with self.argument_context('iot dps create') as c:
        c.argument('location', get_location_type(self.cli_ctx),
                   help='Location of your IoT Provisioning Service. Default is the location of target resource group.')
        c.argument('sku', arg_type=get_enum_type(IotDpsSku),
                   help='Pricing tier for the IoT provisioning service.')
        c.argument('unit', help='Units in your IoT Provisioning Service.', type=int)

    for subgroup in ['access-policy', 'linked-hub', 'certificate']:
        with self.argument_context('iot dps {}'.format(subgroup)) as c:
            c.argument('dps_name', options_list=['--dps-name'], id_part=None)

    with self.argument_context('iot dps access-policy') as c:
        c.argument('access_policy_name', options_list=['--access-policy-name', '--name', '-n'],
                   help='A friendly name for DPS access policy.')

    with self.argument_context('iot dps access-policy create') as c:
        c.argument('rights', options_list=['--rights', '-r'], nargs='+',
                   arg_type=get_enum_type(AccessRightsDescription),
                   help='Access rights for the IoT provisioning service. Use space-separated list for multiple rights.')
        c.argument('primary_key', help='Primary SAS key value.')
        c.argument('secondary_key', help='Secondary SAS key value.')

    with self.argument_context('iot dps access-policy update') as c:
        c.argument('rights', options_list=['--rights', '-r'], nargs='+',
                   arg_type=get_enum_type(AccessRightsDescription),
                   help='Access rights for the IoT provisioning service. Use space-separated list for multiple rights.')
        c.argument('primary_key', help='Primary SAS key value.')
        c.argument('secondary_key', help='Secondary SAS key value.')

    with self.argument_context('iot dps linked-hub') as c:
        c.argument('linked_hub', options_list=['--linked-hub'], help='Host name of linked IoT Hub.')

    with self.argument_context('iot dps linked-hub create') as c:
        c.argument('connection_string', help='Connection string of the IoT hub.')
        c.argument('location', get_location_type(self.cli_ctx),
                   help='Location of the IoT hub.')
        c.argument('apply_allocation_policy',
                   help='A boolean indicating whether to apply allocation policy to the IoT hub.',
                   arg_type=get_three_state_flag())
        c.argument('allocation_weight', help='Allocation weight of the IoT hub.')

    with self.argument_context('iot dps linked-hub update') as c:
        c.argument('apply_allocation_policy',
                   help='A boolean indicating whether to apply allocation policy to the Iot hub.',
                   arg_type=get_three_state_flag())
        c.argument('allocation_weight', help='Allocation weight of the IoT hub.')

    with self.argument_context('iot dps allocation-policy update') as c:
        c.argument('allocation_policy', options_list=['--policy', '-p'], arg_type=get_enum_type(AllocationPolicy),
                   help='Allocation policy for the IoT provisioning service.')

    with self.argument_context('iot dps certificate') as c:
        c.argument('certificate_path', options_list=['--path', '-p'], type=file_type,
                   completer=FilesCompleter([".cer", ".pem"]), help='The path to the file containing the certificate.')
        c.argument('certificate_name', options_list=['--certificate-name', '--name', '-n'],
                   help='A friendly name for the certificate.')
        c.argument('etag', options_list=['--etag', '-e'], help='Entity Tag (etag) of the object.')

    # Arguments for IoT Hub
    with self.argument_context('iot') as c:
        c.argument('device_id', options_list=['--device-id', '-d'], help='Device Id.',
                   completer=get_device_id_completion_list)

    with self.argument_context('iot hub') as c:
        c.argument('hub_name', hub_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('etag', options_list=['--etag', '-e'], help='Entity Tag (etag) of the object.')

    for subgroup in ['consumer-group', 'policy', 'job', 'certificate']:
        with self.argument_context('iot hub {}'.format(subgroup)) as c:
            c.argument('hub_name', options_list=['--hub-name'])

    with self.argument_context('iot device') as c:
        c.argument('hub_name', hub_name_type)

    with self.argument_context('iot hub certificate') as c:
        c.argument('certificate_path', options_list=['--path', '-p'], type=file_type,
                   completer=FilesCompleter([".cer", ".pem"]), help='The path to the file containing the certificate.')
        c.argument('certificate_name', options_list=['--name', '-n'], help='A friendly name for the certificate.')

    with self.argument_context('iot hub consumer-group') as c:
        c.argument('consumer_group_name', options_list=['--name', '-n'], id_part='child_name_2',
                   help='Event hub consumer group name.')
        c.argument('event_hub_name', id_part='child_name_1', help='Event hub endpoint name.')

    with self.argument_context('iot hub policy') as c:
        c.argument('policy_name', options_list=['--name', '-n'], id_part='child_name_1',
                   help='Shared access policy name.')
        permission_values = ', '.join([x.value for x in SimpleAccessRights])
        c.argument('permissions', nargs='*', validator=validate_policy_permissions, type=str.lower,
                   help='Permissions of shared access policy. Use space-separated list for multiple permissions. '
                        'Possible values: {}'.format(permission_values))

    with self.argument_context('iot hub job') as c:
        c.argument('job_id', id_part='child_name_1', help='Job Id.')

    with self.argument_context('iot hub create') as c:
        c.argument('hub_name', completer=None)
        c.argument('location', get_location_type(self.cli_ctx),
                   help='Location of your IoT Hub. Default is the location of target resource group.')
        c.argument('sku', arg_type=get_enum_type(IotHubSku),
                   help='Pricing tier for Azure IoT Hub. Default value is F1, which is free. '
                        'Note that only one free IoT hub instance is allowed in each '
                        'subscription. Exception will be thrown if free instances exceed one.')
        c.argument('unit', help='Units in your IoT Hub.', type=int)
        c.argument('partition_count', help='The number of partitions for device-to-cloud messages.', type=int)

    with self.argument_context('iot hub show-connection-string') as c:
        c.argument('policy_name', help='Shared access policy to use.')
        c.argument('key_type', arg_type=get_enum_type(KeyType), options_list=['--key'], help='The key to use.')

    with self.argument_context('iot device create') as c:
        c.argument('device_id', completer=None)

    with self.argument_context('iot device create', arg_group='X.509 Certificate') as c:
        c.argument('x509', action='store_true', help='Use X.509 certificate for device authentication.')
        c.argument('primary_thumbprint', help='Primary X.509 certificate thumbprint to authenticate device.')
        c.argument('secondary_thumbprint', help='Secondary X.509 certificate thumbprint to authenticate device.')
        c.argument('valid_days', type=int, help='Number of days the generated self-signed X.509 certificate should be '
                                                'valid for. Default validity is 365 days.')
        c.argument('output_dir', help='Output directory for generated self-signed X.509 certificate. '
                                      'Default is current working directory.')

    with self.argument_context('iot device list') as c:
        c.argument('top', help='Maximum number of device identities to return.', type=int)

    with self.argument_context('iot device delete') as c:
        c.argument('etag', help='ETag of the target device. It is used for the purpose of optimistic '
                                'concurrency. Delete operation will be performed only if the specified '
                                'ETag matches the value maintained by the server, indicating that the '
                                'device identity has not been modified since it was retrieved. Default '
                                'value is set to wildcard character (*) to force an unconditional '
                                'delete.')

    with self.argument_context('iot device show-connection-string') as c:
        c.argument('top', type=int, help='Maximum number of connection strings to return.')
        c.argument('key_type', arg_type=get_enum_type(KeyType), options_list=['--key'], help='The key to use.')

    with self.argument_context('iot device message') as c:
        c.argument('lock_token', help='Message lock token.')

    with self.argument_context('iot device message send', arg_group='Messaging') as c:
        c.argument('data', help='Device-to-cloud message body.')
        c.argument('message_id', help='Device-to-cloud message Id.')
        c.argument('correlation_id', help='Device-to-cloud message correlation Id.')
        c.argument('user_id', help='Device-to-cloud message user Id.')

    with self.argument_context('iot device message receive') as c:
        c.argument('lock_timeout', type=int,
                   help='In case a message returned to this call, this specifies the amount of '
                        'time in seconds, the message will be invisible to other receive calls.')

    with self.argument_context('iot device export') as c:
        c.argument('blob_container_uri',
                   help='Blob Shared Access Signature URI with write access to a blob container.'
                        'This is used to output the status of the job and the results.')
        c.argument('include_keys', action='store_true',
                   help='If set, keys are exported normally. Otherwise, keys are set to null in '
                        'export output.')

    with self.argument_context('iot device import') as c:
        c.argument('input_blob_container_uri',
                   help='Blob Shared Access Signature URI with read access to a blob container.'
                        'This blob contains the operations to be performed on the identity '
                        'registry ')
        c.argument('output_blob_container_uri',
                   help='Blob Shared Access Signature URI with write access to a blob container.'
                        'This is used to output the status of the job and the results.')
