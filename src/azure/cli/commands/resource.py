import json
from json import JSONDecodeError

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
        parent_resource_path=args.get('parent', '')
    )
    return results

@command('resource set')
@description(L('Update a resource in a resource group'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--resource-type -r <resourceType>',
        L('the resource type in format: <provider-namespace>/<type>'), required=True)
@option('--properties -p <properties>',
        L('a JSON-formatted string containing properties'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'))
@option('--parent <parent>',
        L('the name of the parent resource (if needed), in <parent-type>/<parent-name> format'))
@option('--tags -t <tags>',
        L('Tags to assign to the resource. Can be multiple. In the format of \'name=value\'.' \
        + ' Name is required and value is optional. For example, -t tag1=value1;tag2'))
# TODO: carried over from Node parameter list
#@option('--no-tags', L('removes all existing tags'))
def set_resource(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources.models import GenericResource

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

    resource_group = args.get('resource-group')
    resource_name = args.get('name')
    parent = args.get('parent', '')
    full_type = args.get('resource-type').split('/')
    try:
        provider_namespace = full_type[0]
        resource_type = full_type[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')

    api_version = _resolve_api_version(args, rmc)
    if not api_version:
        raise ValueError(L('API version is required and could not be resolved for resource {} '
                           .format(full_type) + 'Please specify using option --api-version or -o'))

    resource = rmc.resources.get(
        resource_group_name=resource_group,
        resource_name=resource_name,
        resource_provider_namespace=provider_namespace,
        resource_type=resource_type,
        api_version=api_version,
        parent_resource_path=parent)

    try:
        properties = json.loads(args.get('properties'))
    except JSONDecodeError as ex:
        raise ValueError(ex.msg)

    parameters = GenericResource(resource.location, #pylint: disable=no-member
                                 tags=args.get('tags'),
                                 properties=properties)

    results = rmc.resources.create_or_update(
        resource_group_name=resource_group,
        resource_name=resource_name,
        resource_provider_namespace=provider_namespace,
        resource_type=resource_type,
        api_version=api_version,
        parent_resource_path=parent,
        parameters=parameters
    )
    return results

@command('resource create')
@description(L('Creates a resource in a resource group'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <name>', L('the resource name'), required=True)
@option('--resource-type -r <resourceType>',
        L('the resource type in format: <provider-namespace>/<type>'), required=True)
@option('--location -l <location>',
        L('the location where the resource will be created'), required=True)
@option('--api-version -o <apiVersion>', L('the API version of the resource provider'))
@option('--parent <parent>',
        L('the name of the parent resource (if needed), in <type>/<name> format'))
@option('--properties -p <properties>', L('a JSON-formatted string containing properties'))
@option('--tags -t <tags>',
        L('Tags to assign to the resource. Can be multiple. In the format of \'name=value\'.' \
          + ' Name is required and value is optional. For example, -t tag1=value1;tag2'))
def create_resource(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources.models import GenericResource

    rmc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)
    location = args.get('location')
    full_type = args.get('resource-type').split('/')
    try:
        provider_namespace = full_type[0]
        resource_type = full_type[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')

    try:
        properties = json.loads(args.get('properties'))
    except JSONDecodeError as ex:
        raise ValueError(ex.msg)

    parameters = GenericResource(location,
                                 tags=args.get('tags'),
                                 properties=properties)

    api_version = _resolve_api_version(args, rmc)
    if not api_version:
        raise ValueError(L('API version is required and could not be resolved for resource {}. '
                           .format(full_type) + 'Please specify using option --api-version or -o'))

    results = rmc.resources.create_or_update(
        resource_group_name=args.get('resource-group'),
        resource_name=args.get('name'),
        resource_provider_namespace=provider_namespace,
        resource_type=resource_type,
        api_version=api_version,
        parent_resource_path=args.get('parent', ''),
        parameters=parameters
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
