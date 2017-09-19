#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import argparse
import glob
import mimetypes
import logging
import re

from azure.storage.blob import BlockBlobService, ContentSettings


logger = logging.getLogger('az-publish')

def publish(build, account, container, sas, **_) -> None:
    client = BlockBlobService(account_name=account, sas_token=sas)
    
    publishing_files = (p for p in glob.iglob(os.path.join(build , '**/*'), recursive=True))
    for source in publishing_files:
        if os.path.isdir(source):
            continue

        blob_path = os.path.join(os.environ['TRAVIS_REPO_SLUG'],
                                 os.environ['TRAVIS_BRANCH'],
                                 os.environ['TRAVIS_BUILD_NUMBER'],
                                 os.path.relpath(source, build))

        content_type, content_encoding = mimetypes.guess_type(os.path.basename(source))
        content_settings = ContentSettings(content_type, content_encoding)
        logger.info(f'Uploading {blob_path} ...')
        client.create_blob_from_path(container_name=container,
                                     blob_name=blob_path,
                                     file_path=source,
                                     content_settings=content_settings)


def generate_package_list_in_html(title: str, links: list):
    package_list = '\n'.join((f'    <a href="{p}">{p}</a><br />' for p in links))
    return f"""<html>
<head>
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    {package_list}
</body>
</html>"""


def nightly(build: str, account: str, container: str, sas: str, **_) -> None:
    client = BlockBlobService(account_name=account, sas_token=sas)

    modules_list = []
    for wheel_file in glob.iglob(os.path.join(build, 'build/*.whl')):
        package_name = os.path.basename(wheel_file).split('-', maxsplit=1)[0].replace('_', '-')
        sdist_file = next(glob.iglob(os.path.join(build, 'source', f'{package_name}*.tar.gz')))

        content_type, content_encoding = mimetypes.guess_type(os.path.basename(wheel_file))
        content_settings = ContentSettings(content_type, content_encoding)
        client.create_blob_from_path(container_name=container,
                                     blob_name=f'{package_name}/{os.path.basename(wheel_file)}',
                                     file_path=wheel_file,
                                     content_settings=content_settings)

        content_type, content_encoding = mimetypes.guess_type(os.path.basename(sdist_file))
        content_settings = ContentSettings(content_type, content_encoding)
        client.create_blob_from_path(container_name=container,
                                     blob_name=f'{package_name}/{os.path.basename(sdist_file)}',
                                     file_path=sdist_file,
                                     content_settings=content_settings)

        package_blobs = (os.path.basename(b.name) for b in client.list_blobs(container, prefix=package_name + '/') 
                                                  if b.name != f"{package_name}/")

        client.create_blob_from_text(container_name=container, 
                                     blob_name=f'{package_name}/',
                                     text=generate_package_list_in_html(f'Links for {package_name}', package_blobs),
                                     content_settings=ContentSettings('text/html'))
        
        modules_list.append(f"{package_name}/")
    
    client.create_blob_from_text(container_name=container, 
                                 blob_name='index.html',
                                 text=generate_package_list_in_html('Simple Index', modules_list),
                                 content_settings=ContentSettings('text/html'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='az-publish')
    subparsers = parser.add_subparsers(title='Actions')

    store_parser = subparsers.add_parser('store', help='Publish the build artifacts to a long-term storage.')
    store_parser.set_defaults(func=publish)
    store_parser.add_argument('-b', dest='build', help='The folder where the artifacts are saved.')
    store_parser.add_argument('-a', dest='account', help='The storage account name.')
    store_parser.add_argument('-c', dest='container', help='The storage account container.')
    store_parser.add_argument('-s', dest='sas', help='The storage account access token.')


    nightly_parser = subparsers.add_parser('nightly', help='Publish the build artifacts to a nightly build storage.')
    nightly_parser.set_defaults(func=nightly)
    nightly_parser.add_argument('-b', dest='build', help='The folder where the artifacts are saved.')
    nightly_parser.add_argument('-a', dest='account', help='The storage account name.')
    nightly_parser.add_argument('-c', dest='container', help='The storage account container.')
    nightly_parser.add_argument('-s', dest='sas', help='The storage account access token.')


    args = parser.parse_args()
    args.func(**vars(args))

