#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from __future__ import print_function, unicode_literals

import os
import sys
import tempfile
import glob
import re
import time
import fileinput
import requests
import hashlib

from datetime import datetime

from subprocess import check_call, check_output, CalledProcessError
from uritemplate import URITemplate, expand


script_env = {}

def add_script_env(name):
    script_env[name] = os.environ.get(name)

add_script_env('REPO_NAME')
add_script_env('GITHUB_USER')
add_script_env('GITHUB_USER_TOKEN')
add_script_env('PYPI_REPO')
# although not used directly here, twine env vars are needed for releasing
add_script_env('TWINE_USERNAME')
add_script_env('TWINE_PASSWORD')
# the new version of the CLI
add_script_env('CLI_VERSION')
add_script_env('AZURE_STORAGE_CONNECTION_STRING')

assert (all(script_env[n] != None for n in script_env)), "Not all required environment variables have been set.  {}".format(script_env)

GITHUB_API_AUTH = (script_env.get('GITHUB_USER'), script_env.get('GITHUB_USER_TOKEN'))
GITHUB_API_HEADERS = {'Accept': 'application/vnd.github.v3+json', 'user-agent': 'azure-cli-pypi-github-releaser/v1'}

SOURCE_ARCHIVE_NAME = 'source.tar.gz'

GITHUB_RELEASE_BODY_TMPL = """
The module has been published to PyPI.

View HISTORY.rst of the module for a changelog.

{}

Full release notes at https://docs.microsoft.com/en-us/cli/azure/release-notes-azure-cli

"""

COMMAND_MODULE_PREFIX = 'azure-cli-'
MODULES_TO_ALWAYS_RELEASE = ['azure-cli']
MODULES_TO_SKIP = ['azure-cli-testsdk']

def give_chance_to_cancel(msg_prefix=''):
    cancel_time_secs = 10
    msg_tmpl = '{}: Starting in {} seconds.'
    for i in range(cancel_time_secs, 0, -1):
        print_status(msg_tmpl.format(msg_prefix, i))
        time.sleep(1)

def print_env_vars():
    for n in script_env:
        print('{} = {}'.format(n, script_env[n]))

def print_status(msg=''):
    print('-- '+msg)

def print_heading(heading):
    print('{0}\n{1}\n{0}'.format('=' * len(heading), heading))

def _get_core_modules_paths(repo_working_dir):
    for path in glob.glob(repo_working_dir + '/src/*/setup.py'):
        yield os.path.basename(os.path.dirname(path)), os.path.dirname(path)

def _get_command_modules_paths(repo_working_dir, include_prefix=False):
    for path in glob.glob(repo_working_dir + '/src/command_modules/{}*/setup.py'.format(
            COMMAND_MODULE_PREFIX)):
        folder = os.path.dirname(path)
        name = os.path.basename(folder)
        if not include_prefix:
            name = name[len(COMMAND_MODULE_PREFIX):]
        yield name, folder

def _get_all_module_paths(repo_working_dir):
    return list(_get_core_modules_paths(repo_working_dir)) + list(_get_command_modules_paths(repo_working_dir, include_prefix=True))

def _get_current_module_version(mod_path):
    mod_version = None
    with open(os.path.join(mod_path, 'setup.py'), 'r') as fh:
        version_re = re.compile('VERSION = *')
        lines = fh.readlines()
        for _, line in enumerate(lines):
            if version_re.match(line):
                mod_version = line.split('=')[1].strip(' "\'').split('+')[0]
    return mod_version

def clone_repo(repo_working_dir):
    check_call(['git', 'clone', 'https://github.com/{}'.format(script_env.get('REPO_NAME')), repo_working_dir])
    check_call(['git', 'checkout', 'master'], cwd=repo_working_dir)

def should_release_module(mod_name, mod_path, repo_working_dir):
    if mod_name in MODULES_TO_ALWAYS_RELEASE:
        print_status('We always release {}.'.format(mod_name))
        return True
    if mod_name in MODULES_TO_SKIP:
        print_status('Skipping module {} as in modules to skip list.'.format(mod_name))
        return False
    # Determine if should release based on the current version
    cur_mod_version = _get_current_module_version(mod_path)
    r_start = '{}-{}'.format(mod_name, cur_mod_version)
    revision_range = "{}..{}".format(r_start, 'HEAD')
    try:
        module_changes = check_output(["git", "log", "--pretty=format:* %s", revision_range, "--", mod_path, ":(exclude)*/tests/*"],
                                      cwd=repo_working_dir)
    except CalledProcessError:
        # Maybe the revision_range is invalid if this is a new module.
        return True
    if module_changes:
        print_status('Begin changes in {}'.format(mod_name))
        print(str(module_changes, 'utf-8'))
        print_status('End changes in {}'.format(mod_name))
        return True
    print_status('Skipping module {} as there are no changes.'.format(mod_name))
    return False

def modify_setuppy_version(mod_name, mod_path):
    setuppy_path = os.path.join(mod_path, 'setup.py')
    with open(setuppy_path, 'r') as fh:
        version_re = re.compile('VERSION = *')
        lines = fh.readlines()
        for index, line in enumerate(lines):
            if version_re.match(line):
                old_version = line.split('=')[1].strip(' "\'').split('+')[0]
                major, minor, rev = old_version.split('.')
                rev = int(rev) + 1
                version = '{}.{}.{}'.format(major, minor, rev)
                lines[index] = 'VERSION = "{}+dev"\n'.format(version)
                update_setup = lines
                break
        else:
            raise ValueError('In the setup file {}, version is not found.'.format(setuppy_path))
    if update_setup:
        with open(setuppy_path, 'w') as fh:
            fh.writelines(update_setup)
    else:
        raise ValueError('No updated content for setup.py in {}.'.format(mod_name))
    return old_version, version

def modify_initpy_version(mod_name, mod_path, old_version, new_version):
    if mod_name == 'azure-cli':
        path_to_init = os.path.join(mod_path, 'azure', 'cli', '__init__.py')
    elif mod_name == 'azure-cli-core':
        path_to_init = os.path.join(mod_path, 'azure', 'cli', 'core', '__init__.py')
    for _, line in enumerate(fileinput.input(path_to_init, inplace=1)):
        if line.startswith('__version__'):
            sys.stdout.write(line.replace(old_version, new_version))
        else:
            sys.stdout.write(line)

def modify_historyrst(mod_name, mod_path, old_version, new_version):
    historyrst_path = os.path.join(mod_path, 'HISTORY.rst')
    new_history_lines = []
    just_seen_unreleased = False
    contains_unreleased = False
    with open(historyrst_path, 'r') as fq:
        lines = fq.readlines()
    for _, line in enumerate(lines):
        if 'unreleased' in line.lower() and not line.startswith('* '):
            contains_unreleased = True
    if contains_unreleased:
        for _, line in enumerate(lines):
            if just_seen_unreleased:
                # skip the line as it's just a heading for the old unreleased section
                just_seen_unreleased = False
                continue
            if 'unreleased' in line.lower() and not line.startswith('* '):
                new_heading = '{} ({})'.format(new_version, datetime.utcnow().strftime('%Y-%m-%d'))
                line = '{}\n{}\n'.format(new_heading, '+' * len(new_heading))
                just_seen_unreleased = True
            new_history_lines.append(line)
    else:
        for index, line in enumerate(lines):
            if line.startswith('Release History'):
                begin = index + 2
            if old_version in line:
                end = index
                break
        new_heading = '{} ({})'.format(new_version, datetime.utcnow().strftime('%Y-%m-%d'))
        line = '{}\n{}\n'.format(new_heading, '+' * len(new_heading))
        release_notes = [line]
        if mod_name in MODULES_TO_ALWAYS_RELEASE:
            release_notes.append('* no changes\n\n')
        else:
            release_notes.append('* minor fixes\n\n')
        new_history_lines = lines[:begin] + release_notes + lines[end:]
    with open(historyrst_path, 'w') as fq:
        fq.writelines(new_history_lines)


def release_module(mod_name, mod_path, repo_working_dir):
    # Change version in setup.py
    old_version, new_version = modify_setuppy_version(mod_name, mod_path)
    # Need to modify __init__.py for these modules as well
    if mod_name in ['azure-cli', 'azure-cli-core']:
        modify_initpy_version(mod_name, mod_path, old_version, new_version)
    # Modify HISTORY.rst
    modify_historyrst(mod_name, mod_path, old_version, new_version)
    # Create commit with appropriate message.
    commit_message = 'Release {} {}'.format(mod_name, new_version)
    check_call(['git', 'commit', '-am', commit_message], cwd=repo_working_dir)
    commitish = check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_working_dir)
    commitish = str(commitish, 'utf-8')
    commitish = commitish.strip()
    return mod_name, commitish, new_version


def install_cli_into_venv():
    venv_dir = tempfile.mkdtemp()
    check_call(['virtualenv', venv_dir])
    path_to_pip = os.path.join(venv_dir, 'bin', 'pip')
    extra_index_url = 'https://testpypi.python.org/simple' if script_env.get('PYPI_REPO') == 'https://test.pypi.org/legacy/' else None
    args = [path_to_pip, 'install', 'azure-cli']
    if extra_index_url:
        args.extend(['--extra-index-url', extra_index_url])
    check_call(args)
    deps = check_output([path_to_pip, 'freeze'])
    deps = str(deps, 'utf-8')
    deps = deps.split('\n')
    cli_components = []
    for dep in deps:
        if dep.startswith('azure-cli'):
            cli_components.append(dep.split('=='))
    return cli_components

def run_push_to_git():
    repo_working_dir = tempfile.mkdtemp()
    clone_repo(repo_working_dir)
    configure_git(repo_working_dir)
    commitish_list = []
    for mod_name, mod_path in _get_all_module_paths(repo_working_dir):
        print_heading(mod_name.upper())
        if should_release_module(mod_name, mod_path, repo_working_dir):
            mod_name, commitish, new_version = release_module(mod_name, mod_path, repo_working_dir)
            commitish_list.append((mod_name, commitish, new_version))
        else:
            print_status('Skipped {}'.format(mod_name))
    # Push all commits to master.
    check_call(['git', 'push', '-f', 'origin', 'master'], cwd=repo_working_dir)
    return commitish_list

def set_up_cli_repo_dir():
    working_dir = tempfile.mkdtemp()
    check_call(['git', 'clone', 'https://github.com/{}'.format(script_env.get('REPO_NAME')), working_dir])
    check_call(['pip', 'install', '-e', 'tools'], cwd=working_dir)
    return working_dir

def publish_to_pypi(working_dir, commitish_list):
    # Publish all in commitish list to PyPI
    assets_dir_map = {}
    for mod_name, commitish, _ in commitish_list:
        assets_dir = tempfile.mkdtemp()
        check_call(['git', 'checkout', commitish], cwd=working_dir)
        check_call(['python', '-m', 'tools.automation.release.run', '-c', mod_name,
                    '-r', script_env.get('PYPI_REPO'), '--dest', assets_dir], cwd=working_dir)
        assets_dir_map[mod_name] = assets_dir
    # reset back
    check_call(['git', 'checkout', 'master'], cwd=working_dir)
    return assets_dir_map

def upload_asset(upload_uri_tmpl, filepath, label):
    filename = os.path.basename(filepath)
    upload_url = URITemplate(upload_uri_tmpl).expand(name=filename, label=label)
    headers = GITHUB_API_HEADERS
    headers['Content-Type'] = 'application/octet-stream'
    with open(filepath, 'rb') as payload:
        requests.post(upload_url, data=payload, auth=GITHUB_API_AUTH, headers=headers)

def upload_assets_for_github_release(upload_uri_tmpl, component_name, component_version, assets_dir):
    for filename in os.listdir(assets_dir):
        fullpath = os.path.join(assets_dir, filename)
        if filename == SOURCE_ARCHIVE_NAME:
            upload_asset(upload_uri_tmpl, fullpath, '{} {} source code (.tar.gz)'.format(component_name, component_version))
        elif filename.endswith('.tar.gz'):
            upload_asset(upload_uri_tmpl, fullpath, '{} {} Source Distribution (.tar.gz)'.format(component_name, component_version))
        elif filename.endswith('.whl'):
            upload_asset(upload_uri_tmpl, fullpath, '{} {} Python Wheel (.whl)'.format(component_name, component_version))

def run_create_github_release(commitish_list, assets_dir_map):
    # Create Github release (inc. the artifacts .whl etc.).
    print_heading('Creating GitHub releases')
    for mod_name, commitish, mod_version in commitish_list:
        print_status('Publishing GitHub release for {} {}'.format(mod_name, mod_version))
        tag_name = '{}-{}'.format(mod_name, mod_version)
        release_name = "{} {}".format(mod_name, mod_version)
        if script_env.get('PYPI_REPO') == 'https://upload.pypi.org/legacy/':
            released_pypi_url = 'https://pypi.org/project/{}/{}'.format(mod_name, mod_version)
        elif script_env.get('PYPI_REPO') == 'https://test.pypi.org/legacy/':
            released_pypi_url = 'https://test.pypi.org/project/{}/{}'.format(mod_name, mod_version)
        else:
            released_pypi_url = ''
        payload = {'tag_name': tag_name, "target_commitish": commitish, "name": release_name, "body": GITHUB_RELEASE_BODY_TMPL.format(released_pypi_url), "prerelease": False}
        r = requests.post('https://api.github.com/repos/{}/releases'.format(script_env.get('REPO_NAME')), json=payload, auth=GITHUB_API_AUTH, headers=GITHUB_API_HEADERS)
        if r.status_code == 201:
            upload_url = r.json()['upload_url']
            upload_assets_for_github_release(upload_url, mod_name, mod_version, assets_dir_map[mod_name])
            print_status('Published GitHub release for {} {}'.format(mod_name, mod_version))
        else:
            print_status('ERROR: Failed to create GitHub release for {} {}'.format(mod_name, mod_version))

def run_create_packaged_release(working_dir):
    # After releasing, create a new venv, and pip install and verify then create
    # list of components for the package release step.
    print_status('Start installing CLI into venv')
    components_list = install_cli_into_venv()
    print_status('Finished installing CLI into venv')
    archive_dir = tempfile.mkdtemp()
    # create the packaged releases automatically
    args = ['python', '-m', 'tools.automation.release.packaged', '--version', script_env.get('CLI_VERSION'), '--dest', archive_dir, '--components']
    for name, version in components_list:
        # The tag for this module is slightly different so make that change.
        if name == 'azure-cli-command-modules-nspkg':
            name = 'azure-cli-command_modules-nspkg'
        args.append('{}={}'.format(name, version))
    print_status(' '.join(args))
    check_call(args, cwd=working_dir)
    print_status('Created packaged release in dir {}'.format(archive_dir))
    # Get the sha256sum
    archive_file_name = os.listdir(archive_dir)[0]
    archive_file_path = os.path.join(archive_dir, archive_file_name)
    sha256 = hashlib.sha256()
    with open(archive_file_path, 'rb') as f:
        sha256.update(f.read())
    computed_hash = sha256.hexdigest()
    print_status('SHA256 of {} is {}'.format(archive_file_path, computed_hash))
    # Upload release archive to Azure Storage
    check_call(['az', 'storage', 'blob', 'upload', '--file', archive_file_path, '--name', archive_file_name, '--container-name', 'releases', '--connection-string', script_env.get('AZURE_STORAGE_CONNECTION_STRING')])
    archive_url = check_output(['az', 'storage', 'blob', 'url', '--name', archive_file_name, '--container-name', 'releases', '--connection-string', script_env.get('AZURE_STORAGE_CONNECTION_STRING'), '--output', 'tsv'])
    archive_url = str(archive_url, 'utf-8')
    archive_url = archive_url.strip()
    print_status('Archive URL is {}'.format(archive_url))

def configure_git(repo_working_dir):
    check_call(['git', 'config', 'user.email', '{}@users.noreply.github.com'.format(script_env.get('GITHUB_USER'))], cwd=repo_working_dir)
    check_call(['git', 'config', 'user.name', script_env.get('GITHUB_USER')], cwd=repo_working_dir)
    check_call(['git', 'remote', 'set-url', 'origin', 'https://{}:{}@github.com/{}'.format(script_env.get('GITHUB_USER'), script_env.get('GITHUB_USER_TOKEN'), script_env.get('REPO_NAME'))], cwd=repo_working_dir)

if __name__ == "__main__":
    print_env_vars()
    give_chance_to_cancel('Create Git release commits')
    release_commitish_list = run_push_to_git()
    cli_repo_dir = set_up_cli_repo_dir()
    give_chance_to_cancel('Publish to PyPI')
    release_assets_dir_map = publish_to_pypi(cli_repo_dir, release_commitish_list)
    give_chance_to_cancel('Create GitHub releases and tags')
    run_create_github_release(release_commitish_list, release_assets_dir_map)
    give_chance_to_cancel('Create Packaged Release archive')
    # We need to clone the repo again as we've now pushed the git tags and we need them to create the packaged release.
    # (we could do 'git pull' but this is easier and uses a clean directory just to be safe)
    cli_repo_dir = set_up_cli_repo_dir()
    run_create_packaged_release(cli_repo_dir)
    print_status('Done.')
