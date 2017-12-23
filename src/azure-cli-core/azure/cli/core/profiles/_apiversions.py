# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from functools import total_ordering
from ._shared import SDKProfile, get_client_class, ResourceType


class ApiVersions(object):
    def __init__(self, api_version_data, resource_type=None):
        self._resource_type=resource_type
        self._sdk_profile = None
        self._op_groups = set()

        if isinstance(api_version_data, str):
            self._default_version = api_version_data

        elif isinstance(api_version_data, SDKProfile):
            if not resource_type:
                raise ValueError('The resource_type is missing.')
            self._sdk_profile = api_version_data
            self._default_version = self._sdk_profile.default_api_version
            self._op_groups = set(
                [op for op, t in get_client_class(resource_type).__dict__.items() if isinstance(t, property)])

        else:
            raise ValueError('The given api version data is neither a str or {}'.format(SDKProfile.__name__))

    def __str__(self):
        return self.get_version()

    def is_operation_group_required(self):
        return self._sdk_profile is not None

    def get_version(self, operation_group=None):
        if self.is_operation_group_required():
            if not operation_group:
                raise ValueError("operation group is required for resource type '{}'".format(self._resource_type))

            if operation_group not in self._op_groups:
                raise KeyError("operation group {} is not defined for resource type '{}'".format(operation_group, self._resource_type))

            return self._sdk_profile.profile.get(operation_group, self._default_version)
        else:
            return self._default_version

    def get_default_version(self):
        return self._default_version

    def get_sdk_profile(self):
        return self._sdk_profile

    def is_supported(self, min_api=None, max_api=None, operation_group=None):
        if not operation_group:
            api_version = _DateAPIFormat(self._default_version)
        else:
            if not self.is_operation_group_required():
                raise ValueError("operation group is not supported for resource type '{}'".format(self._resource_type))
            api_version = _DateAPIFormat(self.get_version(operation_group))

        if min_api and api_version < _DateAPIFormat(min_api):
            return False
        if max_api and api_version > _DateAPIFormat(max_api):
            return False
        return True


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