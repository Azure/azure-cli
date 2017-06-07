# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import re
from six import string_types

from azure.cli.core.commands import (CliCommand,
                                     get_op_handler,
                                     command_table as main_command_table,
                                     command_module_map as main_command_module_map,
                                     CONFIRM_PARAM_NAME)
from azure.cli.core.commands._introspection import extract_args_from_signature
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.application import APPLICATION, IterateValue
from azure.cli.core.prompting import prompt_y_n, NoTTYException
from azure.cli.core._config import az_config
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError, todict, shell_safe_json_parse
from azure.cli.core.profiles import ResourceType

logger = azlogging.get_az_logger(__name__)

regex = re.compile(
    '/subscriptions/(?P<subscription>[^/]*)(/resource[gG]roups/(?P<resource_group>[^/]*))?'
    '/providers/(?P<namespace>[^/]*)/(?P<type>[^/]*)/(?P<name>[^/]*)'
    '((/providers/(?P<child_namespace>[^/]*))?/(?P<child_type>[^/]*)/(?P<child_name>[^/]*))?'
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

    return {key: value for key, value in result.items() if value is not None}


def is_valid_resource_id(rid, exception_type=None):
    is_valid = False
    try:
        is_valid = rid and resource_id(**parse_resource_id(rid)).lower() == rid.lower()
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


def resource_exists(resource_group, name, namespace, type, **_):  # pylint: disable=redefined-builtin
    ''' Checks if the given resource exists. '''
    odata_filter = "resourceGroup eq '{}' and name eq '{}'" \
        " and resourceType eq '{}/{}'".format(resource_group, name, namespace, type)
    client = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing


def add_id_parameters(command_table):
    def split_action(arguments):
        class SplitAction(argparse.Action):  # pylint: disable=too-few-public-methods
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
                            self.set_argument_value(namespace, arg, parts)
                except Exception as ex:
                    raise ValueError(ex)

            @staticmethod
            def set_argument_value(namespace, arg, parts):
                existing_values = getattr(namespace, arg.name, None)
                if existing_values is None:
                    existing_values = IterateValue()
                    existing_values.append(parts[arg.id_part])
                else:
                    if isinstance(existing_values, str):
                        if not getattr(arg.type, 'configured_default_applied', None):
                            logger.warning(
                                "Property '%s=%s' being overriden by value '%s' from IDs parameter.",
                                arg.name, existing_values, parts[arg.id_part]
                            )
                        existing_values = IterateValue()
                    existing_values.append(parts[arg.id_part])
                setattr(namespace, arg.name, existing_values)

        return SplitAction

    def command_loaded_handler(command):
        if 'name' not in [arg.id_part for arg in command.arguments.values() if arg.id_part]:
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
                raise ValueError('({} | {}) are required'.format(missing_required, '--ids'))

        group_name = 'Resource Id'
        for key, arg in command.arguments.items():
            if command.arguments[key].id_part:
                command.arguments[key].arg_group = group_name

        command.add_argument('ids',
                             '--ids',
                             metavar='RESOURCE_ID',
                             dest=argparse.SUPPRESS,
                             help="One or more resource IDs (space delimited). If provided, "
                                  "no other 'Resource Id' arguments should be specified.",
                             action=split_action(command.arguments),
                             nargs='+',
                             type=ResourceId,
                             validator=required_values_validator,
                             arg_group=group_name)

    for command in command_table.values():
        command_loaded_handler(command)


APPLICATION.register(APPLICATION.COMMAND_TABLE_PARAMS_LOADED, add_id_parameters)

APPLICATION.register(APPLICATION.COMMAND_TABLE_LOADED, add_id_parameters)

add_usage = '--add property.listProperty <key=value, string or JSON string>'
set_usage = '--set property1.property2=<value>'
remove_usage = '--remove property.list <indexToRemove> OR --remove propertyToRemove'


def _get_child(parent, collection_name, item_name, collection_key):
    items = getattr(parent, collection_name)
    result = next((x for x in items if getattr(x, collection_key, '').lower() ==
                   item_name.lower()), None)
    if not result:
        raise CLIError("Property '{}' does not exist for key '{}'.".format(
            item_name, collection_key))
    else:
        return result


def _user_confirmed(confirmation, command_args):
    if callable(confirmation):
        return confirmation(command_args)
    try:
        if isinstance(confirmation, string_types):
            return prompt_y_n(confirmation)
        return prompt_y_n('Are you sure you want to perform this operation?')
    except NoTTYException:
        logger.warning('Unable to prompt for confirmation as no tty available. Use --yes.')
        return False


def cli_generic_update_command(module_name, name, getter_op, setter_op, factory=None,
                               setter_arg_name='parameters', table_transformer=None,
                               child_collection_prop_name=None, child_collection_key='name',
                               child_arg_name='item_name', custom_function_op=None,
                               no_wait_param=None, transform=None, confirmation=None,
                               exception_handler=None, formatter_class=None):
    if not isinstance(getter_op, string_types):
        raise ValueError("Getter operation must be a string. Got '{}'".format(getter_op))
    if not isinstance(setter_op, string_types):
        raise ValueError("Setter operation must be a string. Got '{}'".format(setter_op))
    if custom_function_op and not isinstance(custom_function_op, string_types):
        raise ValueError("Custom function operation must be a string. Got '{}'".format(
            custom_function_op))

    def get_arguments_loader():
        return dict(extract_args_from_signature(get_op_handler(getter_op)))

    def set_arguments_loader():
        return dict(extract_args_from_signature(get_op_handler(setter_op),
                                                no_wait_param=no_wait_param))

    def function_arguments_loader():
        return dict(extract_args_from_signature(get_op_handler(custom_function_op))) \
            if custom_function_op else {}

    def arguments_loader():
        arguments = {}
        arguments.update(set_arguments_loader())
        arguments.update(get_arguments_loader())
        arguments.update(function_arguments_loader())
        arguments.pop('instance', None)  # inherited from custom_function(instance, ...)
        arguments.pop('parent', None)
        arguments.pop('expand', None)  # possibly inherited from the getter
        arguments.pop(setter_arg_name, None)
        return arguments

    def handler(args):  # pylint: disable=too-many-branches,too-many-statements
        from msrestazure.azure_operation import AzureOperationPoller

        if confirmation \
            and not args.items().get(CONFIRM_PARAM_NAME) \
            and not az_config.getboolean('core', 'disable_confirm_prompt', fallback=False) \
                and not _user_confirmed(confirmation, args.items()):
            raise CLIError('Operation cancelled.')

        ordered_arguments = args.pop('ordered_arguments', [])
        for item in ['properties_to_add', 'properties_to_set', 'properties_to_remove']:
            if args[item]:
                raise CLIError("Unexpected '{}' was not empty.".format(item))
            del args[item]

        try:
            client = factory() if factory else None
        except TypeError:
            client = factory(None) if factory else None

        getterargs = {key: val for key, val in args.items() if key in get_arguments_loader()}
        getter = get_op_handler(getter_op)
        try:
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
            if custom_function_op:
                custom_function = get_op_handler(custom_function_op)
                custom_func_args = \
                    {k: v for k, v in args.items() if k in function_arguments_loader()}
                if child_collection_prop_name:
                    parent = custom_function(instance, parent, **custom_func_args)
                else:
                    instance = custom_function(instance, **custom_func_args)

            # apply generic updates after custom updates
            setterargs = {key: val for key, val in args.items() if key in set_arguments_loader()}

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
            setterargs[setter_arg_name] = parent if child_collection_prop_name else instance
            setter = get_op_handler(setter_op)

            opres = setter(client, **setterargs) if client else setter(**setterargs)

            if setterargs.get(no_wait_param, None):
                return None

            result = opres.result() if isinstance(opres, AzureOperationPoller) else opres
            if child_collection_prop_name:
                result = _get_child(
                    result,
                    child_collection_prop_name,
                    args.get(child_arg_name),
                    child_collection_key
                )
        except Exception as ex:  # pylint: disable=broad-except
            if exception_handler:
                result = exception_handler(ex)
            else:
                raise ex

        # apply results transform if specified
        if transform:
            return transform(result)

        return result

    class OrderedArgsAction(argparse.Action):  # pylint:disable=too-few-public-methods

        def __call__(self, parser, namespace, values, option_string=None):
            if not getattr(namespace, 'ordered_arguments', None):
                setattr(namespace, 'ordered_arguments', [])
            namespace.ordered_arguments.append((option_string, values))

    cmd = CliCommand(name, handler, table_transformer=table_transformer,
                     arguments_loader=arguments_loader, formatter_class=formatter_class)
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
    main_command_module_map[name] = module_name


def cli_generic_wait_command(module_name, name, getter_op, factory=None, exception_handler=None):

    if not isinstance(getter_op, string_types):
        raise ValueError("Getter operation must be a string. Got '{}'".format(type(getter_op)))

    def get_arguments_loader():
        return dict(extract_args_from_signature(get_op_handler(getter_op)))

    def arguments_loader():
        arguments = {}
        arguments.update(get_arguments_loader())
        return arguments

    def get_provisioning_state(instance):
        provisioning_state = getattr(instance, 'provisioning_state', None)
        if not provisioning_state:
            # some SDK, like resource-group, has 'provisioning_state' under 'properties'
            properties = getattr(instance, 'properties', None)
            if properties:
                provisioning_state = getattr(properties, 'provisioning_state', None)
        return provisioning_state

    def _handle_exception(ex):
        if exception_handler:
            return exception_handler(ex)
        else:
            raise ex

    def handler(args):
        from msrest.exceptions import ClientException
        import time
        try:
            client = factory() if factory else None
        except TypeError:
            client = factory(None) if factory else None

        getterargs = {key: val for key, val in args.items()
                      if key in get_arguments_loader()}

        getter = get_op_handler(getter_op)

        timeout = args.pop('timeout')
        interval = args.pop('interval')
        wait_for_created = args.pop('created')
        wait_for_deleted = args.pop('deleted')
        wait_for_updated = args.pop('updated')
        wait_for_exists = args.pop('exists')
        custom_condition = args.pop('custom')
        if not any([wait_for_created, wait_for_updated, wait_for_deleted,
                    wait_for_exists, custom_condition]):
            raise CLIError(
                "incorrect usage: --created | --updated | --deleted | --exists | --custom JMESPATH")

        for _ in range(0, timeout, interval):
            try:
                instance = getter(client, **getterargs) if client else getter(**getterargs)
                if wait_for_exists:
                    return
                provisioning_state = get_provisioning_state(instance)
                # until we have any needs to wait for 'Failed', let us bail out on this
                if provisioning_state == 'Failed':
                    raise CLIError('The operation failed')
                if wait_for_created or wait_for_updated:
                    if provisioning_state == 'Succeeded':
                        return
                if custom_condition and bool(verify_property(instance, custom_condition)):
                    return
            except ClientException as ex:
                if getattr(ex, 'status_code', None) == 404:
                    if wait_for_deleted:
                        return
                    if not any([wait_for_created, wait_for_exists, custom_condition]):
                        _handle_exception(ex)
                else:
                    _handle_exception(ex)
            except Exception as ex:  # pylint: disable=broad-except
                _handle_exception(ex)

            time.sleep(interval)

        return CLIError('Wait operation timed-out after {} seconds'.format(timeout))

    cmd = CliCommand(name, handler, arguments_loader=arguments_loader)
    group_name = 'Wait Condition'
    cmd.add_argument('timeout', '--timeout', default=3600, arg_group=group_name, type=int,
                     help='maximum wait in seconds')
    cmd.add_argument('interval', '--interval', default=30, arg_group=group_name, type=int,
                     help='polling interval in seconds')
    cmd.add_argument('deleted', '--deleted', action='store_true', arg_group=group_name,
                     help='wait till deleted')
    cmd.add_argument('created', '--created', action='store_true', arg_group=group_name,
                     help="wait till created with 'provisioningState' at 'Succeeded'")
    cmd.add_argument('updated', '--updated', action='store_true', arg_group=group_name,
                     help="wait till updated with provisioningState at 'Succeeded'")
    cmd.add_argument('exists', '--exists', action='store_true', arg_group=group_name,
                     help="wait till the resource exists")
    cmd.add_argument('custom', '--custom', arg_group=group_name,
                     help=("Wait until the condition satisfies a custom JMESPath query. E.g. "
                           "provisioningState!='InProgress', "
                           "instanceView.statuses[?code=='PowerState/running']"))
    main_command_table[name] = cmd
    main_command_module_map[name] = module_name


def verify_property(instance, condition):
    from jmespath import compile as compile_jmespath
    result = todict(instance)
    jmes_query = compile_jmespath(condition)
    value = jmes_query.search(result)
    return value


index_or_filter_regex = re.compile(r'\[(.*)\]')


def _split_key_value_pair(expression):

    def _find_split():
        """ Find the first = sign to split on (that isn't in [brackets])"""
        key = []
        value = []
        brackets = False
        chars = list(expression)
        while chars:
            c = chars.pop(0)
            if c == '=' and not brackets:
                # keys done the rest is value
                value = chars
                break
            elif c == '[':
                brackets = True
                key += c
            elif c == ']' and brackets:
                brackets = False
                key += c
            else:
                # normal character
                key += c

        return ''.join(key), ''.join(value)

    equals_count = expression.count('=')
    if equals_count == 1:
        return expression.split('=', 1)
    return _find_split()


def set_properties(instance, expression):
    key, value = _split_key_value_pair(expression)

    try:
        value = shell_safe_json_parse(value)
    except:  # pylint:disable=bare-except
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
            throw_and_show_options(instance, name, key.split('.'))
        else:
            # must be a property name
            name = make_snake_case(name)
            if not hasattr(instance, name):
                logger.warning(
                    "Property '%s' not found on %s. Update may be ignored.", name, parent_name)
            setattr(instance, name, value)
    except IndexError:
        raise CLIError('index {} doesn\'t exist on {}'.format(index_value, name))
    except (AttributeError, KeyError, TypeError):
        throw_and_show_options(instance, name, key.split('.'))


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
                argument = shell_safe_json_parse(argument)
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


def throw_and_show_options(instance, part, path):
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
    try:
        index = index_or_filter_regex.match(part)
        if index and not isinstance(instance, list):
            throw_and_show_options(instance, part, path)

        if index and '=' in index.group(1):
            key, value = index.group(1).split('=', 1)
            try:
                value = shell_safe_json_parse(value)
            except:  # pylint: disable=bare-except
                pass
            matches = []
            for x in instance:
                if isinstance(x, dict) and x.get(key, None) == value:
                    matches.append(x)
                elif not isinstance(x, dict):
                    key = make_snake_case(key)
                    if hasattr(x, key) and getattr(x, key, None) == value:
                        matches.append(x)

            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                raise CLIError("non-unique key '{}' found multiple matches on {}. Key must be unique."
                               .format(key, path[-2]))
            else:
                raise CLIError("item with value '{}' doesn\'t exist for key '{}' on {}".format(value, key, path[-2]))

        if index:
            try:
                index_value = int(index.group(1))
                return instance[index_value]
            except IndexError:
                raise CLIError('index {} doesn\'t exist on {}'.format(index_value, path[-2]))

        if isinstance(instance, dict):
            return instance[part]

        return getattr(instance, make_snake_case(part))
    except (AttributeError, KeyError):
        throw_and_show_options(instance, part, path)


def _find_property(instance, path):
    for part in path:
        instance = _update_instance(instance, part, path)
    return instance
