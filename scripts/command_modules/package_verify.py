## Install the command modules using pip ##
from __future__ import print_function
import os
import sys
import fileinput

from _common import get_all_command_modules, exec_command, print_summary

def set_version(path_to_setup):
    for i, line in enumerate(fileinput.input(path_to_setup, inplace=1)):
        sys.stdout.write(line.replace('version=VERSION', "version='1000.0.0'"));

all_command_modules = get_all_command_modules()

# Build the packages

print('Building CLI package...')
PATH_TO_CLI_PACKAGE = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..'))
success = exec_command('python setup.py sdist', cwd=PATH_TO_CLI_PACKAGE)
if not success:
    print('Error building CLI!', file=sys.stderr)
    sys.exit(1)
print('Built CLI package.')

print('Building command package(s)...')
failed_module_names = []
for name, fullpath in all_command_modules:
    path_to_setup = fullpath+'/setup.py'
    # give package a high version no. so when we install, we install this one
    # and not a version from PyPI
    set_version(path_to_setup)
    success = exec_command('python setup.py sdist', cwd=fullpath)
    if not success:
        failed_module_names.append(name)

if failed_module_names:
    print('Error building command packages!', file=sys.stderr)
    # exits script if there are failed modules
    print_summary(failed_module_names)

print('Built command package(s).')


## TODO Make dynamic
success = exec_command('pip install http://40.112.211.51:8080/packages/adal-0.2.1.zip')
if not success:
    print('Error installing ADAL!', file=sys.stderr)
    sys.exit(1)

# Install the packages
print('Installing CLI package...')
cli_package_dir = os.path.join(PATH_TO_CLI_PACKAGE, 'dist')
success = exec_command('pip install azure-cli --find-links file://{}'.format(cli_package_dir))
if not success:
    print('Error installing CLI!', file=sys.stderr)
    sys.exit(1)
print('Installed CLI package.')

print('Installing command package(s)...')
failed_module_names = []
for name, fullpath in all_command_modules:
    package_dir = os.path.join(fullpath, 'dist')
    success = exec_command('pip install {} --find-links file://{}'.format(name, package_dir))
    if not success:
        failed_module_names.append(name)

if failed_module_names:
    print('Error installing command packages!', file=sys.stderr)
    # exits script if there are failed modules
    print_summary(failed_module_names)

print('Installed command package(s).')

# Validate the installation




failed_module_names = []
for name, fullpath in all_command_modules:
    if not success:
        failed_module_names.append(name)

print_summary(failed_module_names)
