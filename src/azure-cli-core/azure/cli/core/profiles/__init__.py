# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#  pylint: disable=unused-import
from azure.cli.core.profiles._shared import (AZURE_API_PROFILES,
                                             ResourceType,
                                             PROFILE_TYPE,
                                             get_api_version as _sdk_get_api_version,
                                             supported_api_version as _sdk_supported_api_version,
                                             get_versioned_sdk as _sdk_get_versioned_sdk)

# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': AZURE_API_PROFILES['latest'],
    '2017-03-09-profile-preview': AZURE_API_PROFILES['2017-03-09-profile-preview']
}


def get_api_version(resource_type):
    """ Get the current API version for a given resource_type.

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :returns:  str -- The API version.
    """
    from azure.cli.core._profile import CLOUD
    return _sdk_get_api_version(CLOUD.profile, resource_type)


def supported_api_version(resource_type, min_api=None, max_api=None):
    """ Method to check if the current API version for a given resource_type is supported.
        If resource_type is set to None, the current profile version will be used as the basis of
        the comparison.

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :param min_api: The minimum API that is supported (inclusive). Omit for no minimum constraint.
    "type min_api: str
    :param max_api: The maximum API that is supported (inclusive). Omit for no maximum constraint.
    "type max_api: str
    :returns:  bool -- True if the current API version of resource_type satisfies the
                       min/max constraints. False otherwise.
    """
    from azure.cli.core._profile import CLOUD
    return _sdk_supported_api_version(CLOUD.profile, resource_type, min_api, max_api)


def get_sdk(resource_type, *attr_args, **kwargs):
    """ Get any SDK object that's versioned using the current API version for resource_type.
        Supported keyword arguments:
            checked - A boolean specifying if this method should suppress/check import exceptions
                      or not. By default, None is returned.
            mod - A string specifying the submodule that all attr_args should be prefixed with.

        Example usage:
            Get a single SDK model.
            TableService = get_sdk(resource_type, 'table#TableService')

            File, Directory = get_sdk(resource_type,
                                      'file.models#File',
                                      'file.models#Directory')

            Same as above but get multiple models where File and Directory are both part of
            'file.models' and we don't want to specify each full path.
            File, Directory = get_sdk(resource_type,
                                      'File',
                                      'Directory',
                                      mod='file.models')

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :param attr_args: Positional arguments for paths to objects to get.
    :type attr_args: str
    :param kwargs: Keyword arguments.
    :type kwargs: str
    :returns: object -- e.g. an SDK module, model, enum, attribute. The number of objects returned
                        depends on len(attr_args).
    """
    from azure.cli.core._profile import CLOUD
    return _sdk_get_versioned_sdk(CLOUD.profile, resource_type, *attr_args, **kwargs)
