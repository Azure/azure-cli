# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              description=None, clear_key_configuration=False, open_restriction=False,
                              policy_option_name='Basic policy option'):
    from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                         ContentKeyPolicyOpenRestriction)
    default_configuration = None
    default_restriction = None

    if clear_key_configuration:
        default_configuration = ContentKeyPolicyClearKeyConfiguration()

    if open_restriction:
        default_restriction = ContentKeyPolicyOpenRestriction()

    options = [ContentKeyPolicyOption(name=policy_option_name,
                                      configuration=default_configuration,
                                      restriction=default_restriction)]

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, options, description)

def show_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              with_secrets=False):

    if with_secrets:
        return client.get_policy_properties_with_secrets(resource_group_name=resource_group_name, account_name=account_name,
                                                         content_key_policy_name=content_key_policy_name)
    else:
        return client.get(resource_group_name=resource_group_name, account_name=account_name,
                          content_key_policy_name=content_key_policy_name)