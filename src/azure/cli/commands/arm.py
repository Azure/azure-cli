#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import re
from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.cli.application import APPLICATION, IterateValue
from azure.cli._util import CLIError


regex = re.compile('/subscriptions/(?P<subscription>[^/]*)/resourceGroups/(?P<resource_group>[^/]*)'
                   '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
                   '(/(?P<child_type>[^/]*)/(?P<child_name>[^/]*))?')

def resource_id(**kwargs):
    '''Create a valid resource id string from the given parts

    The method accepts the following keyword arguments:

        - subscription      Subscription id
        - resource_group    Name of resource group
        - namespace         Namespace for the resource provider (i.e. Microsoft.Compute)
        - type              Type of the resource (i.e. virtualMachines)
        - name              Name of the resource (or parent if child_name is also specified)
        - child_type        Type of the child resource
        - child_name        Name of the child resource
    '''
    rid = '/subscriptions/{subscription}'.format(**kwargs)
    try:
        rid = '/'.join((rid, 'resourceGroups/{resource_group}'.format(**kwargs)))
        rid = '/'.join((rid, 'providers/{namespace}'.format(**kwargs)))
        rid = '/'.join((rid, '{type}/{name}'.format(**kwargs)))
        rid = '/'.join((rid, '{child_type}/{child_name}'.format(**kwargs)))
    except KeyError:
        pass
    return rid

def parse_resource_id(rid):
    '''Build a dictionary with the following key/value pairs (if found)

        - subscription      Subscription id
        - resource_group    Name of resource group
        - namespace         Namespace for the resource provider (i.e. Microsoft.Compute)
        - type              Type of the resource (i.e. virtualMachines)
        - name              Name of the resource (or parent if child_name is also specified)
        - child_type        Type of the child resource
        - child_name        Name of the child resource
    '''
    m = regex.match(rid)
    if m:
        result = m.groupdict()
    else:
        result = dict(name=rid)

    return {key:value for key, value in result.items() if value is not None}

def is_valid_resource_id(rid, exception_type=None):
    is_valid = False
    try:
        is_valid = rid and resource_id(**parse_resource_id(rid)) == rid
    except KeyError:
        pass
    if not is_valid and exception_type:
        raise exception_type()
    return is_valid

class ResourceId(str):

    def __new__(cls, val):
        if not is_valid_resource_id(val):
            raise ValueError()
        return str.__new__(cls, val)

def resource_exists(resource_group, name, namespace, type, **_): # pylint: disable=redefined-builtin
    '''Checks if the given resource exists.
    '''
    odata_filter = "resourceGroup eq '{}' and name eq '{}'" \
        " and resourceType eq '{}/{}'".format(resource_group, name, namespace, type)
    client = get_mgmt_service_client(ResourceManagementClient).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing

def add_id_parameters(command_table):

    def split_action(arguments):
        class SplitAction(argparse.Action): #pylint: disable=too-few-public-methods

            def __call__(self, parser, namespace, values, option_string=None):
                ''' The SplitAction will take the given ID parameter and spread the parsed
                parts of the id into the individual backing fields.

                Since the id value is expected to be of type `IterateValue`, all the backing
                (dest) fields will also be of type `IterateValue`
                '''
                try:
                    for value in [values] if isinstance(values, str) else values:
                        parts = parse_resource_id(value)
                        for arg in [arg for arg in arguments.values() if arg.id_part]:
                            existing_values = getattr(namespace, arg.name, None)
                            if existing_values is None:
                                existing_values = IterateValue()
                            existing_values.append(parts[arg.id_part])
                            setattr(namespace, arg.name, existing_values)
                except Exception as ex:
                    raise ValueError(ex)

        return SplitAction

    def command_loaded_handler(command):
        if not 'name' in [arg.id_part for arg in command.arguments.values() if arg.id_part]:
            # Only commands with a resource name are candidates for an id parameter
            return
        if command.name.split()[-1] == 'create':
            # Somewhat blunt hammer, but any create commands will not have an automatic id
            # parameter
            return

        required_arguments = []
        optional_arguments = []
        for arg in [argument for argument in command.arguments.values() if argument.id_part]:
            if arg.options.get('required', False):
                required_arguments.append(arg)
            else:
                optional_arguments.append(arg)
            arg.required = False

        def required_values_validator(namespace):
            errors = [arg for arg in required_arguments
                      if getattr(namespace, arg.name, None) is None]

            if errors:
                missing_required = ' '.join((arg.options_list[0] for arg in errors))
                raise CLIError('({} | {}) are required'.format(missing_required, '--ids'))

        command.add_argument(argparse.SUPPRESS,
                             '--ids',
                             metavar='RESOURCE_ID',
                             help='ID of resource',
                             action=split_action(command.arguments),
                             nargs='+',
                             type=ResourceId,
                             validator=required_values_validator)

    for command in command_table.values():
        command_loaded_handler(command)

    APPLICATION.remove(APPLICATION.COMMAND_TABLE_LOADED, add_id_parameters)

APPLICATION.register(APPLICATION.COMMAND_TABLE_LOADED, add_id_parameters)
