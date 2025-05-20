# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import inspect
import re
from enum import Enum
from typing import get_args, get_type_hints

from azure.batch._model_base import _RestField
from azure.cli.command_modules.batch import _format as transformers
from azure.cli.command_modules.batch._transformers import batch_transformer
from azure.cli.command_modules.batch import _parameter_format as pformat
from azure.cli.command_modules.batch import _validators as validators
from azure.cli.core import EXCLUDED_PARAMS
from azure.cli.core.commands import CONFIRM_PARAM_NAME, AzCommandGroup
from azure.cli.core.util import get_file_json
from azure.core import MatchConditions
from azure.core.paging import ItemPaged
from knack.arguments import CLICommandArgument, IgnoreAction
from knack.introspection import extract_args_from_signature

_CLASS_NAME = re.compile(r"~(.*)")  # Strip model name from class docstring
_UNDERSCORE_CASE = re.compile('(?!^)([A-Z]+)')  # Convert from CamelCase to underscore_case


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
    if prefix.endswith("_patch_parameter"):
        return prefix[:-16] + "_" + name
    if prefix.endswith("_update_parameter"):
        return prefix[:-17] + "_" + name
    return prefix + "_" + name


def _build_prefix(arg, param, path):
    """Recursively build a command line argument prefix from the request
    parameter object to avoid name conflicts.
    :param str arg: Current argument name.
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
    pattern = rf":type {param}:(.*?)\n(\s*:param |\s*:keyword |\s*:rtype:|\s*:raises:|\s*\"{{3}})"
    param_type = re.search(pattern, model.__doc__, re.DOTALL)
    if param_type is None:
        return None

    return re.sub(r"\n\s*", "", param_type.group(1).strip())


def find_param_help(model, param):
    """Parse the parameter help info from the model docstring.
    :param class model: Model class.
    :param str param: The name of the parameter.
    :returns: str
    """
    # Search for :param param_name: in the docstring
    pattern = rf":ivar {param}:(.*?)\n\s*:vartype "
    param_doc = re.search(pattern, model.__doc__, re.DOTALL)
    return re.sub(r"\n\s*", " ", param_doc.group(1).strip())


# pylint: disable=inconsistent-return-statements
def find_return_type(model):
    """Parse the parameter help info from the model docstring.
    :param class model: Model class.
    :returns: str
    """
    # Search for :rtype: in the docstring
    pattern = r':rtype: (.*?)( or)?\n.*(:raises:)?'
    return_type = re.search(pattern, model.__doc__, re.DOTALL)
    if return_type:
        return re.sub(r"\n\s*", "", return_type.group(1))


def enum_value(enum_str):
    """Strip chars around enum value str.
    :param str enum_str: Enum value.
    """
    return enum_str.strip(' \'').lower()


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
    for each in group_path:
        title = title.replace(each, " ".join([n.title() for n in each.split('_')]), 1)
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
    return f"{op_class}_{op_function}_options"


class BatchArgumentTree:
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

    def _is_silent(self, name):
        """Whether argument should not be exposed"""
        arg = self._arg_tree[name]
        full_path = full_name(arg)
        return arg['path'] in pformat.SILENT_PARAMETERS or full_path in pformat.SILENT_PARAMETERS

    def _is_bool(self, name):
        """Whether argument value is a boolean"""
        return self._arg_tree[name]['type'] == 'bool'

    def _is_list(self, name):
        """Whether argument value is a list"""
        return self._arg_tree[name]['type'].startswith('List[') or self._arg_tree[name]['type'] == '{str}'

    def _is_datetime(self, name):
        """Whether argument value is a timestamp"""
        return self._arg_tree[name]['type'] in ['iso-8601', 'rfc-1123'] or \
            self._arg_tree[name]['type'] == 'datetime.datetime'

    def _is_duration(self, name):
        """Whether argument is value is a duration"""
        return self._arg_tree[name]['type'] == 'duration' or self._arg_tree[name]['type'] == 'datetime.timedelta'

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
            if not any(getattr(namespace, n) for n in children):
                return []
        siblings = self._get_siblings(path)
        if not siblings:
            raise ValueError("Invalid argument dependency tree")  # TODO
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

    def deserialize_json(self, kwargs, json_obj):
        """Deserialize the contents of a JSON file into the request body
        parameter.
        :param dict kwargs: The request kwargs
        :param dict json_obj: The loaded JSON content
        """
        from msrest.exceptions import DeserializationError
        message = "Failed to deserialized JSON file into object {}"
        try:
            def remove_none_values(d):
                """Recursively remove None values from dictionaries."""
                if isinstance(d, dict):
                    return {k: remove_none_values(v) for k, v in d.items() if v is not None}
                if isinstance(d, list):
                    return [remove_none_values(v) for v in d if v is not None]
                return d

            json_obj = remove_none_values(json_obj)
            import azure.batch.models
            model_type = getattr(azure.batch.models, self._request_param['model'])
            # Use from_dict in order to deserialize with case insensitive
            kwargs[self._request_param['name']] = model_type(json_obj).as_dict(exclude_readonly=True)
        except DeserializationError as error:
            message += f": {error}"
            raise ValueError(message.format(self._request_param['model']))

        if kwargs[self._request_param['name']] is None:
            raise ValueError(message.format(self._request_param['model']))

    def queue_argument(self, name=None, path=None, root=None,
                       options=None, type=None,  # pylint: disable=redefined-builtin
                       dependencies=None, restname=None, restpath=None):
        """Add pending command line argument
        :param str name: The name of the command line argument.
        :param str path: The complex object path to the parameter.
        :param str root: The original name of the parameter.
        :param dict options: The kwargs to be used to instantiate CLICommandArgument.
        :param list dependencies: A list of complete paths to other parameters that
         are required if this parameter is set.
        """
        self._arg_tree[name] = {
            'path': path,
            'root': root,
            'restpath': restpath,
            'restname': restname,
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
        """Generator to convert pending arguments into CLICommandArgument
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
                details['options']['nargs'] = '?'
                details['options']['help'] = argparse.SUPPRESS
                details['options']['required'] = False
                details['options']['action'] = IgnoreAction
            yield (name, CLICommandArgument(dest=name, **details['options']))

    def existing(self, name):
        """Whether the argument name is already used by a pending
        argument.
        :param str name: The name of the argument to check.
        :returns: bool
        """
        return name in self._arg_tree

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
                    namespace.json_file = get_file_json(namespace.json_file)
                except OSError:
                    raise ValueError("Cannot access JSON request file: " + namespace.json_file)
                except ValueError as err:
                    raise ValueError(f"Invalid JSON file: {err}")
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


class AzureBatchDataPlaneCommand:
    # pylint: disable=too-many-instance-attributes, too-few-public-methods, too-many-statements
    def __init__(self, operation, command_loader, client_factory=None, validator=None, **kwargs):

        if not isinstance(operation, str):
            raise ValueError(f"Operation must be a string. Got '{operation}'")

        self._flatten = kwargs.pop('flatten', pformat.FLATTEN)  # Number of object levels to flatten
        self._head_cmd = False

        self.parser = None
        self.validator = validator
        self.client_factory = client_factory
        self.confirmation = 'delete' in operation
        self._operation_func = None

        # The name of the request options parameter
        # self._options_param = format_options_name(operation)
        # Arguments used for request options
        self._options_attrs = []
        # The loaded options model to populate for the request
        self._options_model = None

        def _get_operation():
            if not self._operation_func:
                self._operation_func = command_loader.get_op_handler(operation)

            return self._operation_func

        def _load_arguments():
            return self._load_transformed_arguments(_get_operation())

        def _load_descriptions():
            return self.extract_full_summary_from_signature(_get_operation())

        # pylint: disable=inconsistent-return-statements
        def _execute_command(kwargs):
            cmd = kwargs.pop('cmd')

            client = self.client_factory(cmd.cli_ctx, kwargs)

            stream_output = kwargs.pop('destination', None)
            json_file = kwargs.pop('json_file', None)

            # Build the request parameters from command line arguments
            if json_file:
                self.parser.deserialize_json(kwargs, json_file)
                for arg, _ in self.parser:
                    del kwargs[arg]
            else:
                for arg, details in self.parser:
                    try:
                        param_value = kwargs.pop(arg)
                        if param_value is None:
                            continue
                        self._build_parameters(
                            details['restpath'],
                            kwargs,
                            details['restname'],
                            param_value)
                    except KeyError:
                        continue
            self.filter_args(kwargs)
            # Make request
            if self._head_cmd:
                kwargs['raw'] = True
            result = _get_operation()(client, **kwargs)

            # Head output
            if self._head_cmd:
                return result

            # File download
            if stream_output:
                with open(stream_output, "wb") as file_handle:
                    for data in result:
                        file_handle.write(data)
                return

            # Otherwise handle based on return type of results
            if isinstance(result, ItemPaged):
                return list(result)

            return result

        self.table_transformer = None
        try:
            transform_func = operation.split('.')[-1].replace('-', '_')
            self.table_transformer = getattr(transformers, transform_func + "_table_format")
        except AttributeError:
            pass

        self.handler = _execute_command
        self.argument_loader = _load_arguments
        self.description_loader = _load_descriptions
        self.merged_kwargs = kwargs

    def filter_args(self, kwargs):
        for key in list(kwargs.keys()):
            if kwargs[key] is None:
                del kwargs[key]
        # in track1 we had --if-match and --if-none-match, in track2 they are packaged in a match-condition param
        if kwargs.get('if_match') is not None:
            if kwargs['if_match'] == '*':
                kwargs['match_condition'] = MatchConditions.IfPresent
            else:
                kwargs['etag'] = kwargs['if_match']
                kwargs['match_condition'] = MatchConditions.IfNotModified
            del kwargs['if_match']

        if kwargs.get('if_none_match') is not None:
            kwargs['etag'] = kwargs['if_none_match']
            kwargs['match_condition'] = MatchConditions.IfModified
            del kwargs['if_none_match']

        # in track1 we had --start-range and --end-range, in track2 they are packaged in a ocp_range param
        if kwargs.get('start_range') or kwargs.get('end_range'):
            start = kwargs.get('start_range') if kwargs.get('start_range') else 0
            end = kwargs.get('end_range') if kwargs.get('end_range') else ""
            if kwargs.get('start_range'):
                del kwargs['start_range']
            if kwargs.get('end_range'):
                del kwargs['end_range']
            kwargs['ocp_range'] = f"bytes={start}-{end}"

    def get_kwargs(self):
        args = {
            'handler': self.handler,
            'argument_loader': self.argument_loader,
            'description_loader': self.description_loader,
            'transform': batch_transformer.transform_result,
            'table_transformer': self.table_transformer,
            'confirmation': self.confirmation,
            'client_factory': self.client_factory
        }
        args.update(self.merged_kwargs)
        return args

    def _build_parameters(self, path, kwargs, param, value):
        """Recursively build request parameter dictionary from command line args.
        :param str path: Current parameter namespace.
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
            if param in pformat.IGNORE_OPTIONS:
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
        return param.count('.') < self._flatten and param not in pformat.IGNORE_PARAMETERS

    def _get_attrs(self, model, path):
        """Get all the attributes from the complex parameter model that should
        be exposed as command line arguments.
        :param class model: The parameter model class.
        :param str path: Request parameter namespace.
        """
        attribute_map = self.get_track1_attribute_map(model)
        validations = self.get_track1_validations(model)

        for attr, details in attribute_map.items():  # pylint: disable=protected-access
            conditions = []
            full_path = '.'.join([self.parser._request_param['name'], path, attr])  # pylint: disable=protected-access
            conditions.append(
                validations.get(attr, {}).get('readonly'))  # pylint: disable=protected-access
            conditions.append(
                validations.get(attr, {}).get('constant'))  # pylint: disable=protected-access
            conditions.append(any(i for i in pformat.IGNORE_PARAMETERS if i in full_path))
            if not any(conditions):
                yield attr, details

    def _process_options(self):
        """Process the request options parameter to expose as arguments."""
        for param in [o for o in self._options_attrs if o not in pformat.IGNORE_OPTIONS]:
            options = {}
            options['required'] = False
            options['arg_group'] = 'Pre-condition and Query'
            if param in ['if_modified_since', 'if_unmodified_since']:
                options['type'] = validators.datetime_format
            if param in pformat.FLATTEN_OPTIONS:
                for f_param, f_docstring in pformat.FLATTEN_OPTIONS[param].items():
                    options['default'] = None
                    options['help'] = f_docstring
                    options['options_list'] = [arg_name(f_param)]
                    options['validator'] = validators.validate_options
                    yield (f_param, CLICommandArgument(f_param, **options))
            else:
                options['default'] = getattr(self._options_model, param)
                options['help'] = find_param_help(self._options_model, param)
                options['options_list'] = [arg_name(param)]
                yield (param, CLICommandArgument(param, **options))

    def _resolve_conflict(self,
                          arg, param, path, options, typestr, dependencies, conflicting, restname, restpath):
        """Resolve conflicting command line arguments.
        :param str arg: Name of the command line argument.
        :param str param: Original request parameter name.
        :param str path: Request parameter namespace.
        :param dict options: The kwargs to be used to instantiate CLICommandArgument.
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
            self._resolve_conflict(new, param, path, options, typestr, dependencies, conflicting, restname, restpath)
        elif arg in conflicting or arg in pformat.QUALIFIED_PROPERTIES:
            new = _build_prefix(arg, param, path)
            if new in conflicting or new in pformat.QUALIFIED_PROPERTIES and '.' not in path:
                self.parser.queue_argument(arg, path, param, options, typestr, dependencies, restname, restpath)
            else:
                options['options_list'] = [arg_name(new)]
                self._resolve_conflict(new, param, path, options,
                                       typestr, dependencies, conflicting, restname, restpath)
        else:
            self.parser.queue_argument(arg, path, param, options, typestr, dependencies, restname, restpath)

    def get_track1_validations(self, cls):
        """Method that takes in a class and a list of members from get_optional_state and overrides any values that have
        a readyonly field.  This matches track1's _validation model structure
        """
        # pylint: disable=protected-access
        filtered_members = self.get_optional_state(cls)
        for name, value in inspect.getmembers(cls):
            if not name.startswith('__') and not inspect.isroutine(value):
                if (value is not None and
                        isinstance(value, _RestField) and
                        hasattr(value, "_visibility") and
                        value._visibility is not None and
                        len(value._visibility) > 0):
                    read_only = value._visibility[0] == "read"
                    filtered_members[name] = {'readonly': read_only}
        return filtered_members

    def convert_to_track1_type(self, original_type):
        if original_type is not None and "ForwardRef" in original_type:
            pattern = r"ForwardRef\('_models\.(.*?)'\)"
            original_type = re.sub(pattern, r'\1', original_type)
        if original_type is not None and "_models." in original_type:
            original_type = original_type.replace("_models.", "")
        if original_type is not None and "typing.List" in original_type:
            original_type = original_type.replace("typing.List", "List")
        if original_type is not None and "typing.Dict" in original_type:
            original_type = original_type.replace("typing.Dict", "Dict")
        if original_type is not None and "typing.Union" in original_type:
            pattern = r"typing\.Union\[\w+, (\w+), \w+\]"
            match = re.search(pattern, original_type)
            if match:
                original_type = match.group(1)
        if original_type is not None and "typing.Union" in original_type:
            pattern = r"typing\.Union\[str, (\w+)\]"
            match = re.search(pattern, original_type)
            if match:
                pattern = r"typing\.Union\[str, (.+?)\]"
                original_type = re.sub(pattern, r"\1", original_type)

        if original_type is not None and "<class" in original_type:
            pattern = r"<class '([\w\.]+)'>"
            match = re.search(pattern, original_type)
            if match:
                original_type = match.group(1)
        return original_type

    def get_track1_rest_names(self, cls):
        # pylint: disable=protected-access
        rest_names = {}
        for name, value in inspect.getmembers(cls):
            rest_name = name
            if not name.startswith('_') and not inspect.isroutine(value):
                try:
                    if (value is not None and
                            isinstance(value, _RestField) and
                            hasattr(value, "_rest_name") and
                            value._rest_name is not None and
                            len(value._rest_name) > 0):
                        rest_name = value._rest_name
                except ValueError:
                    pass  # The _rest_name property can throw a ValueError when calling hasattr()
                rest_names[name] = rest_name
        return rest_names

    def get_track1_attribute_map(self, cls):
        # pylint: disable=protected-access
        member_types = {}
        pattern1 = r"^typing\.Union\[str, (.+), NoneType\]$"
        pattern2 = r"^typing\.Union\[(.+), NoneType\]$"
        pattern3 = r"^typing\.Optional\[(.+)\]$"

        rest_names = self.get_track1_rest_names(cls)
        for name, typ in cls.__annotations__.items():
            if hasattr(typ, '_name') and typ._name is not None and typ._name == 'Optional':
                track1_type = self.convert_to_track1_type(str(get_args(typ)[0]))
            else:
                track1_type = str(typ)

                if re.match(pattern1, track1_type):
                    track1_type = self.convert_to_track1_type(str(get_args(typ)[1]))
                elif re.match(pattern2, track1_type):
                    track1_type = self.convert_to_track1_type(str(get_args(typ)[0]))
                elif re.match(pattern3, track1_type):
                    track1_type = self.convert_to_track1_type(str(get_args(typ)[0]))
                else:
                    track1_type = self.convert_to_track1_type(track1_type)

            if rest_names[name] is None:
                print("none")
            member_types[name] = {'key': rest_names[name], 'type': track1_type}

        return member_types

    def get_optional_state(self, cls):
        """Method that will go through a class and return a list of its member variables and their required status"""
        # pylint: disable=protected-access
        globalns = {}
        # Add the global namespace of the module where the class is defined
        globalns.update(vars(importlib.import_module(cls.__module__)))
        # azure batch models uses an alias _models which throws off the get_type_hints eval, need this to correct
        globalns['_models'] = importlib.import_module('azure.batch.models')

        members = get_type_hints(cls, globalns=globalns)
        filtered_members = {}
        for name, type_hint in members.items():
            is_optional = (type_hint._name == 'Optional' or type_hint._name is None
                           if hasattr(type_hint, '_name') else False)
            filtered_members[name] = {'required': not is_optional}
        return filtered_members

    def _flatten_object(self, path, param_model, conflict_names=None, restpath=None):
        """Flatten a complex parameter object into command line arguments.
        :param str path: The complex parameter namespace.
        :param class param_model: The complex parameter class.
        :param list conflict_names: List of argument names that conflict.
        """
        conflict_names = conflict_names or []

        if self._should_flatten(path):
            validations = self.get_track1_validations(param_model)
            required_attrs = [key for key, val in validations.items() if val.get('required')]

            for param_attr, details in self._get_attrs(param_model, path):
                options = {}
                options['options_list'] = [arg_name(param_attr)]
                options['required'] = False
                options['arg_group'] = group_title(path)
                options['help'] = find_param_help(param_model, param_attr)
                options['validator'] = \
                    lambda ns: validators.validate_required_parameter(ns, self.parser)
                options['default'] = None  # Extract details from signature

                if details['type'] in pformat.BASIC_TYPES:
                    self._resolve_conflict(param_attr, param_attr, path, options,
                                           details['type'], required_attrs, conflict_names, details['key'], restpath)
                elif details['type'].startswith('List['):
                    # We only expose a list arg if there's a validator for it
                    # This will fail for 2D arrays - though Batch doesn't have any yet
                    inner_type = details['type'][5:-1]
                    if inner_type in pformat.BASIC_TYPES:
                        options['help'] += " Space-separated values."
                        self._resolve_conflict(
                            param_attr, param_attr, path, options,
                            details['type'], required_attrs, conflict_names, details['key'], restpath)
                    else:
                        inner_type = operations_name(inner_type)
                        try:
                            validator = getattr(validators, inner_type + "_format")
                            options['help'] += ' ' + validator.__doc__
                            options['type'] = validator
                            self._resolve_conflict(
                                param_attr, param_attr, path, options,
                                details['type'], required_attrs, conflict_names, details['key'], restpath)
                        except AttributeError:
                            continue
                elif details['type'] == 'Dict[str, str]':
                    # Only string dictionaries are currently supported, but right now
                    # Batch doesn't have any other kind
                    options['help'] += " Space-separated values in 'key=value' format."
                    options['type'] = validators.string_dictionary_format
                    self._resolve_conflict(
                        param_attr, param_attr, path, options,
                        details['type'], required_attrs, conflict_names, details['key'], restpath)
                else:
                    attr_model = _load_model(details['type'])
                    if issubclass(attr_model, Enum):  # Must be an enum
                        values_index = options['help'].find(' Possible values include')
                        if values_index >= 0:
                            choices = options['help'][values_index + 25:].split(', ')
                            options['choices'] = [enum_value(c)
                                                  for c in choices if enum_value(c) != "unmapped"]
                            options['help'] = options['help'][0:values_index]
                        self._resolve_conflict(param_attr, param_attr, path, options,
                                               details['type'], required_attrs, conflict_names,
                                               details['key'], restpath)
                    else:
                        self._flatten_object(path='.'.join([path, param_attr]),
                                             param_model=attr_model,
                                             restpath='.'.join([restpath, details['key']]))

    def extract_full_summary_from_signature(self, operation):
        """ Extract the summary from the docstring of the command. """
        lines = inspect.getdoc(operation)
        regex = r'\s*(:param|:keyword)\s+(.+?)\s*:(.*)'
        summary = ''
        if lines:
            match = re.search(regex, lines)
            summary = lines[:match.regs[0][0]] if match else lines

        summary = summary.replace('\n', ' ').replace('\r', '')
        return summary

    def _load_transformed_arguments(self, handler):
        """Load all the command line arguments from the request parameters.
        :param func handler: The operation function.
        """
        from argcomplete.completers import DirectoriesCompleter, FilesCompleter
        from azure.cli.core.commands.parameters import file_type
        self.parser = BatchArgumentTree(self.validator)
        # self._load_options_model(handler)
        args = []

        for arg in extract_args_from_signature(handler, excluded_params=EXCLUDED_PARAMS):
            arg_type = find_param_type(handler, arg[0])
            if arg_type is None:
                continue  # we get into this case for keyword params that we want to skip

            if arg_type.startswith("str or"):
                docstring = find_param_help(handler, arg[0])
                choices = []
                values_index = docstring.find(' Possible values include')
                if values_index >= 0:
                    choices = docstring[values_index + 25:].split(', ')
                    choices = [enum_value(c) for c in choices if enum_value(c) != "'unmapped'"]
                    docstring = docstring[0:values_index]
                args.append((arg[0], CLICommandArgument(arg[0],
                                                        options_list=[arg_name(arg[0])],
                                                        required=False,
                                                        default=None,
                                                        choices=choices,
                                                        help=docstring)))
            elif arg_type.startswith("~"):  # TODO: could add handling for enums
                param_type = class_name(arg_type)
                self.parser.set_request_param(arg[0], param_type)
                param_model = _load_model(param_type)
                self._flatten_object(path=arg[0], param_model=param_model, restpath=arg[0])
                for flattened_arg in self.parser.compile_args():
                    args.append(flattened_arg)
                param = 'json_file'
                docstring = f"A file containing the {arg[0].replace('_', ' ')} specification in JSON " \
                            "(formatted to match the respective REST API body). " \
                            f"If this parameter is specified, all '{group_title(arg[0])} Arguments'" \
                            " are ignored."
                args.append((param, CLICommandArgument(param,
                                                       options_list=[arg_name(param)],
                                                       required=False,
                                                       default=None,
                                                       type=file_type,
                                                       completer=FilesCompleter(),
                                                       help=docstring)))
            elif arg[0] not in pformat.IGNORE_PARAMETERS:
                args.append(arg)
        return_type = find_return_type(handler)
        if return_type and return_type.startswith('bytes'):  # track2 bytes
            param = 'destination'
            docstring = "The path to the destination file or directory."
            args.append((param, CLICommandArgument(param,
                                                   options_list=[arg_name(param)],
                                                   required=True,
                                                   default=None,
                                                   completer=DirectoriesCompleter(),
                                                   type=file_type,
                                                   validator=validators.validate_file_destination,
                                                   help=docstring)))
        if return_type == 'None' and handler.__name__.startswith('get'):
            self._head_cmd = True
        if self.confirmation:
            param = CONFIRM_PARAM_NAME
            docstring = 'Do not prompt for confirmation.'
            args.append((param, CLICommandArgument(param,
                                                   options_list=['--yes', '-y'],
                                                   required=False,
                                                   action='store_true',
                                                   help=docstring)))
        auth_group_name = 'Batch Account'
        args.append(('cmd', CLICommandArgument('cmd', action=IgnoreAction)))
        args.append(('account_name', CLICommandArgument(
            'account_name', options_list=['--account-name'], required=False, default=None,
            validator=validators.validate_client_parameters, arg_group=auth_group_name,
            help='Batch account name. Alternatively, set by environment variable: AZURE_BATCH_ACCOUNT')))
        args.append(('account_key', CLICommandArgument(
            'account_key', options_list=['--account-key'], required=False, default=None, arg_group=auth_group_name,
            help='Batch account key. Alternatively, set by environment variable: AZURE_BATCH_ACCESS_KEY')))
        args.append(('account_endpoint', CLICommandArgument(
            'account_endpoint', options_list=['--account-endpoint'], required=False,
            default=None, arg_group=auth_group_name,
            help='Batch service endpoint. Alternatively, set by environment variable: AZURE_BATCH_ENDPOINT')))
        return args


class BatchCommandGroup(AzCommandGroup):

    def batch_command(self, name, method_name=None, command_type=None, **kwargs):
        self._check_stale()
        merged_kwargs = self.group_kwargs.copy()
        group_command_type = merged_kwargs.get('command_type', None)
        if command_type:
            merged_kwargs.update(command_type.settings)
        elif group_command_type:
            merged_kwargs.update(group_command_type.settings)
        merged_kwargs.update(kwargs)

        operations_tmpl = merged_kwargs.get('operations_tmpl')
        command_name = f'{self.group_name} {name}' if self.group_name else name
        operation = operations_tmpl.format(method_name) if operations_tmpl else None
        command = AzureBatchDataPlaneCommand(operation, self.command_loader, **merged_kwargs)

        self.command_loader._cli_command(command_name, **command.get_kwargs())  # pylint: disable=protected-access
