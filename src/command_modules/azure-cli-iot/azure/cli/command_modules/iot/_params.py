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
from azure.mgmt.iothub.models import IotHubSku
from azure.mgmt.iothubprovisioningservices.models import (IotDpsSku,
                                                          AllocationPolicy,
                                                          AccessRightsDescription)

from .custom import KeyType, SimpleAccessRights
from ._validators import validate_policy_permissions


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
    with self.argument_context('iot hub') as c:
        c.argument('hub_name', hub_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('etag', options_list=['--etag', '-e'], help='Entity Tag (etag) of the object.')

    for subgroup in ['consumer-group', 'policy', 'job', 'certificate']:
        with self.argument_context('iot hub {}'.format(subgroup)) as c:
            c.argument('hub_name', options_list=['--hub-name'])

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
        c.argument('partition_count',
                   help='The number of partitions of the backing Event Hub for device-to-cloud messages.', type=int)

    with self.argument_context('iot hub show-connection-string') as c:
        c.argument('policy_name', help='Shared access policy to use.')
        c.argument('key_type', arg_type=get_enum_type(KeyType), options_list=['--key'], help='The key to use.')
