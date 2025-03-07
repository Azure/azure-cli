# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._constants import CREDENTIAL_SET_RESOURCE_ID_TEMPLATE
from ._utils import get_resource_group_name_by_registry_name
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.core.serialization import NULL as AzureCoreNull


def acr_cache_show(cmd,
                   client,
                   registry_name,
                   name,
                   resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(resource_group_name=rg,
                      registry_name=registry_name,
                      cache_rule_name=name)


def acr_cache_list(cmd,
                   client,
                   registry_name,
                   resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(resource_group_name=rg,
                       registry_name=registry_name)


def acr_cache_delete(cmd,
                     client,
                     registry_name,
                     name,
                     resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.begin_delete(resource_group_name=rg,
                               registry_name=registry_name,
                               cache_rule_name=name)


def acr_cache_create(cmd,
                     client,
                     registry_name,
                     name,
                     source_repo,
                     target_repo,
                     resource_group_name=None,
                     cred_set=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    if cred_set:
        sub_id = get_subscription_id(cmd.cli_ctx)
        # Format the credential set ID using subscription ID, resource group, registry name, and credential set name
        cred_set_id = CREDENTIAL_SET_RESOURCE_ID_TEMPLATE.format(
            sub_id=sub_id,
            rg=rg,
            reg_name=registry_name,
            cred_set_name=cred_set
        )
    else:
        cred_set_id = AzureCoreNull

    CacheRuleCreateParameters = cmd.get_models('CacheRule', operation_group='cache_rules')

    cache_rule_create_params = CacheRuleCreateParameters()
    cache_rule_create_params.name = name
    cache_rule_create_params.source_repository = source_repo
    cache_rule_create_params.target_repository = target_repo
    cache_rule_create_params.credential_set_resource_id = cred_set_id

    return client.begin_create(resource_group_name=rg,
                               registry_name=registry_name,
                               cache_rule_name=name,
                               cache_rule_create_parameters=cache_rule_create_params)


def acr_cache_update_custom(cmd,
                            instance,
                            registry_name,
                            resource_group_name=None,
                            cred_set=None,
                            remove_cred_set=False):

    if cred_set is None and remove_cred_set is False:
        raise InvalidArgumentValueError("You must either update the credential set ID or remove it.")

    if remove_cred_set:
        cred_set_id = AzureCoreNull
    else:
        sub_id = get_subscription_id(cmd.cli_ctx)
        rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
        # Format the credential set ID using subscription ID, resource group, registry name, and credential set name
        cred_set_id = CREDENTIAL_SET_RESOURCE_ID_TEMPLATE.format(
            sub_id=sub_id,
            rg=rg,
            reg_name=registry_name,
            cred_set_name=cred_set
        )

    instance.credential_set_resource_id = cred_set_id

    return instance


def acr_cache_update_get(cmd):
    """Returns an empty CacheRuleUpdateParameters object.
    """

    CacheRuleUpdateParameters = cmd.get_models('CacheRuleUpdateParameters', operation_group='cache_rules')

    return CacheRuleUpdateParameters()


def acr_cache_update_set(cmd,
                         client,
                         registry_name,
                         name,
                         resource_group_name=None,
                         parameters=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.begin_update(resource_group_name=rg,
                               registry_name=registry_name,
                               cache_rule_name=name,
                               cache_rule_update_parameters=parameters)
