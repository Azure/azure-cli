#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import re
import json

from azure.cli.core.commands import CliCommand, command_table as main_command_table
from azure.cli.core.commands._introspection import extract_args_from_signature
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.application import APPLICATION, IterateValue
import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError

logger = _logging.get_az_logger(__name__)

regex = re.compile('/subscriptions/(?P<subscription>[^/]*)/resourceGroups/(?P<resource_group>[^/]*)'
                   '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
                   '(/(?P<child_type>[^/]*)/(?P<child_name>[^/]*))?'
                   '(/(?P<grandchild_type>[^/]*)/(?P<grandchild_name>[^/]*))?')

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
        - grandchild_type   Type of the grandchild resource
        - grandchild_name   Name of the grandchild resource
    '''
    rid = '/subscriptions/{subscription}'.format(**kwargs)
    try:
        rid = '/'.join((rid, 'resourceGroups/{resource_group}'.format(**kwargs)))
        rid = '/'.join((rid, 'providers/{namespace}'.format(**kwargs)))
        rid = '/'.join((rid, '{type}/{name}'.format(**kwargs)))
        rid = '/'.join((rid, '{child_type}/{child_name}'.format(**kwargs)))
        rid = '/'.join((rid, '{grandchild_type}/{grandchild_name}'.format(**kwargs)))
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
        - grandchild_type   Type of the grandchild resource
        - grandchild_name   Name of the grandchild resource
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
    from azure.mgmt.resource.resources import ResourceManagementClient

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

        group_name = 'Resource Id'
        for key, arg in command.arguments.items():
            if command.arguments[key].id_part:
                command.arguments[key].arg_group = group_name

        command.add_argument('ids',
                             '--ids',
                             metavar='RESOURCE_ID',
                             dest=argparse.SUPPRESS,
                             help="One or more resource IDs. If provided, no other 'Resource Id' "
                                  "arguments should be specified.",
                             action=split_action(command.arguments),
                             nargs='+',
                             type=ResourceId,
                             validator=required_values_validator,
                             arg_group=group_name)

    for command in command_table.values():
        command_loaded_handler(command)

    APPLICATION.remove(APPLICATION.COMMAND_TABLE_LOADED, add_id_parameters)

APPLICATION.register(APPLICATION.COMMAND_TABLE_LOADED, add_id_parameters)

add_usage = '--add property.listProperty <key=value, string or JSON string>'
set_usage = '--set property1.property2=<value>'
remove_usage = '--remove property.list <indexToRemove> OR --remove propertyToRemove'

def _get_child(parent, collection_name, item_name, collection_key):
    items = getattr(parent, collection_name)
    result = next((x for x in items if getattr(x, collection_key, '').lower() == item_name.lower()), None) # pylint: disable=line-too-long
    if not result:
        raise CLIError("Property '{}' does not exist for key '{}'.".format(
            item_name, collection_key))
    else:
        return result

def cli_generic_update_command(name, getter, setter, factory=None, setter_arg_name='parameters', # pylint: disable=too-many-arguments
                               table_transformer=None, child_collection_prop_name=None,
                               child_collection_key='name', child_arg_name='item_name',
                               custom_function=None):

    get_arguments = dict(extract_args_from_signature(getter))
    set_arguments = dict(extract_args_from_signature(setter))
    function_arguments = dict(extract_args_from_signature(custom_function)) \
        if custom_function else None

    def handler(args):
        from msrestazure.azure_operation import AzureOperationPoller

        ordered_arguments = args.pop('ordered_arguments') if 'ordered_arguments' in args else []

        try:
            client = factory() if factory else None
        except TypeError:
            client = factory(None) if factory else None

        getterargs = {key: val for key, val in args.items()
                      if key in get_arguments}
        if child_collection_prop_name:
            parent = getter(client, **getterargs) if client else getter(**getterargs)
            instance = _get_child(
                parent,
                child_collection_prop_name,
                args.get(child_arg_name),
                child_collection_key
            )
        else:
            parent = None
            instance = getter(client, **getterargs) if client else getter(**getterargs)

        # pass instance to the custom_function, if provided
        if custom_function:
            custom_func_args = {k: v for k, v in args.items() if k in function_arguments}
            if child_collection_prop_name:
                parent = custom_function(instance, parent, **custom_func_args)
            else:
                instance = custom_function(instance, **custom_func_args)

        # apply generic updates after custom updates
        for k in args.copy().keys():
            if k in get_arguments or k in set_arguments \
                or k in ('properties_to_add', 'properties_to_remove', 'properties_to_set'):
                args.pop(k)
        for key, val in args.items():
            ordered_arguments.append((key, val))

        for arg in ordered_arguments:
            arg_type, arg_values = arg
            if arg_type == '--set':
                try:
                    for expression in arg_values:
                        set_properties(instance, expression)
                except ValueError:
                    raise CLIError('invalid syntax: {}'.format(set_usage))
            elif arg_type == '--add':
                try:
                    add_properties(instance, arg_values)
                except ValueError:
                    raise CLIError('invalid syntax: {}'.format(add_usage))
            elif arg_type == '--remove':
                try:
                    remove_properties(instance, arg_values)
                except ValueError:
                    raise CLIError('invalid syntax: {}'.format(remove_usage))

        # Done... update the instance!
        getterargs[setter_arg_name] = parent if child_collection_prop_name else instance
        opres = setter(client, **getterargs) if client else setter(**getterargs)
        result = opres.result() if isinstance(opres, AzureOperationPoller) else opres
        if child_collection_prop_name:
            return _get_child(
                result,
                child_collection_prop_name,
                args.get(child_arg_name),
                child_collection_key
            )
        else:
            return result

    class OrderedArgsAction(argparse.Action): #pylint:disable=too-few-public-methods
        def __call__(self, parser, namespace, values, option_string=None):
            if not getattr(namespace, 'ordered_arguments', None):
                setattr(namespace, 'ordered_arguments', [])
            namespace.ordered_arguments.append((option_string, values))

    cmd = CliCommand(name, handler, table_transformer=table_transformer)
    cmd.arguments.update(set_arguments)
    cmd.arguments.update(get_arguments)
    if function_arguments:
        cmd.arguments.update(function_arguments)
    cmd.arguments.pop('instance', None) # inherited from custom_function(instance, ...)
    cmd.arguments.pop('parent', None)
    cmd.arguments.pop('expand', None) # possibly inherited from the getter
    cmd.arguments.pop(setter_arg_name, None)
    group_name = 'Generic Update'
    cmd.add_argument('properties_to_set', '--set', nargs='+', action=OrderedArgsAction, default=[],
                     help='Update an object by specifying a property path and value to set.'
                     '  Example: {}'.format(set_usage),
                     metavar='KEY=VALUE', arg_group=group_name)
    cmd.add_argument('properties_to_add', '--add', nargs='+', action=OrderedArgsAction, default=[],
                     help='Add an object to a list of objects by specifying a path and key'
                     ' value pairs.  Example: {}'.format(add_usage),
                     metavar='LIST KEY=VALUE', arg_group=group_name)
    cmd.add_argument('properties_to_remove', '--remove', nargs='+', action=OrderedArgsAction,
                     default=[], help='Remove a property or an element from a list.  Example: '
                     '{}'.format(remove_usage), metavar='LIST INDEX',
                     arg_group=group_name)
    main_command_table[name] = cmd

index_or_filter_regex = re.compile(r'\[(.*)\]')
def set_properties(instance, expression):
    key, value = expression.rsplit('=', 1)

    try:
        value = json.loads(value)
    except: #pylint:disable=bare-except
        pass

    # name should be the raw casing as it could refer to a property OR a dictionary key
    name, path = _get_name_path(key)
    parent_name = path[-1] if path else 'root'
    root = instance
    instance = _find_property(instance, path)
    if instance is None:
        parent = _find_property(root, path[:-1])
        set_properties(parent, '{}={{}}'.format(parent_name))
        instance = _find_property(root, path)

    match = index_or_filter_regex.match(name)
    index_value = int(match.group(1)) if match else None
    try:
        if index_value is not None:
            instance[index_value] = value
        elif isinstance(instance, dict):
            instance[name] = value
        elif isinstance(instance, list):
            show_options(instance, name, key.split('.'))
        else:
            # must be a property name
            name = make_snake_case(name)
            if not hasattr(instance, name):
                logger.warning(
                    "Property '%s' not found on %s. Update may be ignored.", name, parent_name)
            setattr(instance, name, value)
    except IndexError:
        raise CLIError('index {} doesn\'t exist on {}'.format(index_value, name))
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

    if not isinstance(list_to_add_to, list):
        raise ValueError

    dict_entry = {}
    for argument in argument_values:
        if '=' in argument:
            # consecutive key=value entries get added to the same dictionary
            split_arg = argument.split('=', 1)
            dict_entry[split_arg[0]] = split_arg[1]
        else:
            if dict_entry:
                # if an argument is supplied that is not key=value, append any dictionary entry
                # to the list and reset. A subsequent key=value pair will be added to another
                # dictionary.
                list_to_add_to.append(dict_entry)
                dict_entry = {}

            # attempt to convert anything else to JSON and fallback to string if error
            try:
                argument = json.loads(argument)
            except ValueError:
                pass
            list_to_add_to.append(argument)

    # if only key=value pairs used, must check at the end to append the dictionary
    if dict_entry:
        list_to_add_to.append(dict_entry)

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
        if isinstance(parent_to_remove_from, dict):
            del parent_to_remove_from[list_attribute_path[-1]]
        elif hasattr(parent_to_remove_from, make_snake_case(list_attribute_path[-1])):
            setattr(parent_to_remove_from, make_snake_case(list_attribute_path[-1]), None)
        else:
            raise ValueError
    else:
        list_to_remove_from = _find_property(instance, list_attribute_path)
        try:
            list_to_remove_from.pop(int(list_index))
        except IndexError:
            raise CLIError('index {} doesn\'t exist on {}'
                           .format(list_index, list_attribute_path[-1]))

def show_options(instance, part, path):
    options = instance.__dict__ if hasattr(instance, '__dict__') else instance
    parent = '.'.join(path[:-1]).replace('.[', '[')
    error_message = "Couldn't find '{}' in '{}'.".format(part, parent)
    if isinstance(options, dict):
        options = options.keys()
        options = sorted([make_camel_case(x) for x in options])
        error_message = '{} Available options: {}'.format(error_message, options)
    elif isinstance(options, list):
        options = "index into the collection '{}' with [<index>] or [<key=value>]".format(parent)
        error_message = '{} Available options: {}'.format(error_message, options)
    else:
        error_message = "{} '{}' does not support further indexing.".format(error_message, parent)
    raise CLIError(error_message)

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

internal_path_regex = re.compile(r'(\[.*?\])|([^.]+)')
def _get_internal_path(path):
    # to handle indexing in the same way as other dot qualifiers,
    # we split paths like foo[0][1] into foo.[0].[1]
    path = path.replace('.[', '[').replace('[', '.[')
    path_segment_pairs = internal_path_regex.findall(path)
    final_paths = []
    for regex_result in path_segment_pairs:
        # the regex matches two capture group, one of which will be None
        segment = regex_result[0] or regex_result[1]
        final_paths.append(segment)
    return final_paths

def _get_name_path(path):
    pathlist = _get_internal_path(path)
    return pathlist.pop(), pathlist

def _update_instance(instance, part, path):
    try: # pylint: disable=too-many-nested-blocks
        index = index_or_filter_regex.match(part)
        if index:
            # indexing on anything but a list is not allowed
            if not isinstance(instance, list):
                show_options(instance, part, path)

            if '=' in index.group(1):
                key, value = index.group(1).split('=')
                matches = []
                for x in instance:
                    if isinstance(x, dict) and x.get(key, None) == value:
                        matches.append(x)
                    elif not isinstance(x, dict):
                        key = make_snake_case(key)
                        if hasattr(x, key) and getattr(x, key, None) == value:
                            matches.append(x)
                if len(matches) == 1:
                    instance = matches[0]
                elif len(matches) > 1:
                    raise CLIError("non-unique key '{}' found multiple matches on {}. "
                                   "Key must be unique.".format(
                                       key, path[-2]))
                else:
                    raise CLIError("item with value '{}' doesn\'t exist for key '{}' on {}".format(
                        value, key, path[-2]))
            else:
                try:
                    index_value = int(index.group(1))
                    instance = instance[index_value]
                except IndexError:
                    raise CLIError('index {} doesn\'t exist on {}'.format(
                        index_value, path[-2]))
        elif isinstance(instance, dict):
            instance = instance[part]
        else:
            instance = getattr(instance, make_snake_case(part))
    except (AttributeError, KeyError):
        show_options(instance, part, path)
    return instance

def _find_property(instance, path):
    for part in path:
        instance = _update_instance(instance, part, path)
    return instance

