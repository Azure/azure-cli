# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._constants import CREDENTIAL_SET_RESOURCE_ID_TEMPLATE
from ._utils import get_resource_group_name_by_registry_name
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.core.serialization import NULL as AzureCoreNull
from azure.cli.vendored_sdks.containerregistry.v2026_01_01_preview.generated.container_registry_management_client.models import (
    CacheRule,
    CacheRuleProperties,
    CacheRuleUpdateParameters,
    IdentityProperties,
    UserIdentityProperties
)


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
                     cred_set=None,
                     identity=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    
    # Handle credential set
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
    
    # Handle identity
    identity_properties = None
    if identity:
        # Create IdentityProperties with UserAssigned type
        identity_properties = IdentityProperties(
            type="UserAssigned",
            user_assigned_identities={
                identity: UserIdentityProperties()
            }
        )

    # Create cache rule properties
    cache_rule_properties = CacheRuleProperties(
        source_repository=source_repo,
        target_repository=target_repo,
        credential_set_resource_id=cred_set_id
    )

    # Create cache rule with direct SDK model
    cache_rule_create_params = CacheRule(
        properties=cache_rule_properties,
        identity=identity_properties
    )

    return client.begin_create(resource_group_name=rg,
                               registry_name=registry_name,
                               cache_rule_name=name,
                               cache_rule_create_parameters=cache_rule_create_params)


def acr_cache_update_custom(cmd,
                            instance,
                            registry_name,
                            resource_group_name=None,
                            cred_set=None,
                            remove_cred_set=False,
                            identity=None):

    # Check if any update parameters are provided
    has_cred_update = cred_set is not None or remove_cred_set
    has_identity_update = identity is not None
    
    if not has_cred_update and not has_identity_update:
        raise InvalidArgumentValueError("You must provide at least one parameter to update (credential set, identity, or removal flag).")

    #initilize properties if not already set
    if instance.properties is None:
        instance.properties = CacheRuleProperties() 

    # Handle credential set updates
    if has_cred_update:
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
    
    # Handle identity updates
    if has_identity_update:
        if identity:
            # Create IdentityProperties with UserAssigned type
            identity_properties = IdentityProperties(
                type="UserAssigned",
                user_assigned_identities={
                    identity: UserIdentityProperties()
                }
            )
            instance.identity = identity_properties
        else:
            # Remove identity by setting to None
            instance.identity = None

    return instance


def acr_cache_update_get(cmd):
    """Returns an empty CacheRuleUpdateParameters object.
    """

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
