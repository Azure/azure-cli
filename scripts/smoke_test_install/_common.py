# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import hashlib
from six import StringIO, text_type, u
import sh
from sh import az, ssh

RESOURCE_GROUP = os.environ.get('AZ_TEST_RG')
AZURE_CLI_PACKAGE_VERSION_PREV = os.environ.get('AZ_TEST_CLI_VERSION_PREV')
AZURE_CLI_PACKAGE_VERSION = os.environ.get('AZ_TEST_CLI_VERSION')
AZ_TEST_LOGIN_USERNAME = os.environ.get('AZ_TEST_LOGIN_USERNAME')
AZ_TEST_LOGIN_PASSWORD = os.environ.get('AZ_TEST_LOGIN_PASSWORD')

assert (RESOURCE_GROUP and AZURE_CLI_PACKAGE_VERSION_PREV and AZURE_CLI_PACKAGE_VERSION and
        AZ_TEST_LOGIN_USERNAME and AZ_TEST_LOGIN_PASSWORD),\
        "Not all required environment variables have been set. Set AZ_TEST_RG, AZ_TEST_CLI_VERSION_PREV, "\
        "AZ_TEST_CLI_VERSION, AZ_TEST_LOGIN_USERNAME and AZ_TEST_LOGIN_PASSWORD"

INSTALL_URL = os.environ.get('AZ_TEST_INSTALL_URL') or 'https://aka.ms/projectazinstalldev'
VM_USERNAME = os.environ.get('AZ_TEST_VM_USERNAME') or 'myuser'

INSTALL_DIRECTORY_PROMPT_MSG = "In what directory would you like to place the install? (leave blank to use /usr/local/az): "
INSTALL_EXEC_DIRECTORY_PROMPT_MSG = "In what directory would you like to place the executable? (leave blank to use /usr/local/bin): "
INSTALL_TAB_COMPLETE_PROMPT_MSG = "Enable shell/tab completion? [y/N]: "

# By default, sh will truncate stdout/stderr output.
# But we want to see everything to make test debugging easier.
# see: https://github.com/amoffat/sh/blob/master/sh.py#L171
sh.ErrorReturnCode.truncate_cap = None

def create_vm(vm_name_prefix, vm_image):
    # _ is not valid in a vm name
    vm_name = '{}-{}'.format(vm_name_prefix.replace('_', '-'), RESOURCE_GROUP)
    vm_name = hashlib.md5(vm_name.encode()).hexdigest()[:10]
    az(['vm', 'create', '-g', RESOURCE_GROUP, '-n', vm_name, '--authentication-type', 'ssh', '--image', vm_image, '--admin-username', VM_USERNAME, '--deployment-name', vm_name])
    io = StringIO()
    az(['vm', 'list-ip-addresses', '--resource-group', RESOURCE_GROUP, '--name', vm_name, '--query', '[0].virtualMachine.network.publicIpAddresses[0].ipAddress'], _out=io)
    vm_ip_address = io.getvalue().strip().replace('"', '')
    io.close()
    vm = ssh.bake(['-oStrictHostKeyChecking=no', '-tt', "{}@{}".format(VM_USERNAME, vm_ip_address)])
    return vm

def _get_install_command(install_url, nightly_version, sudo):
    return "export AZURE_CLI_PACKAGE_VERSION={nightly_version}; curl -L {install_url} | {sudo_str} bash".format(
        nightly_version=nightly_version,
        install_url=install_url,
        sudo_str = 'sudo -E' if sudo else '')

def _decode_str(output):
    if not isinstance(output, text_type):
        output = u(str(output))
    return output

def install_cli_interactive(vm, install_directory=None, exec_directory=None, tab_completion_ans=None, install_url=INSTALL_URL, nightly_version=AZURE_CLI_PACKAGE_VERSION, sudo=False):
    # Follows pattern suggested at https://amoffat.github.io/sh/tutorials/2-interacting_with_processes.html#tutorial2
    io = StringIO()
    def interact(char, stdin):
        io.write(_decode_str(char))
        aggregated_out = io.getvalue()
        if aggregated_out.endswith(INSTALL_DIRECTORY_PROMPT_MSG):
            stdin.put('{}\n'.format(install_directory if install_directory else ''))
        elif aggregated_out.endswith(INSTALL_EXEC_DIRECTORY_PROMPT_MSG):
            stdin.put('{}\n'.format(exec_directory if exec_directory else ''))
        elif aggregated_out.endswith(INSTALL_TAB_COMPLETE_PROMPT_MSG):
            stdin.put('{}\n'.format(tab_completion_ans if tab_completion_ans else ''))
    vm(_get_install_command(install_url, nightly_version, sudo), _out=interact, _err=interact, _out_bufsize=0, _tty_in=True).wait()
    io.close()

def verify_basic(vm, az='az'):
    '''
    az: the executable to run (e.g. '~/localinstall/az')
    '''
    # TODO Check to error loading command module
    vm([az])
    vm([az, "login", "-u", AZ_TEST_LOGIN_USERNAME, "-p", AZ_TEST_LOGIN_PASSWORD])
    vm([az, 'vm', 'list'])

def verify_tab_complete(vm):
    # TODO: Also check completion by running 'complete' and using grep to verify the output
    try:
        vm(['grep', '-q', "\"source '/usr/local/az/az.completion'\"", '~/.bashrc'])
    except sh.ErrorReturnCode_1 as e:
        raise Exception("Tab completion should be enabled but source command not found in rc file")
