# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError

logger = get_logger(__name__)


def maps_account_create(client,
                        resource_group_name,
                        account_name,
                        name,
                        tags=None,
                        kind=None,
                        location=None,
                        disable_local_auth=None,
                        linked_resources=None,
                        type_=None,
                        user_assigned_identities=None,
                        force=None):
    terms = 'By creating an Azure Maps account, you agree that you have read and agree to the ' \
            '\nLicense (https://azure.microsoft.com/support/legal/) and ' \
            '\nPrivacy Statement (https://privacy.microsoft.com/privacystatement).' \
            '\nNote - Azure Maps shares customer-provided address/location queries (“Queries”) ' \
            'with third party TomTom for mapping functionality purposes.' \
            '\nQueries are not linked to any customer or end-user when shared with TomTom ' \
            'and cannot be used to identify individuals.' \
            '\nMicrosoft is currently in the process of adding TomTom to the Online Services Subcontractor List. ' \
            '\nNote that Weather Services integrates with AccuWeather and is currently in PREVIEW ' \
            '(see https://azure.microsoft.com/support/legal/preview-supplemental-terms/). '
    hint = 'Please select.'
    client_denied_terms = 'You must agree to the License and Privacy Statement to create an account.'

    # Show ToS message to the user
    logger.warning(terms)

    # Prompt yes/no for the user, if --force parameter is not passed in.
    if not force:
        option = prompt_y_n(hint)
        if not option:
            raise CLIError(client_denied_terms)
    if disable_local_auth is None:
        disable_local_auth = False
    maps_account = {}
    if tags is not None:
        maps_account['tags'] = tags
    maps_account['kind'] = kind or 'Gen2'
    maps_account['location'] = location or 'eastus'
    maps_account['properties'] = {}
    maps_account['properties']['disable_local_auth'] = False if disable_local_auth is None else disable_local_auth
    if linked_resources is not None:
        maps_account['properties']['linked_resources'] = linked_resources
    maps_account['identity'] = {}
    if type_ is not None:
        maps_account['identity']['type'] = type_
    if user_assigned_identities is not None:
        maps_account['identity']['user_assigned_identities'] = user_assigned_identities
    maps_account['sku'] = {}
    maps_account['sku']['name'] = name
    return client.create_or_update(resource_group_name=resource_group_name,
                                   account_name=account_name,
                                   maps_account=maps_account)


def list_accounts(client, resource_group_name=None):
    # Retrieve accounts via subscription
    if resource_group_name is None:
        return client.list_by_subscription()
    # Retrieve accounts via resource group
    return client.list_by_resource_group(resource_group_name)


def maps_account_show(client,
                      resource_group_name,
                      account_name):
    return client.get(resource_group_name=resource_group_name,
                      account_name=account_name)


def maps_account_update(client,
                        resource_group_name,
                        account_name,
                        tags=None,
                        kind=None,
                        disable_local_auth=None,
                        linked_resources=None,
                        type_=None,
                        user_assigned_identities=None,
                        name=None):
    maps_account_update_parameters = {}
    if tags is not None:
        maps_account_update_parameters['tags'] = tags
    if kind is not None:
        maps_account_update_parameters['kind'] = kind
    if disable_local_auth is not None:
        maps_account_update_parameters['disable_local_auth'] = disable_local_auth
    if linked_resources is not None:
        maps_account_update_parameters['linked_resources'] = linked_resources
    if type_ is not None or user_assigned_identities is not None:
        maps_account_update_parameters['identity'] = {}
    if type_ is not None:
        maps_account_update_parameters['identity']['type'] = type_
    if user_assigned_identities is not None:
        maps_account_update_parameters['identity']['user_assigned_identities'] = user_assigned_identities
    if name is not None:
        maps_account_update_parameters['sku'] = {'name': name}
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         maps_account_update_parameters=maps_account_update_parameters)


def maps_account_delete(client,
                        resource_group_name,
                        account_name):
    return client.delete(resource_group_name=resource_group_name,
                         account_name=account_name)


def maps_account_list_key(client,
                          resource_group_name,
                          account_name):
    return client.list_keys(resource_group_name=resource_group_name,
                            account_name=account_name)


def maps_account_regenerate_key(client,
                                resource_group_name,
                                account_name,
                                key_type):
    key_specification = {}
    key_specification['key_type'] = key_type
    return client.regenerate_keys(resource_group_name=resource_group_name,
                                  account_name=account_name,
                                  key_specification=key_specification)


def maps_map_list_operation(client):
    return client.list_operations()
