# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from importlib import import_module

from azure.cli.core.profiles.shared import (AZURE_API_PROFILES,
                                            ResourceType,
                                            get_api_version as _sdk_get_api_version,
                                            get_versioned_models as _sdk_get_versioned_models)

# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': AZURE_API_PROFILES['latest'],
    '2016-sample': AZURE_API_PROFILES['2016-sample'],
    '2015-sample': AZURE_API_PROFILES['2015-sample']
}


def get_api_version(resource_type):
    from azure.cli.core._profile import CLOUD
    return _sdk_get_api_version(CLOUD.profile, resource_type)


def get_versioned_models(resource_type, *model_args, **kwargs):
    from azure.cli.core._profile import CLOUD
    return _sdk_get_versioned_models(CLOUD.profile, resource_type, *model_args, **kwargs)


def get_versioned_sdk_path(unversioned_path):
    """ Patch the unversioned sdk path to include the appropriate API version for the
        resource type in question.
        e.g. Converts azure.mgmt.storage.operations.storage_accounts_operations to
                      azure.mgmt.storage.v2016_12_01.operations.storage_accounts_operations
    """
    for rt in ResourceType:
        if unversioned_path.startswith(rt.import_prefix):
            return unversioned_path.replace(rt.import_prefix,
                                            rt.import_prefix + '.v' +
                                            get_api_version(rt).replace('-', '_'))
    return unversioned_path


def get_sdk_attr(mod_attr_path, checked=True):
    try:
        mod_attr_path = get_versioned_sdk_path(mod_attr_path)
        mod_to_import, attr_path = mod_attr_path.split('#')
        op = import_module(mod_to_import)
        for part in attr_path.split('.'):
            op = getattr(op, part)
        return op
    except (ImportError, AttributeError) as ex:
        if checked:
            return None
        raise ex
