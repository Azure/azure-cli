# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from distutils import dir_util
import os
import re
import shutil
import sys

import argparse

from template_to_swagger import convert_template_to_swagger
from upload_arm_templates import upload_template_files
from _common import get_name_from_path, get_config, to_snake_case

def _autorest_client_name(name):
    return '{}creationclient'.format(str.lower(name))

HEADER = """# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: skip-file
"""

INIT_FILE_CONTENTS = HEADER + """import pkg_resources
pkg_resources.declare_namespace(__name__)

"""

def _args_to_list(**kwargs):
    arg_list = []
    for k, v in kwargs.items():
        k = k.replace('_','-')
        arg_list.append('--{}'.format(k))
        arg_list.append(v)
    return arg_list 

def generate_smart_create(*args):

    print('\n== GENERATE SMART CREATE ==')
    
    parser = argparse.ArgumentParser(description='Smart Create Generation')
    parser.add_argument('--src', metavar='PATH', required=True, help='Path to the directory containing the main ARM template. Must contain a directory in the format \'mgmt_<name>\'. Default name of main template is \'azuredeploy.json\' but a different name can be specified.')
    parser.add_argument('--api-version', metavar='VERSION', required=True, help='API version for the template being generated in yyyy-MM-dd format. (ex: 2016-07-01)')
    parser.add_argument('--no-upload', action='store_true', help='Turn off upload to only regenerate the client-side code.')
    args = parser.parse_args(args)

    api_version = args.api_version
    src = args.src or os.path.join(os.getcwd())
    if not os.path.isfile(src):
        root = src
        src = os.path.join(root, 'azuredeploy.json')
    else:
        root = os.path.split(src)[0]
    name = get_name_from_path(root) # name in CamelCase
    dest = root
    if not os.path.isfile(src):
        raise RuntimeError('Main template not found at path: {}'.format(src))
    if not name:
        raise RuntimeError('Unable to parse name from path: {}. Path must contain a directory in the format \'mgmt_<name>\'.'.format(src))

    # Convert the supplied template into Swagger
    swagger_path = convert_template_to_swagger(*_args_to_list(api_version=api_version, src=src, name=to_snake_case(name)))

    # Use AutoRest to generate the Python files from the Swagger
    config = get_config()
    if not config:
        sys.exit(-1)

    AUTO_REST_PATH = config['autorest']['path'] or 'AutoRest.exe'
    cmd = '{} -Namespace Default -CodeGenerator Azure.Python -addcredentials -input {} -OutputDirectory {}'.format(AUTO_REST_PATH, swagger_path, root)
    os.system(cmd)

    # Insert Pylint ignore statements into the generated files
    autorest_generated_path = os.path.join(root, _autorest_client_name(name))
    for root, dirs, files in os.walk(autorest_generated_path):
        path = root.split('/')
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as original: data = original.read()
                with open(os.path.join(root, file), 'w') as modified: modified.write(HEADER + '\n' + data)

    # Rename the generated file directory to lib
    dir_util.copy_tree(autorest_generated_path, os.path.join(dest, 'lib'))
    
    # Create the cheesy __init__.py file in <dest>
    with open(os.path.join(dest, '__init__.py'), 'w') as f:
        f.write(INIT_FILE_CONTENTS)

    if not args.no_upload:
        # Publish template files into blob storage
        upload_template_files(*_args_to_list(src=dest, api_version=api_version, name=name))
    
    # Delete the Generated folder
    shutil.rmtree(autorest_generated_path)
    os.remove(os.path.join(dest, 'setup.py'))

    print("""SMART GENERATION COMPLETE!

Your template is almost ready to be integrated into the CLI. You need to do the following:

(1) If you did not generate your files in-place, move the directory into the project structure.
    Import the newly added directory in Visual Studio so it appears in the Solution Explorer.

(2) Add your folders to the 'packages' list in the parent module's 'setup.py' file with the
    following pattern:
     'azure.cli.command_modules.<module>.mgmt_<resource>_create'
     'azure.cli.command_modules.<module>.mgmt_<resource>_create.lib'
     'azure.cli.command_modules.<module>.mgmt_<resource>_create.lib.models'
     'azure.cli.command_modules.<module>.mgmt_<resource>_create.lib.operations'

(3) Expose your SmartCreate command in the module's 'generated.py' file and tweak any necessary
    parameter aliasing in '_params.py'.
"""
    )

if __name__ == '__main__':
    generate_smart_create(*sys.argv[1:])
