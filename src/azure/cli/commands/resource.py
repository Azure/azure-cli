from .._argparse import IncorrectUsageError
from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client
from .._locale import L

from azure.mgmt.resource.resources import (ResourceManagementClient,
                                           ResourceManagementClientConfiguration)

@command('resource group list')
@description('List resource groups')
@option('--tag-name -tn <tagName>', L("the resource group's tag name"))
@option('--tag-value -tv <tagValue>', L("the resource group's tag value"))
def list_groups(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources.models import ResourceGroup, ResourceGroupFilter

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    filters = []
    if args.get('tag-name'):
        filters.append("tagname eq '{}'".format(args.get('tag-name')))
    if args.get('tag-value'):
        filters.append("tagvalue eq '{}'".format(args.get('tag-value')))

    filter_text = ' and '.join(filters) if len(filters) > 0 else None

    groups = rmc.resource_groups.list(filter=filter_text)
    return list(groups)

@command('resource show')
@description(L('Show details of a specific resource in a resource group or subscription'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--resource-type -r <resourceType>',
        L('the resource type in format: <provider-namespace>/<type>'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'))
@option('--parent <parent>',
        L('the name of the parent resource (if needed), in <parent-type>/<parent-name> format'))
def show_resource(args, unexpected): #pylint: disable=unused-argument
    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)
    full_type = args.get('resource-type').split('/')
    try:
        provider_namespace = full_type[0]
        resource_type = full_type[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')

    api_version = _resolve_api_version(args, rmc)
    if not api_version:
        raise IncorrectUsageError(
            L('API version is required and could not be resolved for resource {}'
              .format(full_type)))

    results = rmc.resources.get(
        resource_group_name=args.get('resource-group'),
        resource_name=args.get('name'),
        resource_provider_namespace=provider_namespace,
        resource_type=resource_type,
        api_version=api_version,
        parent_resource_path=args.get('parent', ''),
        custom_headers={'Accept': 'application/json'}
    )
    return results

def _resolve_api_version(args, rmc):
    api_version = args.get('api-version')
    if api_version:
        return api_version

    # if api-version not supplied, attempt to resolve using provider namespace
    parent = args.get('parent')
    full_type = args.get('resource-type').split('/')
    try:
        provider_namespace = full_type[0]
        resource_type = full_type[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')

    if parent:
        try:
            parent_type = parent.split('/')[0]
        except IndexError:
            raise IncorrectUsageError('Parameter --parent must be in <type>/<name> format.')

        resource_type = "{}/{}".format(parent_type, resource_type)
    provider = rmc.providers.get(provider_namespace)

    rt = [t for t in provider.resource_types if t.resource_type == resource_type]
    if not rt:
        raise IncorrectUsageError('Resource type {} not found.'.format(full_type))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if "preview" not in v]
        return npv[0] if npv else rt[0].api_versions[0]
    return None
