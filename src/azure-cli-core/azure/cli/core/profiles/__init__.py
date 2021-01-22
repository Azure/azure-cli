# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#  pylint: disable=unused-import
from azure.cli.core.profiles._shared import AZURE_API_PROFILES, ResourceType, CustomResourceType, PROFILE_TYPE,\
    SDKProfile


def get_api_version(cli_ctx, resource_type, as_sdk_profile=False):
    """ Get the current API version for a given resource_type.

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :param bool as_sdk_profile: Return SDKProfile instance.
    :returns: The API version
     Can return a tuple<operation_group, str> if the resource_type supports SDKProfile.
    :rtype: str or tuple[str]
    """
    from azure.cli.core.profiles._shared import get_api_version as _sdk_get_api_version
    return _sdk_get_api_version(cli_ctx.cloud.profile, resource_type, as_sdk_profile)


def supported_api_version(cli_ctx, resource_type, min_api=None, max_api=None, operation_group=None):
    """ Method to check if the current API version for a given resource_type is supported.
        If resource_type is set to None, the current profile version will be used as the basis of
        the comparison.

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :param min_api: The minimum API that is supported (inclusive). Omit for no minimum constraint.
    "type min_api: str
    :param max_api: The maximum API that is supported (inclusive). Omit for no maximum constraint.
    :type max_api: str
    :returns: True if the current API version of resource_type satisfies the min/max constraints. False otherwise.
     Can return a tuple<operation_group, bool> if the resource_type supports SDKProfile.
    :rtype: bool or tuple[bool]
    """
    from azure.cli.core.profiles._shared import supported_api_version as _sdk_supported_api_version
    return _sdk_supported_api_version(cli_ctx.cloud.profile,
                                      resource_type=resource_type,
                                      min_api=min_api,
                                      max_api=max_api,
                                      operation_group=operation_group)


def supported_resource_type(cli_ctx, resource_type):
    from azure.cli.core.profiles._shared import supported_resource_type as _supported_resource_type
    return _supported_resource_type(cli_ctx.cloud.profile,
                                    resource_type=resource_type)


def get_sdk(cli_ctx, resource_type, *attr_args, **kwargs):
    """ Get any SDK object that's versioned using the current API version for resource_type.
        Supported keyword arguments:
            checked - A boolean specifying if this method should suppress/check import exceptions
                        or not. By default, None is returned.
            mod - A string specifying the submodule that all attr_args should be prefixed with.
            operation_group - A string specifying the operation group name we want models.

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
            VirtualMachine = get_sdk(resource_type,
                                     'VirtualMachine',
                                     mod='models',
                                     operation_group='virtual_machines')

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :param attr_args: Positional arguments for paths to objects to get.
    :type attr_args: str
    :param kwargs: Keyword arguments.
    :type kwargs: str
    :returns: object -- e.g. an SDK module, model, enum, attribute. The number of objects returned
                        depends on len(attr_args).
    """
    from azure.cli.core.profiles._shared import get_versioned_sdk as _sdk_get_versioned_sdk
    return _sdk_get_versioned_sdk(cli_ctx.cloud.profile, resource_type, *attr_args, **kwargs)


# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': AZURE_API_PROFILES['latest'],
    '2017-03-09-profile': AZURE_API_PROFILES['2017-03-09-profile'],
    '2018-03-01-hybrid': AZURE_API_PROFILES['2018-03-01-hybrid'],
    '2019-03-01-hybrid': AZURE_API_PROFILES['2019-03-01-hybrid'],
    '2020-09-01-hybrid': AZURE_API_PROFILES['2020-09-01-hybrid']
}


def register_resource_type(profile_name, resource_type, api_version):
    err_msg = "Failed to add resource type to profile '{p}': "
    if not isinstance(resource_type, CustomResourceType):
        raise TypeError((err_msg + "resource_type should be of type {c}, got {r}.").format(p=profile_name,
                                                                                           c=CustomResourceType,
                                                                                           r=type(resource_type)))
    try:
        API_PROFILES[profile_name].update({resource_type: api_version})
    except KeyError:
        raise ValueError((err_msg + "Profile '{p}' not found.").format(p=profile_name))
