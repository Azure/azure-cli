# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import tempfile
import datetime
from subprocess import check_output, CalledProcessError
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib  # pylint: disable=import-error

from ..utilities.display import print_heading
from ..utilities.path import get_repo_root
from ..utilities.pypi import is_available_on_pypi

# TODO Add 'msi' once we support it
BUILD_TYPES = ['debian', 'docker', 'rpm', 'pypi', 'homebrew']

def build_all_debian(git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    # To only build a certain debian package, comment out the ones you don't want from the list below
    dists = [
        ('wheezy', 'debian:wheezy'),
        ('jessie', 'debian:jessie'),
        ('stretch', 'debian:stretch'),
        ('artful', 'ubuntu:artful'),
        ('xenial', 'ubuntu:xenial'),
        ('trusty', 'ubuntu:trusty'),
        ('bionic', 'ubuntu:bionic'),
    ]
    with ThreadPoolExecutor(max_workers=len(dists)) as executor:
            tasks = {executor.submit(build_debian, dist_info, git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns) for dist_info
                    in dists}
            for t in as_completed(tasks):
                t.result()
    print('Finished debian builds for {}. Check each build message above for completion status.'.format(', '.join([d[0] for d in dists])))

def build_debian(dist_info, git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    # If you need to release a revision to the package, change this number then reset back to 1 for the next release
    revision = 1
    dist_codename = dist_info[0]
    docker_image = dist_info[1]
    cmd = ['docker', 'run', '-d', '-e', 'CLI_VERSION=' + cli_version,
           '-e', 'CLI_VERSION_REVISION={}~{}'.format(revision, dist_codename), '-e', 'BUILD_ARTIFACT_DIR=/artifacts',
           '-v', artifact_dir + ':/artifacts', docker_image, '/bin/bash', '-cx',
           'apt-get update && apt-get install -y git wget sudo && git clone --progress --verbose {} --branch {} /repo_clone '
           '&& cd /repo_clone && build_scripts/debian/build.sh /repo_clone'.format(git_url, git_branch)]
    container_id = check_output(cmd, universal_newlines=True).strip()
    print('Debian {} build running. Use `docker logs -f {}`'.format(dist_info[0], container_id))
    exit_code = check_output(['docker', 'wait', container_id], universal_newlines=True).strip()
    print('FINISHED Debian {} build. Exit code {} (0 for success)'.format(dist_info[0], exit_code))


def build_docker(git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    cmd = ['docker', 'build', '--no-cache', '--quiet', '--build-arg', 'BUILD_DATE="`date -u +"%Y-%m-%dT%H:%M:%SZ"`"',
           '--build-arg', 'CLI_VERSION=' + cli_version, get_repo_root()]
    print('Docker build started. The git url and branch parameters are ignored. We use the current repository.')
    image_id = check_output(cmd, universal_newlines=True).strip()
    image_id = image_id.split(':')[1]
    image_file_location = os.path.join(artifact_dir, 'docker-azure-cli-{}.tar'.format(cli_version))
    cmd = ['docker', 'save', '-o', image_file_location, image_id]
    image_id = check_output(cmd, universal_newlines=True).strip()
    print('COMPLETED Docker build. image id: {}, saved to {}'.format(image_id, image_file_location))


def build_rpm(git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    cmd = ['docker', 'run', '-d', '-e', 'CLI_VERSION=' + cli_version, '-e', 'REPO_PATH=/repo_clone',
           '-v', artifact_dir + ':/artifacts', 'centos:7', '/bin/bash', '-cx',
           'yum check-update; yum install -y gcc git rpm-build rpm-devel rpmlint make bash coreutils diffutils patch '
           'rpmdevtools python libffi-devel python-devel openssl-devel wget && git clone --progress --verbose {} '
           '--branch {} /repo_clone && cd /repo_clone && rpmbuild -v -bb --clean build_scripts/rpm/azure-cli.spec && '
           'cp /root/rpmbuild/RPMS/x86_64/* /artifacts/'.format(git_url, git_branch)]
    container_id = check_output(cmd, universal_newlines=True).strip()
    print('RPM build running. Use `docker logs -f {}` to view logs'.format(container_id))
    exit_code = check_output(['docker', 'wait', container_id], universal_newlines=True).strip()
    print('FINISHED RPM build. Exit code {} (0 for success)'.format(exit_code))


def build_pypi(git_url, git_branch, _, artifact_dir, arg_ns=None):
    cmd = ['docker', 'run', '-d', '-v', artifact_dir + ':/artifacts', 'python:3.6', '/bin/bash', '-cx',
           'mkdir /artifacts/pypi && git clone --progress --verbose {} --branch {} /repo_clone && cd /repo_clone && '
           'python build_scripts/pypi/build.py /artifacts/pypi /repo_clone'.format(git_url, git_branch)]
    container_id = check_output(cmd, universal_newlines=True).strip()
    print('Python pypi build message: The version numbers of packages will be as defined in source code.')
    print('Python pypi build running. Use `docker logs -f {}`'.format(container_id))
    exit_code = check_output(['docker', 'wait', container_id], universal_newlines=True).strip()
    print('COMPLETED Python pypi build. Exit code {}'.format(exit_code))


def build_msi(git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    # TODO
    print('SKIPPED MSI build. Not Yet Implemented. Please build manually.')


def build_homebrew(git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    if not is_available_on_pypi('azure-cli', cli_version):
        print('Homebrew message : The Homebrew formula requires CLI packages to be available on public PyPI. '
              'Version {} of the CLI does not appear to be on PyPI. '
              'If it was just updated, this message can be safely ignored.'.format(cli_version))

    upstream_url = arg_ns.homebrew_upstream_url or 'https://github.com/Azure/azure-cli/archive/azure-cli-{cli_version}.tar.gz'.format(
        cli_version=cli_version)
    print('Homebrew message: The generated formula uses the latest public packages that are available on PyPI, '
          'not the code in your Git repo.')
    cmd = ['docker', 'run', '-d', '-e', 'CLI_VERSION=' + cli_version, '-e', 'BUILD_ARTIFACT_DIR=/artifacts',
           '-e', 'UPSTREAM_URL=' + upstream_url,
           '-v', artifact_dir + ':/artifacts', 'python:3.6', '/bin/bash', '-cx',
           'pip install sh && git clone --progress --verbose {} --branch {} /repo_clone && cd /repo_clone && '
           'python build_scripts/homebrew/formula-generate.py'.format(git_url, git_branch)]
    container_id = check_output(cmd, universal_newlines=True).strip()
    print('Homebrew formula generation running. Use `docker logs -f {}`'.format(container_id))
    exit_code = check_output(['docker', 'wait', container_id], universal_newlines=True).strip()
    print('COMPLETED Homebrew formula generation. Exit code {}'.format(exit_code))


def build_dispatch(build_type, git_url, git_branch, cli_version, artifact_dir, arg_ns=None):
    if build_type == 'debian':
        build_all_debian(git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns)
    elif build_type == 'docker':
        build_docker(git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns)
    elif build_type == 'rpm':
        build_rpm(git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns)
    elif build_type == 'pypi':
        build_pypi(git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns)
    elif build_type == 'msi':
        build_msi(git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns)
    elif build_type == 'homebrew':
        build_homebrew(git_url, git_branch, cli_version, artifact_dir, arg_ns=arg_ns)


def cli_build(args):
    assert check_output(['docker', 'ps']), "Docker required."
    build_types = args.build_types
    git_url = args.git_clone_url
    git_branch = args.git_clone_branch
    cli_version = args.cli_version
    artifact_dir = tempfile.mkdtemp(
        prefix='cli-build-{}-'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')), dir=os.getcwd())
    if len(build_types) == 1 and build_types[0] == '*':
        build_types = BUILD_TYPES
    print_heading('Building for {} from branch {} of {} '
                  'and version number will be {}\n'
                  'Build artifacts will be in {}'.format(', '.join(build_types), git_branch, git_url, cli_version,
                                                         artifact_dir))
    with ThreadPoolExecutor(max_workers=len(build_types)) as executor:
        tasks = {executor.submit(build_dispatch, bt, git_url, git_branch, cli_version, artifact_dir, arg_ns=args) for bt
                 in build_types}
        for t in as_completed(tasks):
            t.result()
    print('Done.')


def init_args(root):
    cli_build_parser = root.add_parser('build', help='Build the CLI. Docker is required.')
    cli_build_parser.set_defaults(func=cli_build)
    git_args = cli_build_parser.add_argument_group('Git Clone Arguments')
    git_args.add_argument('-b', '--git-clone-branch', dest='git_clone_branch',
                          help='Branch name that should be checked out. (default: %(default)s)', default='master')
    git_args.add_argument('-u', '--git-clone-url', dest='git_clone_url',
                          help='The url to clone. This will be passed to `git clone`. (default: %(default)s)',
                          default='https://github.com/Azure/azure-cli.git')
    cli_build_parser.add_argument('-t', '--type', dest='build_types', required=True, nargs='+',
                                  choices=BUILD_TYPES + ['*'],
                                  help="Space-separated list of the artifacts to build. Use '*' for all.")
    cli_build_parser.add_argument('-c', '--cli-version', dest='cli_version', required=True,
                                  help="The version of the build. (ignored for 'pypi' type)")
    homebrew_args = cli_build_parser.add_argument_group('Homebrew Specific Arguments')
    homebrew_args.add_argument('--homebrew-upstream-url', dest='homebrew_upstream_url',
                               help='The upstream URL to specify in the formula.')
