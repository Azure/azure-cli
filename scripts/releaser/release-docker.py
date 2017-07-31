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
add_script_env('DOCKER_REPO')
add_script_env('DOCKER_USERNAME')
add_script_env('DOCKER_PASSWORD')

assert (all(script_env[n] != None for n in script_env)), "Not all required environment variables have been set.  {}".format(script_env)

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
    resource_group = 'azurecli-release-docker-' + time_str
    vm_name = 'vm-docker-' + time_str
    print_status('Creating resource group.')
    az(['group', 'create', '-l', 'westus', '-n', resource_group], _out=sys.stdout, _err=sys.stdout)
    print_status('Creating VM.')
    az(['vm', 'create', '-g', resource_group, '-n', vm_name, '--generate-ssh-keys', '--authentication-type', 'ssh',
        '--image', 'Canonical:UbuntuServer:16.04-LTS:latest', '--admin-username', 'ubuntu'],
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
    print_status('Installing Docker.')
    my_vm(['curl', '-sSL', 'https://get.docker.com/', '-o', 'docker_install_script.sh'],
          _out=sys.stdout, _err=sys.stdout)
    my_vm(['sh', 'docker_install_script.sh'], _out=sys.stdout, _err=sys.stdout)
    print_status('Docker installed.')
    io = StringIO()
    my_vm(['mktemp', '-d'], _out=io)
    repo_dir = io.getvalue().strip()
    io.close()
    print_status('Cloning repo.')
    my_vm(['git', 'clone', 'https://github.com/{}'.format(script_env.get('REPO_NAME')), repo_dir], _out=sys.stdout, _err=sys.stdout)
    image_tag = '{}:{}'.format(script_env.get('DOCKER_REPO'), script_env.get('CLI_VERSION'))
    path_to_dockerfile = os.path.join(repo_dir, 'packaged_releases', 'docker', 'Dockerfile')
    path_to_docker_context = os.path.join(repo_dir, 'packaged_releases', 'docker')
    print_status('Running Docker build.')
    my_vm(['sudo', 'docker', 'build', '--no-cache',
           '--build-arg', 'BUILD_DATE="`date -u +"%Y-%m-%dT%H:%M:%SZ"`"',
           '--build-arg', 'CLI_VERSION={}'.format(script_env.get('CLI_VERSION')),
           '--build-arg', 'CLI_DOWNLOAD_SHA256={}'.format(script_env.get('CLI_DOWNLOAD_SHA256')),
           '-f', path_to_dockerfile,
           '-t', image_tag,
           path_to_docker_context], _out=sys.stdout, _err=sys.stdout)
    print_status('Docker build complete.')
    print_status('Running Docker log in.')
    my_vm(['sudo', 'docker', 'login', '--username', script_env.get('DOCKER_USERNAME'), '--password', '"{}"'.format(script_env.get('DOCKER_PASSWORD'))],
          _out=sys.stdout, _err=sys.stdout)
    print_status('Running Docker push.')
    my_vm(['sudo', 'docker', 'push', image_tag], _out=sys.stdout, _err=sys.stdout)
    print_status('Image pushed to Docker Hub.')
    print_status('Done. :)')
    give_chance_to_cancel('Delete resource group (in background)')
    az(['group', 'delete', '--name', resource_group, '--yes', '--no-wait'], _out=sys.stdout, _err=sys.stdout)
    print_status('Finished. :)')

if __name__ == '__main__':
    main()
