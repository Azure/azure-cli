# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO Move this to a package shared by CLI and SDK
from functools import total_ordering
from importlib import import_module
from enum import Enum


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

    MGMT_STORAGE = ('azure.mgmt.storage',
                    'StorageManagementClient')
    MGMT_COMPUTE = ('azure.mgmt.compute.compute',
                    'ComputeManagementClient')
    MGMT_CONTAINER_SERVICE = ('azure.mgmt.compute.containerservice',
                              'ContainerServiceClient')
    MGMT_NETWORK = ('azure.mgmt.network',
                    'NetworkManagementClient')
    MGMT_RESOURCE_FEATURES = ('azure.mgmt.resource.features',
                              'FeatureClient')
    MGMT_RESOURCE_LINKS = ('azure.mgmt.resource.links',
                           'ManagementLinkClient')
    MGMT_RESOURCE_LOCKS = ('azure.mgmt.resource.locks',
                           'ManagementLockClient')
    MGMT_RESOURCE_POLICY = ('azure.mgmt.resource.policy',
                            'PolicyClient')
    MGMT_RESOURCE_RESOURCES = ('azure.mgmt.resource.resources',
                               'ResourceManagementClient')
    MGMT_RESOURCE_SUBSCRIPTIONS = ('azure.mgmt.resource.subscriptions',
                                   'SubscriptionClient')
    DATA_STORAGE = ('azure.multiapi.storage', None)

    def __init__(self, import_prefix, client_name):
        """Constructor.

        :param import_prefix: Path to the (unversioned) module.
        :type import_prefix: str.
        :param client_name: Name the client for this resource type.
        :type client_name: str.
        """
        self.import_prefix = import_prefix
        self.client_name = client_name


AZURE_API_PROFILES = {
    'latest': {
        ResourceType.MGMT_STORAGE: '2016-12-01',
        ResourceType.MGMT_NETWORK: '2017-03-01',
        ResourceType.MGMT_CONTAINER_SERVICE: '2017-01-31',
        ResourceType.MGMT_COMPUTE: '2016-04-30-preview',
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-04-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2017-05-10',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.DATA_STORAGE: '2016-05-31'
    },
    '2017-03-09-profile-preview': {
        ResourceType.MGMT_STORAGE: '2015-06-15',
        ResourceType.MGMT_NETWORK: '2015-06-15',
        ResourceType.MGMT_CONTAINER_SERVICE: '2017-01-31',
        ResourceType.MGMT_COMPUTE: '2015-06-15',
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2015-01-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-04-01',
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
    :returns:  str -- the API version.
    :raises: APIVersionException
    """
    try:
        return AZURE_API_PROFILES[api_profile][resource_type]
    except KeyError:
        raise APIVersionException(resource_type, api_profile)


@total_ordering  # pylint: disable=too-few-public-methods
class _DateAPIFormat(object):
    """ Class to support comparisons for API versions in
        YYYY-MM-DD, YYYY-MM-DD-preview, YYYY-MM-DD-profile, YYYY-MM-DD-profile-preview
        or any string that starts with YYYY-MM-DD format. A special case is made for 'latest'.
    """

    def __init__(self, api_version_str):
        try:
            self.latest = self.preview = False
            self.yyyy = self.mm = self.dd = None
            if api_version_str == 'latest':
                self.latest = True
            else:
                if 'preview' in api_version_str:
                    self.preview = True
                parts = api_version_str.split('-')
                self.yyyy = int(parts[0])
                self.mm = int(parts[1])
                self.dd = int(parts[2])
        except (ValueError, TypeError):
            raise ValueError('The API version {} is not in a '
                             'supported format'.format(api_version_str))

    def __eq__(self, other):
        return self.latest == other.latest and self.yyyy == other.yyyy and self.mm == other.mm and \
            self.dd == other.dd and self.preview == other.preview

    def __lt__(self, other):  # pylint: disable=too-many-return-statements
        if self.latest or other.latest:
            if not self.latest and other.latest:
                return True
            if self.latest and not other.latest:
                return False
            return False
        if self.yyyy < other.yyyy:
            return True
        if self.yyyy == other.yyyy:
            if self.mm < other.mm:
                return True
            if self.mm == other.mm:
                if self.dd < other.dd:
                    return True
                if self.dd == other.dd:
                    if self.preview and not other.preview:
                        return True
        return False


def supported_api_version(api_profile, resource_type, min_api=None, max_api=None):
    """
    Returns True if current API version for the resource type satisfies min/max range.
    To compare profile versions, set resource type to None.
    note: Currently supports YYYY-MM-DD, YYYY-MM-DD-preview, YYYY-MM-DD-profile
    or YYYY-MM-DD-profile-preview  formatted strings.
    """
    if not isinstance(resource_type, ResourceType) and resource_type != PROFILE_TYPE:
        raise TypeError()
    if min_api is None and max_api is None:
        raise ValueError('At least a min or max version must be specified')
    api_version_str = get_api_version(api_profile, resource_type) \
        if isinstance(resource_type, ResourceType) else api_profile
    api_version = _DateAPIFormat(api_version_str)
    if min_api and api_version < _DateAPIFormat(min_api):
        return False
    if max_api and api_version > _DateAPIFormat(max_api):
        return False
    return True


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


def get_versioned_sdk_path(api_profile, resource_type):
    """ Patch the unversioned sdk path to include the appropriate API version for the
        resource type in question.
        e.g. Converts azure.mgmt.storage.operations.storage_accounts_operations to
                      azure.mgmt.storage.v2016_12_01.operations.storage_accounts_operations
    """
    return '{}.v{}'.format(
        resource_type.import_prefix,
        get_api_version(api_profile, resource_type).replace('-', '_')
    )


def get_versioned_sdk(api_profile, resource_type, *attr_args, **kwargs):
    checked = kwargs.get('checked', True)
    sub_mod_prefix = kwargs.get('mod', None)
    sdk_path = get_versioned_sdk_path(api_profile, resource_type)
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
