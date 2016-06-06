from __future__ import print_function

import configparser
import distutils
import os
import re
import shutil
import sys

import argparse

from template_to_swagger import convert_template_to_swagger
from upload_arm_templates import upload_template_files
from _common import get_name_from_path, validate_src, parser

def _autorest_client_name(name):
    return '{}creationclient'.format(str.lower(name))

INIT_FILE_CONTENTS = """#pylint: skip-file 
import pkg_resources
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
    
    args = parser.parse_args(args)

    api_version = args.api_version
    root = args.src or os.path.join(os.getcwd())
    src = os.path.join(root, 'azuredeploy.json')
    validate_src(src)
    name = get_name_from_path(root)
    dest = root

    # Convert the supplied template into Swagger
    swagger_path = convert_template_to_swagger(*_args_to_list(api_version=api_version, src=root))

    # Use AutoRest to generate the Python files from the Swagger
    config = configparser.ConfigParser()
    config.read('config.ini')
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
                with open(os.path.join(root, file), 'w') as modified: modified.write("#pylint: skip-file\n" + data)    

    # Rename the generated file directory to lib
    distutils.dir_util.copy_tree(autorest_generated_path, os.path.join(dest, 'lib'))
    
    # Create the cheesy __init__.py file in <dest>
    with open(os.path.join(dest, '__init__.py'), 'w') as f:
        f.write(INIT_FILE_CONTENTS)

    # Publish template files into blob storage
    upload_template_files(*_args_to_list(src=dest, api_version=api_version))
    
    # Delete the Generated folder
    shutil.rmtree(autorest_generated_path)
    os.remove(os.path.join(dest, 'setup.py'))

    print('SMART CREATE GENERATION COMPLETE!')

if __name__ == '__main__':
    generate_smart_create(*sys.argv[1:])