# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO Move this to a package shared by CLI and SDK
from enum import Enum
from importlib import import_module


class APIVersionException(Exception):
    def __init__(self, type_name, api_profile):
        super(APIVersionException, self).__init__(type_name, api_profile)
        self.type_name = type_name
        self.api_profile = api_profile

    def __str__(self):
        return "Unable to get API version for type '{}' in profile '{}'".format(
            self.type_name, self.api_profile)


# Sentinel value for profile
PROFILE_TYPE = object()


class ResourceType(Enum):  # pylint: disable=too-few-public-methods

    MGMT_STORAGE = ('azure.mgmt.storage', 'StorageManagementClient')
    MGMT_COMPUTE = ('azure.mgmt.compute', 'ComputeManagementClient')
    MGMT_NETWORK = ('azure.mgmt.network', 'NetworkManagementClient')
    MGMT_RESOURCE_FEATURES = ('azure.mgmt.resource.features', 'FeatureClient')
    MGMT_RESOURCE_LINKS = ('azure.mgmt.resource.links', 'ManagementLinkClient')
    MGMT_RESOURCE_LOCKS = ('azure.mgmt.resource.locks', 'ManagementLockClient')
    MGMT_RESOURCE_POLICY = ('azure.mgmt.resource.policy', 'PolicyClient')
    MGMT_RESOURCE_RESOURCES = ('azure.mgmt.resource.resources', 'ResourceManagementClient')
    MGMT_RESOURCE_SUBSCRIPTIONS = ('azure.mgmt.resource.subscriptions', 'SubscriptionClient')
    DATA_STORAGE = ('azure.multiapi.storage', None)
    DATA_COSMOS_TABLE = ('azure.multiapi.cosmosdb', None)

    def __init__(self, import_prefix, client_name):
        """Constructor.

        :param import_prefix: Path to the (unversioned) module.
        :type import_prefix: str.
        :param client_name: Name the client for this resource type.
        :type client_name: str.
        """
        self.import_prefix = import_prefix
        self.client_name = client_name


class SDKProfile(object):  # pylint: disable=too-few-public-methods

    def __init__(self, default_api_version, profile=None):
        """Constructor.

        :param str default_api_version: Default API version if not overriden by a profile. Nullable.
        :param profile: A dict operation group name to API version.
        :type profile: dict[str, str]
        """
        self.default_api_version = default_api_version
        self.profile = profile if profile is not None else {}


AZURE_API_PROFILES = {
    'latest': {
        ResourceType.MGMT_STORAGE: '2017-10-01',
        ResourceType.MGMT_NETWORK: '2017-11-01',
        ResourceType.MGMT_COMPUTE: SDKProfile('2017-12-01', {
            'resource_skus': '2017-09-01',
            'disks': '2017-03-30',
            'snapshots': '2017-03-30',
            'virtual_machine_run_commands': '2017-03-30'
        }),
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2017-06-01-preview',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2017-05-10',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.DATA_STORAGE: '2017-04-17',
        ResourceType.DATA_COSMOS_TABLE: '2017-04-17'
    },
    '2017-03-09-profile': {
        ResourceType.MGMT_STORAGE: '2016-01-01',
        ResourceType.MGMT_NETWORK: '2015-06-15',
        ResourceType.MGMT_COMPUTE: SDKProfile('2016-03-30'),
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2015-01-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2015-10-01-preview',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2016-02-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.DATA_STORAGE: '2015-04-05'
    }
}


def get_api_version(api_profile, resource_type):
    """Get the API version of a resource type given an API profile.

    :param api_profile: The name of the API profile.
    :type api_profile: str.
    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :returns: A structure represents the api version of specific resource type. The structure can be
              converted to an API version string. When the api version data is of type SDKProfile, the
              structure will support api version for specific operation groups.
    :rtype: ApiVersions
    :raises: APIVersionException
    """
    try:
        from ._apiversions import ApiVersions
        return ApiVersions(api_version_data=AZURE_API_PROFILES[api_profile][resource_type],
                           resource_type=resource_type)
    except KeyError:
        raise APIVersionException(resource_type, api_profile)


def supported_api_version(api_profile, resource_type, min_api=None, max_api=None, operation_group=None):
    """
    Returns True if current API version for the resource type satisfies min/max range.
    To compare profile versions, set resource type to None.
    Can return a tuple<operation_group, bool> if the resource_type supports SDKProfile.
    note: Currently supports YYYY-MM-DD, YYYY-MM-DD-preview, YYYY-MM-DD-profile
    or YYYY-MM-DD-profile-preview  formatted strings.
    """
    if not isinstance(resource_type, ResourceType) and resource_type != PROFILE_TYPE:
        raise TypeError()
    if min_api is None and max_api is None:
        raise ValueError('At least a min or max version must be specified')

    if isinstance(resource_type, ResourceType):
        api_versions = get_api_version(api_profile, resource_type)
    else:
        from ._apiversions import ApiVersions
        api_versions = ApiVersions(api_profile)

    return api_versions.is_supported(min_api=min_api, max_api=max_api, operation_group=operation_group)


def _get_attr(sdk_path, mod_attr_path, checked=True):
    try:
        attr_mod, attr_path = mod_attr_path.split('#') \
            if '#' in mod_attr_path else (mod_attr_path, '')
        full_mod_path = '{}.{}'.format(sdk_path, attr_mod) if attr_mod else sdk_path
        op = import_module(full_mod_path)
        if attr_path:
            # Only load attributes if needed
            for part in attr_path.split('.'):
                op = getattr(op, part)
        return op
    except (ImportError, AttributeError) as ex:
        if checked:
            return None
        raise ex


def get_client_class(resource_type):
    return _get_attr(resource_type.import_prefix, '#' + resource_type.client_name)


def get_versioned_sdk_path(api_profile, resource_type, operation_group=None):
    """ Patch the unversioned sdk path to include the appropriate API version for the
        resource type in question.
        e.g. Converts azure.mgmt.storage.operations.storage_accounts_operations to
                      azure.mgmt.storage.v2016_12_01.operations.storage_accounts_operations
    """
    api_version = get_api_version(api_profile, resource_type).get_version(operation_group)
    return '{}.v{}'.format(resource_type.import_prefix, api_version.replace('-', '_'))


def get_versioned_sdk(api_profile, resource_type, *attr_args, **kwargs):
    checked = kwargs.get('checked', True)
    sub_mod_prefix = kwargs.get('mod', None)
    operation_group = kwargs.get('operation_group', None)
    sdk_path = get_versioned_sdk_path(api_profile, resource_type, operation_group)
    if not attr_args:
        # No attributes to load. Return the versioned sdk
        return import_module(sdk_path)
    results = []
    for mod_attr_path in attr_args:
        if sub_mod_prefix and '#' not in mod_attr_path:
            mod_attr_path = '{}#{}'.format(sub_mod_prefix, mod_attr_path)
        loaded_obj = _get_attr(sdk_path, mod_attr_path, checked)
        results.append(loaded_obj)
    return results[0] if len(results) == 1 else results
