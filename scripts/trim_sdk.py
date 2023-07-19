# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This script trims Python SDKs by
- Removing aio folders
- Removing unused API versions
"""

import glob
import importlib
import logging
import os
import re
import shutil

import azure.mgmt

from azure.cli.core.profiles import AD_HOC_API_VERSIONS, AZURE_API_PROFILES, ResourceType

_LOGGER = logging.getLogger(__name__)

DRY_RUN = False  # Change to True to dry run


def _rmtree(path):
    _LOGGER.warning(path)
    if not DRY_RUN:
        shutil.rmtree(path)


def calculate_folder_size(start_path):
    """Calculate total size of a folder and file count."""
    # https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python
    total_size = 0
    total_count = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_count += 1
                total_size += os.path.getsize(fp)

    return total_size, total_count


def remove_aio_folders():
    _LOGGER.info("Removing aio folders:")
    mgmt_sdk_dir = azure.mgmt.__path__[0]
    for aio_folder in glob.glob(os.path.join(mgmt_sdk_dir, '**/aio'), recursive=True):
        _rmtree(aio_folder)


def remove_unused_api_versions(resource_type):
    _LOGGER.info(f"Removing unused api folders for {resource_type.import_prefix}:")
    try:
        sdk_path = importlib.import_module(resource_type.import_prefix).__path__[0]
    except ImportError:
        _LOGGER.info(f'{resource_type} is not installed, skip')
        return

    used_api_versions = set()

    # Hard-coded API versions
    if resource_type in AD_HOC_API_VERSIONS:
        ad_hoc_api_versions = set(AD_HOC_API_VERSIONS[resource_type].values())
        used_api_versions.update(ad_hoc_api_versions)

    # API versions in profile
    for profile in AZURE_API_PROFILES.values():
        if resource_type in profile:
            # value is str like '2022-01-01' or SDKProfile
            value = profile[resource_type]
            if value is None:
                _LOGGER.info(f'{resource_type}\'s API version is None, skip')
                return
            if isinstance(value, str):
                used_api_versions.add(value)
            else:
                # SDKProfile
                # default_api_version is in value.profile[None]
                used_api_versions.update(value.profile.values())

    # Convert API version to its folder format: 2019-02-01 -> v2019_02_01
    used_api_folders = {f"v{api.replace('-','_')}" for api in used_api_versions}

    # SDK has a set of versions imported in models.py to form all latest models
    model_file = os.path.join(sdk_path, 'models.py')
    if os.path.exists(model_file):
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(r'from \.(v[_\d\w]*)\.models import \*', content):
            used_api_folders.add(m.group(1))

    _LOGGER.info(f'Used API folders: {sorted(used_api_folders)}')

    all_api_folders = {d for d in os.listdir(sdk_path) if os.path.isdir(os.path.join(sdk_path, d)) and d.startswith('v')}
    _LOGGER.info(f'All API folders: {sorted(all_api_folders)}')

    remove_api_folders = sorted(all_api_folders - used_api_folders)
    _LOGGER.info(f'API folders to remove: {remove_api_folders}')

    for api_folder in remove_api_folders:
        full_path = os.path.join(sdk_path, api_folder)
        _rmtree(full_path)


def _print_folder_size(folder):
    size, count = calculate_folder_size(folder)
    size_in_mb = size / 1048576  # 1 MB = 1024 * 1024 B = 1048576 B
    _LOGGER.info(f"{size_in_mb:.2f} MB, {count} files")


def _get_all_sdks_to_trim():
    resource_types = [k for k, v in AZURE_API_PROFILES['latest'].items() if k.import_prefix.startswith('azure.mgmt')]
    return resource_types


def main():
    mgmt_sdk_dir = azure.mgmt.__path__[0]

    # Remove aio folders
    _print_folder_size(mgmt_sdk_dir)
    remove_aio_folders()

    _print_folder_size(mgmt_sdk_dir)

    # Removed unused API versions
    resource_types = _get_all_sdks_to_trim()

    for r in resource_types:
        remove_unused_api_versions(r)

    _print_folder_size(mgmt_sdk_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
