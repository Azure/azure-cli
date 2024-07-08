# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from knack.util import CLIError
from knack.log import get_logger

from azure.mgmt.cognitiveservices.models import Account as CognitiveServicesAccount, Sku, \
    VirtualNetworkRule, IpRule, NetworkRuleSet, NetworkRuleAction, \
    AccountProperties as CognitiveServicesAccountProperties, ApiProperties as CognitiveServicesAccountApiProperties, \
    Identity, ResourceIdentityType as IdentityType, \
    Deployment, DeploymentModel, DeploymentScaleSettings, DeploymentProperties, \
    CommitmentPlan, CommitmentPlanProperties, CommitmentPeriod
from azure.cli.command_modules.cognitiveservices._client_factory import cf_accounts, cf_resource_skus

logger = get_logger(__name__)


def list_resources(client, resource_group_name=None):
    """
    List all Azure Cognitive Services accounts.
    """
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def recover(client, location, resource_group_name, account_name):
    """
    Recover a deleted Azure Cognitive Services account.
    """
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
    """
    List skus for Azure Cognitive Services account.
    """
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
        tags=None, api_properties=None, assign_identity=False, storage=None, encryption=None,
        yes=None):  # pylint: disable=unused-argument
    """
    Create an Azure Cognitive Services account.
    """

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
    """
    Update an Azure Cognitive Services account.
    """
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
    """
    List network rules for Azure Cognitive Services account.
    """
    sa = client.get(resource_group_name, account_name)
    rules = sa.properties.network_acls
    if rules is None:
        rules = default_network_acls()
    return rules


def add_network_rule(client, resource_group_name, account_name, subnet=None,
                     vnet_name=None, ip_address=None):  # pylint: disable=unused-argument
    """
    Add a network rule for Azure Cognitive Services account.
    """
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
    """
    Remove a network rule for Azure Cognitive Services account.
    """
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
    """
    Assign the identity for Azure Cognitive Services account.
    """
    params = CognitiveServicesAccount()
    params.identity = Identity(type=IdentityType.system_assigned)
    sa = client.begin_update(resource_group_name, account_name, params).result()
    return sa.identity if sa.identity else {}


def identity_remove(client, resource_group_name, account_name):
    """
    Remove the identity for Azure Cognitive Services account.
    """
    params = CognitiveServicesAccount()
    params.identity = Identity(type=IdentityType.none)
    return client.begin_update(resource_group_name, account_name, params)


def identity_show(client, resource_group_name, account_name):
    """
    Show the identity for Azure Cognitive Services account.
    """
    sa = client.get(resource_group_name, account_name)
    return sa.identity if sa.identity else {}


def deployment_begin_create_or_update(
        client, resource_group_name, account_name, deployment_name,
        model_format, model_name, model_version, model_source=None,
        sku_name=None, sku_capacity=None,
        scale_settings_scale_type=None, scale_settings_capacity=None):
    """
    Create a deployment for Azure Cognitive Services account.
    """
    dpy = Deployment()
    dpy.properties = DeploymentProperties()
    dpy.properties.model = DeploymentModel()
    dpy.properties.model.format = model_format
    dpy.properties.model.name = model_name
    dpy.properties.model.version = model_version
    if model_source is not None:
        dpy.properties.model.source = model_source
    if sku_name is not None:
        dpy.sku = Sku(name=sku_name)
        dpy.sku.capacity = sku_capacity
    if scale_settings_scale_type is not None:
        dpy.properties.scale_settings = DeploymentScaleSettings()
        dpy.properties.scale_settings.scale_type = scale_settings_scale_type
        dpy.properties.scale_settings.capacity = scale_settings_capacity

    return client.begin_create_or_update(resource_group_name, account_name, deployment_name, dpy, polling=False)


def commitment_plan_create_or_update(
        client, resource_group_name, account_name, commitment_plan_name,
        hosting_model, plan_type, auto_renew,
        current_tier=None, current_count=None,
        next_tier=None, next_count=None):
    """
    Create a commitment plan for Azure Cognitive Services account.
    """
    plan = CommitmentPlan()
    plan.properties = CommitmentPlanProperties()
    plan.properties.hosting_model = hosting_model
    plan.properties.plan_type = plan_type
    if (current_tier is not None or current_count is not None):
        plan.properties.current = CommitmentPeriod()
        plan.properties.current.tier = current_tier
        plan.properties.current.count = current_count
    if (next_tier is not None or next_count is not None):
        plan.properties.next = CommitmentPeriod()
        plan.properties.next.tier = next_tier
        plan.properties.next.count = next_count
    plan.properties.auto_renew = auto_renew
    return client.create_or_update(resource_group_name, account_name, commitment_plan_name, plan)
