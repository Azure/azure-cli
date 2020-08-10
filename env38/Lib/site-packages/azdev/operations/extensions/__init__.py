# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from collections import OrderedDict
import json
import os
import shutil
import sys

from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError

from azdev.utilities import (
    cmd, py_cmd, pip_cmd, display, get_ext_repo_paths, find_files, get_azure_config, get_azdev_config,
    require_azure_cli, heading, subheading, EXTENSION_PREFIX)

logger = get_logger(__name__)


def add_extension(extensions):

    ext_paths = get_ext_repo_paths()
    all_extensions = find_files(ext_paths, 'setup.py')

    if extensions == ['*']:
        paths_to_add = [os.path.dirname(path) for path in all_extensions if 'site-packages' not in path]
    else:
        paths_to_add = []
        for path in all_extensions:
            folder = os.path.dirname(path)
            long_name = os.path.basename(folder)
            if long_name in extensions:
                paths_to_add.append(folder)
                extensions.remove(long_name)
        # raise error if any extension wasn't found
        if extensions:
            raise CLIError('extension(s) not found: {}'.format(' '.join(extensions)))

    for path in paths_to_add:
        result = pip_cmd('install -e {}'.format(path), "Adding extension '{}'...".format(path))
        if result.error:
            raise result.error  # pylint: disable=raising-bad-type


def remove_extension(extensions):

    ext_paths = get_ext_repo_paths()
    installed_paths = find_files(ext_paths, '*.*-info')
    paths_to_remove = []
    names_to_remove = []
    if extensions == ['*']:
        paths_to_remove = [os.path.dirname(path) for path in installed_paths]
        names_to_remove = [os.path.basename(os.path.dirname(path)) for path in installed_paths]
    else:
        for path in installed_paths:
            folder = os.path.dirname(path)
            long_name = os.path.basename(folder)
            if long_name in extensions:
                paths_to_remove.append(folder)
                names_to_remove.append(long_name)
                extensions.remove(long_name)
        # raise error if any extension not installed
        if extensions:
            raise CLIError('extension(s) not installed: {}'.format(' '.join(extensions)))

    # removes any links that may have been added to site-packages.
    for ext in names_to_remove:
        pip_cmd('uninstall {} -y'.format(ext))

    for path in paths_to_remove:
        for d in os.listdir(path):
            # delete the egg-info and dist-info folders to make the extension invisible to the CLI and azdev
            if d.endswith('egg-info') or d.endswith('dist-info'):
                path_to_remove = os.path.join(path, d)
                display("Removing '{}'...".format(path_to_remove))
                shutil.rmtree(path_to_remove)


def _get_installed_dev_extensions(dev_sources):
    from glob import glob
    installed = []

    def _collect(path, depth=0, max_depth=3):
        if not os.path.isdir(path) or depth == max_depth or os.path.split(path)[-1].startswith('.'):
            return
        pattern = os.path.join(path, '*.egg-info')
        match = glob(pattern)
        if match:
            ext_path = os.path.dirname(match[0])
            ext_name = os.path.split(ext_path)[-1]
            installed.append({'name': ext_name, 'path': ext_path})
        else:
            for item in os.listdir(path):
                _collect(os.path.join(path, item), depth + 1, max_depth)
    for source in dev_sources:
        _collect(source)
    return installed


def list_extensions():
    from glob import glob

    azure_config = get_azure_config()
    dev_sources = azure_config.get('extension', 'dev_sources', None)
    dev_sources = dev_sources.split(',') if dev_sources else []

    installed = _get_installed_dev_extensions(dev_sources)
    installed_names = [x['name'] for x in installed]
    results = []

    for ext_path in find_files(dev_sources, 'setup.py'):
        # skip non-extension packages that may be in the extension folder (for example, from a virtual environment)
        try:
            glob_pattern = os.path.join(os.path.split(ext_path)[0], '{}*'.format(EXTENSION_PREFIX))
            _ = glob(glob_pattern)[0]
        except IndexError:
            continue

        # ignore anything in site-packages folder
        if 'site-packages' in ext_path:
            continue

        folder = os.path.dirname(ext_path)
        long_name = os.path.basename(folder)
        if long_name not in installed_names:
            results.append({'name': long_name, 'install': '', 'path': folder})
        else:
            results.append({'name': long_name, 'install': 'Installed', 'path': folder})

    return results


def _get_sha256sum(a_file):
    import hashlib
    sha256 = hashlib.sha256()
    with open(a_file, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def add_extension_repo(repos):

    from azdev.operations.setup import _check_repo
    az_config = get_azure_config()
    env_config = get_azdev_config()
    dev_sources = az_config.get('extension', 'dev_sources', None)
    dev_sources = dev_sources.split(',') if dev_sources else []
    for repo in repos:
        repo = os.path.abspath(repo)
        _check_repo(repo)
        if repo not in dev_sources:
            dev_sources.append(repo)
    az_config.set_value('extension', 'dev_sources', ','.join(dev_sources))
    env_config.set_value('ext', 'repo_paths', ','.join(dev_sources))

    return list_extension_repos()


def remove_extension_repo(repos):

    az_config = get_azure_config()
    env_config = get_azdev_config()
    dev_sources = az_config.get('extension', 'dev_sources', None)
    dev_sources = dev_sources.split(',') if dev_sources else []
    for repo in repos:
        try:
            dev_sources.remove(os.path.abspath(repo))
        except CLIError:
            logger.warning("Repo '%s' was not found in the list of repositories to search.", os.path.abspath(repo))
    az_config.set_value('extension', 'dev_sources', ','.join(dev_sources))
    env_config.set_value('ext', 'repo_paths', ','.join(dev_sources))
    return list_extension_repos()


def list_extension_repos():

    az_config = get_azure_config()
    dev_sources = az_config.get('extension', 'dev_sources', None)
    return dev_sources.split(',') if dev_sources else dev_sources


def update_extension_index(extensions):
    import re
    import tempfile

    from .util import get_ext_metadata, get_whl_from_url

    ext_repos = get_ext_repo_paths()
    index_path = next((x for x in find_files(ext_repos, 'index.json') if 'azure-cli-extensions' in x), None)
    if not index_path:
        raise CLIError("Unable to find 'index.json' in your extension repos. Have "
                       "you cloned 'azure-cli-extensions' and added it to you repo "
                       "sources with `azdev extension repo add`?")

    NAME_REGEX = r'.*/([^/]*)-\d+.\d+.\d+'

    for extension in extensions:
        # Get the URL
        extension = extension[extension.index('https'):]
        # Get extension WHL from URL
        if not extension.endswith('.whl') or not extension.startswith('https:'):
            raise CLIError('usage error: only URL to a WHL file currently supported.')

        # TODO: extend to consider other options
        ext_path = extension

        # Extract the extension name
        try:
            extension_name = re.findall(NAME_REGEX, ext_path)[0]
            extension_name = extension_name.replace('_', '-')
        except IndexError:
            raise CLIError('unable to parse extension name')

        # TODO: Update this!
        extensions_dir = tempfile.mkdtemp()
        ext_dir = tempfile.mkdtemp(dir=extensions_dir)
        whl_cache_dir = tempfile.mkdtemp()
        whl_cache = {}
        ext_file = get_whl_from_url(ext_path, extension_name, whl_cache_dir, whl_cache)

        with open(index_path, 'r') as infile:
            curr_index = json.loads(infile.read())

        entry = {
            'downloadUrl': ext_path,
            'sha256Digest': _get_sha256sum(ext_file),
            'filename': ext_path.split('/')[-1],
            'metadata': get_ext_metadata(ext_dir, ext_file, extension_name)
        }

        if extension_name not in curr_index['extensions'].keys():
            logger.info("Adding '%s' to index...", extension_name)
            curr_index['extensions'][extension_name] = [entry]
        else:
            logger.info("Updating '%s' in index...", extension_name)
            curr_index['extensions'][extension_name].append(entry)

        # update index and write back to file
        with open(os.path.join(index_path), 'w') as outfile:
            outfile.write(json.dumps(curr_index, indent=4, sort_keys=True))


def build_extensions(extensions, dist_dir='dist'):
    ext_paths = get_ext_repo_paths()
    all_extensions = find_files(ext_paths, 'setup.py')

    paths_to_build = []
    for path in all_extensions:
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        if long_name in extensions:
            paths_to_build.append(folder)
            extensions.remove(long_name)
    # raise error if any extension wasn't found
    if extensions:
        raise CLIError('extension(s) not found: {}'.format(' '.join(extensions)))

    original_cwd = os.getcwd()
    dist_dir = os.path.join(original_cwd, dist_dir)
    for path in paths_to_build:
        os.chdir(path)
        command = 'setup.py bdist_wheel -b bdist -d {}'.format(dist_dir)
        result = py_cmd(command, "Building extension '{}'...".format(path), is_module=False)
        if result.error:
            raise result.error  # pylint: disable=raising-bad-type
    os.chdir(original_cwd)


def publish_extensions(extensions, storage_account, storage_account_key, storage_container,
                       dist_dir='dist', update_index=False, yes=False):
    from azure.storage.blob import BlockBlobService

    heading('Publish Extensions')

    require_azure_cli()

    # rebuild the extensions
    subheading('Building WHLs')
    try:
        shutil.rmtree(dist_dir)
    except Exception as ex:  # pylint: disable=broad-except
        logger.debug("Unable to clear folder '%s'. Error: %s", dist_dir, ex)
    build_extensions(extensions, dist_dir=dist_dir)

    whl_files = find_files(dist_dir, '*.whl')
    uploaded_urls = []

    subheading('Uploading WHLs')
    for whl_path in whl_files:
        whl_file = os.path.split(whl_path)[-1]

        client = BlockBlobService(account_name=storage_account, account_key=storage_account_key)
        exists = client.exists(container_name=storage_container, blob_name=whl_file)

        # check if extension already exists unless user opted not to
        if not yes:
            if exists:
                if not prompt_y_n(
                        "{} already exists. You may need to bump the extension version. Replace?".format(whl_file),
                        default='n'):
                    logger.warning("Skipping '%s'...", whl_file)
                    continue
        # upload the WHL file
        client.create_blob_from_path(container_name=storage_container, blob_name=whl_file,
                                     file_path=os.path.abspath(whl_path))
        url = client.make_blob_url(container_name=storage_container, blob_name=whl_file)

        logger.info(url)
        uploaded_urls.append(url)

    if update_index:
        subheading('Updating Index')
        update_extension_index(uploaded_urls)

    subheading('Published WHLs')
    for url in uploaded_urls:
        display(url)

    if not update_index:
        logger.warning('You still need to update the index for your changes!')
        logger.warning('    az extension update-index <URL>')
