import json
from json import JSONDecodeError

from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client
from .._locale import L
    
from azure.mgmt.resource.resources import (ResourceManagementClient,
                                           ResourceManagementClientConfiguration)

@command('resource group list')
@description(L('List resource groups'))
# TODO: waiting on Python Azure SDK bug fixes
# @option('--tag-name -g <tagName>', L('the resource group's tag name'))
# @option('--tag-value -g <tagValue>', L('the resource group's tag value'))
# @option('--top -g <number>', L('Top N resource groups to retrieve'))
def list_groups(args, unexpected): #pylint: disable=unused-argument
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
@option('--resource-type -r <resourceType>', L('the resource type in format: <provider-namespace>/<type>'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'), required=True)
@option('--parent <parent>', L('the name of the parent resource (if needed), in <parent-type>/<parent-name> format'))
def show_resource(args, unexpected):

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    full_type = args.get('resource-type').split('/')

    results = rmc.resources.get(
        resource_group_name=args.get('resource-group'),
        resource_name=args.get('name'),
        resource_provider_namespace=full_type[0],
        resource_type=full_type[1],
        api_version=args.get('api-version'),
        parent_resource_path=args.get('parent') or ''
    )
    return results

@command('resource set')
@description(L('Update a resource in a resource group'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--resource-type -r <resourceType>', L('the resource type in format: <provider-namespace>/<type>'), required=True)
@option('--properties -p <properties>', L('a JSON-formatted string containing properties'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'), required=True)
@option('--parent <parent>', L('the name of the parent resource (if needed), in <parent-type>/<parent-name> format'))
@option('--tags -t <tags>', L('Tags to assign to the resource. Can be multiple. In the format of \'name=value\'.' \
    + ' Name is required and value is optional. For example, -t tag1=value1;tag2'))
# TODO: implement
#@option('--no-tags', L('removes all existing tags'))
#@option('--subscription <subscription>', L('the subscription identifier'))
def set_resource(args, unexpected):

    return _create_or_update(args, unexpected)

@command('resource create')
@description(L('Creates a resource in a resource group'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--resource-type -r <resourceType>', L('the resource type in format: <provider-namespace>/<type>'), required=True)
@option('--location -l <location>', L('the location where the resource will be created'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'), required=True)
@option('--parent <parent>', L('the name of the parent resource (if needed), in <parent-type>/<parent-name> format'))
@option('--properties -p <properties>', L('a JSON-formatted string containing properties'))
@option('--tags -t <tags>', L('Tags to assign to the resource. Can be multiple. In the format of \'name=value\'.' \
    + ' Name is required and value is optional. For example, -t tag1=value1;tag2'))
# TODO: implement
#@option('--subscription <subscription>', L('the subscription identifier'))
def create_resource(args, unexpected):

    return _create_or_update(args, unexpected)

def _create_or_update(args, unexpected):

    from azure.mgmt.resource.resources.models import GenericResource

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    full_type = args.get('resource-type').split('/')

    location = args.get('location')
    if not location:
        # TODO: retrieve resource and get location from there? Default for now.
        location = 'West US'
    
    try:
        properties = json.loads(args.get('properties'))
    except JSONDecodeError as ex:
        print(L('Invalid property format. Please use: "{\\"foo\\":\\"bar\\"}"'))
        return None
    
    parameters = GenericResource(location,
                                 tags=args.get('tags') or None,
                                 properties=properties) 

    results = rmc.resources.create_or_update(
        resource_group_name=args.get('resource-group'),
        resource_name=args.get('name'),
        resource_provider_namespace=full_type[0],
        resource_type=full_type[1],
        api_version=args.get('api-version'),
        parent_resource_path=args.get('parent') or '',
        parameters=parameters
    )
    return results