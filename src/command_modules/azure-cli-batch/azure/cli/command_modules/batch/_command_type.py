# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import json
import re

from six import string_types
from six.moves.urllib.parse import urlsplit  # pylint: disable=import-error

from azure.cli.command_modules.batch import _validators as validators
from azure.cli.command_modules.batch import _format as transformers
from azure.cli.core.commands import (
    CONFIRM_PARAM_NAME,
    command_table,
    command_module_map,
    CliCommand,
    CliCommandArgument,
    get_op_handler)
from azure.cli.core.commands._introspection import (
    extract_full_summary_from_signature,
    extract_args_from_signature)

_CLASS_NAME = re.compile(r"<(.*?)>")  # Strip model name from class docstring
_UNDERSCORE_CASE = re.compile('(?!^)([A-Z]+)')  # Convert from CamelCase to underscore_case
FLATTEN = 3  # The level of complex object namespace to flatten.
IGNORE_OPTIONS = {  # Options parameters that should not be exposed as arguments.
    'ocp_date',
    'timeout',
    'client_request_id',
    'return_client_request_id',
    'max_results'
}
IGNORE_PARAMETERS = [
    'callback',
    'thumbprint_algorithm',
    'display_name',
    'common_environment_settings'
]
FLATTEN_OPTIONS = {  # Options to be flattened into multiple arguments.
    'ocp_range': {'start_range': "The byte range to be retrieved. "
                                 "If not set the file will be retrieved from the beginning.",
                  'end_range': "The byte range to be retrieved. "
                               "If not set the file will be retrieved to the end."}
}
BASIC_TYPES = {  # Argument types that should not be flattened.
    'str',
    'int',
    'bool',
    'float',
    'long',
    'duration',
    'iso-8601',
    'rfc-1123',
    'date',
    'decimal',
    'unix-time'
}
QUALIFIED_PROPERTIES = [  # Common argument names the should always be prefixed by their context
    'id',
    'display_name',
    'command_line',
    'environment_settings',
    'wait_for_success',
    'max_task_retry_count',
    'constraints_max_task_retry_count',
    'max_wall_clock_time',
    'constraints_max_wall_clock_time',
    'retention_time',
    'constraints_retention_time',
    'application_package_references',
    'resource_files',
    'user_name'
]


def _load_model(name):
    """Load a model class from the SDK in order to inspect for
    parameter names and whether they're required.
    :param str name: The model class name to load.
    :returns: Model class
    """
    if name.startswith('azure.'):
        namespace = name.split('.')
    else:
        namespace = ['azure', 'batch', 'models', name]
    model = __import__(namespace[0])
    for level in namespace[1:]:
        model = getattr(model, level)
    return model


def _join_prefix(prefix, name):
    """Filter certain superflous parameter name suffixes
    from argument names.
    :param str prefix: The potential prefix that will be filtered.
    :param str name: The arg name to be prefixed.
    :returns: Combined name with prefix.
    """
    if prefix.endswith("_specification"):
        return prefix[:-14] + "_" + name
    elif prefix.endswith("_patch_parameter"):
        return prefix[:-16] + "_" + name
    elif prefix.endswith("_update_parameter"):
        return prefix[:-17] + "_" + name
    return prefix + "_" + name


def _build_prefix(arg, param, path):
    """Recursively build a command line argument prefix from the request
    parameter object to avoid name conflicts.
    :param str arg: Currenct argument name.
    :param str param: Original request parameter name.
    :param str path: Request parameter namespace.
    """
    prefix_list = path.split('.')
    if len(prefix_list) == 1:
        return arg
    resolved_name = _join_prefix(prefix_list[0], param)
    if arg == resolved_name:
        return arg
    for prefix in prefix_list[1:]:
        new_name = _join_prefix(prefix, param)
        if new_name == arg:
            return resolved_name
        resolved_name = new_name
    return resolved_name


def find_param_type(model, param):
    """Parse the parameter type from the model docstring.
    :param class model: Model class.
    :param str param: The name of the parameter.
    :returns: str
    """
    # Search for the :type param_name: in the docstring
    pattern = r":type {}:(.*?)\n(\s*:param |\s*:rtype:|\s*:raises:|\s*\"{{3}})".format(param)
    param_type = re.search(pattern, model.__doc__, re.DOTALL)
    return re.sub(r"\n\s*", "", param_type.group(1).strip())


def find_param_help(model, param):
    """Parse the parameter help info from the model docstring.
    :param class model: Model class.
    :param str param: The name of the parameter.
    :returns: str
    """
    # Search for :param param_name: in the docstring
    pattern = r":param {}:(.*?)\n\s*:type ".format(param)
    param_doc = re.search(pattern, model.__doc__, re.DOTALL)
    return re.sub(r"\n\s*", " ", param_doc.group(1).strip())


def find_return_type(model):
    """Parse the parameter help info from the model docstring.
    :param class model: Model class.
    :param str param: The name of the parameter.
    :returns: str
    """
    # Search for :rtype: in the docstring
    pattern = r":rtype: (.*?)\n(\s*:rtype:|\s*:raises:|\"\"\")"
    return_type = re.search(pattern, model.__doc__, re.DOTALL)
    if return_type:
        return re.sub(r"\n\s*", "", return_type.group(1))


def enum_value(enum_str):
    """Strip chars around enum value str.
    :param str enum_str: Enum value.
    """
    return enum_str.strip(' \'')


def class_name(type_str):
    """Extract class name from type docstring.
    :param str type_str: Parameter type docstring.
    :returns: class name
    """
    return _CLASS_NAME.findall(type_str)[0]


def operations_name(class_str):
    """Convert the operations class name into Python case.
    :param str class_str: The class name.
    """
    if class_str.endswith('Operations'):
        class_str = class_str[:-10]
    return _UNDERSCORE_CASE.sub(r'_\1', class_str).lower()


def full_name(arg_details):
    """Create a full path to the complex object parameter of a
    given argument.
    :param dict arg_details: The details of the argument.
    :returns: str
    """
    return ".".join([arg_details['path'], arg_details['root']])


def group_title(path):
    """Create a group title from the argument path.
    :param str path: The complex object path of the argument.
    :returns: str
    """

    def filter_group(group):
        for suffix in ["_patch_parameter", "_update_parameter", "_parameter"]:
            if group.endswith(suffix):
                group = group[:0 - len(suffix)]
        return group

    group_path = path.split('.')
    group_path = list(map(filter_group, group_path))
    title = ': '.join(group_path)
    for group in group_path:
        title = title.replace(group, " ".join([n.title() for n in group.split('_')]), 1)
    return title


def arg_name(name):
    """Convert snake case argument name to a command line name.
    :param str name: The argument parameter name.
    :returns: str
    """
    return "--" + name.replace('_', '-')


def format_options_name(operation):
    """Format the name of the request options parameter from the
    operation name and path.
    :param str operation: Operation path
    :returns: str - options parameter name.
    """
    operation = operation.split('#')[-1]
    op_class, op_function = operation.split('.')
    op_class = operations_name(op_class)
    return "{}_{}_options".format(op_class, op_function)


class BatchArgumentTree(object):
    """Dependency tree parser for arguments of complex objects"""

    def __init__(self, validator, silent):
        self._arg_tree = {}
        self._request_param = {}
        self._custom_validator = validator
        self._silent_args = silent
        self.done = False

    def __iter__(self):
        """Iterate over arguments"""
        for arg, details in self._arg_tree.items():
            yield arg, details

    def _is_silent(self, name):
        """Whether argument should not be exposed"""
        arg = self._arg_tree[name]
        full_path = full_name(arg)
        return arg['path'] in self._silent_args or full_path in self._silent_args

    def _is_bool(self, name):
        """Whether argument value is a boolean"""
        return self._arg_tree[name]['type'] == 'bool'

    def _is_list(self, name):
        """Whether argument value is a list"""
        return self._arg_tree[name]['type'].startswith('[')

    def _is_datetime(self, name):
        """Whether argument value is a timestamp"""
        return self._arg_tree[name]['type'] in ['iso-8601', 'rfc-1123']

    def _is_duration(self, name):
        """Whether argument is value is a duration"""
        return self._arg_tree[name]['type'] == 'duration'

    def _help(self, name, text):
        """Append phrase to existing help text"""
        self._arg_tree[name]['options']['help'] += ' ' + text

    def _get_children(self, group):
        """Find all the arguments under to a specific complex argument group.
        :param str group: The namespace of the complex parameter.
        :returns: The names of the related arugments.
        """
        return [arg for arg, value in self._arg_tree.items() if value['path'].startswith(group)]

    def _get_siblings(self, group):
        """Find all the arguments at the same level of a specific complex argument group.
        :param str group: The namespace of the complex parameter.
        :returns: The names of the related arugments.
        """
        return [arg for arg, value in self._arg_tree.items() if value['path'] == group]

    def _parse(self, namespace, path, required):
        """Parse dependency tree to list all required command line arguments based on
        current inputs.
        :param namespace: The namespace container all current argument inputs
        :param path: The current complex object path
        :param required: Whether the args in this object path are required
        """
        required_args = []
        children = self._get_children(path)
        if not required:
            if not any([getattr(namespace, n) for n in children]):
                return []
        siblings = self._get_siblings(path)
        if not siblings:
            raise ValueError("Invalid argmuent dependency tree")  # TODO
        dependencies = self._arg_tree[siblings[0]]['dependencies']
        for child_arg in children:
            if child_arg in required_args:
                continue
            details = self._arg_tree[child_arg]
            if full_name(details) in dependencies:
                required_args.append(child_arg)
            elif details['path'] in dependencies:
                required_args.extend(self._parse(namespace, details['path'], True))
            elif details['path'] == path:
                continue
            else:
                required_args.extend(self._parse(namespace, details['path'], False))
        return set(required_args)

    def set_request_param(self, name, model):
        """Set the name of the parameter that will be serialized for the
        request body.
        :param str name: The name of the parameter
        :param str model: The name of the class
        """
        self._request_param['name'] = name
        self._request_param['model'] = model.split('.')[-1]

    def deserialize_json(self, client, kwargs, json_obj):
        """Deserialize the contents of a JSON file into the request body
        parameter.
        :param client: An Azure Batch SDK client
        :param dict kwargs: The request kwargs
        :param dict json_obj: The loaded JSON content
        """
        from msrest.exceptions import DeserializationError
        message = "Failed to deserialized JSON file into object {}"
        try:
            kwargs[self._request_param['name']] = client._deserialize(  # pylint: disable=protected-access
                self._request_param['model'], json_obj)
        except DeserializationError as error:
            message += ": {}".format(error)
            raise ValueError(message.format(self._request_param['model']))
        else:
            if kwargs[self._request_param['name']] is None:
                raise ValueError(message.format(self._request_param['model']))

    def queue_argument(self, name=None, path=None, root=None,
                       options=None, type=None,  # pylint: disable=redefined-builtin
                       dependencies=None):
        """Add pending command line argument
        :param str name: The name of the command line argument.
        :param str path: The complex object path to the parameter.
        :param str root: The original name of the parameter.
        :param dict options: The kwargs to be used to instantiate CliCommandArgument.
        :param list dependencies: A list of complete paths to other parameters that
         are required if this parameter is set.
        """
        self._arg_tree[name] = {
            'path': path,
            'root': root,
            'options': options,
            'type': type,
            'dependencies': [".".join([path, arg]) for arg in dependencies]
        }

    def dequeue_argument(self, name):
        """Remove pending command line argument for modification
        :param str name: The command line argument to remove.
        :returns: The details of the argument.
        """
        return self._arg_tree.pop(name, {})

    def compile_args(self):
        """Generator to convert pending arguments into CliCommandArgument
        objects.
        """
        for name, details in self._arg_tree.items():
            if self._is_bool(name):
                if self._request_param['name'].endswith('patch_parameter'):
                    self._help(name, "Specify either 'true' or 'false' to update the property.")
                else:
                    details['options']['action'] = 'store_true'
                    self._help(name, "True if flag present.")
            elif self._is_list(name):
                details['options']['nargs'] = '+'
            elif self._is_datetime(name):
                details['options']['type'] = validators.datetime_format
                self._help(name, "Expected format is an ISO-8601 timestamp.")
            elif self._is_duration(name):
                details['options']['type'] = validators.duration_format
                self._help(name, "Expected format is an ISO-8601 duration.")
            elif self._is_silent(name):
                import argparse
                from azure.cli.core.commands.parameters import IgnoreAction
                details['options']['nargs'] = '?'
                details['options']['help'] = argparse.SUPPRESS
                details['options']['required'] = False
                details['options']['action'] = IgnoreAction
            yield (name, CliCommandArgument(dest=name, **details['options']))

    def existing(self, name):
        """Whether the argument name is already used by a pending
        argument.
        :param str name: The name of the argument to check.
        :returns: bool
        """
        return name in self._arg_tree

    def parse_mutually_exclusive(self, namespace, required, params):
        """Validate whether two or more mutually exclusive arguments or
        argument groups have been set correctly.
        :param bool required: Whether one of the parameters must be set.
        :param list params: List of namespace paths for mutually exclusive
         request properties.
        """
        argtree = self._arg_tree.items()
        ex_arg_names = [a for a, v in argtree if full_name(v) in params]
        ex_args = [getattr(namespace, a) for a, v in argtree if a in ex_arg_names]
        ex_args = [x for x in ex_args if x is not None]
        ex_group_names = []
        ex_groups = []
        for arg_group in params:
            child_args = self._get_children(arg_group)
            if child_args:
                ex_group_names.append(group_title(arg_group))
                if any([getattr(namespace, arg) for arg in child_args]):
                    ex_groups.append(ex_group_names[-1])

        message = None
        if not ex_groups and not ex_args and required:
            message = "One of the following arguments, or argument groups are required: \n"
        elif len(ex_groups) > 1 or len(ex_args) > 1 or (ex_groups and ex_args):
            message = ("The follow arguments or argument groups are mutually "
                       "exclusive and cannot be combined: \n")
        if message:
            missing = [arg_name(n) for n in ex_arg_names] + ex_group_names
            message += '\n'.join(missing)
            raise ValueError(message)

    def parse(self, namespace):
        """Parse all arguments in the namespace to validate whether all required
        arguments have been set.
        :param namespace: The namespace object.
        :raises: ValueError if a require argument was not set.
        """
        if self._custom_validator:
            try:
                self._custom_validator(namespace, self)
            except TypeError:
                raise ValueError("Custom validator must be a function that takes two arguments.")
        try:
            if namespace.json_file:
                try:
                    with open(namespace.json_file) as file_handle:
                        namespace.json_file = json.load(file_handle)
                except EnvironmentError:
                    raise ValueError("Cannot access JSON request file: " + namespace.json_file)
                except ValueError as err:
                    raise ValueError("Invalid JSON file: {}".format(err))
                other_values = [arg_name(n) for n in self._arg_tree if getattr(namespace, n)]
                if other_values:
                    message = "--json-file cannot be combined with:\n"
                    raise ValueError(message + '\n'.join(other_values))
                self.done = True
                return
        except AttributeError:
            pass
        required_args = self._parse(namespace, self._request_param['name'], True)
        missing_args = [n for n in required_args if not getattr(namespace, n)]
        if missing_args:
            message = "The following additional arguments are required:\n"
            message += "\n".join([arg_name(m) for m in missing_args])
            raise ValueError(message)
        self.done = True


class AzureBatchDataPlaneCommand(object):
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    def __init__(self, module_name, name,  # pylint:disable=too-many-statements
                 operation, factory, transform_result,
                 flatten, ignore, validator, silent):

        if not isinstance(operation, string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        self.flatten = flatten  # Number of object levels to flatten
        self.silent = silent if silent else []
        self.ignore = list(IGNORE_PARAMETERS)  # Parameters to ignore
        if ignore:
            self.ignore.extend(ignore)
        self.parser = None
        self.validator = validator
        self.confirmation = 'delete' in operation
        self.head_cmd = False

        # The name of the request options parameter
        self._options_param = format_options_name(operation)
        # Arguments used for request options
        self._options_attrs = []
        # The loaded options model to populate for the request
        self._options_model = None

        def _execute_command(kwargs):
            from msrest.paging import Paged
            from msrest.exceptions import ValidationError, ClientRequestError
            from azure.batch.models import BatchErrorException
            from azure.cli.core.util import CLIError
            from azure.cli.core._config import az_config
            from azure.cli.core.commands import _user_confirmed

            if self._cancel_operation(kwargs, az_config, _user_confirmed):
                raise CLIError('Operation cancelled.')

            try:
                client = factory(kwargs)
                self._build_options(kwargs)

                stream_output = kwargs.pop('destination', None)
                json_file = kwargs.pop('json_file', None)

                # Build the request parameters from command line arguments
                if json_file:
                    self.parser.deserialize_json(client, kwargs, json_file)
                    for arg, _ in self.parser:
                        del kwargs[arg]
                else:
                    for arg, details in self.parser:
                        try:
                            param_value = kwargs.pop(arg)
                            if param_value is None:
                                continue
                            else:
                                self._build_parameters(
                                    details['path'],
                                    kwargs,
                                    details['root'],
                                    param_value)
                        except KeyError:
                            continue

                # Make request
                op = get_op_handler(operation)
                if self.head_cmd:
                    kwargs['raw'] = True
                result = op(client, **kwargs)

                # Head output
                if self.head_cmd:
                    return transformers.transform_response_headers(result)

                # File download
                if stream_output:
                    with open(stream_output, "wb") as file_handle:
                        for data in result:
                            file_handle.write(data)
                    return

                # Apply results transform if specified
                elif transform_result:
                    return transform_result(result)

                # Otherwise handle based on return type of results
                elif isinstance(result, Paged):
                    return list(result)

                return result
            except BatchErrorException as ex:
                try:
                    message = ex.error.message.value
                    if ex.error.values:
                        for detail in ex.error.values:
                            message += "\n{}: {}".format(detail.key, detail.value)
                    raise CLIError(message)
                except AttributeError:
                    raise CLIError(ex)
            except (ValidationError, ClientRequestError) as ex:
                raise CLIError(ex)

        table_transformer = None
        try:
            transform_func = '_'.join(name.split()[1:]).replace('-', '_')
            table_transformer = getattr(transformers, transform_func + "_table_format")
        except AttributeError:
            pass
        command_module_map[name] = module_name
        self.cmd = CliCommand(
            ' '.join(name.split()),
            _execute_command,
            table_transformer=table_transformer,
            arguments_loader=lambda: self._load_transformed_arguments(
                get_op_handler(operation)),
            description_loader=lambda: extract_full_summary_from_signature(
                get_op_handler(operation))
        )

    def _cancel_operation(self, kwargs, config, user):
        """Whether to cancel the current operation because user
        declined the confirmation prompt.
        :param dict kwargs: The request arguments.
        :returns: bool
        """
        return not (not self.confirmation or
                    kwargs.get(CONFIRM_PARAM_NAME) or
                    config.getboolean('core', 'disable_confirm_prompt', fallback=False) or
                    user(self.confirmation, kwargs))

    def _build_parameters(self, path, kwargs, param, value):
        """Recursively build request parameter dictionary from command line args.
        :param str arg_path: Current parameter namespace.
        :param dict kwargs: The request arguments being built.
        :param param: The name of the request parameter.
        :param value: The value of the request parameter.
        """
        keys = path.split('.')
        if keys[0] not in kwargs:
            kwargs[keys[0]] = {}
        if len(keys) < 2:
            kwargs[keys[0]][param] = value
        else:
            self._build_parameters('.'.join(keys[1:]), kwargs[keys[0]], param, value)

        path = param[0]
        return path.split('.')[0]

    def _build_options(self, kwargs):
        """Build request options model from command line arguments.
        :param dict kwargs: The request arguments being built.
        """
        kwargs[self._options_param] = self._options_model
        for param in self._options_attrs:
            if param in IGNORE_OPTIONS:
                continue
            param_value = kwargs.pop(param)
            if param_value is None:
                continue
            setattr(kwargs[self._options_param], param, param_value)

    def _load_options_model(self, func_obj):
        """Load the request headers options model to gather arguments.
        :param func func_obj: The request function.
        """
        option_type = find_param_type(func_obj, self._options_param)
        option_type = class_name(option_type)
        self._options_model = _load_model(option_type)()
        self._options_attrs = list(self._options_model.__dict__.keys())

    def _should_flatten(self, param):
        """Check whether the current parameter object should be flattened.
        :param str param: The parameter name with complete namespace.
        :returns: bool
        """
        return param.count('.') < self.flatten and param not in self.ignore

    def _get_attrs(self, model, path):
        """Get all the attributes from the complex parameter model that should
        be exposed as command line arguments.
        :param class model: The parameter model class.
        :param str path: Request parameter namespace.
        """
        for attr, details in model._attribute_map.items():  # pylint: disable=protected-access
            conditions = []
            conditions.append(
                model._validation.get(attr, {}).get('readonly'))  # pylint: disable=protected-access
            conditions.append(
                model._validation.get(attr, {}).get('constant'))  # pylint: disable=protected-access
            conditions.append('.'.join([path, attr]) in self.ignore)
            conditions.append(details['type'][0] in ['{'])
            if not any(conditions):
                yield attr, details

    def _process_options(self):
        """Process the request options parameter to expose as arguments."""
        for param in [o for o in self._options_attrs if o not in IGNORE_OPTIONS]:
            options = {}
            options['required'] = False
            options['arg_group'] = 'Pre-condition and Query'
            if param in ['if_modified_since', 'if_unmodified_since']:
                options['type'] = validators.datetime_format
            if param in FLATTEN_OPTIONS:
                for f_param, f_docstring in FLATTEN_OPTIONS[param].items():
                    options['default'] = None
                    options['help'] = f_docstring
                    options['options_list'] = [arg_name(f_param)]
                    options['validator'] = validators.validate_options
                    yield (f_param, CliCommandArgument(f_param, **options))
            else:
                options['default'] = getattr(self._options_model, param)
                options['help'] = find_param_help(self._options_model, param)
                options['options_list'] = [arg_name(param)]
                yield (param, CliCommandArgument(param, **options))

    def _resolve_conflict(self,
                          arg, param, path, options, typestr, dependencies, conflicting):
        """Resolve conflicting command line arguments.
        :param str arg: Name of the command line argument.
        :param str param: Original request parameter name.
        :param str path: Request parameter namespace.
        :param dict options: The kwargs to be used to instantiate CliCommandArgument.
        :param list dependencies: A list of complete paths to other parameters that are required
         if this parameter is set.
        :param list conflicting: A list of the argument names that have already conflicted.
        """
        if self.parser.existing(arg):
            conflicting.append(arg)
            existing = self.parser.dequeue_argument(arg)
            existing['name'] = _build_prefix(arg, existing['root'], existing['path'])
            existing['options']['options_list'] = [arg_name(existing['name'])]
            self.parser.queue_argument(**existing)
            new = _build_prefix(arg, param, path)
            options['options_list'] = [arg_name(new)]
            self._resolve_conflict(new, param, path, options, typestr, dependencies, conflicting)
        elif arg in conflicting or arg in QUALIFIED_PROPERTIES:
            new = _build_prefix(arg, param, path)
            if new in conflicting or new in QUALIFIED_PROPERTIES and '.' not in path:
                self.parser.queue_argument(arg, path, param, options, typestr, dependencies)
            else:
                options['options_list'] = [arg_name(new)]
                self._resolve_conflict(new, param, path, options,
                                       typestr, dependencies, conflicting)
        else:
            self.parser.queue_argument(arg, path, param, options, typestr, dependencies)

    def _flatten_object(self, path, param_model, conflict_names=None):
        """Flatten a complex parameter object into command line arguments.
        :param str path: The complex parameter namespace.
        :param class param_model: The complex parameter class.
        :param list conflict_name: List of argument names that conflict.
        """
        conflict_names = conflict_names or []

        if self._should_flatten(path):
            validations = param_model._validation.items()  # pylint: disable=protected-access
            required_attrs = [key for key, val in validations if val.get('required')]

            for param_attr, details in self._get_attrs(param_model, path):
                if param_attr in IGNORE_PARAMETERS:
                    continue
                options = {}
                options['options_list'] = [arg_name(param_attr)]
                options['required'] = False
                options['arg_group'] = group_title(path)
                options['help'] = find_param_help(param_model, param_attr)
                options['validator'] = \
                    lambda ns: validators.validate_required_parameter(ns, self.parser)
                options['default'] = None  # Extract details from signature

                if details['type'] in BASIC_TYPES:
                    self._resolve_conflict(param_attr, param_attr, path, options,
                                           details['type'], required_attrs, conflict_names)
                elif details['type'].startswith('['):
                    # We only expose a list arg if there's a validator for it
                    # This will fail for 2D arrays - though Batch doesn't have any yet
                    inner_type = details['type'][1:-1]
                    if inner_type in BASIC_TYPES:
                        options['help'] += " Space separated values."
                        self._resolve_conflict(
                            param_attr, param_attr, path, options,
                            details['type'], required_attrs, conflict_names)
                    else:
                        inner_type = operations_name(inner_type)
                        try:
                            validator = getattr(validators, inner_type + "_format")
                            options['help'] += ' ' + validator.__doc__
                            options['type'] = validator
                            self._resolve_conflict(
                                param_attr, param_attr, path, options,
                                details['type'], required_attrs, conflict_names)
                        except AttributeError:
                            continue
                else:
                    attr_model = _load_model(details['type'])
                    if not hasattr(attr_model, '_attribute_map'):  # Must be an enum
                        values_index = options['help'].find(' Possible values include')
                        if values_index >= 0:
                            choices = options['help'][values_index + 25:].split(', ')
                            options['choices'] = [enum_value(c)
                                                  for c in choices if enum_value(c) != "unmapped"]
                            options['help'] = options['help'][0:values_index]
                        self._resolve_conflict(param_attr, param_attr, path, options,
                                               details['type'], required_attrs, conflict_names)
                    else:
                        self._flatten_object('.'.join([path, param_attr]), attr_model)

    def _load_transformed_arguments(self, handler):
        """Load all the command line arguments from the request parameters.
        :param func handler: The operation function.
        """
        from azure.cli.core.commands.parameters import file_type
        from argcomplete.completers import FilesCompleter, DirectoriesCompleter

        self.parser = BatchArgumentTree(self.validator, self.silent)
        self._load_options_model(handler)
        for arg in extract_args_from_signature(handler):
            arg_type = find_param_type(handler, arg[0])
            if arg[0] == self._options_param:
                for option_arg in self._process_options():
                    yield option_arg
            elif arg_type.startswith("str or"):
                docstring = find_param_help(handler, arg[0])
                choices = []
                values_index = docstring.find(' Possible values include')
                if values_index >= 0:
                    choices = docstring[values_index + 25:].split(', ')
                    choices = [c for c in choices if c != "'unmapped'"]
                    docstring = docstring[0:values_index]
                yield (arg[0], CliCommandArgument(arg[0],
                                                  options_list=[arg_name(arg[0])],
                                                  required=False,
                                                  default=None,
                                                  choices=choices,
                                                  help=docstring))
            elif arg_type.startswith(":class:"):  # TODO: could add handling for enums
                param_type = class_name(arg_type)
                self.parser.set_request_param(arg[0], param_type)
                param_model = _load_model(param_type)
                self._flatten_object(arg[0], param_model)
                for flattened_arg in self.parser.compile_args():
                    yield flattened_arg
                param = 'json_file'
                docstring = "A file containing the {} specification in JSON format. " \
                            "If this parameter is specified, all '{} Arguments'" \
                            " are ignored.".format(arg[0].replace('_', ' '), group_title(arg[0]))
                yield (param, CliCommandArgument(param,
                                                 options_list=[arg_name(param)],
                                                 required=False,
                                                 default=None,
                                                 type=file_type,
                                                 completer=FilesCompleter(),
                                                 help=docstring))
            elif arg[0] not in self.ignore:
                yield arg
        return_type = find_return_type(handler)
        if return_type == 'Generator':
            param = 'destination'
            docstring = "The path to the destination file or directory."
            yield (param, CliCommandArgument(param,
                                             options_list=[arg_name(param)],
                                             required=True,
                                             default=None,
                                             completer=DirectoriesCompleter(),
                                             type=file_type,
                                             validator=validators.validate_file_destination,
                                             help=docstring))
        if return_type == 'None' and handler.__name__.startswith('get'):
            self.head_cmd = True
        if self.confirmation:
            param = CONFIRM_PARAM_NAME
            docstring = 'Do not prompt for confirmation.'
            yield (param, CliCommandArgument(param,
                                             options_list=['--yes', '-y'],
                                             required=False,
                                             action='store_true',
                                             help=docstring))


def validate_client_parameters(namespace):
    """Retrieves Batch connection parameters from environment variables"""
    from azure.mgmt.batch import BatchManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core._config import az_config

    # simply try to retrieve the remaining variables from environment variables
    if not namespace.account_name:
        namespace.account_name = az_config.get('batch', 'account', None)
    if not namespace.account_key:
        namespace.account_key = az_config.get('batch', 'access_key', None)
    if not namespace.account_endpoint:
        namespace.account_endpoint = az_config.get('batch', 'endpoint', None)

    # if account name is specified but no key, attempt to query if we use shared key auth
    if namespace.account_name and namespace.account_endpoint and not namespace.account_key:
        if az_config.get('batch', 'auth_mode', 'shared_key') == 'shared_key':
            endpoint = urlsplit(namespace.account_endpoint)
            host = endpoint.netloc
            client = get_mgmt_service_client(BatchManagementClient)
            acc = next((x for x in client.batch_account.list()
                        if x.name == namespace.account_name and x.account_endpoint == host), None)
            if acc:
                from azure.cli.core.commands.arm import parse_resource_id
                rg = parse_resource_id(acc.id)['resource_group']
                namespace.account_key = \
                    client.batch_account.get_keys(rg,  # pylint: disable=no-member
                                                  namespace.account_name).primary
            else:
                raise ValueError("Batch account '{}' not found.".format(namespace.account_name))
    else:
        if not namespace.account_name:
            raise ValueError("Specify batch account in command line or enviroment variable.")
        if not namespace.account_endpoint:
            raise ValueError("Specify batch endpoint in command line or enviroment variable.")

    if az_config.get('batch', 'auth_mode', 'shared_key') == 'aad':
        namespace.account_key = None


def cli_batch_data_plane_command(name,
                                 operation, client_factory, transform=None, flatten=FLATTEN,
                                 ignore=None, validator=None, silent=None):
    """ Registers an Azure CLI Batch Data Plane command. These commands must respond to a
    challenge from the service when they make requests. """
    command = AzureBatchDataPlaneCommand(__name__, name, operation, client_factory, transform,
                                         flatten, ignore, validator, silent)

    # add parameters required to create a batch client
    group_name = 'Batch Account'
    command.cmd.add_argument('account_name', '--account-name', required=False, default=None,
                             validator=validate_client_parameters, arg_group=group_name,
                             help='Batch account name. Alternatively, set by environment variable: '
                                  'AZURE_BATCH_ACCOUNT')
    command.cmd.add_argument('account_key', '--account-key', required=False, default=None,
                             arg_group=group_name,
                             help='Batch account key. Alternatively, set by environment'
                                  ' variable: AZURE_BATCH_ACCESS_KEY')
    command.cmd.add_argument('account_endpoint', '--account-endpoint', required=False, default=None,
                             arg_group=group_name,
                             help='Batch service endpoint. Alternatively, set by environment'
                                  ' variable: AZURE_BATCH_ENDPOINT')
    command_table[command.cmd.name] = command.cmd
