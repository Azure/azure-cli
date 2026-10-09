# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import fnmatch
import os
import subprocess
import sys


def verify_rpm_installation(rpm_name=None, python_package=None):
    metadata = subprocess.check_output(
        ['rpm', '-q', '--queryformat', '%{NAME} %{VERSION} %{RELEASE} %{ARCH}', 'azure-cli'],
        text=True).split()
    if len(metadata) != 4 or metadata[0] != 'azure-cli':
        raise RuntimeError(f'Expected one installed azure-cli RPM, got: {metadata}')
    name, version, release, arch = metadata
    filename = f'{name}-{version}-{release}.{arch}.rpm'
    if rpm_name and not fnmatch.fnmatchcase(filename, rpm_name):
        raise RuntimeError(f'Installed RPM {filename} does not match the requested artifact {rpm_name}')

    native_arch = subprocess.check_output(['rpm', '--eval', '%{_arch}'], text=True).strip()
    if arch != native_arch:
        raise RuntimeError(f'Installed RPM architecture {arch} does not match {native_arch}')

    cli_version = subprocess.check_output(
        ['az', 'version', '--query', '"azure-cli"', '--output', 'tsv'], text=True).strip()
    # Development builds label the RPM "dev" without changing the embedded CLI version.
    if version != 'dev' and cli_version != version:
        raise RuntimeError(f'Installed CLI version {cli_version} does not match RPM version {version}')

    if python_package:
        requires = subprocess.check_output(['rpm', '-q', '--requires', 'azure-cli'], text=True)
        if not any(line.split()[0] == python_package for line in requires.splitlines() if line.strip()):
            raise RuntimeError(f'Installed RPM does not require the selected Python package {python_package}')
        subprocess.check_call(['rpm', '-q', python_package])


def main():
    verify_rpm_installation(os.environ.get('RPM_NAME'), os.environ.get('PYTHON_PACKAGE'))
    python_version = os.listdir('/usr/lib64/az/lib/')[0]
    root_dir = f'/usr/lib64/az/lib/{python_version}/site-packages/azure/cli/command_modules'
    mod_list = [mod for mod in sorted(os.listdir(root_dir)) if os.path.isdir(os.path.join(root_dir, mod)) and mod != '__pycache__']

    pytest_base_cmd = f'PYTHONPATH=/usr/lib64/az/lib/{python_version}/site-packages python -m pytest -v --forked -p no:warnings --log-level=WARN'
    pytest_parallel_cmd = '{} -n logical'.format(pytest_base_cmd)

    # cloud: https://github.com/Azure/azure-cli/pull/14994
    # appservice: https://github.com/Azure/azure-cli/pull/19810
    # iot, resource, azure-cli-core: https://github.com/Azure/azure-cli/pull/26176
    serial_test_modules = ['botservice', 'network', 'cloud', 'appservice', 'iot', 'resource']

    for mod_name in mod_list:
        cmd = '{} --junit-xml /azure_cli_test_result/{}.xml --pyargs azure.cli.command_modules.{}'.format(
            pytest_base_cmd if mod_name in serial_test_modules else pytest_parallel_cmd, mod_name, mod_name)
        print('Running:', cmd, flush=True)
        exit_code = subprocess.call(cmd, shell=True)
        if exit_code == 5:
            print('No tests found for {}'.format(mod_name))
        elif exit_code != 0:
            sys.exit(exit_code)

    exit_code = subprocess.call(['{} --junit-xml /azure_cli_test_result/azure-cli-core.xml --pyargs azure.cli.core'.format(pytest_base_cmd)], shell=True)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
