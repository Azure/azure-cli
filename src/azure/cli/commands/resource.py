from ..parser import IncorrectUsageError
from ..commands import CommandTable, COMMON_PARAMETERS
from ._command_creation import get_mgmt_service_client
from .._locale import L

from azure.mgmt.resource.resources import (ResourceManagementClient,
                                           ResourceManagementClientConfiguration)

command_table = CommandTable()

@command_table.command('resource group list', description=L('List resource groups'))
@command_table.option('--tag-name -tn', help=L("the resource group's tag name"))
@command_table.option('--tag-value -tv', help=L("the resource group's tag value"))
def list_groups(args):
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

@command_table.command('resource show')
@command_table.description(
    L('Show details of a specific resource in a resource group or subscription'))
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option('--name -n', help=L('the resource name'), required=True)
@command_table.option('--resource-type -r',
                      help=L('the resource type in format: <provider-namespace>/<type>'),
                      required=True)
@command_table.option('--api-version -o', help=L('the API version of the resource provider'))
@command_table.option('--parent',
                      help=L('the name of the parent resource (if needed), in <parent-type>/<parent-name> format')) # pylint: disable=line-too-long
def show_resource(args):
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
        parent_resource_path=args.get('parent', '')
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
    else:
        resource_type = resource_type
    provider = rmc.providers.get(provider_namespace)
    for t in provider.resource_types:
        if t.resource_type == resource_type:
            # Return first non-preview version
            for version in t.api_versions:
                if not version.find('preview'):
                    return version
            # No non-preview version found. Take first preview version
            try:
                return t.api_versions[0]
            except IndexError:
                return None
    return None
