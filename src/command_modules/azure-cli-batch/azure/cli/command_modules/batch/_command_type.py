# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
import re

from six import string_types

from azure.cli.core._util import CLIError
from azure.cli.core.commands import (
    create_command,
    command_table,
    command_module_map,
    CliCommand,
    CliCommandArgument,
    get_op_handler)
from argcomplete.completers import (
    FilesCompleter,
    DirectoriesCompleter)
from azure.cli.core.commands._introspection import (
    extract_full_summary_from_signature,
    extract_args_from_signature)
from ._validators import (
    validate_options,
    validate_file_destination,
    validate_client_parameters,
    validate_required_parameter)


FLATTEN = 3  # The level of complex object namespace to flatten.
IGNORE_OPTIONS = {  # Options parameters that should not be exposed as arguments.
    'ocp_date',
    'timeout',
    'client_request_id',
    'return_client_request_id'
}
IGNORE_PARAMETERS = {'callback'}
FLATTEN_OPTIONS = {  # Options to be flattened into multiple arguments.
    'ocp_range': {'start_range':"The byte range to be retrieved. If not set the file will be retrieved from the beginning.",
                  'end_range':"The byte range to be retrieved. If not set the file will be retrieved to the end."}
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


class BatchArgumentTree(object):
    """Dependency tree parser for arguments of complex objects"""

    _class_name = re.compile(r"<(.*?)>")  # Strip model name from class docstring

    def __init__(self):
        self._arg_tree = {}
        self.done = False

    def __iter__(self):
        """Iterate over arguments"""
        for arg, details in self._arg_tree.items():
            yield arg, details

    def queue_argument(self, name=None, path=None, root=None, options=None, dependencies=None):
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
            yield (name, CliCommandArgument(dest=name, **details['options']))

    def existing(self, name):
        """Whether the argument name is already used by a pending
        argument.
        :param str name: The name of the argument to check.
        :returns: bool
        """
        return name in self._arg_tree

    def class_name(self, type_str):
        """Extract class name from type docstring.
        :param str type_str: Parameter type docstring.
        :returns: class name
        """
        return self._class_name.findall(type_str)[0]

    def full_name(self, arg_details):
        """Create a full path to the complex object parameter of a
        given argument.
        :param dict arg_details: The details of the argument.
        :returns: str
        """
        return ".".join([arg_details['path'], arg_details['root']])

    def group_title(self, path):
        """Create a group title from the argument path.
        :param str path: The complex object path of the argument.
        :returns: str
        """
        group_name = path.split('.')[-1]
        return " ".join([n.title() for n in group_name.split('_')])

    def arg_name(self, name):
        """Convert snake case argument name to a command line name.
        :param str name: The argument parameter name.
        :returns: str
        """
        return "--" + name.replace('_', '-')

    def find_param_type(self, model, param):
        """Parse the parameter type from the model docstring.
        :param class model: Model class.
        :param str param: The name of the parameter.
        :returns: str
        """
        # Search for the :type param_name: in the docstring
        pattern = r":type {}:(.*?)\n(\s*:param |\s*:rtype:|\s*:raises:|\"\"\")".format(param)
        param_type = re.search(pattern, model.__doc__, re.DOTALL)
        return re.sub(r"\n\s*", "", param_type.group(1))

    def find_param_help(self, model, param):
        """Parse the parameter help info from the model docstring.
        :param class model: Model class.
        :param str param: The name of the parameter.
        :returns: str
        """
        # Search for :param param_name: in the docstring
        pattern = r":param {}:(.*?)\n\s*:type ".format(param)
        param_doc = re.search(pattern, model.__doc__, re.DOTALL)
        return re.sub(r"\n\s*", "", param_doc.group(1))

    def find_return_type(self, model):
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

    def parse(self, namespace):
        """Parse all arguments in the namespace to validate whether all required
        arguments have been set.
        :param namespace: The namespace object.
        :raises: ValueError if a require argument was not set.
        """
        for name, details in self._arg_tree.items():
            if not getattr(namespace, name):
                continue
            dependencies = details['dependencies']
            siblings = [arg for arg, value in self._arg_tree.items() \
                if self.full_name(value) in dependencies]
            for arg in self.find_complex_dependencies(dependencies):
                siblings.append(arg)
            for arg in siblings:
                if not getattr(namespace, arg):
                    arg_name = self.arg_name(name)
                    arg_group = self.group_title(self._arg_tree[name]['path'])
                    required_arg = self.arg_name(arg)
                    message = "When using {} of {}, the following is also required: {}".format(
                        arg_name, arg_group, required_arg)
                    raise ValueError(message)
        self.done = True

    def find_complex_dependencies(self, dependencies):
        """Recursive generator to find required argments from dependent
        complect objects.
        :param list dependencies: A list of the dependencies of the current object.
        :returns: The names of the required arguments.
        """
        cmplx_args = [arg for arg, value in self._arg_tree.items() if value['path'] in dependencies]
        for arg in cmplx_args:
            for sub_arg in self.find_complex_dependencies(self._arg_tree[arg]['dependencies']):
                yield sub_arg
            yield arg

class AzureDataPlaneCommand(object):

    def __init__(self, module_name, name, operation, factory, transform_result, #pylint:disable=too-many-arguments
                 table_transformer, flatten, ignore):

        if not isinstance(operation, string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        self.flatten = flatten  # Number of object levels to flatten
        self.ignore = list(IGNORE_PARAMETERS)  # Parameters to ignore
        if ignore:
            self.ignore.extend(ignore)
        self.parser = BatchArgumentTree()

        # The name of the request options parameter
        self._options_param = self._format_options_name(operation)
        # The name of the group for options arguments
        self._options_group = self.parser.group_title(self._options_param)
        # Arguments used for request options
        self._options_attrs = []
        # The loaded options model to populate for the request
        self._options_model = None

        def _execute_command(kwargs):
            from msrest.paging import Paged
            from msrest.exceptions import ValidationError, ClientRequestError
            from azure.batch.models import BatchErrorException
            try:
                client = factory(kwargs)
                self._build_options(kwargs)

                stream_output = kwargs.pop('destination', None)

                # Build the request parameters from command line arguments
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
            except (ValidationError, BatchErrorException) as ex:
                try:
                    message = ex.error.message.value
                    if ex.error.values:
                        for detail in ex.error.values:
                            message += "\n{}: {}".format(detail.key, detail.value)
                    raise CLIError(message)
                except AttributeError:
                    raise CLIError(ex)
            except ClientRequestError as ex:
                raise CLIError(ex)

        command_module_map[name] = module_name
        self.cmd = CliCommand(
            ' '.join(name.split()),
            _execute_command,
            table_transformer=table_transformer,
            arguments_loader=lambda: self._load_transformed_arguments(
                operation,
                get_op_handler(operation)),
            description_loader=lambda: extract_full_summary_from_signature(
                get_op_handler(operation))
        )

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

    def _load_model(self, name):
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

    def _load_options_model(self, func_obj):
        """Load the request headers options model to gather arguments.
        :param func func_obj: The request function.
        """
        option_type = self.parser.find_param_type(func_obj, self._options_param)
        option_type = self.parser.class_name(option_type)
        self._options_model = self._load_model(option_type)()
        self._options_attrs =  list(self._options_model.__dict__.keys())

    #def _inspect(self, func):
    #    """Inspect a model signature to extract parameter information."""
    #    try:
    #        # only supported in python3 - falling back to argspec if not available
    #        sig = inspect.signature(operation)
    #        return sig.parameters
    #    except AttributeError:
    #        sig = inspect.getargspec(operation) #pylint: disable=deprecated-method
    #        return sig.args

    def _format_options_name(self, operation):
        """Format the name of the request options parameter from the
        operation name and path.
        :param str operation: Operation path
        :returns: str - options parameter name.
        """
        operation = operation.split('#')[-1]
        op_class, op_function = operation.split('.')
        return "{}_{}_options".format(op_class[:-10].lower(), op_function)

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
        for attr, details in model._attribute_map.items(): #pylint: disable=W0212
            if model._validation.get(attr, {}).get('readonly'): #pylint: disable=W0212
                continue
            elif model._validation.get(attr, {}).get('constant'): #pylint: disable=W0212
                continue
            elif '.'.join([path, attr]) in self.ignore:
                continue
            elif details['type'][0] in ['[', '{']: # TODO: Add support for lists.
                continue
            yield attr, details

    def _build_prefix(self, arg, param, path):
        """Recursively build a command line argument prefix from the request
        parameter object to avoid name conflicts.
        :param str arg: Currenct argument name.
        :param str param: Original request parameter name.
        :param str path: Request parameter namespace.
        """
        prefix_list = path.split('.')
        resolved_name = prefix_list[0] + "_" + param
        if arg == resolved_name:
            return arg
        for prefix in prefix_list[1:]:
            new_name = prefix + "_" + param
            if new_name == arg:
                return resolved_name
            resolved_name = new_name
        return resolved_name

    def _process_options(self):
        """Process the request options parameter to expose as arguments."""
        for param in [o for o in self._options_attrs if o not in IGNORE_OPTIONS]:
            if param in FLATTEN_OPTIONS:
                for f_param, f_docstring in FLATTEN_OPTIONS[param].items():
                    yield (f_param, CliCommandArgument(f_param,
                                                       options_list=[self.parser.arg_name(f_param)],
                                                       required=False,
                                                       default=None,
                                                       help=f_docstring,
                                                       validator=validate_options,
                                                       arg_group=self._options_group))
            else:
                docstring = self.parser.find_param_help(self._options_model, param)
                yield (param, CliCommandArgument(param,
                                                 options_list=[self.parser.arg_name(param)],
                                                 required=False,
                                                 default=getattr(self._options_model, param),
                                                 help=docstring,
                                                 arg_group=self._options_group))

    def _resolve_conflict(self, arg, param, path, options, dependencies, conflicting):
        """Resolve conflicting command line arguments.
        :param str arg: Name of the command line argument.
        :param str param: Original request parameter name.
        :param str path: Request parameter namespace.
        :param dict options: The kwargs to be used to instantiate CliCommandArgument.
        :param list dependencies: A list of complete paths to other parameters that.
        :param list conflicting: A list of the argument names that have already conflicted.
        """
        if self.parser.existing(arg):
            conflicting.append(arg)
            existing = self.parser.dequeue_argument(arg)
            existing['name'] = self._build_prefix(arg, existing['root'], existing['path'])
            existing['options']['options_list'] = [self.parser.arg_name(existing['name'])]
            self.parser.queue_argument(**existing)
            new = self._build_prefix(arg, param, path)
            options['options_list'] = [self.parser.arg_name(new)]
            self._resolve_conflict(new, param, path, options, dependencies, conflicting)
        elif arg in conflicting:
            new = self._build_prefix(arg, param, path)
            options['options_list'] = [self.parser.arg_name(new)]
            self._resolve_conflict(new, param, path, options, dependencies, conflicting)
        else:
            self.parser.queue_argument(arg, path, param, options, dependencies)

    def _flatten_object(self, path, param_model, required, conflict_names=[]): #pylint: disable=W0102
        """Flatten a complex parameter object into command line arguments.
        :param str path: The complex parameter namespace.
        :param class param_model: The complex parameter class.
        :param bool required: Whether the parameter is required.
        :param list conflict_name: List of argument names that conflict.
        """
        if self._should_flatten(path):
            required_attrs = [key for key,
                              val in param_model._validation.items() if val.get('required')] #pylint: disable=W0212

            for param_attr, details in self._get_attrs(param_model, path):
                options = {}
                options['options_list'] = [self.parser.arg_name(param_attr)]
                options['required'] = (required and param_attr in required_attrs)
                options['arg_group'] = self.parser.group_title(path)
                options['help'] = self.parser.find_param_help(param_model, param_attr)
                options['validator'] = lambda ns: validate_required_parameter(ns, self.parser)
                options['default'] = None  # Extract details from signature

                if details['type'] == 'bool':
                    options['action'] = 'store_true'
                    self._resolve_conflict(param_attr, param_attr, path, options,
                                           required_attrs, conflict_names)
                elif details['type'] in BASIC_TYPES:
                    self._resolve_conflict(param_attr, param_attr, path, options,
                                           required_attrs, conflict_names)
                else:
                    attr_model = self._load_model(details['type'])
                    if not hasattr(attr_model, '_attribute_map'): # Must be an enum
                        self._resolve_conflict(param_attr, param_attr, path, options,
                                               required_attrs, conflict_names)
                    else:
                        self._flatten_object('.'.join([path, param_attr]),
                                             attr_model, options['required'])

    def _load_transformed_arguments(self, operation, handler):
        """Load all the command line arguments from the request parameters.
        :param str operation: The operation function reference.
        :param func handler: The operation function.
        """
        self._load_options_model(handler)
        for arg in extract_args_from_signature(handler):
            arg_type = self.parser.find_param_type(handler, arg[0])
            if arg[0] == self._options_param:
                for option_arg in self._process_options():
                    yield option_arg
            elif arg_type.startswith(":class:"):
                param_type = self.parser.class_name(arg_type)
                param_model = self._load_model(param_type)
                self._flatten_object(arg[0], param_model, True)
                for flattened_arg in self.parser.compile_args():
                    yield flattened_arg
            elif arg[0] not in self.ignore:
                yield arg
        if self.parser.find_return_type(handler) == 'Generator':
            param = 'destination'
            docstring = "The path to the destination file or directory."
            yield (param, CliCommandArgument(param,
                                             options_list=[self.parser.arg_name(param)],
                                             required=True,
                                             default=None,
                                             completer=DirectoriesCompleter(),
                                             validator=validate_file_destination,
                                             help=docstring))


def cli_data_plane_command(name, operation, client_factory, transform=None,
                           table_transformer=None, flatten=FLATTEN, ignore=None):
    """ Registers an Azure CLI Batch Data Plane command. These commands must respond to a
    challenge from the service when they make requests. """

    command = AzureDataPlaneCommand(__name__, name, operation, client_factory,
                                    transform, table_transformer, flatten, ignore)

    # add parameters required to create a batch client
    group_name = 'Batch Account'
    command.cmd.add_argument('account_name', '--account-name', required=False, default=None,
                             validator=validate_client_parameters, arg_group=group_name,
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

def cli_custom_data_plane_command(name, operation, client_factory, transform=None,
                                  table_transformer=None):
    """ Registers an Azure CLI Batch Data Plane custom command. """

    command = create_command(__name__, name, operation,
                             transform, table_transformer, client_factory)
    # add parameters required to create a batch client
    group_name = 'Batch Account'
    command.add_argument('account_name', '--account-name', required=False, default=None,
                         validator=validate_client_parameters, arg_group=group_name,
                         help='Batch account name. Environment variable: AZURE_BATCH_ACCOUNT')
    command.add_argument('account_key', '--account-key', required=False, default=None,
                         arg_group=group_name,
                         help='Batch account key. Must be used in conjunction with Batch '
                         'account name and endpoint. Environment variable: AZURE_BATCH_ACCESS_KEY')
    command.add_argument('account_endpoint', '--account-endpoint', required=False, default=None,
                         arg_group=group_name,
                         help='Batch service endpoint. Environment variable: AZURE_BATCH_ENDPOINT')
    command_table[command.name] = command
