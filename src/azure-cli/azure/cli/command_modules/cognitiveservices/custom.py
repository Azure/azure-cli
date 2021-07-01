# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from knack.prompting import prompt_y_n
from knack.util import CLIError
from knack.log import get_logger

from azure.mgmt.cognitiveservices.models import Account as CognitiveServicesAccount, Sku,\
    VirtualNetworkRule, IpRule, NetworkRuleSet, NetworkRuleAction,\
    AccountProperties as CognitiveServicesAccountProperties, ApiProperties as CognitiveServicesAccountApiProperties,\
    Identity, ResourceIdentityType as IdentityType
from azure.cli.command_modules.cognitiveservices._client_factory import cf_accounts, cf_resource_skus

logger = get_logger(__name__)


def list_resources(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def recover(client, location, resource_group_name, account_name):
    properties = CognitiveServicesAccountProperties()
    properties.restore = True
    params = CognitiveServicesAccount(properties=properties)
    params.location = location

    return client.begin_create(resource_group_name, account_name, params)


def list_usages(client, resource_group_name, account_name):
    """
    List usages for Azure Cognitive Services account.
    """
    return client.list_usages(resource_group_name, account_name).value


def list_kinds(client):
    """
    List all valid kinds for Azure Cognitive Services account.

    :param client: the ResourceSkusOperations
    :return: a list
    """
    # The client should be ResourceSkusOperations, and list() should return a list of SKUs for all regions.
    # The sku will have "kind" and we use that to extract full list of kinds.
    kinds = {x.kind for x in client.list()}
    return sorted(list(kinds))


def list_skus(cmd, kind=None, location=None, resource_group_name=None, account_name=None):
    if resource_group_name is not None or account_name is not None:
        logger.warning(
            'list-skus with an existing account has been deprecated and will be removed in a future release.')
        if resource_group_name is None:
            # account_name must not be None
            raise CLIError('--resource-group is required when --name is specified.')
        # keep the original behavior to avoid breaking changes
        return cf_accounts(cmd.cli_ctx).list_skus(resource_group_name, account_name)

    # in other cases, use kind and location to filter SKUs
    def _filter_sku(_sku):
        if kind is not None:
            if _sku.kind != kind:
                return False
        if location is not None:
            if location.lower() not in [x.lower() for x in _sku.locations]:
                return False
        return True

    return [x for x in cf_resource_skus(cmd.cli_ctx).list() if _filter_sku(x)]


def create(
        client, resource_group_name, account_name, sku_name, kind, location, custom_domain=None,
        tags=None, api_properties=None, assign_identity=False, storage=None, encryption=None, yes=None):

    terms = 'Notice\nMicrosoft will use data you send to Bing Search Services'\
        ' to improve Microsoft products and services.'\
        'Where you send personal data to these Cognitive Services, you are responsible '\
        'for obtaining sufficient consent from the data subjects.'\
        'The General Privacy and Security Terms in the Online Services Terms '\
        'do not apply to these Cognitive Services.'\
        'Please refer to the Microsoft Cognitive Services section in the Online '\
        'Services Terms'\
        ' (https://www.microsoft.com/Licensing/product-licensing/products.aspx)'\
        ' for details.'\
        'Microsoft offers policy controls that may be used to disable new Cognitive'\
        ' Services deployments (https://docs.microsoft.com/azure/cognitive-servic'\
        'es/cognitive-services-apis-create-account).'
    terms_not_police = 'Notice\n' \
                       'I certify that use of this service is not by or for a police department in the United States.'
    hint = 'Please select'
    import re
    pattern = re.compile("^[Bb]ing\\..*$")
    if pattern.match(kind):
        if yes:
            logger.warning(terms)
        else:
            logger.warning(terms)
            option = prompt_y_n(hint)
            if not option:
                raise CLIError('Operation cancelled.')
    if kind.lower() == 'face' or kind.lower() == 'cognitiveservices':
        if yes:
            logger.warning(terms_not_police)
        else:
            logger.warning(terms_not_police)
            option = prompt_y_n(hint)
            if not option:
                raise CLIError('Operation cancelled.')

    sku = Sku(name=sku_name)

    properties = CognitiveServicesAccountProperties()
    if api_properties is not None:
        api_properties = CognitiveServicesAccountApiProperties.deserialize(api_properties)
        properties.api_properties = api_properties
    if custom_domain:
        properties.custom_sub_domain_name = custom_domain
    params = CognitiveServicesAccount(sku=sku, kind=kind, location=location,
                                      properties=properties, tags=tags)
    if assign_identity:
        params.identity = Identity(type=IdentityType.system_assigned)

    if storage is not None:
        params.properties.user_owned_storage = json.loads(storage)

    if encryption is not None:
        params.properties.encryption = json.loads(encryption)

    return client.begin_create(resource_group_name, account_name, params)


def update(client, resource_group_name, account_name, sku_name=None, custom_domain=None,
           tags=None, api_properties=None, storage=None, encryption=None):

    if sku_name is None:
        sa = client.get(resource_group_name, account_name)
        sku_name = sa.sku.name

    sku = Sku(name=sku_name)

    properties = CognitiveServicesAccountProperties()
    if api_properties is not None:
        api_properties = CognitiveServicesAccountApiProperties.deserialize(api_properties)
        properties.api_properties = api_properties
    if custom_domain:
        properties.custom_sub_domain_name = custom_domain
    params = CognitiveServicesAccount(sku=sku, properties=properties, tags=tags)

    if storage is not None:
        params.properties.user_owned_storage = json.loads(storage)

    if encryption is not None:
        params.properties.encryption = json.loads(encryption)

    return client.begin_update(resource_group_name, account_name, params)


def default_network_acls():
    rules = NetworkRuleSet()
    rules.default_action = NetworkRuleAction.deny
    rules.ip_rules = []
    rules.virtual_network_rules = []
    return rules


def list_network_rules(client, resource_group_name, account_name):
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        rules = default_network_acls()
    return rules


def add_network_rule(client, resource_group_name, account_name, subnet=None,
                     vnet_name=None, ip_address=None):  # pylint: disable=unused-argument
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        rules = default_network_acls()

    if subnet:
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(subnet):
            raise CLIError("Expected fully qualified resource ID: got '{}'".format(subnet))

        if not rules.virtual_network_rules:
            rules.virtual_network_rules = []
        rules.virtual_network_rules.append(VirtualNetworkRule(id=subnet, ignore_missing_vnet_service_endpoint=True))
    if ip_address:
        if not rules.ip_rules:
            rules.ip_rules = []
        rules.ip_rules.append(IpRule(value=ip_address))

    properties = CognitiveServicesAccountProperties()
    properties.network_acls = rules
    params = CognitiveServicesAccount(properties=properties)

    return client.begin_update(resource_group_name, account_name, params)


def remove_network_rule(client, resource_group_name, account_name, ip_address=None, subnet=None,
                        vnet_name=None):  # pylint: disable=unused-argument
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        # nothing to update, but return the object
        return client.update(resource_group_name, account_name)

    if subnet:
        rules.virtual_network_rules = [x for x in rules.virtual_network_rules
                                       if not x.id.endswith(subnet)]
    if ip_address:
        rules.ip_rules = [x for x in rules.ip_rules if x.value != ip_address]

    properties = CognitiveServicesAccountProperties()
    properties.network_acls = rules
    params = CognitiveServicesAccount(properties=properties)

    return client.begin_update(resource_group_name, account_name, params)


def identity_assign(client, resource_group_name, account_name):
    params = CognitiveServicesAccount()
    params.identity = Identity(type=IdentityType.system_assigned)
    sa = client.begin_update(resource_group_name, account_name, params).result()
    return sa.identity if sa.identity else {}


def identity_remove(client, resource_group_name, account_name):
    params = CognitiveServicesAccount()
    params.identity = Identity(type=IdentityType.none)
    client.begin_update(resource_group_name, account_name, params)


def identity_show(client, resource_group_name, account_name):
    sa = client.get(resource_group_name, account_name)
    return sa.identity if sa.identity else {}
