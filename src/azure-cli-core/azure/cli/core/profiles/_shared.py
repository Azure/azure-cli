# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO Move this to a package shared by CLI and SDK
from enum import Enum
from functools import total_ordering
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


class CustomResourceType(object):  # pylint: disable=too-few-public-methods
    def __init__(self, import_prefix, client_name):
        self.import_prefix = import_prefix
        self.client_name = client_name


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
        self.profile = profile if profile is not None else {}
        self.profile[None] = default_api_version

    @property
    def default_api_version(self):
        return self.profile[None]


AZURE_API_PROFILES = {
    'latest': {
        ResourceType.MGMT_STORAGE: '2017-10-01',
        ResourceType.MGMT_NETWORK: '2018-02-01',
        ResourceType.MGMT_COMPUTE: SDKProfile('2017-12-01', {
            'resource_skus': '2017-09-01',
            'disks': '2018-04-01',
            'snapshots': '2018-04-01',
            'virtual_machine_run_commands': '2017-03-30'
        }),
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2017-06-01-preview',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2017-05-10',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01',
        ResourceType.DATA_STORAGE: '2017-07-29',
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


class _ApiVersions(object):  # pylint: disable=too-few-public-methods
    def __init__(self, client_type, sdk_profile, post_process):
        self._client_type = client_type
        self._sdk_profile = sdk_profile
        self._post_process = post_process
        self._operations_groups_value = None
        self._resolved = False

    def _resolve(self):
        if self._resolved:
            return

        self._operations_groups_value = {}
        for operation_group_name, operation_type in self._client_type.__dict__.items():
            if not isinstance(operation_type, property):
                continue

            value_to_save = self._sdk_profile.profile.get(
                operation_group_name,
                self._sdk_profile.default_api_version
            )
            self._operations_groups_value[operation_group_name] = self._post_process(value_to_save)
        self._resolved = True

    def __getattr__(self, item):
        try:
            self._resolve()
            return self._operations_groups_value[item]
        except KeyError:
            raise AttributeError('Attribute {} does not exist.'.format(item))


def _get_api_version_tuple(resource_type, sdk_profile, post_process=lambda x: x):
    """Return a _ApiVersion instance where key are operation group and value are api version."""
    return _ApiVersions(client_type=get_client_class(resource_type),
                        sdk_profile=sdk_profile,
                        post_process=post_process)


def get_api_version(api_profile, resource_type, as_sdk_profile=False):
    """Get the API version of a resource type given an API profile.

    :param api_profile: The name of the API profile.
    :type api_profile: str.
    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :returns:  str -- the API version.
    :raises: APIVersionException
    """
    try:
        api_version = AZURE_API_PROFILES[api_profile][resource_type]
        if as_sdk_profile:
            return api_version  # Could be SDKProfile or string
        if isinstance(api_version, SDKProfile):
            api_version = _get_api_version_tuple(resource_type, api_version)
        return api_version
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


def _validate_api_version(api_version_str, min_api=None, max_api=None):
    api_version = _DateAPIFormat(api_version_str)
    if min_api and api_version < _DateAPIFormat(min_api):
        return False
    if max_api and api_version > _DateAPIFormat(max_api):
        return False
    return True


def supported_api_version(api_profile, resource_type, min_api=None, max_api=None, operation_group=None):
    """
    Returns True if current API version for the resource type satisfies min/max range.
    To compare profile versions, set resource type to None.
    Can return a tuple<operation_group, bool> if the resource_type supports SDKProfile.
    note: Currently supports YYYY-MM-DD, YYYY-MM-DD-preview, YYYY-MM-DD-profile
    or YYYY-MM-DD-profile-preview  formatted strings.
    """
    if not isinstance(resource_type, (ResourceType, CustomResourceType)) and resource_type != PROFILE_TYPE:
        raise ValueError("'resource_type' is required.")
    if min_api is None and max_api is None:
        raise ValueError('At least a min or max version must be specified')
    api_version_obj = get_api_version(api_profile, resource_type, as_sdk_profile=True) \
        if isinstance(resource_type, (ResourceType, CustomResourceType)) else api_profile
    if isinstance(api_version_obj, SDKProfile):
        api_version_obj = api_version_obj.profile.get(operation_group or '', api_version_obj.default_api_version)
    return _validate_api_version(api_version_obj, min_api, max_api)


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
    api_version = get_api_version(api_profile, resource_type)
    if isinstance(api_version, _ApiVersions):
        if operation_group is None:
            raise ValueError("operation_group is required for resource type '{}'".format(resource_type))
        api_version = getattr(api_version, operation_group)
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
