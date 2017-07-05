# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.lab.validators import (validate_lab_vm_create,
                                                      validate_lab_vm_list,
                                                      validate_user_name,
                                                      validate_template_id,
                                                      validate_claim_vm,
                                                      _validate_artifacts)
from azure.cli.core.commands.parameters import resource_group_name_type
from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.util import get_json_object


with ParametersContext(command='lab') as c:
    c.argument('resource_group', arg_type=resource_group_name_type,
               help='Name of lab\'s resource group. You can configure the default group '
                    'using \'az configure --defaults group=<name>\'')

with ParametersContext(command='lab vm create') as c:
    c.register_alias('resource_group', ('--resource-group', '-g'), validator=validate_lab_vm_create)
    c.register_alias('name', ('--name', '-n'))

    # Authentication related arguments
    authentication_group_name = 'Authentication'
    c.argument('admin_username', arg_group=authentication_group_name)
    c.argument('admin_password', arg_group=authentication_group_name)
    c.argument('authentication_type', arg_group=authentication_group_name)
    c.argument('ssh_key', arg_group=authentication_group_name)
    c.argument('generate_ssh_keys', action='store_true', arg_group=authentication_group_name)
    c.argument('saved_secret', arg_group=authentication_group_name)

    # Add Artifacts from json object
    c.argument('artifacts', type=get_json_object)

    # Image related arguments
    c.ignore('os_type')
    c.ignore('gallery_image_reference')
    c.ignore('custom_image_id')
    c.argument('image')

    # Network related arguments
    network_group_name = 'Network'
    c.argument('ip_configuration', arg_group=network_group_name)
    c.argument('subnet', arg_group=network_group_name)
    c.argument('vnet_name', arg_group=network_group_name)
    c.ignore('lab_subnet_name')
    c.ignore('lab_virtual_network_id')
    c.ignore('disallow_public_ip_address')
    c.ignore('network_interface')

    # Creating VM in the different location then lab is an officially unsupported scenario
    c.ignore('location')

    c.argument('expiration_date')
    c.argument('formula')
    c.argument('allow_claim', action='store_true')


with ParametersContext(command='lab vm list') as c:
    filter_arg_group_name = 'Filter'
    c.argument('filters', arg_group=filter_arg_group_name)
    c.argument('all', action='store_true', arg_group=filter_arg_group_name)
    c.argument('claimable', action='store_true', arg_group=filter_arg_group_name)
    c.argument('environment', arg_group=filter_arg_group_name)
    c.register_alias('resource_group', ('--resource-group', '-g'), validator=validate_lab_vm_list)


with ParametersContext(command='lab vm claim') as c:
    c.register_alias('resource_group', ('--resource-group', '-g'), validator=validate_claim_vm)
    c.register_alias('name', ('--name', '-n'), id_part='child_name')
    c.argument('lab_name', id_part='name')


with ParametersContext(command='lab vm apply-artifacts') as c:
    c.register('artifacts', ('--artifacts',), type=get_json_object, validator=_validate_artifacts)
    c.register_alias('name', ('--name', '-n'))


with ParametersContext(command='lab formula') as c:
    c.register_alias('name', ('--name', '-n'))


with ParametersContext(command='lab secret') as c:
    from azure.mgmt.devtestlabs.models.secret import Secret

    c.register_alias('name', ('--name', '-n'))
    c.register_alias('secret', ('--value', ), type=lambda x: Secret(value=x))
    c.ignore('user_name')
    c.argument('lab_name', validator=validate_user_name)


with ParametersContext(command='lab formula export-artifacts') as c:
    # Exporting artifacts does not need expand filter
    c.ignore('expand')


with ParametersContext(command='lab environment') as c:
    c.register_alias('name', ('--name', '-n'))
    c.ignore('user_name')
    c.argument('lab_name', validator=validate_user_name)


with ParametersContext(command='lab environment create') as c:
    c.argument('arm_template', validator=validate_template_id)
    c.argument('parameters', type=get_json_object)

with ParametersContext(command='lab arm-template') as c:
    c.register_alias('name', ('--name', '-n'))

with ParametersContext(command='lab arm-template show') as c:
    c.argument('export_parameters', action='store_true')
