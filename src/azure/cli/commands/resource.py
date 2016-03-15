from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client
from .._locale import L

@command('resource group list')
@description(L('List resource groups'))
# TODO: waiting on Python Azure SDK bug fixes
# @option('--tag-name -g <tagName>', L('the resource group's tag name'))
# @option('--tag-value -g <tagValue>', L('the resource group's tag value'))
# @option('--top -g <number>', L('Top N resource groups to retrieve'))
def list_groups(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources import (ResourceManagementClient,
                                              ResourceManagementClientConfiguration)
    from azure.mgmt.resource.resources.models import ResourceGroup, ResourceGroupFilter

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    # TODO: waiting on Python Azure SDK bug fixes
    #group_filter = ResourceGroupFilter(args.get('tag-name'), args.get('tag-value'))
    #groups = rmc.resource_groups.list(filter=None, top=args.get('top'))
    groups = rmc.resource_groups.list()
    return list(groups)

@command('resource show')
@description(L('Show details of a specific resource in a resource group or subscription'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--provider-namespace -p <providerNamespace>', L('the resource provider namespace'), required=True)
@option('--resource-type -r <resourceType>', L('the resource type'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'), required=True)
@option('--parent <parent>', L('the name of the parent resource (if needed), in path/path/path format'))
def show_resource(args, unexpected):
    from azure.mgmt.resource.resources import (ResourceManagementClient,
                                              ResourceManagementClientConfiguration)
    from azure.mgmt.resource.resources.models import ResourceGroup, ResourceGroupFilter

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    results = rmc.resources.get(
        resource_group_name=args.get('resource-group'),
        resource_name=args.get('name'),
        resource_provider_namespace=args.get('provider-namespace'),
        resource_type=args.get('resource-type'),
        api_version=args.get('api-version'),
        parent_resource_path=args.get('parent') or ''
    )

    return list(results)

@command('resource set')
@description(L('Update a resource in a resource group'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--resource-type -r <resourceType>', L('the resource type'), required=True)
@option('--properties -p <properties>', L('a JSON-formatted string containing properties'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'), required=True)
@option('--parent <parent>', L('the name of the parent resource (if needed), in path/path/path format'))
@option('--tags -t <tags>', L('Tags to set to the source. Can be multiple. In the format of \'name=value\'.' \
    + ' Name is required and value is optional. For example, -t tag1=value1;tag2'))
@option('--no-tags', L('removes all existing tags'))
@option('--subscription <subscription>', L('the subscription identifier'))
def set_resource(args, unexpected):
    print('  Command: resource set (IN PROGRESS) with args: %s' % args)
    return None

#@command('resource create')
#@description(L('Creates a resource in a resource group'))
#@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
#@option('--name -n <name>', L('the resource name'), required=True)
#@option('--resource-type -r <resourceType>', L('the resource type'), required=True)
#@option('--location -l <location>', L('the location where the resource will be created'), required=True)
#@option('--api-version -o <apiVersion>', L('the API version of the resource provider'), required=True)
#@option('--parent <parent>', L('the name of the parent resource (if needed), in path/path/path format'))
#@option('--properties -p <properties>', L('a JSON-formatted string containing properties'))
#@option('--tags -t <tags>', L('Tags to set to the source. Can be multiple. In the format of \'name=value\'.' \
#    + ' Name is required and value is optional. For example, -t tag1=value1;tag2'))
#@option('--subscription <subscription>', L('the subscription identifier'))
#def create_resource(args, unexpected):
#    print('  Command: resource create (IN PROGRESS) with args: %s' % args)