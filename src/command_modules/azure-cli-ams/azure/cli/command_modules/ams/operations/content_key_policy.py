# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_content_key_policy(client, resource_group_name, account_name,
                              content_key_policy_name, description=None):
    from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                         ContentKeyPolicyOpenRestriction)

    options = [ContentKeyPolicyOption(name='test',
                                      configuration=ContentKeyPolicyClearKeyConfiguration(),
                                      restriction=ContentKeyPolicyOpenRestriction())]

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, options, description)
