# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

import argparse
from collections import OrderedDict
import json
import re
import copy
from six import string_types

from knack.arguments import CLICommandArgument, ignore_type
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.log import get_logger
from knack.util import todict, CLIError

from azure.cli.core import AzCommandsLoader, EXCLUDED_PARAMS
from azure.cli.core.commands import LongRunningOperation, _is_poller
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import IterateValue
from azure.cli.core.util import shell_safe_json_parse, augment_no_wait_handler_args, get_command_type_kwarg
from azure.cli.core.profiles import ResourceType, get_sdk

logger = get_logger(__name__)
EXCLUDED_NON_CLIENT_PARAMS = list(set(EXCLUDED_PARAMS) - set(['self', 'client']))


# pylint:disable=too-many-lines
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
    if result.get('properties', None):
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


# pylint: disable=too-many-statements
def register_ids_argument(cli_ctx):

    from knack import events
    from msrestazure.tools import parse_resource_id, is_valid_resource_id

    ids_metadata = {}

    def add_ids_arguments(_, **kwargs):  # pylint: disable=unused-argument

        command_table = kwargs.get('commands_loader').command_table

        if not command_table:
            return

        for command in command_table.values():

            # Somewhat blunt hammer, but any create commands will not have an automatic id parameter
            if command.name.split()[-1] == 'create':
                continue

            # Only commands with a resource name are candidates for an id parameter
            id_parts = [a.type.settings.get('id_part') for a in command.arguments.values()]
            if 'name' not in id_parts and 'resource_name' not in id_parts:
                continue

            group_name = 'Resource Id'

            # determine which arguments are required and optional and store in ids_metadata
            ids_metadata[command.name] = {'required': [], 'optional': []}
            for arg in [a for a in command.arguments.values() if a.type.settings.get('id_part')]:
                if arg.options.get('required', False):
                    ids_metadata[command.name]['required'].append(arg.name)
                else:
                    ids_metadata[command.name]['optional'].append(arg.name)
                arg.required = False
                arg.arg_group = group_name

            # retrieve existing `ids` arg if it exists
            id_arg = command.loader.argument_registry.arguments[command.name].get('ids', None)
            deprecate_info = id_arg.settings.get('deprecate_info', None) if id_arg else None
            id_kwargs = {
                'metavar': 'ID',
                'help': "One or more resource IDs (space-delimited). If provided, "
                        "no other 'Resource Id' arguments should be specified.",
                'dest': 'ids' if id_arg else '_ids',
                'deprecate_info': deprecate_info,
                'nargs': '+',
                'arg_group': group_name
            }
            command.add_argument('ids', '--ids', **id_kwargs)

    def parse_ids_arguments(_, command, args):
        namespace = args
        cmd = namespace._cmd  # pylint: disable=protected-access

        # some commands have custom IDs and parsing. This will not work for that.
        if not ids_metadata.get(command, None):
            return

        ids = getattr(namespace, 'ids', getattr(namespace, '_ids', None))
        required_args = [cmd.arguments[x] for x in ids_metadata[command]['required']]
        optional_args = [cmd.arguments[x] for x in ids_metadata[command]['optional']]
        combined_args = required_args + optional_args

        if not ids:
            # ensure the required parameters are provided if --ids is not
            errors = [arg for arg in required_args if getattr(namespace, arg.name, None) is None]
            if errors:
                missing_required = ' '.join((arg.options_list[0] for arg in errors))
                raise CLIError('({} | {}) are required'.format(missing_required, '--ids'))
            return

        # show warning if names are used in conjunction with --ids
        other_values = {arg.name: {'arg': arg, 'value': getattr(namespace, arg.name, None)}
                        for arg in combined_args}
        for _, data in other_values.items():
            if data['value'] and not getattr(data['value'], 'is_default', None):
                logger.warning("option '%s' will be ignored due to use of '--ids'.",
                               data['arg'].type.settings['options_list'][0])

        # create the empty lists, overwriting any values that may already be there
        for arg in combined_args:
            setattr(namespace, arg.name, IterateValue())

        def assemble_json(ids):
            lcount = 0
            lind = None
            for i, line in enumerate(ids):
                if line == '[':
                    if lcount == 0:
                        lind = i
                    lcount += 1
                elif line == ']':
                    lcount -= 1
                    # final closed set of matching brackets
                    if lcount == 0:
                        left = lind
                        right = i + 1
                        l_comp = ids[:left]
                        m_comp = [''.join(ids[left:right])]
                        r_comp = ids[right:]
                        ids = l_comp + m_comp + r_comp
                        return assemble_json(ids)
            # base case--no more merging required
            return ids

        # reassemble JSON strings from bash
        ids = assemble_json(ids)

        # expand the IDs into the relevant fields
        full_id_list = []
        for val in ids:
            try:
                # support piping values from JSON. Does not require use of --query
                json_vals = json.loads(val)
                if not isinstance(json_vals, list):
                    json_vals = [json_vals]
                for json_val in json_vals:
                    if 'id' in json_val:
                        full_id_list += [json_val['id']]
            except ValueError:
                # supports piping of --ids to the command when using TSV. Requires use of --query
                full_id_list = full_id_list + val.splitlines()
        if full_id_list:
            setattr(namespace, '_ids', full_id_list)

        for val in full_id_list:
            if not is_valid_resource_id(val):
                raise CLIError('invalid resource ID: {}'.format(val))
            # place the ID parts into the correct property lists
            parts = parse_resource_id(val)
            for arg in combined_args:
                getattr(namespace, arg.name).append(parts[arg.type.settings['id_part']])

        # support deprecating --ids
        deprecate_info = cmd.arguments['ids'].type.settings.get('deprecate_info')
        if deprecate_info:
            if not hasattr(namespace, '_argument_deprecations'):
                setattr(namespace, '_argument_deprecations', [deprecate_info])
            else:
                namespace._argument_deprecations.append(deprecate_info)  # pylint: disable=protected-access

    cli_ctx.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, add_ids_arguments)
    cli_ctx.register_event(events.EVENT_INVOKER_POST_PARSE_ARGS, parse_ids_arguments)


def register_global_subscription_argument(cli_ctx):

    import knack.events as events

    def add_subscription_parameter(_, **kwargs):
        from azure.cli.core._completers import get_subscription_id_list

        commands_loader = kwargs['commands_loader']
        cmd_tbl = commands_loader.command_table
        subscription_kwargs = {
            'help': 'Name or ID of subscription. You can configure the default subscription '
                    'using `az account set -s NAME_OR_ID`',
            'completer': get_subscription_id_list,
            'arg_group': 'Global',
            'configured_default': 'subscription',
            'id_part': 'subscription'
        }
        for _, cmd in cmd_tbl.items():
            if 'subscription' not in cmd.arguments:
                cmd.add_argument('_subscription', '--subscription', **subscription_kwargs)

    cli_ctx.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, add_subscription_parameter)


add_usage = '--add property.listProperty <key=value, string or JSON string>'
set_usage = '--set property1.property2=<value>'
remove_usage = '--remove property.list <indexToRemove> OR --remove propertyToRemove'


def _get_child(parent, collection_name, item_name, collection_key):
    if not item_name:
        raise CLIError("Name property for collection '{}' not provided. Check your input.".format(collection_name))
    items = getattr(parent, collection_name)
    result = next((x for x in items if getattr(x, collection_key, '').lower() == item_name.lower()), None)
    if not result:
        raise CLIError("Property '{}' does not exist for key '{}'.".format(item_name, collection_key))
    return result


def _get_operations_tmpl(cmd, custom_command=False):
    operations_tmpl = cmd.command_kwargs.get('operations_tmpl') or \
        cmd.command_kwargs.get(get_command_type_kwarg(custom_command)).settings['operations_tmpl']
    if not operations_tmpl:
        raise CLIError("command authoring error: cmd '{}' does not have an operations_tmpl.".format(cmd.name))
    return operations_tmpl


def _get_client_factory(_, custom_command=False, **kwargs):
    command_type = kwargs.get(get_command_type_kwarg(custom_command), None)
    factory = kwargs.get('client_factory', None)
    if not factory and command_type:
        factory = command_type.settings.get('client_factory', None)
    return factory


def get_arguments_loader(context, getter_op, cmd_args=None):
    getter_args = dict(extract_args_from_signature(context.get_op_handler(getter_op), excluded_params=EXCLUDED_PARAMS))
    cmd_args = cmd_args or {}
    cmd_args.update(getter_args)
    cmd_args['cmd'] = CLICommandArgument('cmd', arg_type=ignore_type)
    return cmd_args


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

    def set_arguments_loader():
        return dict(extract_args_from_signature(context.get_op_handler(setter_op), excluded_params=EXCLUDED_PARAMS))

    def function_arguments_loader():
        if not custom_function_op:
            return {}

        custom_op = context.get_op_handler(custom_function_op)
        context._apply_doc_string(custom_op, kwargs)  # pylint: disable=protected-access
        return dict(extract_args_from_signature(custom_op, excluded_params=EXCLUDED_PARAMS))

    def generic_update_arguments_loader():
        arguments = get_arguments_loader(context, getter_op)
        arguments.update(set_arguments_loader())
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
        arguments['force_string'] = CLICommandArgument(
            'force_string', action='store_true', arg_group=group_name,
            help="When using 'set' or 'add', preserve string literals instead of attempting to convert to JSON."
        )
        return [(k, v) for k, v in arguments.items()]

    def _extract_handler_and_args(args, commmand_kwargs, op, context):
        from azure.cli.core.commands.client_factory import resolve_client_arg_name
        factory = _get_client_factory(name, **commmand_kwargs)
        client = None
        if factory:
            try:
                client = factory(context.cli_ctx)
            except TypeError:
                client = factory(context.cli_ctx, args)

        client_arg_name = resolve_client_arg_name(op, kwargs)
        op_handler = context.get_op_handler(op)
        raw_args = dict(extract_args_from_signature(op_handler, excluded_params=EXCLUDED_NON_CLIENT_PARAMS))
        op_args = {key: val for key, val in args.items() if key in raw_args}
        if client_arg_name in raw_args:
            op_args[client_arg_name] = client
        return op_handler, op_args

    def handler(args):  # pylint: disable=too-many-branches,too-many-statements
        cmd = args.get('cmd')
        context_copy = copy.copy(context)
        context_copy.cli_ctx = cmd.cli_ctx
        force_string = args.get('force_string', False)
        ordered_arguments = args.pop('ordered_arguments', [])
        for item in ['properties_to_add', 'properties_to_set', 'properties_to_remove']:
            if args[item]:
                raise CLIError("Unexpected '{}' was not empty.".format(item))
            del args[item]

        getter, getterargs = _extract_handler_and_args(args, cmd.command_kwargs, getter_op, context_copy)
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
            custom_function, custom_func_args = _extract_handler_and_args(
                args, cmd.command_kwargs, custom_function_op, context_copy)
            if child_collection_prop_name:
                parent = custom_function(instance=instance, parent=parent, **custom_func_args)
            else:
                instance = custom_function(instance=instance, **custom_func_args)

        # apply generic updates after custom updates
        setter, setterargs = _extract_handler_and_args(args, cmd.command_kwargs, setter_op, context_copy)

        for arg in ordered_arguments:
            arg_type, arg_values = arg
            if arg_type == '--set':
                try:
                    for expression in arg_values:
                        set_properties(instance, expression, force_string)
                except ValueError:
                    raise CLIError('invalid syntax: {}'.format(set_usage))
            elif arg_type == '--add':
                try:
                    add_properties(instance, arg_values, force_string)
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


def _cli_wait_command(context, name, getter_op, custom_command=False, **kwargs):

    if not isinstance(getter_op, string_types):
        raise ValueError("Getter operation must be a string. Got '{}'".format(type(getter_op)))

    factory = _get_client_factory(name, custom_command=custom_command, **kwargs)

    def generic_wait_arguments_loader():
        cmd_args = get_arguments_loader(context, getter_op)

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

        context_copy = copy.copy(context)
        getter_args = dict(extract_args_from_signature(context.get_op_handler(getter_op),
                                                       excluded_params=EXCLUDED_NON_CLIENT_PARAMS))
        cmd = args.get('cmd') if 'cmd' in getter_args else args.pop('cmd')
        context_copy.cli_ctx = cmd.cli_ctx
        operations_tmpl = _get_operations_tmpl(cmd, custom_command=custom_command)
        client_arg_name = resolve_client_arg_name(operations_tmpl, kwargs)
        try:
            client = factory(context_copy.cli_ctx) if factory else None
        except TypeError:
            client = factory(context_copy.cli_ctx, args) if factory else None
        if client and (client_arg_name in getter_args):
            args[client_arg_name] = client

        getter = context_copy.get_op_handler(getter_op)

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

        progress_indicator = context_copy.cli_ctx.get_progress_controller()
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
            except Exception:  # pylint: disable=broad-except
                progress_indicator.stop()
                raise

            time.sleep(interval)

        progress_indicator.end()
        return CLIError('Wait operation timed-out after {} seconds'.format(timeout))

    context._cli_command(name, handler=handler, argument_loader=generic_wait_arguments_loader, **kwargs)  # pylint: disable=protected-access


def _cli_show_command(context, name, getter_op, custom_command=False, **kwargs):

    if not isinstance(getter_op, string_types):
        raise ValueError("Getter operation must be a string. Got '{}'".format(type(getter_op)))

    factory = _get_client_factory(name, custom_command=custom_command, **kwargs)

    def generic_show_arguments_loader():
        cmd_args = get_arguments_loader(context, getter_op)
        return [(k, v) for k, v in cmd_args.items()]

    def description_loader():
        return extract_full_summary_from_signature(context.get_op_handler(getter_op))

    def handler(args):
        from azure.cli.core.commands.client_factory import resolve_client_arg_name
        context_copy = copy.copy(context)
        getter_args = dict(extract_args_from_signature(context_copy.get_op_handler(getter_op),
                                                       excluded_params=EXCLUDED_NON_CLIENT_PARAMS))
        cmd = args.get('cmd') if 'cmd' in getter_args else args.pop('cmd')
        context_copy.cli_ctx = cmd.cli_ctx
        operations_tmpl = _get_operations_tmpl(cmd, custom_command=custom_command)
        client_arg_name = resolve_client_arg_name(operations_tmpl, kwargs)
        try:
            client = factory(context_copy.cli_ctx) if factory else None
        except TypeError:
            client = factory(context_copy.cli_ctx, args) if factory else None

        if client and (client_arg_name in getter_args):
            args[client_arg_name] = client

        getter = context_copy.get_op_handler(getter_op)
        try:
            return getter(**args)
        except Exception as ex:  # pylint: disable=broad-except
            show_exception_handler(ex)
    context._cli_command(name, handler=handler, argument_loader=generic_show_arguments_loader,  # pylint: disable=protected-access
                         description_loader=description_loader, **kwargs)


def show_exception_handler(ex):
    if getattr(getattr(ex, 'response', ex), 'status_code', None) == 404:
        logger.error(getattr(ex, 'message', ex))
        import sys
        sys.exit(3)
    raise ex


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


def set_properties(instance, expression, force_string):
    key, value = _split_key_value_pair(expression)

    if not force_string:
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
        set_properties(parent, '{}={{}}'.format(parent_name), force_string)
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


def add_properties(instance, argument_values, force_string):
    # The first argument indicates the path to the collection to add to.
    argument_values = list(argument_values)
    list_attribute_path = _get_internal_path(argument_values.pop(0))
    list_to_add_to = _find_property(instance, list_attribute_path)

    if list_to_add_to is None:
        parent = _find_property(instance, list_attribute_path[:-1])
        set_properties(parent, '{}=[]'.format(list_attribute_path[-1]), force_string)
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

            if not force_string:
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
    # The first argument indicates the path to the collection to remove from.
    argument_values = list(argument_values) if isinstance(argument_values, list) else [argument_values]

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
            if len(matches) > 1:
                raise CLIError("non-unique key '{}' found multiple matches on {}. Key must be unique."
                               .format(key, path[-2]))
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
        if part in getattr(instance, 'additional_properties', {}):
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
    from msrestazure.azure_exceptions import CloudError

    # get
    resource = getter()
    resource = setter(resource)

    # create role assignment:
    if identity_scope:
        principal_id = resource.identity.principal_id

        identity_role_id = resolve_role_id(cli_ctx, identity_role, identity_scope)
        assignments_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION).role_assignments
        RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                                 'RoleAssignmentCreateParameters', mod='models',
                                                 operation_group='role_assignments')
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
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION).role_definitions

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


def get_arm_resource_by_id(cli_ctx, arm_id, api_version=None):
    from msrestazure.tools import parse_resource_id, is_valid_resource_id

    if not is_valid_resource_id(arm_id):
        raise CLIError("'{}' is not a valid ID.".format(arm_id))

    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

    if not api_version:

        parts = parse_resource_id(arm_id)

        # to retrieve the provider, we need to know the namespace
        namespaces = {k: v for k, v in parts.items() if 'namespace' in k}

        # every ARM ID has at least one namespace, so start with that
        namespace = namespaces.pop('namespace')
        namespaces.pop('resource_namespace')
        # find the most specific child namespace (if any) and use that value instead
        highest_child = 0
        for k, v in namespaces.items():
            child_number = int(k.split('_')[2])
            if child_number > highest_child:
                namespace = v
                highest_child = child_number

        # retrieve provider info for the namespace
        provider = client.providers.get(namespace)

        # assemble the resource type key used by the provider list operation.  type1/type2/type3/...
        resource_type_str = ''
        if not highest_child:
            resource_type_str = parts['resource_type']
        else:
            types = {int(k.split('_')[2]): v for k, v in parts.items() if k.startswith('child_type')}
            for k in sorted(types.keys()):
                if k < highest_child:
                    continue
                resource_type_str = '{}{}/'.format(resource_type_str, parts['child_type_{}'.format(k)])
            resource_type_str = resource_type_str.rstrip('/')

        api_version = None
        rt = next((t for t in provider.resource_types if t.resource_type.lower() == resource_type_str.lower()), None)
        if not rt:
            from azure.cli.core.parser import IncorrectUsageError
            raise IncorrectUsageError('Resource type {} not found.'.format(resource_type_str))
        try:
            # if the service specifies, use the default API version
            api_version = rt.default_api_version
        except AttributeError:
            # if the service doesn't specify, use the most recent non-preview API version unless there is only a
            # single API version. API versions are returned by the service in a sorted list
            api_version = next((x for x in rt.api_versions if not x.endswith('preview')), rt.api_versions[0])

    return client.resources.get_by_id(arm_id, api_version)
