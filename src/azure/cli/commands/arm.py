#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import re
import json

from msrestazure.azure_operation import AzureOperationPoller
from azure.cli.commands import CliCommand, command_table as main_command_table
from azure.cli.commands._introspection import extract_args_from_signature
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

def register_generic_update(name, getter, setter, factory=None, setter_arg_name='parameters', #pylint:disable=too-many-arguments
                            simple_output_query=None):

    get_arguments = dict(extract_args_from_signature(getter))
    set_arguments = dict(extract_args_from_signature(setter))

    def handler(args):
        ordered_arguments = args.pop('ordered_arguments')

        try:
            client = factory() if factory else None
        except TypeError:
            client = factory(None) if factory else None

        getterargs = {key: val for key, val in args.items()
                      if key in get_arguments}
        instance = getter(client, **getterargs) if client else getter(**getterargs)

        # Update properties
        for arg in ordered_arguments:
            arg_type, expressions = arg
            if arg_type == '--set':
                try:
                    for expression in expressions:
                        set_properties(instance, expression)
                except ValueError:
                    raise CLIError('--set should be of the form:'
                                   ' --set property.property=<value>'
                                   ' property2.property=<value>')
            elif arg_type == '--add':
                try:
                    add_properties(instance, expressions)
                except ValueError:
                    raise CLIError('--add should be of the form:'
                                   ' --add property.list key1=value1 key2=value2')
            elif arg_type == '--remove':
                try:
                    remove_properties(instance, expressions)
                except ValueError:
                    raise CLIError('--remove should be of the form: --remove'
                                   ' property.propertyToRemove or'
                                   ' --remove property.list <indexToRemove>')
            else:
                raise ValueError('Unsupported arg type {}'.format(arg_type))

        # Done... update the instance!
        getterargs[setter_arg_name] = instance
        opres = setter(client, **getterargs) if client else setter(**getterargs)
        return opres.result() if isinstance(opres, AzureOperationPoller) else opres

    class OrderedArgsAction(argparse.Action): #pylint:disable=too-few-public-methods
        def __call__(self, parser, namespace, values, option_string=None):
            if not getattr(namespace, 'ordered_arguments', None):
                setattr(namespace, 'ordered_arguments', [])
            namespace.ordered_arguments.append((option_string, values))

    def one_required(namespace):
        if not getattr(namespace, 'ordered_arguments', None):
            raise ValueError('At least one must be specified: --add, --set, --remove')

    cmd = CliCommand(name, handler, simple_output_query=simple_output_query)
    cmd.arguments.update(set_arguments)
    cmd.arguments.update(get_arguments)
    cmd.arguments.pop(setter_arg_name, None)
    cmd.add_argument('properties_to_set', '--set', nargs='+', action=OrderedArgsAction, default=[],
                     help='Update an object by specifying a property path and value to set.'
                     '  Example: --set property1.property2=value',
                     metavar='KEY=VALUE')
    cmd.add_argument('properties_to_add', '--add', nargs='+', action=OrderedArgsAction, default=[],
                     help='Add an object to a list of objects by specifying a path and key'
                     ' value pairs.  Example: --add property.list key=<value>',
                     metavar='LIST KEY=VALUE')
    cmd.add_argument('properties_to_remove', '--remove', nargs='+', action=OrderedArgsAction,
                     default=[], help='Remove a property or an element from a list.  Example: '
                     '--remove property.list <index>', metavar='LIST INDEX',
                     validator=one_required)
    main_command_table[name] = cmd

index_regex = re.compile(r'\[(.*)\]')
def set_properties(instance, expression):
    key, value = expression.split('=', 1)

    try:
        value = json.loads(value)
    except: #pylint:disable=bare-except
        pass

    name, path = _get_name_path(key)
    root = instance
    instance = _find_property(instance, path)
    if instance is None:
        parent = _find_property(root, path[:-1])
        set_properties(parent, '{}={{}}'.format(path[-1]))
        instance = _find_property(root, path)

    match = index_regex.match(name)
    index_value = int(match.group(1)) if match else None
    try:
        if index_value is not None:
            instance[index_value] = value
        elif isinstance(instance, dict):
            instance[name] = value
        else:
            setattr(instance, name, value)
    except IndexError:
        raise CLIError('index {} doesn\'t exist on {}'.format(index_value, make_camel_case(name)))
    except (AttributeError, KeyError):
        show_options(instance, name, key.split('.'))

def add_properties(instance, argument_values):
    # The first argument indicates the path to the collection to add to.
    list_attribute_path = _get_internal_path(argument_values.pop(0))
    list_to_add_to = _find_property(instance, list_attribute_path)

    if list_to_add_to is None:
        parent = _find_property(instance, list_attribute_path[:-1])
        set_properties(parent, '{}=[]'.format(list_attribute_path[-1]))
        list_to_add_to = _find_property(instance, list_attribute_path)

    new_value = {}
    for expression in argument_values:
        set_properties(new_value, expression)
    list_to_add_to.append(new_value)

def remove_properties(instance, argument_values):
    # The first argument indicates the path to the collection to add to.
    argument_values = argument_values if isinstance(argument_values, list) else [argument_values]

    list_attribute_path = _get_internal_path(argument_values.pop(0))
    list_index = None
    try:
        list_index = argument_values.pop(0)
    except IndexError:
        pass

    if not list_index:
        _find_property(instance, list_attribute_path)
        parent_to_remove_from = _find_property(instance, list_attribute_path[:-1])
        del parent_to_remove_from[list_attribute_path[-1]]
    else:
        list_to_remove_from = _find_property(instance, list_attribute_path)
        try:
            list_to_remove_from.pop(int(list_index))
        except IndexError:
            raise CLIError('index {} doesn\'t exist on {}'
                           .format(list_index,
                                   make_camel_case(list_attribute_path[-1])))

def show_options(instance, part, path):
    options = instance.__dict__ if hasattr(instance, '__dict__') else instance
    options = options.keys() if isinstance(options, dict) else options
    options = [make_camel_case(x) for x in options]
    raise CLIError('Couldn\'t find "{}" in "{}".  Available options: {}'
                   .format(make_camel_case(part),
                           make_camel_case('.'.join(path[:-1]).replace('.[', '[')),
                           sorted(list(options), key=str)))

snake_regex_1 = re.compile('(.)([A-Z][a-z]+)')
snake_regex_2 = re.compile('([a-z0-9])([A-Z])')
def make_snake_case(s):
    if isinstance(s, str):
        s1 = re.sub(snake_regex_1, r'\1_\2', s)
        return re.sub(snake_regex_2, r'\1_\2', s1).lower()
    return s

def make_camel_case(s):
    if isinstance(s, str):
        parts = s.split('_')
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
    return s

def _get_internal_path(path):
    # to handle indexing in the same way as other dot qualifiers,
    # we split paths like foo[0][1] into foo.[0].[1]
    _path = path.split('.') \
        if '.[' in path \
        else path.replace('[', '.[').split('.')
    return [make_snake_case(x) for x in _path]

def _get_name_path(path):
    pathlist = _get_internal_path(path)
    return pathlist.pop(), pathlist

def _update_instance(instance, part, path):
    try:
        index = index_regex.match(part)
        if index:
            try:
                index_value = int(index.group(1))
                instance = instance[index_value]
            except IndexError:
                raise CLIError('index {} doesn\'t exist on {}'.format(index_value,
                                                                      make_camel_case(path[-2])))
        elif isinstance(instance, dict):
            instance = instance[part]
        else:
            instance = getattr(instance, part)
    except (AttributeError, KeyError):
        show_options(instance, part, path)
    return instance

def _find_property(instance, path):
    for part in path:
        instance = _update_instance(instance, part, path)
    return instance

