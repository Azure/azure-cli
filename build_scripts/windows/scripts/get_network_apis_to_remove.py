from azure.cli.core.profiles import AD_HOC_API_VERSIONS, AZURE_API_PROFILES, ResourceType

used_network_api_versions = set(AD_HOC_API_VERSIONS[ResourceType.MGMT_NETWORK].values())
for name, profile in AZURE_API_PROFILES:
    if ResourceType.MGMT_NETWORK in profile:
        used_network_api_versions.add(profile[ResourceType.MGMT_NETWORK])

print(used_network_api_versions)