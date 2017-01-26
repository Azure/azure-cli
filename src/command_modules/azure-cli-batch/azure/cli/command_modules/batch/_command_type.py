# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import json
import re

from six import string_types
from argcomplete.completers import (
    FilesCompleter,
    DirectoriesCompleter)

from msrest.exceptions import DeserializationError

from azure.cli.command_modules.batch import _validators as validators
from azure.cli.core.commands import (
    FORCE_PARAM_NAME,
    command_table,
    command_module_map,
    CliCommand,
    CliCommandArgument,
    get_op_handler,
    _user_confirmed)
from azure.cli.core._util import CLIError
from azure.cli.core._config import az_config
from azure.cli.core.commands._introspection import (
    extract_full_summary_from_signature,
    extract_args_from_signature)
from azure.cli.core.commands.parameters import file_type

# TODO: Enum choice lists


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
IGNORE_PARAMETERS = {'callback'}
FLATTEN_OPTIONS = {  # Options to be flattened into multiple arguments.
    'ocp_range': {'start_range':"The byte range to be retrieved. "
                                "If not set the file will be retrieved from the beginning.",
                  'end_range':"The byte range to be retrieved. "
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
    resolved_name = prefix_list[0] + "_" + param
    if arg == resolved_name:
        return arg
    for prefix in prefix_list[1:]:
        new_name = prefix + "_" + param
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
    group_path = path.split('.')
    title = ' : '.join(group_path)
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

    def __init__(self, validator):
        self._arg_tree = {}
        self._request_param = {}
        self._custom_validator = validator
        self.done = False

    def __iter__(self):
        """Iterate over arguments"""
        for arg, details in self._arg_tree.items():
            yield arg, details

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
        message = "Failed to deserialized JSON file into object {}"
        try:
            kwargs[self._request_param['name']] = client._deserialize(  # pylint:disable=W0212
                self._request_param['model'], json_obj)
        except DeserializationError as error:
            message += ": {}".format(error)
            raise ValueError(message.format(self._request_param['model']))
        else:
            if kwargs[self._request_param['name']] is None:
                raise ValueError(message.format(self._request_param['model']))

    def queue_argument(self, name=None, path=None, root=None,  # pylint:disable=too-many-arguments
                       options=None, type=None, dependencies=None):  # pylint:disable=W0622
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
            if details['type'] == 'bool':
                details['options']['action'] = 'store_true'
            elif details['type'].startswith('['):
                details['options']['nargs'] = '+'
            elif details['type'] in ['iso-8601', 'rfc-1123']:
                details['options']['type'] = validators.datetime_format
            elif details['type'] == 'duration':
                details['options']['type'] = validators.duration_format
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


class AzureDataPlaneCommand(object):
    # pylint:disable=too-many-instance-attributes, too-few-public-methods

    def __init__(self, module_name, name, operation, factory, transform_result,  # pylint:disable=too-many-arguments
                 table_transformer, flatten, ignore, validator):

        if not isinstance(operation, string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        self.flatten = flatten  # Number of object levels to flatten
        self.ignore = list(IGNORE_PARAMETERS)  # Parameters to ignore
        if ignore:
            self.ignore.extend(ignore)
        self.parser = None
        self.validator = validator
        self.confirmation = 'delete' in operation

        # The name of the request options parameter
        self._options_param = format_options_name(operation)
        # The name of the group for options arguments
        self._options_group = group_title(self._options_param)
        # Arguments used for request options
        self._options_attrs = []
        # The loaded options model to populate for the request
        self._options_model = None

        def _execute_command(kwargs):
            from msrest.paging import Paged
            from msrest.exceptions import ValidationError, ClientRequestError
            from azure.batch.models import BatchErrorException
            if self._cancel_operation(kwargs):
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
                result = op(client, **kwargs)

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
                else:
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

    def _cancel_operation(self, kwargs):
        """Whether to cancel the current operation because user
        declined the confirmation prompt.
        :param dict kwargs: The request arguments.
        :returns: bool
        """
        return self.confirmation \
            and not kwargs.get(FORCE_PARAM_NAME) \
            and not az_config.getboolean('core', 'disable_confirm_prompt', fallback=False) \
            and not _user_confirmed(self.confirmation, kwargs)

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
        for attr, details in model._attribute_map.items():  # pylint: disable=W0212
            conditions = []
            conditions.append(model._validation.get(attr, {}).get('readonly'))  # pylint: disable=W0212
            conditions.append(model._validation.get(attr, {}).get('constant'))  # pylint: disable=W0212
            conditions.append('.'.join([path, attr]) in self.ignore)
            conditions.append(details['type'][0] in ['{'])
            if not any(conditions):
                yield attr, details

    def _process_options(self):
        """Process the request options parameter to expose as arguments."""
        for param in [o for o in self._options_attrs if o not in IGNORE_OPTIONS]:
            options = {}
            options['required'] = False
            options['arg_group'] = self._options_group
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

    def _resolve_conflict(self, arg, param, path, options, typestr, dependencies, conflicting):  # pylint:disable=too-many-arguments
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
        elif arg in conflicting:
            new = _build_prefix(arg, param, path)
            if new in conflicting and '.' not in path:
                self.parser.queue_argument(arg, path, param, options, typestr, dependencies)
            else:
                options['options_list'] = [arg_name(new)]
                self._resolve_conflict(new, param, path, options,
                                       typestr, dependencies, conflicting)
        else:
            self.parser.queue_argument(arg, path, param, options, typestr, dependencies)

    def _flatten_object(self, path, param_model, conflict_names=[]):  # pylint: disable=W0102
        """Flatten a complex parameter object into command line arguments.
        :param str path: The complex parameter namespace.
        :param class param_model: The complex parameter class.
        :param list conflict_name: List of argument names that conflict.
        """
        if self._should_flatten(path):
            required_attrs = [key for key,
                              val in param_model._validation.items() if val.get('required')]  # pylint: disable=W0212

            for param_attr, details in self._get_attrs(param_model, path):
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
                    if inner_type in BASIC_TYPES:  # TODO
                        continue
                    else:
                        inner_type = operations_name(inner_type)
                        try:
                            validator = getattr(validators, inner_type + "_format")
                            options['type'] = validator
                            self._resolve_conflict(
                                param_attr, param_attr, path, options,
                                details['type'], required_attrs, conflict_names)
                        except AttributeError:
                            continue
                else:
                    attr_model = _load_model(details['type'])
                    if not hasattr(attr_model, '_attribute_map'):  # Must be an enum
                        self._resolve_conflict(param_attr, param_attr, path, options,
                                               details['type'], required_attrs, conflict_names)
                    else:
                        self._flatten_object('.'.join([path, param_attr]), attr_model)

    def _load_transformed_arguments(self, handler):
        """Load all the command line arguments from the request parameters.
        :param func handler: The operation function.
        """
        self.parser = BatchArgumentTree(self.validator)
        self._load_options_model(handler)
        for arg in extract_args_from_signature(handler):
            arg_type = find_param_type(handler, arg[0])
            if arg[0] == self._options_param:
                for option_arg in self._process_options():
                    yield option_arg
            elif arg_type.startswith(":class:"):  # TODO: could add handling for enums
                param_type = class_name(arg_type)
                self.parser.set_request_param(arg[0], param_type)
                param_model = _load_model(param_type)
                self._flatten_object(arg[0], param_model)
                for flattened_arg in self.parser.compile_args():
                    yield flattened_arg
                param = 'json_file'
                json_class = class_name(arg_type).split('.')[-1]
                docstring = "A file containing the {} object in JSON format, " \
                            "if this parameter is specified, all other parameters" \
                            " are ignored.".format(json_class)
                yield (param, CliCommandArgument(param,
                                                 options_list=[arg_name(param)],
                                                 required=False,
                                                 default=None,
                                                 type=file_type,
                                                 completer=FilesCompleter(),
                                                 help=docstring))
            elif arg[0] not in self.ignore:
                yield arg
        if find_return_type(handler) == 'Generator':
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
        if self.confirmation:
            param = FORCE_PARAM_NAME
            docstring = 'Do not prompt for confirmation.'
            yield (param, CliCommandArgument(param,
                                             options_list=[arg_name(param)],
                                             required=False,
                                             action='store_true',
                                             help=docstring))


def cli_data_plane_command(name, operation, client_factory, transform=None,  # pylint:disable=too-many-arguments
                           table_transformer=None, flatten=FLATTEN, ignore=None, validator=None):
    """ Registers an Azure CLI Batch Data Plane command. These commands must respond to a
    challenge from the service when they make requests. """
    command = AzureDataPlaneCommand(__name__, name, operation, client_factory,
                                    transform, table_transformer, flatten, ignore, validator)

    # add parameters required to create a batch client
    group_name = 'Batch Account'
    command.cmd.add_argument('account_name', '--account-name', required=False, default=None,
                             validator=validators.validate_client_parameters, arg_group=group_name,
                             help='Batch account name. Environment variable: '
                             'AZURE_BATCH_ACCOUNT')
    command.cmd.add_argument('account_key', '--account-key', required=False, default=None,
                             arg_group=group_name,
                             help='Batch account key. Must be used in conjunction with Batch '
                             'account name and endpoint. Environment variable: '
                             'AZURE_BATCH_ACCESS_KEY')
    command.cmd.add_argument('account_endpoint', '--account-endpoint', required=False, default=None,
                             arg_group=group_name,
                             help='Batch service endpoint. Environment variable: '
                             'AZURE_BATCH_ENDPOINT')
    command_table[command.cmd.name] = command.cmd
