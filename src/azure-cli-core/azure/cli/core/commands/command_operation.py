# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse
from six import string_types, get_method_function
from azure.cli.core import AzCommandsLoader, EXCLUDED_PARAMS
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.arguments import CLICommandArgument, ignore_type


class BaseCommandOperation:

    def __init__(self, ctx, **kwargs):
        if not isinstance(ctx, AzCommandsLoader):
            raise TypeError("'ctx' expected type '{}'. Got: '{}'".format(AzCommandsLoader.__name__, type(ctx)))
        self.ctx = ctx
        self.cmd = None
        self.kwargs = kwargs
        self.client_factory = kwargs.get('client_factory')
        self.operation_group = kwargs.get('operation_group')

    @property
    def cli_ctx(self):
        return self.cmd.cli_ctx if self.cmd else self.ctx.cli_ctx

    def handler(self, command_args):
        raise NotImplementedError()

    def arguments_loader(self):
        raise NotImplementedError()

    def description_loader(self):
        raise NotImplementedError()

    def get_op_handler(self, operation):
        """ Import and load the operation handler """
        # Patch the unversioned sdk path to include the appropriate API version for the
        # resource type in question.
        from importlib import import_module
        import types

        from azure.cli.core.profiles import AZURE_API_PROFILES
        from azure.cli.core.profiles._shared import get_versioned_sdk_path

        for rt in AZURE_API_PROFILES[self.cli_ctx.cloud.profile]:
            if operation.startswith(rt.import_prefix + '.'):
                operation = operation.replace(rt.import_prefix,
                                              get_versioned_sdk_path(self.cli_ctx.cloud.profile, rt,
                                                                     operation_group=self.operation_group))

        try:
            mod_to_import, attr_path = operation.split('#')
            handler = import_module(mod_to_import)
            for part in attr_path.split('.'):
                handler = getattr(handler, part)
            if isinstance(handler, types.FunctionType):
                return handler
            return get_method_function(handler)
        except (ValueError, AttributeError):
            raise ValueError("The operation '{}' is invalid.".format(operation))

    def load_getter_op_arguments(self, getter_op, cmd_args=None):
        op = self.get_op_handler(getter_op)
        getter_args = dict(
            extract_args_from_signature(op, excluded_params=EXCLUDED_PARAMS))
        cmd_args = cmd_args or {}
        cmd_args.update(getter_args)
        cmd_args['cmd'] = CLICommandArgument('cmd', arg_type=ignore_type)
        return cmd_args

    def apply_doc_string(self, handler):
        return self.ctx._apply_doc_string(handler, self.kwargs)  # pylint: disable=protected-access

    def load_op_description(self, handler=None):
        if handler is None:
            def default_handler():
                """"""  # default_handler should have __doc__ property
            handler = default_handler
        self.apply_doc_string(handler)
        return extract_full_summary_from_signature(handler)

    def resolve_client_arg_name(self, operation):
        from azure.cli.core.commands.client_factory import resolve_client_arg_name
        return resolve_client_arg_name(operation, self.kwargs)


class CommandOperation(BaseCommandOperation):

    def __init__(self, ctx, operation, **kwargs):
        if not isinstance(operation, string_types):
            raise TypeError("operation must be a string. Got '{}'".format(operation))
        super(CommandOperation, self).__init__(ctx, **kwargs)
        self.operation = operation

    def handler(self, command_args):
        from azure.cli.core.util import get_arg_list, augment_no_wait_handler_args

        op = self.get_op_handler(self.operation)
        op_args = get_arg_list(op)
        cmd = command_args.get('cmd') if 'cmd' in op_args else command_args.pop('cmd')

        client = self.client_factory(cmd.cli_ctx, command_args) if self.client_factory else None
        supports_no_wait = self.kwargs.get('supports_no_wait', None)
        if supports_no_wait:
            no_wait_enabled = command_args.pop('no_wait', False)
            augment_no_wait_handler_args(no_wait_enabled, op, command_args)
        if client:
            client_arg_name = self.resolve_client_arg_name(self.operation)
            if client_arg_name in op_args:
                command_args[client_arg_name] = client
        return op(**command_args)

    def arguments_loader(self):
        op = self.get_op_handler(self.operation)
        self.apply_doc_string(op)
        cmd_args = list(extract_args_from_signature(op, excluded_params=self.ctx.excluded_command_handler_args))
        return cmd_args

    def description_loader(self):
        op = self.get_op_handler(self.operation)
        return self.load_op_description(op)


class WaitCommandOperation(BaseCommandOperation):

    def __init__(self, ctx, operation, **kwargs):
        if not isinstance(operation, string_types):
            raise TypeError("operation must be a string. Got '{}'".format(operation))
        super(WaitCommandOperation, self).__init__(ctx, **kwargs)
        self.operation = operation

    def handler(self, command_args):    # pylint: disable=too-many-statements
        from msrest.exceptions import ClientException
        from azure.core.exceptions import HttpResponseError
        from knack.util import CLIError
        from azure.cli.core.commands.arm import EXCLUDED_NON_CLIENT_PARAMS, verify_property

        import time

        op = self.get_op_handler(self.operation)

        getter_args = dict(extract_args_from_signature(op, excluded_params=EXCLUDED_NON_CLIENT_PARAMS))
        self.cmd = command_args.get('cmd') if 'cmd' in getter_args else command_args.pop('cmd')

        client_arg_name = self.resolve_client_arg_name(self.operation)
        try:
            client = self.client_factory(self.cli_ctx) if self.client_factory else None
        except TypeError:
            client = self.client_factory(self.cli_ctx, command_args) if self.client_factory else None
        if client and (client_arg_name in getter_args):
            command_args[client_arg_name] = client

        getter = self.get_op_handler(self.operation)

        timeout = command_args.pop('timeout')
        interval = command_args.pop('interval')
        wait_for_created = command_args.pop('created')
        wait_for_deleted = command_args.pop('deleted')
        wait_for_updated = command_args.pop('updated')
        wait_for_exists = command_args.pop('exists')
        custom_condition = command_args.pop('custom')
        if not any([wait_for_created, wait_for_updated, wait_for_deleted,
                    wait_for_exists, custom_condition]):
            raise CLIError(
                "incorrect usage: --created | --updated | --deleted | --exists | --custom JMESPATH")

        progress_indicator = self.cli_ctx.get_progress_controller()
        progress_indicator.begin()
        for _ in range(0, timeout, interval):
            try:
                progress_indicator.add(message='Waiting')
                instance = getter(**command_args)
                if wait_for_exists:
                    progress_indicator.end()
                    return None
                provisioning_state = self._get_provisioning_state(instance)
                # until we have any needs to wait for 'Failed', let us bail out on this
                if provisioning_state:
                    provisioning_state = provisioning_state.lower()
                if provisioning_state == 'failed':
                    progress_indicator.stop()
                    raise CLIError('The operation failed')
                if ((wait_for_created or wait_for_updated) and provisioning_state == 'succeeded') or \
                        custom_condition and bool(verify_property(instance, custom_condition)):
                    progress_indicator.end()
                    return None
            except (ClientException, HttpResponseError) as ex:
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

    @staticmethod
    def _get_provisioning_state(instance):
        provisioning_state = getattr(instance, 'provisioning_state', None)
        if not provisioning_state:
            # some SDK, like resource-group, has 'provisioning_state' under 'properties'
            properties = getattr(instance, 'properties', None)
            if properties:
                provisioning_state = getattr(properties, 'provisioning_state', None)
                # some SDK, like keyvault, has 'provisioningState' under 'properties.additional_properties'
                if not provisioning_state:
                    additional_properties = getattr(properties, 'additional_properties', {})
                    provisioning_state = additional_properties.get('provisioningState')
        return provisioning_state

    def arguments_loader(self):
        cmd_args = self.load_getter_op_arguments(self.operation)

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

    def description_loader(self):
        return self.load_op_description()


class ShowCommandOperation(BaseCommandOperation):

    def __init__(self, ctx, operation, **kwargs):
        if not isinstance(operation, string_types):
            raise TypeError("operation must be a string. Got '{}'".format(operation))
        super(ShowCommandOperation, self).__init__(ctx, **kwargs)
        self.operation = operation

    def handler(self, command_args):
        from azure.cli.core.commands.arm import show_exception_handler, EXCLUDED_NON_CLIENT_PARAMS

        op = self.get_op_handler(self.operation)
        getter_args = dict(extract_args_from_signature(op, excluded_params=EXCLUDED_NON_CLIENT_PARAMS))

        self.cmd = command_args.get('cmd') if 'cmd' in getter_args else command_args.pop('cmd')

        client_arg_name = self.resolve_client_arg_name(self.operation)
        try:
            client = self.client_factory(self.cli_ctx) if self.client_factory else None
        except TypeError:
            client = self.client_factory(self.cli_ctx, command_args) if self.client_factory else None

        if client and (client_arg_name in getter_args):
            command_args[client_arg_name] = client

        op = self.get_op_handler(self.operation)
        try:
            return op(**command_args)
        except Exception as ex:  # pylint: disable=broad-except
            show_exception_handler(ex)

    def arguments_loader(self):
        cmd_args = self.load_getter_op_arguments(self.operation)
        return [(k, v) for k, v in cmd_args.items()]

    def description_loader(self):
        op = self.get_op_handler(self.operation)
        return self.load_op_description(op)


class GenericUpdateCommandOperation(BaseCommandOperation):     # pylint: disable=too-many-instance-attributes

    class OrderedArgsAction(argparse.Action):  # pylint:disable=too-few-public-methods
        def __call__(self, parser, namespace, values, option_string=None):
            if not getattr(namespace, 'ordered_arguments', None):
                setattr(namespace, 'ordered_arguments', [])
            namespace.ordered_arguments.append((option_string, values))

    def __init__(self, ctx, getter_op, setter_op, setter_arg_name, custom_function_op, child_collection_prop_name,
                 child_collection_key, child_arg_name, **kwargs):
        if not isinstance(getter_op, string_types):
            raise TypeError("Getter operation must be a string. Got '{}'".format(getter_op))
        if not isinstance(setter_op, string_types):
            raise TypeError("Setter operation must be a string. Got '{}'".format(setter_op))
        if custom_function_op and not isinstance(custom_function_op, string_types):
            raise TypeError("Custom function operation must be a string. Got '{}'".format(custom_function_op))
        super(GenericUpdateCommandOperation, self).__init__(ctx, **kwargs)

        self.getter_operation = getter_op
        self.setter_operation = setter_op
        self.custom_function_operation = custom_function_op
        self.setter_arg_name = setter_arg_name
        self.child_collection_prop_name = child_collection_prop_name
        self.child_collection_key = child_collection_key
        self.child_arg_name = child_arg_name

    def handler(self, command_args):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
        from knack.util import CLIError
        from azure.cli.core.commands import cached_get, cached_put, _is_poller
        from azure.cli.core.util import find_child_item, augment_no_wait_handler_args
        from azure.cli.core.commands.arm import add_usage, remove_usage, set_usage,\
            add_properties, remove_properties, set_properties

        self.cmd = command_args.get('cmd')

        force_string = command_args.get('force_string', False)
        ordered_arguments = command_args.pop('ordered_arguments', [])
        dest_names = self.child_arg_name.split('.')
        child_names = [command_args.get(key, None) for key in dest_names]
        for item in ['properties_to_add', 'properties_to_set', 'properties_to_remove']:
            if command_args[item]:
                raise CLIError("Unexpected '{}' was not empty.".format(item))
            del command_args[item]

        getter, getterargs = self._extract_handler_and_args(command_args, self.getter_operation)

        if self.child_collection_prop_name:
            parent = cached_get(self.cmd, getter, **getterargs)
            instance = find_child_item(
                parent, *child_names, path=self.child_collection_prop_name, key_path=self.child_collection_key)
        else:
            parent = None
            instance = cached_get(self.cmd, getter, **getterargs)

        # pass instance to the custom_function, if provided
        if self.custom_function_operation:
            custom_function, custom_func_args = self._extract_handler_and_args(
                command_args, self.custom_function_operation)
            if self.child_collection_prop_name:
                parent = custom_function(instance=instance, parent=parent, **custom_func_args)
            else:
                instance = custom_function(instance=instance, **custom_func_args)

        # apply generic updates after custom updates
        setter, setterargs = self._extract_handler_and_args(command_args, self.setter_operation)

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
        setterargs[self.setter_arg_name] = parent if self.child_collection_prop_name else instance

        # Handle no-wait
        supports_no_wait = self.cmd.command_kwargs.get('supports_no_wait', None)
        if supports_no_wait:
            no_wait_enabled = command_args.get('no_wait', False)
            augment_no_wait_handler_args(no_wait_enabled,
                                         setter,
                                         setterargs)
        else:
            no_wait_param = self.cmd.command_kwargs.get('no_wait_param', None)
            if no_wait_param:
                setterargs[no_wait_param] = command_args[no_wait_param]

        if self.setter_arg_name == 'parameters':
            result = cached_put(self.cmd, setter, **setterargs)
        else:
            result = cached_put(self.cmd, setter, setterargs[self.setter_arg_name],
                                setter_arg_name=self.setter_arg_name, **setterargs)

        if supports_no_wait and no_wait_enabled:
            return None

        no_wait_param = self.cmd.command_kwargs.get('no_wait_param', None)
        if no_wait_param and setterargs.get(no_wait_param, None):
            return None

        if _is_poller(result):
            result = result.result()

        if self.child_collection_prop_name:
            result = find_child_item(
                result, *child_names, path=self.child_collection_prop_name, key_path=self.child_collection_key)
        return result

    def _extract_handler_and_args(self, args, operation):
        from azure.cli.core.commands.arm import EXCLUDED_NON_CLIENT_PARAMS

        client = None
        if self.client_factory:
            try:
                client = self.client_factory(self.cli_ctx)
            except TypeError:
                client = self.client_factory(self.cli_ctx, args)

        client_arg_name = self.resolve_client_arg_name(operation)
        op = self.get_op_handler(operation)
        raw_args = dict(extract_args_from_signature(op, excluded_params=EXCLUDED_NON_CLIENT_PARAMS))
        op_args = {key: val for key, val in args.items() if key in raw_args}
        if client_arg_name in raw_args:
            op_args[client_arg_name] = client
        return op, op_args

    def arguments_loader(self):
        from azure.cli.core.commands.arm import set_usage, add_usage, remove_usage

        arguments = self.load_getter_op_arguments(self.getter_operation)
        arguments.update(self._set_arguments_loader())
        arguments.update(self._function_arguments_loader())
        arguments.pop('instance', None)  # inherited from custom_function(instance, ...)
        arguments.pop('parent', None)
        arguments.pop('expand', None)  # possibly inherited from the getter
        arguments.pop(self.setter_arg_name, None)

        # Add the generic update parameters
        group_name = 'Generic Update'
        arguments['properties_to_set'] = CLICommandArgument(
            'properties_to_set', options_list=['--set'], nargs='+',
            action=self.OrderedArgsAction, default=[],
            help='Update an object by specifying a property path and value to set.  Example: {}'.format(set_usage),
            metavar='KEY=VALUE', arg_group=group_name
        )
        arguments['properties_to_add'] = CLICommandArgument(
            'properties_to_add', options_list=['--add'], nargs='+',
            action=self.OrderedArgsAction, default=[],
            help='Add an object to a list of objects by specifying a path and '
                 'key value pairs.  Example: {}'.format(add_usage),
            metavar='LIST KEY=VALUE', arg_group=group_name
        )
        arguments['properties_to_remove'] = CLICommandArgument(
            'properties_to_remove', options_list=['--remove'], nargs='+',
            action=self.OrderedArgsAction, default=[],
            help='Remove a property or an element from a list.  Example: {}'.format(remove_usage),
            metavar='LIST INDEX', arg_group=group_name
        )
        arguments['force_string'] = CLICommandArgument(
            'force_string', action='store_true', arg_group=group_name,
            help="When using 'set' or 'add', preserve string literals instead of attempting to convert to JSON."
        )
        return [(k, v) for k, v in arguments.items()]

    def _set_arguments_loader(self):
        op = self.get_op_handler(self.setter_operation)
        return dict(extract_args_from_signature(op, excluded_params=EXCLUDED_PARAMS))

    def _function_arguments_loader(self):
        if not self.custom_function_operation:
            return {}
        op = self.get_op_handler(self.custom_function_operation)
        self.apply_doc_string(op)  # pylint: disable=protected-access
        return dict(extract_args_from_signature(op, excluded_params=EXCLUDED_PARAMS))

    def description_loader(self):
        return self.load_op_description()
