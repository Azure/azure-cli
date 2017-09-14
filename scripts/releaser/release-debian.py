#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This script is interactive as you need to log in to 'az'.

from __future__ import print_function

import os
import sys
import time
from datetime import datetime
from six import StringIO
from sh import az, ssh


script_env = {}

def add_script_env(name):
    script_env[name] = os.environ.get(name)

add_script_env('REPO_NAME')
add_script_env('CLI_VERSION')
add_script_env('CLI_DOWNLOAD_SHA256')
add_script_env('AZURE_STORAGE_CONNECTION_STRING')
add_script_env('DEBIAN_REPO_ID')
add_script_env('MS_REPO_URL')
add_script_env('MS_REPO_USERNAME')
add_script_env('MS_REPO_PASSWORD')

assert (all(script_env[n] != None for n in script_env)), "Not all required environment variables have been set.  {}".format(script_env)

REPO_UPLOAD_SCRIPT_TMPL = """
import os, requests
payload = {{'name': 'azure-cli', 'version': '{cli_version}-1', 'repositoryId': '{repo_id}', 'sourceUrl': '{source_url}'}}
r = requests.post('{repo_package_url}', verify=False, auth=('{repo_user}', '{repo_pass}'), json=payload)
print('Status Code')
print(r.status_code)
print('Query with a GET to the following:')
print(r.headers['Location'])
"""

def print_env_vars():
    for n in script_env:
        print('{} = {}'.format(n, script_env[n]))


def print_status(msg=''):
    print('-- '+msg)

def print_heading(heading):
    print('{0}\n{1}\n{0}'.format('=' * len(heading), heading))

def give_chance_to_cancel(msg_prefix=''):
    cancel_time_secs = 10
    msg_tmpl = '{}: Starting in {} seconds.'
    for i in range(cancel_time_secs, 0, -1):
        print_status(msg_tmpl.format(msg_prefix, i))
        time.sleep(1)

def main():
    print_env_vars()
    time_str = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    az(["login"], _out=sys.stdout, _err=sys.stdout)
    resource_group = 'azurecli-release-debian-' + time_str
    vm_name = 'vm-debian-' + time_str
    print_status('Creating resource group.')
    az(['group', 'create', '-l', 'westus', '-n', resource_group], _out=sys.stdout, _err=sys.stdout)
    print_status('Creating VM.')
    az(['vm', 'create', '-g', resource_group, '-n', vm_name, '--generate-ssh-keys', '--authentication-type', 'ssh',
        '--image', 'Canonical:UbuntuServer:14.04.4-LTS:latest', '--admin-username', 'ubuntu'],
       _out=sys.stdout, _err=sys.stdout)
    io = StringIO()
    print_status('Getting VM IP address.')
    az(['vm', 'list-ip-addresses', '--resource-group', resource_group, '--name', vm_name,
        '--query', '[0].virtualMachine.network.publicIpAddresses[0].ipAddress'], _out=io)
    ip_address = io.getvalue().strip().replace('"', '')
    print_status('VM IP address is {}'.format(ip_address))
    io.close()
    vm_connect_str = "ubuntu@{}".format(ip_address)
    my_vm = ssh.bake(['-oStrictHostKeyChecking=no', vm_connect_str])
    print_status('Installing git.')
    my_vm(['sudo', 'apt-get', 'update', '&&', 'sudo', 'apt-get', 'install', '-y', 'git'],
          _out=sys.stdout, _err=sys.stdout)
    io = StringIO()
    my_vm(['mktemp', '-d'], _out=io)
    repo_dir = io.getvalue().strip()
    io.close()
    print_status('Cloning repo.')
    my_vm(['git', 'clone', 'https://github.com/{}'.format(script_env.get('REPO_NAME')), repo_dir], _out=sys.stdout, _err=sys.stdout)
    path_to_debian_build_script = os.path.join(repo_dir, 'packaged_releases', 'debian', 'debian_build.sh')
    path_to_dir_creator = os.path.join(repo_dir, 'packaged_releases', 'debian', 'debian_dir_creator.sh')
    io = StringIO()
    my_vm(['mktemp', '-d'], _out=io)
    build_artifact_dir = io.getvalue().strip()
    io.close()
    print_status('Running debian build scripts.')
    my_vm(['chmod', '+x', path_to_debian_build_script, path_to_dir_creator], _out=sys.stdout, _err=sys.stdout)
    my_vm(['export', 'CLI_VERSION={}'.format(script_env.get('CLI_VERSION')), '&&',
           'export', 'CLI_DOWNLOAD_SHA256={}'.format(script_env.get('CLI_DOWNLOAD_SHA256')), '&&',
           'export', 'BUILD_ARTIFACT_DIR={}'.format(build_artifact_dir), '&&',
           path_to_debian_build_script, path_to_dir_creator],
          _out=sys.stdout, _err=sys.stdout)
    print_status('Debian build complete.')
    io = StringIO()
    my_vm(['ls', build_artifact_dir], _out=io)
    artifact_name = io.getvalue().strip()
    io.close()
    deb_file_path = os.path.join(build_artifact_dir, artifact_name)
    print_status('Installing the .deb on the build machine')
    my_vm(['sudo', 'dpkg', '-i', deb_file_path], _out=sys.stdout, _err=sys.stdout)
    # Upload to Azure Storage
    print_status('Uploading .deb to Azure storage.')
    my_vm(['az', 'storage', 'container', 'create', '--name', 'repos', '--public-access', 'blob',
           '--connection-string', '"{}"'.format(script_env.get('AZURE_STORAGE_CONNECTION_STRING'))],
          _out=sys.stdout, _err=sys.stdout)
    my_vm(['az', 'storage', 'blob', 'upload', '-f', deb_file_path,
           '-n', artifact_name, '-c', 'repos', '--connection-string', '"{}"'.format(script_env.get('AZURE_STORAGE_CONNECTION_STRING'))],
          _out=sys.stdout, _err=sys.stdout)
    io = StringIO()
    my_vm(['az', 'storage', 'blob', 'url', '-n', artifact_name, '-c', 'repos', '--output', 'tsv',
           '--connection-string', '"{}"'.format(script_env.get('AZURE_STORAGE_CONNECTION_STRING'))], _out=io)
    deb_url = io.getvalue().strip()
    io.close()
    print_status('Debian file uploaded to the following URL.')
    print_status(deb_url)
    # Publish to apt service
    my_vm(['wget', '-q', 'https://bootstrap.pypa.io/get-pip.py'], _out=sys.stdout, _err=sys.stdout)
    my_vm(['sudo', 'python', 'get-pip.py'], _out=sys.stdout, _err=sys.stdout)
    my_vm(['sudo', 'pip', 'install', '--upgrade', 'requests'], _out=sys.stdout, _err=sys.stdout)
    upload_script = REPO_UPLOAD_SCRIPT_TMPL.format(cli_version=script_env.get('CLI_VERSION'),
                                                   repo_id=script_env.get('DEBIAN_REPO_ID'),
                                                   source_url=deb_url,
                                                   repo_package_url=script_env.get('MS_REPO_URL'),
                                                   repo_user=script_env.get('MS_REPO_USERNAME'),
                                                   repo_pass=script_env.get('MS_REPO_PASSWORD'))
    my_vm(['echo', '-e', '"{}"'.format(upload_script), '>>', 'repo_upload.py'], _out=sys.stdout, _err=sys.stdout)
    my_vm(['python', 'repo_upload.py'], _out=sys.stdout, _err=sys.stdout)
    print_status('Done. :)')
    give_chance_to_cancel('Delete resource group (in background)')
    az(['group', 'delete', '--name', resource_group, '--yes', '--no-wait'], _out=sys.stdout, _err=sys.stdout)
    print_status('Finished. :)')

if __name__ == '__main__':
    main()
