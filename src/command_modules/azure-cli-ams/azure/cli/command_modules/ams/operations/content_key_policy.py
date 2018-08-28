# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              description=None, clear_key_configuration=False, open_restriction=False):
    from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                         ContentKeyPolicyOpenRestriction)
    default_configuration = None
    default_restriction = None

    if clear_key_configuration:
        default_configuration = ContentKeyPolicyClearKeyConfiguration()

    if open_restriction:
        default_restriction = ContentKeyPolicyOpenRestriction()

    options = [ContentKeyPolicyOption(name='Basic policy option',
                                      configuration=default_configuration,
                                      restriction=default_restriction)]

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, options, description)
