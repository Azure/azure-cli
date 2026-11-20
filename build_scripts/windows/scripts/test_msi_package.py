# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Invoke this script in Powershell with:
# & 'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe' test_msi_package.py <start_mod_name>

import os
import struct
import sys
import subprocess
import sysconfig


def main():
    if sysconfig.get_platform() != 'win-amd64' or struct.calcsize('P') != 8:
        print('MSI package tests require the installed x64 Python interpreter.', file=sys.stderr)
        return 1

    base_dir = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'azure', 'cli')
    root_dir = os.path.join(base_dir, 'command_modules')
    mod_list = [mod for mod in sorted(os.listdir(root_dir))
                if os.path.isdir(os.path.join(root_dir, mod)) and mod != '__pycache__']

    pytest_base_cmd = [sys.executable, '-m', 'pytest', '-x', '-v', '-p', 'no:warnings', '--log-level', 'WARN']
    pytest_parallel_cmd = pytest_base_cmd + ['-n', 'auto']

    start_mod = sys.argv[1] if len(sys.argv) > 1 else ''
    for mod_name in mod_list:
        if mod_name < start_mod:
            continue
        mod_cmd = ['--junit-xml', '{}\\azure_cli_test_result\\{}.xml'.format(os.path.expanduser('~'), mod_name),
                   '--pyargs', 'azure.cli.command_modules.{}'.format(mod_name)]
        if mod_name in ['botservice', 'network']:
            exit_code = subprocess.call(pytest_base_cmd + mod_cmd)
        else:
            exit_code = subprocess.call(pytest_parallel_cmd + mod_cmd)
        if exit_code == 5:
            print('No tests found for {}'.format(mod_name))
        elif exit_code != 0:
            return exit_code

    core_dir = os.path.join(base_dir, 'core')
    return subprocess.call(pytest_base_cmd + [
        '--junit-xml', '{}\\azure_cli_test_result\\azure-cli-core.xml'.format(os.path.expanduser('~')),
        '-n', 'auto', '--import-mode=append', core_dir])


if __name__ == '__main__':
    sys.exit(main())
