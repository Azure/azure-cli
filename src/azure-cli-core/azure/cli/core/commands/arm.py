# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from collections import OrderedDict
import json
import re
from six import string_types

from knack.arguments import CLICommandArgument, ignore_type
from knack.introspection import extract_args_from_signature
from knack.log import get_logger
from knack.util import todict, CLIError

from azure.cli.core import AzCommandsLoader, EXCLUDED_PARAMS
from azure.cli.core.commands import LongRunningOperation, _is_poller
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import IterateValue
from azure.cli.core.util import shell_safe_json_parse, augment_no_wait_handler_args
from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)


class ArmTemplateBuilder(object):

    def __init__(self):
        template = OrderedDict()
        template['$schema'] = \
            'https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#'
        template['contentVersion'] = '1.0.0.0'
        template['parameters'] = {}
        template['variables'] = {}
        template['resources'] = []
        template['outputs'] = {}
        self.template = template
        self.parameters = OrderedDict()

    def add_resource(self, resource):
        self.template['resources'].append(resource)

    def add_variable(self, key, value):
        self.template['variables'][key] = value

    def add_parameter(self, key, value):
        self.template['parameters'][key] = value

    def add_secure_parameter(self, key, value, description=None):
        param = {
            "type": "securestring",
            "metadata": {
                "description": description or 'Secure {}'.format(key)
            }
        }
        self.template['parameters'][key] = param
        self.parameters[key] = {'value': value}

    def add_id_output(self, key, provider, property_type, property_name):
        new_output = {
            key: {
                'type': 'string',
                'value': "[resourceId('{}/{}', '{}')]".format(
                    provider, property_type, property_name)
            }
        }
        self.template['outputs'].update(new_output)

    def add_output(self, key, property_name, provider=None, property_type=None,
                   output_type='string', path=None):

        if provider and property_type:
            value = "[reference(resourceId('{provider}/{type}', '{property}'),providers('{provider}', '{type}').apiVersions[0])".format(  # pylint: disable=line-too-long
                provider=provider, type=property_type, property=property_name)
        else:
            value = "[reference('{}')".format(property_name)
        value = '{}.{}]'.format(value, path) if path else '{}]'.format(value)
        new_output = {
            key: {
                'type': output_type,
                'value': value
            }
        }
        self.template['outputs'].update(new_output)

    def build(self):
        return json.loads(json.dumps(self.template))

    def build_parameters(self):
        return json.loads(json.dumps(self.parameters))


def handle_template_based_exception(ex):
    try:
        raise CLIError(ex.inner_exception.error.message)
    except AttributeError:
        raise CLIError(ex)


def handle_long_running_operation_exception(ex):
    import azure.cli.core.telemetry as telemetry

    telemetry.set_exception(
        ex,
        fault_type='failed-long-running-operation',
        summary='Unexpected client exception in {}.'.format(LongRunningOperation.__name__))

    message = getattr(ex, 'message', ex)
    error_message = 'Deployment failed.'

    try:
        correlation_id = ex.response.headers['x-ms-correlation-request-id']
        error_message = '{} Correlation ID: {}.'.format(error_message, correlation_id)
    except:  # pylint: disable=bare-except
        pass

    try:
        inner_message = json.loads(ex.response.text)['error']['details'][0]['message']
        error_message = '{} {}'.format(error_message, inner_message)
    except:  # pylint: disable=bare-except
        error_message = '{} {}'.format(error_message, message)

    cli_error = CLIError(error_message)
    # capture response for downstream commands (webapp) to dig out more details
    setattr(cli_error, 'response', getattr(ex, 'response', None))
    raise cli_error


def deployment_validate_table_format(result):

    if result.get('error', None):
        error_result = OrderedDict()
        error_result['result'] = result['error']['code']
        try:
            tracking_id = re.match(r".*(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})", str(result['error']['message'])).group(1)
            error_result['trackingId'] = tracking_id
        except:  # pylint: disable=bare-except
            pass
        try:
            error_result['message'] = result['error']['details'][0]['message']
        except:  # pylint: disable=bare-except
            error_result['message'] = result['error']['message']
        return error_result
    elif result.get('properties', None):
        success_result = OrderedDict()
        success_result['result'] = result['properties']['provisioningState']
        success_result['correlationId'] = result['properties']['correlationId']
        return success_result
    return result


class ResourceId(str):

    def __new__(cls, val):
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(val):
            raise ValueError()
        return str.__new__(cls, val)


def resource_exists(cli_ctx, resource_group, name, namespace, type, **_):  # pylint: disable=redefined-builtin
    ''' Checks if the given resource exists. '''
    odata_filter = "resourceGroup eq '{}' and name eq '{}'" \
        " and resourceType eq '{}/{}'".format(resource_group, name, namespace, type)
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).resources
    existing = len(list(client.list(filter=odata_filter))) == 1
    return existing


def add_id_parameters(_, **kwargs):  # pylint: disable=unused-argument

    command_table = kwargs.get('cmd_tbl')

    if not command_table:
        return

    def split_action(arguments):
        class SplitAction(argparse.Action):  # pylint: disable=too-few-public-methods
            def __call__(self, parser, namespace, values, option_string=None):
                ''' The SplitAction will take the given ID parameter and spread the parsed
                parts of the id into the individual backing fields.

                Since the id value is expected to be of type `IterateValue`, all the backing
                (dest) fields will also be of type `IterateValue`
                '''
                from msrestazure.tools import parse_resource_id
                import os
                if isinstance(values, str):
                    values = [values]
                expanded_values = []
                for val in values:
                    try:
                        # support piping values from JSON. Does not require use of --query
                        json_vals = json.loads(val)
                        if not isinstance(json_vals, list):
                            json_vals = [json_vals]
                        for json_val in json_vals:
                            if 'id' in json_val:
                                expanded_values += [json_val['id']]
                    except ValueError:
                        # supports piping of --ids to the command when using TSV. Requires use of --query
                        expanded_values = expanded_values + val.split(os.linesep)
                try:
                    for value in expanded_values:
                        parts = parse_resource_id(value)
                        for arg in [arg for arg in arguments.values() if arg.type.settings.get('id_part')]:
                            self.set_argument_value(namespace, arg, parts)
                except Exception as ex:
                    raise ValueError(ex)

            @staticmethod
            def set_argument_value(namespace, arg, parts):

                existing_values = getattr(namespace, arg.name, None)
                if existing_values is None:
                    existing_values = IterateValue()
                    existing_values.append(parts.get(arg.type.settings['id_part'], None))
                else:
                    if isinstance(existing_values, str):
                        if not getattr(arg.type, 'configured_default_applied', None):
                            logger.warning(
                                "Property '%s=%s' being overriden by value '%s' from IDs parameter.",
                                arg.name, existing_values, parts[arg.type.settings['id_part']]
                            )
                        existing_values = IterateValue()
                    existing_values.append(parts.get(arg.type.settings['id_part']))
                setattr(namespace, arg.name, existing_values)

        return SplitAction

    def command_loaded_handler(command):
        id_parts = [arg.type.settings['id_part'] for arg in command.arguments.values()
                    if arg.type.settings.get('id_part')]
        if 'name' not in id_parts and 'resource_name' not in id_parts:
            # Only commands with a resource name are candidates for an id parameter
            return
        if command.name.split()[-1] == 'create':
            # Somewhat blunt hammer, but any create commands will not have an automatic id
            # parameter
            return

        required_arguments = []
        optional_arguments = []
        for arg in [argument for argument in command.arguments.values() if argument.type.settings.get('id_part')]:
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
            if command.arguments[key].type.settings.get('id_part'):
                command.arguments[key].arg_group = group_name

        command.add_argument('ids',
                             '--ids',
                             metavar='RESOURCE_ID',
                             dest=argparse.SUPPRESS,
                             help="One or more resource IDs (space-delimited). If provided, "
                                  "no other 'Resource Id' arguments should be specified.",
                             action=split_action(command.arguments),
                             nargs='+',
                             validator=required_values_validator,
                             arg_group=group_name)

    for command in command_table.values():
        command_loaded_handler(command)


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


def _get_operations_tmpl(cmd):
    operations_tmpl = cmd.command_kwargs.get('operations_tmpl',
                                             cmd.command_kwargs.get('command_type').settings['operations_tmpl'])
    if not operations_tmpl:
        raise CLIError("command authoring error: cmd '{}' does not have an operations_tmpl.".format(cmd.name))
    return operations_tmpl


def _get_client_factory(_, kwargs):
    command_type = kwargs.get('command_type', None)
    factory = kwargs.get('client_factory', None)
    if not factory and command_type:
        factory = command_type.settings.get('client_factory', None)
    return factory


# pylint: disable=too-many-statements
def _cli_generic_update_command(context, name, getter_op, setter_op, setter_arg_name='parameters',
                                child_collection_prop_name=None, child_collection_key='name',
                                child_arg_name='item_name', custom_function_op=None, **kwargs):
    if not isinstance(context, AzCommandsLoader):
        raise TypeError("'context' expected type '{}'. Got: '{}'".format(AzCommandsLoader.__name__, type(context)))
    if not isinstance(getter_op, string_types):
        raise TypeError("Getter operation must be a string. Got '{}'".format(getter_op))
    if not isinstance(setter_op, string_types):
        raise TypeError("Setter operation must be a string. Got '{}'".format(setter_op))
    if custom_function_op and not isinstance(custom_function_op, string_types):
        raise TypeError("Custom function operation must be a string. Got '{}'".format(
            custom_function_op))

    def get_arguments_loader():
        return dict(extract_args_from_signature(context.get_op_handler(getter_op), excluded_params=EXCLUDED_PARAMS))

    def set_arguments_loader():
        return dict(extract_args_from_signature(context.get_op_handler(setter_op), excluded_params=EXCLUDED_PARAMS))

    def function_arguments_loader():
        if not custom_function_op:
            return {}

        custom_op = context.get_op_handler(custom_function_op)
        context._apply_doc_string(custom_op, kwargs)  # pylint: disable=protected-access
        return dict(extract_args_from_signature(custom_op, excluded_params=EXCLUDED_PARAMS))

    def generic_update_arguments_loader():

        arguments = {}
        arguments.update(set_arguments_loader())
        arguments.update(get_arguments_loader())
        arguments.update(function_arguments_loader())
        arguments.pop('instance', None)  # inherited from custom_function(instance, ...)
        arguments.pop('parent', None)
        arguments.pop('expand', None)  # possibly inherited from the getter
        arguments.pop(setter_arg_name, None)

        # Add the generic update parameters
        class OrderedArgsAction(argparse.Action):  # pylint:disable=too-few-public-methods

            def __call__(self, parser, namespace, values, option_string=None):
                if not getattr(namespace, 'ordered_arguments', None):
                    setattr(namespace, 'ordered_arguments', [])
                namespace.ordered_arguments.append((option_string, values))

        group_name = 'Generic Update'
        arguments['properties_to_set'] = CLICommandArgument(
            'properties_to_set', options_list=['--set'], nargs='+',
            action=OrderedArgsAction, default=[],
            help='Update an object by specifying a property path and value to set.  Example: {}'.format(set_usage),
            metavar='KEY=VALUE', arg_group=group_name
        )
        arguments['properties_to_add'] = CLICommandArgument(
            'properties_to_add', options_list=['--add'], nargs='+',
            action=OrderedArgsAction, default=[],
            help='Add an object to a list of objects by specifying a path and '
                 'key value pairs.  Example: {}'.format(add_usage),
            metavar='LIST KEY=VALUE', arg_group=group_name
        )
        arguments['properties_to_remove'] = CLICommandArgument(
            'properties_to_remove', options_list=['--remove'], nargs='+',
            action=OrderedArgsAction, default=[],
            help='Remove a property or an element from a list.  Example: {}'.format(remove_usage),
            metavar='LIST INDEX', arg_group=group_name
        )
        arguments['cmd'] = CLICommandArgument('cmd', arg_type=ignore_type)
        return [(k, v) for k, v in arguments.items()]

    def _extract_handler_and_args(args, commmand_kwargs, op):
        from azure.cli.core.commands.client_factory import resolve_client_arg_name
        factory = _get_client_factory(name, commmand_kwargs)
        client = None
        if factory:
            try:
                client = factory(context.cli_ctx)
            except TypeError:
                client = factory(context.cli_ctx, None)

        client_arg_name = resolve_client_arg_name(op, kwargs)
        op_handler = context.get_op_handler(op)
        exclude = list(set(EXCLUDED_PARAMS) - set(['self', 'client']))
        raw_args = dict(extract_args_from_signature(op_handler, excluded_params=exclude))
        op_args = {key: val for key, val in args.items() if key in raw_args}
        if client_arg_name in raw_args:
            op_args[client_arg_name] = client
        return op_handler, op_args

    def handler(args):  # pylint: disable=too-many-branches,too-many-statements
        cmd = args.get('cmd')
        ordered_arguments = args.pop('ordered_arguments', [])
        for item in ['properties_to_add', 'properties_to_set', 'properties_to_remove']:
            if args[item]:
                raise CLIError("Unexpected '{}' was not empty.".format(item))
            del args[item]

        getter, getterargs = _extract_handler_and_args(args, cmd.command_kwargs, getter_op)
        if child_collection_prop_name:
            parent = getter(**getterargs)
            instance = _get_child(
                parent,
                child_collection_prop_name,
                args.get(child_arg_name),
                child_collection_key
            )
        else:
            parent = None
            instance = getter(**getterargs)

        # pass instance to the custom_function, if provided
        if custom_function_op:
            custom_function, custom_func_args = _extract_handler_and_args(args, cmd.command_kwargs, custom_function_op)
            if child_collection_prop_name:
                parent = custom_function(instance=instance, parent=parent, **custom_func_args)
            else:
                instance = custom_function(instance=instance, **custom_func_args)

        # apply generic updates after custom updates
        setter, setterargs = _extract_handler_and_args(args, cmd.command_kwargs, setter_op)

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

        # Handle no-wait
        supports_no_wait = cmd.command_kwargs.get('supports_no_wait', None)
        if supports_no_wait:
            no_wait_enabled = args.get('no_wait', False)
            augment_no_wait_handler_args(no_wait_enabled,
                                         setter,
                                         setterargs)
        else:
            no_wait_param = cmd.command_kwargs.get('no_wait_param', None)
            if no_wait_param:
                setterargs[no_wait_param] = args[no_wait_param]

        result = setter(**setterargs)

        if supports_no_wait and no_wait_enabled:
            return None
        else:
            no_wait_param = cmd.command_kwargs.get('no_wait_param', None)
            if no_wait_param and setterargs.get(no_wait_param, None):
                return None

        if _is_poller(result):
            result = LongRunningOperation(cmd.cli_ctx, 'Starting {}'.format(cmd.name))(result)

        if child_collection_prop_name:
            result = _get_child(
                result,
                child_collection_prop_name,
                args.get(child_arg_name),
                child_collection_key
            )

        return result

    context._cli_command(name, handler=handler, argument_loader=generic_update_arguments_loader, **kwargs)  # pylint: disable=protected-access


def _cli_generic_wait_command(context, name, getter_op, **kwargs):

    if not isinstance(getter_op, string_types):
        raise ValueError("Getter operation must be a string. Got '{}'".format(type(getter_op)))

    factory = _get_client_factory(name, kwargs)

    def generic_wait_arguments_loader():

        getter_args = dict(extract_args_from_signature(context.get_op_handler(getter_op),
                                                       excluded_params=EXCLUDED_PARAMS))
        cmd_args = getter_args.copy()

        group_name = 'Wait Condition'
        cmd_args['timeout'] = CLICommandArgument(
            'timeout', options_list=['--timeout'], default=3600, arg_group=group_name, type=int,
            help='maximum wait in seconds'
        )
        cmd_args['interval'] = CLICommandArgument(
            'interval', options_list=['--interval'], default=30, arg_group=group_name, type=int,
            help='polling interval in seconds'
        )
        cmd_args['deleted'] = CLICommandArgument(
            'deleted', options_list=['--deleted'], action='store_true', arg_group=group_name,
            help='wait until deleted'
        )
        cmd_args['created'] = CLICommandArgument(
            'created', options_list=['--created'], action='store_true', arg_group=group_name,
            help="wait until created with 'provisioningState' at 'Succeeded'"
        )
        cmd_args['updated'] = CLICommandArgument(
            'updated', options_list=['--updated'], action='store_true', arg_group=group_name,
            help="wait until updated with provisioningState at 'Succeeded'"
        )
        cmd_args['exists'] = CLICommandArgument(
            'exists', options_list=['--exists'], action='store_true', arg_group=group_name,
            help="wait until the resource exists"
        )
        cmd_args['custom'] = CLICommandArgument(
            'custom', options_list=['--custom'], arg_group=group_name,
            help="Wait until the condition satisfies a custom JMESPath query. E.g. "
                 "provisioningState!='InProgress', "
                 "instanceView.statuses[?code=='PowerState/running']"
        )
        cmd_args['cmd'] = CLICommandArgument('cmd', arg_type=ignore_type)
        return [(k, v) for k, v in cmd_args.items()]

    def get_provisioning_state(instance):
        provisioning_state = getattr(instance, 'provisioning_state', None)
        if not provisioning_state:
            # some SDK, like resource-group, has 'provisioning_state' under 'properties'
            properties = getattr(instance, 'properties', None)
            if properties:
                provisioning_state = getattr(properties, 'provisioning_state', None)
        return provisioning_state

    def handler(args):
        from azure.cli.core.commands.client_factory import resolve_client_arg_name
        from msrest.exceptions import ClientException
        import time

        cmd = args.get('cmd')

        operations_tmpl = _get_operations_tmpl(cmd)
        getter_args = dict(extract_args_from_signature(context.get_op_handler(getter_op),
                                                       excluded_params=EXCLUDED_PARAMS))
        client_arg_name = resolve_client_arg_name(operations_tmpl, kwargs)
        try:
            client = factory(context.cli_ctx) if factory else None
        except TypeError:
            client = factory(context.cli_ctx, None) if factory else None
        if client and (client_arg_name in getter_args or client_arg_name == 'self'):
            args[client_arg_name] = client

        getter = context.get_op_handler(getter_op)

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

        progress_indicator = context.cli_ctx.get_progress_controller()
        progress_indicator.begin()
        for _ in range(0, timeout, interval):
            try:
                progress_indicator.add(message='Waiting')
                instance = getter(**args)
                if wait_for_exists:
                    progress_indicator.end()
                    return None
                provisioning_state = get_provisioning_state(instance)
                # until we have any needs to wait for 'Failed', let us bail out on this
                if provisioning_state == 'Failed':
                    progress_indicator.stop()
                    raise CLIError('The operation failed')
                if ((wait_for_created or wait_for_updated) and provisioning_state == 'Succeeded') or \
                        custom_condition and bool(verify_property(instance, custom_condition)):
                    progress_indicator.end()
                    return None
            except ClientException as ex:
                progress_indicator.stop()
                if getattr(ex, 'status_code', None) == 404:
                    if wait_for_deleted:
                        return None
                    if not any([wait_for_created, wait_for_exists, custom_condition]):
                        raise
                else:
                    raise
            except Exception as ex:  # pylint: disable=broad-except
                progress_indicator.stop()
                raise

            time.sleep(interval)

        progress_indicator.end()
        return CLIError('Wait operation timed-out after {} seconds'.format(timeout))

    context._cli_command(name, handler=handler, argument_loader=generic_wait_arguments_loader, **kwargs)  # pylint: disable=protected-access


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
            if hasattr(instance, make_snake_case(name)):
                setattr(instance, make_snake_case(name), value)
            else:
                if instance.additional_properties is None:
                    instance.additional_properties = {}
                instance.additional_properties[name] = value
                instance.enable_additional_properties_sending()
                logger.warning(
                    "Property '%s' not found on %s. Send it as an additional property .", name, parent_name)

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
            except (ValueError, CLIError):
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
        property_val = _find_property(instance, list_attribute_path)
        parent_to_remove_from = _find_property(instance, list_attribute_path[:-1])
        if isinstance(parent_to_remove_from, dict):
            del parent_to_remove_from[list_attribute_path[-1]]
        elif hasattr(parent_to_remove_from, make_snake_case(list_attribute_path[-1])):
            setattr(parent_to_remove_from, make_snake_case(list_attribute_path[-1]),
                    [] if isinstance(property_val, list) else None)
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
    from msrest.serialization import Model
    options = instance.__dict__ if hasattr(instance, '__dict__') else instance
    if isinstance(instance, Model) and isinstance(getattr(instance, 'additional_properties', None), dict):
        options.update(options.pop('additional_properties'))
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
        return (parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])) if len(parts) > 1 else s
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


def _update_instance(instance, part, path):  # pylint: disable=too-many-return-statements, inconsistent-return-statements
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
                    snake_key = make_snake_case(key)
                    if hasattr(x, snake_key) and getattr(x, snake_key, None) == value:
                        matches.append(x)

            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                raise CLIError("non-unique key '{}' found multiple matches on {}. Key must be unique."
                               .format(key, path[-2]))
            else:
                if key in getattr(instance, 'additional_properties', {}):
                    instance.enable_additional_properties_sending()
                    return instance.additional_properties[key]
                raise CLIError("item with value '{}' doesn\'t exist for key '{}' on {}".format(value, key, path[-2]))

        if index:
            try:
                index_value = int(index.group(1))
                return instance[index_value]
            except IndexError:
                raise CLIError('index {} doesn\'t exist on {}'.format(index_value, path[-2]))

        if isinstance(instance, dict):
            return instance[part]

        if hasattr(instance, make_snake_case(part)):
            return getattr(instance, make_snake_case(part), None)
        elif part in getattr(instance, 'additional_properties', {}):
            instance.enable_additional_properties_sending()
            return instance.additional_properties[part]
        raise AttributeError()
    except (AttributeError, KeyError):
        throw_and_show_options(instance, part, path)


def _find_property(instance, path):
    for part in path:
        instance = _update_instance(instance, part, path)
    return instance


def assign_identity(cli_ctx, getter, setter, identity_role=None, identity_scope=None):
    import time
    from azure.mgmt.authorization import AuthorizationManagementClient
    from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
    from msrestazure.azure_exceptions import CloudError

    # get
    resource = getter()
    resource = setter(resource)

    # create role assignment:
    if identity_scope:
        principal_id = resource.identity.principal_id

        identity_role_id = resolve_role_id(cli_ctx, identity_role, identity_scope)
        assignments_client = get_mgmt_service_client(cli_ctx, AuthorizationManagementClient).role_assignments
        parameters = RoleAssignmentCreateParameters(role_definition_id=identity_role_id, principal_id=principal_id)

        logger.info("Creating an assignment with a role '%s' on the scope of '%s'", identity_role_id, identity_scope)
        retry_times = 36
        assignment_name = _gen_guid()
        for l in range(0, retry_times):
            try:
                assignments_client.create(scope=identity_scope, role_assignment_name=assignment_name,
                                          parameters=parameters)
                break
            except CloudError as ex:
                if 'role assignment already exists' in ex.message:
                    logger.info('Role assignment already exists')
                    break
                elif l < retry_times and ' does not exist in the directory ' in ex.message:
                    time.sleep(5)
                    logger.warning('Retrying role assignment creation: %s/%s', l + 1,
                                   retry_times)
                    continue
                else:
                    raise
    return resource


def resolve_role_id(cli_ctx, role, scope):
    import uuid
    from azure.mgmt.authorization import AuthorizationManagementClient
    client = get_mgmt_service_client(cli_ctx, AuthorizationManagementClient).role_definitions

    role_id = None
    if re.match(r'/subscriptions/[^/]+/providers/Microsoft.Authorization/roleDefinitions/',
                role, re.I):
        role_id = role
    else:
        try:
            uuid.UUID(role)
            role_id = '/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(
                client.config.subscription_id, role)
        except ValueError:
            pass
        if not role_id:  # retrieve role id
            role_defs = list(client.list(scope, "roleName eq '{}'".format(role)))
            if not role_defs:
                raise CLIError("Role '{}' doesn't exist.".format(role))
            elif len(role_defs) > 1:
                ids = [r.id for r in role_defs]
                err = "More than one role matches the given name '{}'. Please pick an id from '{}'"
                raise CLIError(err.format(role, ids))
            role_id = role_defs[0].id
    return role_id


def _gen_guid():
    import uuid
    return uuid.uuid4()
