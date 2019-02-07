# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.lab.validators import validate_artifacts, validate_template_id
from azure.cli.core.util import get_json_object


def load_arguments(self, _):
    with self.argument_context('lab custom-image create') as c:
        c.argument('name', options_list=['--name', '-n'])

    with self.argument_context('lab vm create') as c:
        c.argument('name', options_list=['--name', '-n'])

        # Authentication related arguments
        for arg_name in ['admin_username', 'admin_password', 'authentication_type', 'ssh_key', 'generate_ssh_keys',
                         'saved_secret']:
            c.argument(arg_name, arg_group='Authentication')
        c.argument('generate_ssh_keys', action='store_true')

        # Add Artifacts from json object
        c.argument('artifacts', type=get_json_object)

        # Image related arguments
        c.ignore('os_type', 'gallery_image_reference', 'custom_image_id')

        # Network related arguments
        for arg_name in ['ip_configuration', 'subnet', 'vnet_name']:
            c.argument(arg_name, arg_group='Network')

        c.ignore('lab_subnet_name', 'lab_virtual_network_id', 'disallow_public_ip_address', 'network_interface')

        # Creating VM in the different location then lab is an officially unsupported scenario
        c.ignore('location')
        c.argument('allow_claim', action='store_true')

    with self.argument_context('lab vm list') as c:
        for arg_name in ['filters', 'all', 'claimable', 'environment']:
            c.argument(arg_name, arg_group='Filter')

        for arg_name in ['all', 'claimable']:
            c.argument(arg_name, action='store_true')

    with self.argument_context('lab vm claim') as c:
        c.argument('name', options_list=['--name', '-n'], id_part='child_name_1')
        c.argument('lab_name', id_part='name')

    with self.argument_context('lab vm apply-artifacts') as c:
        c.argument('artifacts', type=get_json_object, validator=validate_artifacts)
        c.argument('name', options_list=['--name', '-n'])

    with self.argument_context('lab formula') as c:
        c.argument('name', options_list=['--name', '-n'])

    with self.argument_context('lab secret') as c:
        from azure.mgmt.devtestlabs.models import Secret

        c.argument('name', options_list=['--name', '-n'])
        c.argument('secret', options_list=['--value'], type=lambda x: Secret(value=x))
        c.ignore('user_name')

    with self.argument_context('lab formula export-artifacts') as c:
        # Exporting artifacts does not need expand filter
        c.ignore('expand')

    with self.argument_context('lab environment') as c:
        c.argument('name', options_list=['--name', '-n'])
        c.ignore('user_name')

    with self.argument_context('lab environment create') as c:
        c.argument('arm_template', validator=validate_template_id)
        c.argument('parameters', type=get_json_object)

    with self.argument_context('lab arm-template') as c:
        c.argument('name', options_list=['--name', '-n'])

    with self.argument_context('lab arm-template show') as c:
        c.argument('export_parameters', action='store_true')
