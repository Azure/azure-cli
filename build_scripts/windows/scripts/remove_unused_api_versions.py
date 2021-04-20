import logging
import os
import shutil
import azure.mgmt.network

from azure.cli.core.profiles import AD_HOC_API_VERSIONS, AZURE_API_PROFILES, ResourceType


_LOGGER = logging.getLogger(__name__)


def remove_unused_network_api_versions():
    used_network_api_versions = set(AD_HOC_API_VERSIONS[ResourceType.MGMT_NETWORK].values())
    for _, profile in AZURE_API_PROFILES.items():
        if ResourceType.MGMT_NETWORK in profile:
            used_network_api_versions.add(profile[ResourceType.MGMT_NETWORK])

    used_network_api_vers = {f"v{api.replace('-','_')}" for api in used_network_api_versions}
    _LOGGER.info('Used network API versions:')
    _LOGGER.info(sorted(used_network_api_vers))

    path = azure.mgmt.network.__path__[0]
    all_api_vers = {d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d.startswith('v')}
    _LOGGER.info('All network API versions:')
    _LOGGER.info(sorted(all_api_vers))

    remove_api_vers = sorted(all_api_vers - used_network_api_vers)
    _LOGGER.info('Network API versions that can be removed:')
    _LOGGER.info(remove_api_vers)

    for ver in remove_api_vers:
        shutil.rmtree(os.path.join(path, ver))


def main():
    remove_unused_network_api_versions()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
