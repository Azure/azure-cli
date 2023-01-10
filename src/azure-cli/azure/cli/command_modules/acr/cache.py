# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from msrestazure.tools import is_valid_resource_id, parse_resource_id
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import sdk_no_wait
from ._utils import validate_premium_registry, get_registry_by_name



def acr_cache_show(cmd,
                   client,
                   registry_name,
                   name):

    _, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    return client.cache_rules.get(resource_group_name=rg,
                                  registry_name=registry_name,
                                  cache_rule_name=name)

def acr_cache_list(cmd,
                   client,
                   registry_name):
    _, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)
    return client.cache_rules.list(resource_group_name=rg,
                                  registry_name=registry_name)

def acr_cache_delete(cmd,
                   client,
                   registry_name,
                   name):
    _, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)
    return client.cache_rules.begin_delete(resource_group_name=rg,
                                  registry_name=registry_name,
                                  cache_rule_name=name)

def acr_cache_create(cmd,
                     client,
                     registry_name,
                     name,
                     source_repo,
                     target_repo,
                     cred_set=None):

    registry, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    cred_set_id = None if not cred_set else f'{registry.id}/credentialSets/{cred_set}'

    cache_rule_create_parameters = {
                    "name": name,
                    "properties": {
                        "sourceRepository": source_repo,
                        "targetRepository": target_repo,
                        "credentialSetResourceId": cred_set_id
                    }
                }
    return client.cache_rules.begin_create(resource_group_name=rg,
                                  registry_name=registry_name,
                                  cache_rule_name=name,
                                  cache_rule_create_parameters=cache_rule_create_parameters)

def acr_cache_update(cmd,
                   client,
                   registry_name,
                   name,
                   cred_set=None,
                   remove_cred_set=False):

    registry, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    cred_set_id = None if remove_cred_set else f'{registry.id}/credentialSets/{cred_set}'

    cache_rule_update_parameters = {
                    "name": name,
                    "properties": {
                        "credentialSetResourceId": cred_set_id
                    }
                }

    return client.cache_rules.begin_update(resource_group_name=rg,
                                  registry_name=registry_name,
                                  cache_rule_name=name,
                                  cache_rule_update_parameters=cache_rule_update_parameters)
