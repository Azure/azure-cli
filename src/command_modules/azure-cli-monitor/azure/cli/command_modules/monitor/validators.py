# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.arm import is_valid_resource_id, resource_id, parse_resource_id
from azure.cli.core.util import CLIError


def get_target_resource_validator(dest, required):
    def _validator(namespace):
        name_or_id = getattr(namespace, dest)
        rg = namespace.resource_group_name
        res_ns = namespace.namespace
        parent = namespace.parent
        res_type = namespace.resource_type

        usage_error = CLIError('usage error: --{0} ID | --{0} NAME --resource-group NAME '
                               '--{0}-namespace NAMESPACE [--{0}-parent PARENT] '
                               '[--{0}-type TYPE]'.format(dest))
        if not name_or_id and required:
            raise usage_error
        elif name_or_id:
            if is_valid_resource_id(name_or_id) and any((res_ns, parent, res_type)):
                raise usage_error
            elif not is_valid_resource_id(name_or_id):
                from azure.cli.core.commands.client_factory import get_subscription_id
                if res_type and '/' in res_type:
                    res_ns = res_ns or res_type.rsplit('/', 1)[0]
                    res_type = res_type.rsplit('/', 1)[1]
                if not all((rg, res_ns, res_type, name_or_id)):
                    raise usage_error

                setattr(namespace, dest,
                        '/subscriptions/{}/resourceGroups/{}/providers/{}/{}{}/{}'.format(
                            get_subscription_id(), rg, res_ns, parent + '/' if parent else '',
                            res_type, name_or_id))

        del namespace.namespace
        del namespace.parent
        del namespace.resource_type
    return _validator


def validate_diagnostic_settings(namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    resource_group_error = "--resource-group is required when name is provided for "\
                           "storage account or workspace or service bus namespace and rule. "

    if namespace.namespace or namespace.rule_name:
        if namespace.namespace is None:
            raise CLIError(resource_group_error)
        if namespace.rule_name is None:
            raise CLIError(resource_group_error)
        if namespace.resource_group is None:
            raise CLIError(resource_group_error)

        if not is_valid_resource_id(namespace.namespace):
            namespace.service_bus_rule_id = resource_id(subscription=get_subscription_id(),
                                                        resource_group=namespace.resource_group,
                                                        namespace='microsoft.ServiceBus',
                                                        type='namespaces',
                                                        name=namespace.namespace,
                                                        child_type='AuthorizationRules',
                                                        child_name=namespace.rule_name)
        else:
            resource_dict = parse_resource_id(namespace.namespace)
            namespace.service_bus_rule_id = resource_id(subscription=resource_dict['subscription'],
                                                        resource_group=resource_dict['resource_group'],
                                                        namespace=resource_dict['namespace'],
                                                        type=resource_dict['type'],
                                                        name=resource_dict['name'],
                                                        child_type='AuthorizationRules',
                                                        child_name=namespace.rule_name)

    if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
        if namespace.resource_group is None:
            raise CLIError(resource_group_error)
        namespace.storage_account = resource_id(subscription=get_subscription_id(),
                                                resource_group=namespace.resource_group,
                                                namespace='microsoft.Storage',
                                                type='storageAccounts',
                                                name=namespace.storage_account)

    if namespace.workspace and not is_valid_resource_id(namespace.workspace):
        if namespace.resource_group is None:
            raise CLIError(resource_group_error)
        namespace.workspace = resource_id(subscription=get_subscription_id(),
                                          resource_group=namespace.resource_group,
                                          namespace='microsoft.OperationalInsights',
                                          type='workspaces', name=namespace.workspace)

    _validate_tags(namespace)


def _validate_tags(namespace):
    """ Extracts multiple space-separated tags in key[=value] format """
    if isinstance(namespace.tags, list):
        tags_dict = {}
        for item in namespace.tags:
            tags_dict.update(_validate_tag(item))
        namespace.tags = tags_dict


def _validate_tag(string):
    """ Extracts a single tag in key[=value] format """
    result = {}
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result
