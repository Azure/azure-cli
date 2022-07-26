# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import os
import re
import shutil
import azure.mgmt.network

from azure.cli.core.profiles import AD_HOC_API_VERSIONS, AZURE_API_PROFILES, ResourceType


_LOGGER = logging.getLogger(__name__)


def remove_unused_network_api_versions():
    # Hard-coded API versions
    used_network_api_versions = set(AD_HOC_API_VERSIONS[ResourceType.MGMT_NETWORK].values())

    # API versions in profile
    for _, profile in AZURE_API_PROFILES.items():
        if ResourceType.MGMT_NETWORK in profile:
            used_network_api_versions.add(profile[ResourceType.MGMT_NETWORK])

    # Normalize API version: 2019-02-01 -> v2019_02_01
    used_network_api_vers = {f"v{api.replace('-','_')}" for api in used_network_api_versions}

    # Network SDK has a set of versions imported in models.py.
    # Let's keep them before we figure out how to remove a version in all related SDK files.
    path = azure.mgmt.network.__path__[0]
    model_file = os.path.join(path, 'models.py')
    with open(model_file, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.finditer(r'from \.(v[_\d\w]*)\.models import \*', content):
        used_network_api_vers.add(m.group(1))

    _LOGGER.info('Used network API versions:')
    _LOGGER.info(sorted(used_network_api_vers))

    all_api_vers = {d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d.startswith('v')}
    _LOGGER.info('All network API versions:')
    _LOGGER.info(sorted(all_api_vers))

    remove_api_vers = sorted(all_api_vers - used_network_api_vers)
    _LOGGER.info('Network API versions that will be removed:')
    _LOGGER.info(remove_api_vers)

    for ver in remove_api_vers:
        shutil.rmtree(os.path.join(path, ver))


def main():
    remove_unused_network_api_versions()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
