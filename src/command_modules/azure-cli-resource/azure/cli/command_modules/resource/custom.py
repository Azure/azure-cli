from azure.mgmt.resource.resources.models.resource_group import ResourceGroup

from azure.cli.parser import IncorrectUsageError
from azure.cli.commands import CommandTable, COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli._locale import L

command_table = CommandTable()

def _resource_client_factory(_):
    from azure.mgmt.resource.resources import (ResourceManagementClient,
                                               ResourceManagementClientConfiguration)
    return get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

#### RESOURCE GROUP COMMANDS #################################

@command_table.command('resource group list', description=L('List resource groups'))
@command_table.option('--tag-name -tn', help=L("the resource group's tag name"))
@command_table.option('--tag-value -tv', help=L("the resource group's tag value"))
def list_groups(args):
    rcf = _resource_client_factory(args)

    filters = []
    if args.get('tag_name'):
        filters.append("tagname eq '{}'".format(args.get('tag_name')))
    if args.get('tag_value'):
        filters.append("tagvalue eq '{}'".format(args.get('tag_value')))

    filter_text = ' and '.join(filters) if len(filters) > 0 else None

    groups = rcf.resource_groups.list(filter=filter_text)
    return list(groups)

@command_table.command('resource group create', description=L('create a new resource group'))
@command_table.option('--name -n', help=L('the resource group name'), required=True, metavar='NAME')
@command_table.option(**GLOBAL_COMMON_PARAMETERS['location'])
@command_table.option(**GLOBAL_COMMON_PARAMETERS['tags'])
def create_resource_group(args):
    rcf = _resource_client_factory(args)
    name = args.get('name')
    if rcf.resource_groups.check_existence(name):
        raise ValueError('resource group {} already exists'.format(name))
    parameters = ResourceGroup(
        location=args.get('location'),
        tags=args.get('tags')
    )
    return rcf.resource_groups.create_or_update(name, parameters)

#### RESOURCE COMMANDS #######################################

@command_table.command('resource show')
@command_table.description(
    L('Show details of a specific resource in a resource group or subscription'))
@command_table.option(**GLOBAL_COMMON_PARAMETERS['resource_group_name'])
@command_table.option('--name -n', help=L('the resource name'), required=True)
@command_table.option('--resource-type -r',
                      help=L('the resource type in format: <provider-namespace>/<type>'),
                      required=True)
@command_table.option('--api-version -o', help=L('the API version of the resource provider'))
@command_table.option('--parent', default='',
                      help=L('the name of the parent resource (if needed), ' + \
                      'in <parent-type>/<parent-name> format'))
def show_resource(args):
    rcf = _resource_client_factory(args)

    full_type = args.get('resource_type').split('/')
    try:
        provider_namespace = full_type[0]
        resource_type = full_type[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in <namespace>/<type> format.')

    api_version = _resolve_api_version(args, rcf)
    if not api_version:
        raise IncorrectUsageError(
            L('API version is required and could not be resolved for resource {}'
              .format(full_type)))
    results = rcf.resources.get(
        resource_group_name=args.get('resourcegroup'),
        resource_name=args.get('name'),
        resource_provider_namespace=provider_namespace,
        resource_type=resource_type,
        api_version=api_version,
        parent_resource_path=args.get('parent', '')
    )
    return results

def _list_resources_odata_filter_builder(args):
    '''Build up OData filter string from parameters
    '''

    filters = []

    name = args.get('name')
    if name:
        filters.append("name eq '%s'" % name)

    location = args.get('location')
    if location:
        filters.append("location eq '%s'" % location)

    resource_type = args.get('resource_type')
    if resource_type:
        filters.append("resourceType eq '%s'" % resource_type)

    tag = args.get('tag') or ''
    if tag and (name or location):
        raise IncorrectUsageError(
            'you cannot use the tagname or tagvalue filters with other filters')

    tag_name_value = tag.split('=')
    tag_name = tag_name_value[0]
    if tag_name:
        if tag_name[-1] == '*':
            filters.append("startswith(tagname, '%s')" % tag_name[0:-1])
        else:
            filters.append("tagname eq '%s'" % tag_name_value[0])
            if len(tag_name_value) == 2:
                filters.append("tagvalue eq '%s'" % tag_name_value[1])
    return ' and '.join(filters)

@command_table.command('resource list', description=L('List resources'))
@command_table.option('--location -l', help=L("Resource location"))
@command_table.option('--resource-type -r', help=L("Resource type"))
@command_table.option('--tag -t',
                      help=L("Filter by tag in the format of <tagname> or <tagname>=<tagvalue>"))
@command_table.option('--name -n', help=L("Name of resource"))
def list_resources(args):
    ''' EXAMPLES:
            az resource list --location westus
            az resource list --name thename
            az resource list --name thename --location westus
            az resource list --tag something
            az resource list --tag some*
            az resource list --tag something=else
    '''
    rcf = _resource_client_factory(args)
    odata_filter = _list_resources_odata_filter_builder(args)
    resources = rcf.resources.list(filter=odata_filter)
    return list(resources)

def _resolve_api_version(args, rcf):
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
    provider = rcf.providers.get(provider_namespace)

    rt = [t for t in provider.resource_types if t.resource_type == resource_type]
    if not rt:
        raise IncorrectUsageError('Resource type {} not found.'.format(full_type))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if "preview" not in v]
        return npv[0] if npv else rt[0].api_versions[0]
    return None
