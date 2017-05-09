# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

## Install the command modules using pip ##
from __future__ import print_function
import os
import re
import tempfile
from subprocess import check_call
from azure.storage.blob import BlockBlobService, ContentSettings

PATH_TO_COMMAND_MODULES = '/azure-cli/src/command_modules'
PATH_TO_AZURE_CLI = '/azure-cli/src/azure-cli'
PATH_TO_AZURE_CLI_CORE = '/azure-cli/src/azure-cli-core'
PATH_TO_AZURE_CLI_NSPKG = '/azure-cli/src/azure-cli-nspkg'
PATH_TO_AZURE_CLI_COMMAND_MODS_NSPKG = '/azure-cli/src/azure-cli-command_modules-nspkg'
BLOB_SERVICE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER_NAME = 'packages'
PATTERN_PKG_NAME = re.compile(r"([a-z\-]*)-([0-9])")

assert BLOB_SERVICE_CONNECTION_STRING, 'Set AZURE_STORAGE_CONNECTION_STRING environment variable'

def get_all_command_modules():
    modules = []
    for mod_name in os.listdir(PATH_TO_COMMAND_MODULES):
        mod_path = os.path.join(PATH_TO_COMMAND_MODULES, mod_name)
        if os.path.isdir(mod_path):
            modules.append((mod_name, mod_path))
    return modules

def print_heading(heading, f=None):
    print('{0}\n{1}\n{0}'.format('=' * len(heading), heading), file=f)

def build_package(path_to_package, dist_dir):
    print_heading('Building {}'.format(path_to_package))
    check_call('python setup.py bdist_wheel -d {0} sdist -d {0}'.format(dist_dir).split(), cwd=path_to_package)
    print_heading('Built {}'.format(path_to_package))

UPLOADED_PACKAGE_LINKS = []

def upload_index_file(service, blob_name, title, links):
    service.create_blob_from_text(
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        text="<html><head><title>{0}</title></head><body><h1>{0}</h1>{1}</body></html>".format(title, '\n'.join(['<a href="{0}">{0}</a><br/>'.format(link) for link in links])),
        content_settings=ContentSettings(
            content_type='text/html',
            content_disposition=None,
            content_encoding=None,
            content_language=None,
            content_md5=None,
            cache_control=None
        )
    )

def gen_pkg_index_html(service, pkg_name):
    links = []
    index_file_name = pkg_name+'/'
    for blob in list(service.list_blobs(CONTAINER_NAME, prefix=index_file_name)):
        if blob.name == index_file_name:
            # Exclude the index file from being added to the list
            continue
        links.append(blob.name.replace(index_file_name, ''))
    upload_index_file(service, index_file_name, 'Links for {}'.format(pkg_name), links)
    UPLOADED_PACKAGE_LINKS.append(index_file_name)

def upload_package(service, file_path):
    print_heading('Uploading {}'.format(file_path))
    file_name = os.path.basename(file_path)
    norm_file_name = file_name.replace('_', '-') if file_name.endswith('.whl') else file_name
    pkg_name = re.match(PATTERN_PKG_NAME, norm_file_name).group(1)
    blob_name = '{}/{}'.format(pkg_name, file_name)
    service.create_blob_from_path(
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        file_path=file_path
    )
    gen_pkg_index_html(service, pkg_name)
    print_heading('Uploaded {}'.format(file_path))

all_command_modules = get_all_command_modules()

pkg_dir = tempfile.mkdtemp()

# Build the packages
build_package(PATH_TO_AZURE_CLI, pkg_dir)
build_package(PATH_TO_AZURE_CLI_CORE, pkg_dir)
build_package(PATH_TO_AZURE_CLI_NSPKG, pkg_dir)
build_package(PATH_TO_AZURE_CLI_COMMAND_MODS_NSPKG, pkg_dir)
for name, fullpath in all_command_modules:
    build_package(fullpath, pkg_dir)

# Upload packages as blobs
blob_service = BlockBlobService(connection_string=BLOB_SERVICE_CONNECTION_STRING)
for pkg in os.listdir(pkg_dir):
    upload_package(blob_service, os.path.join(pkg_dir, pkg))

# Upload the final index file
upload_index_file(blob_service, 'index.html', 'Simple Index', UPLOADED_PACKAGE_LINKS)

