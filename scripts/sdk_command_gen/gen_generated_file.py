"""
Create the generated.py file for a command module.
"""
from __future__ import print_function
import os
import sys
import re
import inspect
from importlib import import_module

OUT_FILE = sys.stdout

EXCLUDED_PARAMS = frozenset(['self', 'raw', 'custom_headers', 'operation_config',
                             'content_version', 'kwargs', 'client'])

FILTERED_STREAM_COMMANDS = []
FILTERED_COMPLEX_COMMANDS = []

def _error_exit(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def _get_args(argv):
    if len(argv) != 2:
        usage_msg = 'Usage: {} <sdk_package> <command_module_name>'.format(os.path.basename(__file__))
        usage_msg += '\n\n e.g. {} azure.mgmt.web webapp\n'.format(os.path.basename(__file__))
        usage_msg += 'Got {} instead.\n'.format(argv)
        _error_exit(usage_msg)
    sdk_package = argv[0]
    command_module_name = argv[1]
    return sdk_package, command_module_name

def _output_imports(command_module_name, sdk_package_operations, operation_classes):
    '''Generate the headers for the file.'''
    for op_class in operation_classes:
        print('from {} import {}'.format(sdk_package_operations, op_class.__name__), file=OUT_FILE)
    print(file=OUT_FILE)
    print('from azure.cli.commands import cli_command', file=OUT_FILE)
    print(file=OUT_FILE)
    print('from azure.cli.command_modules.{}._factory import client_factory'.format(command_module_name), file=OUT_FILE)
    print(file=OUT_FILE)

def _create_command_name(command_module_name, op_class_name, method_name):
    # Remove 'Operations' from name (e.g. GlobalModelOperations to GlobalModel)
    sub_command_name = op_class_name.replace('Operations', '')
    # Capitalized to hyphenated (e.g. GlobalModel to global-model)
    sub_command_name = re.sub('(?!^)([A-Z]+)', r'-\1', sub_command_name).lower()
    # Create full command name (e.g. webapp global-model get-all-sites)
    if command_module_name == sub_command_name:
        command_name = '{} {}'.format(command_module_name, method_name.replace('_', '-'))
    else:
        command_name = '{} {} {}'.format(command_module_name, sub_command_name, method_name.replace('_', '-'))
    return command_name

def _get_arg_types(method):
    '''
    If the type is split over multiple lines, only the first line is considered.
    e.g. See create_or_update_managed_hosting_environment.managed_hosting_environment_envelope in SDK
    '''
    lines = inspect.getdoc(method)
    arg_types = {}
    if lines:
        lines = lines.splitlines()
        for line in lines:
            match = re.search(r'\s*(:type)\s+(.+)\s*:(.*)', line)
            if match:
                try:
                    name = match.group(2).strip()
                    type = match.group(3).strip()
                    arg_types[name] = type
                except IndexError:
                    pass
    return arg_types

def _is_complex_command(op_class, method_name):
    '''
    A command is defined as complex if the type of its required args is not str or int
    '''
    method = getattr(op_class, method_name)
    arg_types = _get_arg_types(method)
    sig = inspect.getargspec(method)
    args = sig.args
    for arg_name in [a for a in args if not a in EXCLUDED_PARAMS]:
        arg_defaults = (dict(zip(sig.args[-len(sig.defaults):], sig.defaults))
                            if sig.defaults
                            else {})
        required = arg_name not in arg_defaults
        if required and arg_types.get(arg_name) not in ['str', 'int']:
            return True
    return False

def _get_return_type(op_class, method_name):
    return_type = None
    method = getattr(op_class, method_name)
    source_code_lines = inspect.getsourcelines(method)[0]
    for line in source_code_lines:
        type_match = re.search("deserialized = self._deserialize\('(.*)', response\)", line)
        if (type_match):
            return_type = type_match.group(1)
            break
        # Check if it's a stream
        if line.strip() == "deserialized = self._client.stream_download(response, callback)":
            return_type = '<Stream>'
            break
    return "'{}'".format(return_type) if return_type else 'None'

def _output_operation_factory(sdk_package, op_class):
    mgmt_clients = [module_obj for module_name, module_obj in sdk_package.__dict__.iteritems() if module_name.endswith('ManagementClient')]
    # expecting only 1 management client
    if len(mgmt_clients) == 1:
        mgmt_client = mgmt_clients[0]
        source_code_lines = inspect.getsourcelines(getattr(mgmt_client, '__init__'))[0]
        pattern = "self.(.*) = {}".format(op_class.__name__)
        for line in source_code_lines:
            match = re.search(pattern, line)
            if (match):
                factory_name = match.group(1)
                print("factory = lambda _: client_factory().{}".format(factory_name), file=OUT_FILE)
                return
    # By default, just output this
    print('# TODO factory = ...', file=OUT_FILE)

def _output_gen_operation_commands(sdk_package_str, op_class, command_module_name):
    methods = [op for op in dir(op_class) if not op.startswith('_')]
    print('# {}'.format(op_class.__name__), file=OUT_FILE)
    sdk_package = import_module(sdk_package_str)
    _output_operation_factory(sdk_package, op_class)
    for method_name in methods:
        command_name = _create_command_name(command_module_name, op_class.__name__, method_name)
        is_complex = _is_complex_command(op_class, method_name)
        return_type = _get_return_type(op_class, method_name)
        cli_command_str = "cli_command('{}', {}.{}, factory)".format(command_name, op_class.__name__, method_name)
        if is_complex:
            FILTERED_COMPLEX_COMMANDS.append(cli_command_str)
        elif return_type == "'<Stream>'":
            FILTERED_STREAM_COMMANDS.append(cli_command_str)
        else:
            print(cli_command_str, file=OUT_FILE)
    print(file=OUT_FILE)

def main(argv, out_file=None):
    global OUT_FILE
    if out_file:
        OUT_FILE = out_file

    sdk_package, command_module_name = _get_args(argv)

    # Import the operations module
    sdk_package_operations = sdk_package + '.operations'
    operations_pkg = import_module(sdk_package_operations)

    # Get the operation classes
    operation_classes = [module_obj for module_name, module_obj in operations_pkg.__dict__.iteritems() if module_name.endswith('Operations')]
    # Output file header
    _output_imports(command_module_name, sdk_package_operations, operation_classes)

    for op_class in operation_classes:
        _output_gen_operation_commands(sdk_package, op_class, command_module_name)

    if FILTERED_COMPLEX_COMMANDS:
        print('# TODO The following commands have complex params.', file=OUT_FILE)
        for cmd in FILTERED_COMPLEX_COMMANDS:
            print('# TODO-COMPLEX {}'.format(cmd), file=OUT_FILE)
        print(file=OUT_FILE)

    if FILTERED_STREAM_COMMANDS:
        print('# TODO The following commands output streams.', file=OUT_FILE)
        for cmd in FILTERED_STREAM_COMMANDS:
            print('# TODO-STREAM {}'.format(cmd), file=OUT_FILE)
        print(file=OUT_FILE)

if __name__ == '__main__':
    main(sys.argv[1:])

