from azure.mgmt.resource.resources.models.resource_group import ResourceGroup

from azure.cli.parser import IncorrectUsageError
from azure.cli.commands import CommandTable
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli._locale import L

command_table = CommandTable()

def _resource_client_factory(_):
    from azure.mgmt.resource.resources import (ResourceManagementClient,
                                               ResourceManagementClientConfiguration)
    return get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

#### RESOURCE GROUP COMMANDS #################################

class ConvenienceResourceGroupCommands(object): # pylint: disable=too-few-public-methods

    def __init__(self, _):
        pass

    def list(self, tag_name=None, tag_value=None): # pylint: disable=no-self-use
        ''' List resource groups, optionally filtered by tag key or value.
        :param str tag_name:the resource group's tag name
        :param str tag_value:the resource group's tag value
        '''
        rcf = _resource_client_factory(None)

        filters = []
        if tag_name:
            filters.append("tagname eq '{}'".format(tag_name))
        if tag_value:
            filters.append("tagvalue eq '{}'".format(tag_value))

        filter_text = ' and '.join(filters) if len(filters) > 0 else None

        groups = rcf.resource_groups.list(filter=filter_text)
        return list(groups)

    def create(self, resource_group_name, location, tags=None): # pylint: disable=no-self-use
        ''' Create a new resource group.
        :param str resource_group_name:the desired resource group name
        :param str location:the resource group location
        :param str tags:tags in 'a=b;c' format
        '''
        rcf = _resource_client_factory(None)

        if rcf.resource_groups.check_existence(resource_group_name):
            raise ValueError('resource group {} already exists'.format(resource_group_name))
        parameters = ResourceGroup(
            location=location,
            tags=tags
        )
        return rcf.resource_groups.create_or_update(resource_group_name, parameters)

#### RESOURCE COMMANDS #######################################

def _list_resources_odata_filter_builder(location=None, resource_type=None, tag=None, name=None):
    '''Build up OData filter string from parameters
    '''

    filters = []

    if name:
        filters.append("name eq '%s'" % name)

    if location:
        filters.append("location eq '%s'" % location)

    if resource_type:
        filters.append("resourceType eq '%s'" % resource_type)

    if tag:
        if name or location:
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

def _resolve_api_version(rcf, resource_type, parent=None):
    # if api-version not supplied, attempt to resolve using provider namespace
    full_type = resource_type.split('/')
    try:
        provider_namespace = full_type[0]
        resource_type_val = full_type[1]
    except IndexError:
        raise IncorrectUsageError('Parameter --resource-type must be in ' + \
            '<namespace>/<type> format.')

    if parent:
        try:
            parent_type = parent.split('/')[0]
        except IndexError:
            raise IncorrectUsageError('Parameter --parent must be in <type>/<name> format.')

        resource_type_val = "{}/{}".format(parent_type, resource_type_val)

    provider = rcf.providers.get(provider_namespace)

    rt = [t for t in provider.resource_types if t.resource_type == resource_type_val]
    if not rt:
        raise IncorrectUsageError('Resource type {} not found.'.format(full_type))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if "preview" not in v]
        return npv[0] if npv else rt[0].api_versions[0]
    return None

class ConvenienceResourceCommands(object): # pylint: disable=too-few-public-methods

    def __init__(self, _):
        pass

    def show(self, resource_group, resource_name, resource_type, api_version=None, parent=''): # pylint: disable=too-many-arguments,no-self-use
        ''' Show details of a specific resource in a resource group or subscription
        :param str resource-group_name:the containing resource group name
        :param str name:the resource name
        :param str resource_type:the resource type in format: <provider-namespace>/<type>
        :param str api-version:the API version of the resource provider
        :param str parent:the name of the parent resource (if needed) in
        <parent-type>/<parent-name> format'''
        rcf = _resource_client_factory(None)

        type_comps = resource_type.split('/')
        try:
            namespace_comp = type_comps[0]
            resource_comp = type_comps[1]
        except IndexError:
            raise IncorrectUsageError('Parameter --resource-type must be in ' + \
                '<namespace>/<type> format.')

        api_version = _resolve_api_version(rcf, resource_type, parent) \
            if not api_version else api_version

        if not api_version:
            raise IncorrectUsageError(
                L('API version is required and could not be resolved for resource {}'
                  .format(full_type)))
        results = rcf.resources.get(
            resource_group_name=resource_group,
            resource_name=resource_name,
            resource_provider_namespace=namespace_comp,
            resource_type=resource_comp,
            api_version=api_version,
            parent_resource_path=parent
        )
        return results

    def list(self, location=None, resource_type=None, tag=None, name=None): # pylint: disable=no-self-use
        ''' List resources
            EXAMPLES:
                az resource list --location westus
                az resource list --name thename
                az resource list --name thename --location westus
                az resource list --tag something
                az resource list --tag some*
                az resource list --tag something=else
            :param str location:filter by resource location
            :param str resource-type:filter by resource type
            :param str tag:filter by tag in 'a=b;c' format
            :param str name:filter by resource name
        '''
        rcf = _resource_client_factory(None)
        odata_filter = _list_resources_odata_filter_builder(location, resource_type, tag, name)
        resources = rcf.resources.list(filter=odata_filter)
        return list(resources)
