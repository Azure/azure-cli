# pylint: disable=too-few-public-methods,no-self-use,too-many-arguments

from azure.mgmt.resource.resources.models.resource_group import ResourceGroup

from azure.cli.parser import IncorrectUsageError
from azure.cli.commands import CommandTable
from azure.cli._locale import L
from azure.cli._util import CLIError

from ._params import _resource_client_factory

command_table = CommandTable()

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

        tag_comps = tag.split('=')
        tag_name = tag_comps[0]
        if tag_name:
            if tag_name[-1] == '*':
                filters.append("startswith(tagname, '%s')" % tag_name[0:-1])
            else:
                filters.append("tagname eq '%s'" % tag_name)
                if len(tag_comps) == 2:
                    filters.append("tagvalue eq '%s'" % tag_comps[1])
    return ' and '.join(filters)

def _resolve_api_version(rcf, resource_type, parent=None):

    provider = rcf.providers.get(resource_type.namespace)
    resource_type_str = '{}/{}'.format(parent.type, resource_type.type) \
        if parent else resource_type.type

    rt = [t for t in provider.resource_types if t.resource_type == resource_type_str]
    if not rt:
        raise IncorrectUsageError('Resource type {}/{} not found.'
                                  .format(resource_type.namespace, resource_type.type))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if "preview" not in v]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise IncorrectUsageError(
            L('API version is required and could not be resolved for resource {}/{}'
              .format(resource_type.namespace, resource_type.type)))

class ConvenienceResourceGroupCommands(object):

    def __init__(self, **_):
        pass

    def list(self, tag=None): # pylint: disable=no-self-use
        ''' List resource groups, optionally filtered by a tag.
        :param str tag:tag to filter by in 'key[=value]' format
        '''
        rcf = _resource_client_factory()

        filters = []
        if tag:
            key = list(tag.keys())[0]
            filters.append("tagname eq '{}'".format(key))
            filters.append("tagvalue eq '{}'".format(tag[key]))

        filter_text = ' and '.join(filters) if len(filters) > 0 else None

        groups = rcf.resource_groups.list(filter=filter_text)
        return list(groups)

    def create(self, resource_group_name, location, tags=None):
        ''' Create a new resource group.
        :param str resource_group_name:the desired resource group name
        :param str location:the resource group location
        :param str tags:tags in 'a=b;c' format
        '''
        rcf = _resource_client_factory()

        if rcf.resource_groups.check_existence(resource_group_name):
            raise CLIError('resource group {} already exists'.format(resource_group_name))
        parameters = ResourceGroup(
            location=location,
            tags=tags
        )
        return rcf.resource_groups.create_or_update(resource_group_name, parameters)

class ConvenienceResourceCommands(object):

    def __init__(self, **_):
        pass

    def show(self, resource_group, resource_name, resource_type, api_version=None, parent=None):
        ''' Show details of a specific resource in a resource group or subscription
        :param str resource-group-name:the containing resource group name
        :param str name:the resource name
        :param str resource-type:the resource type in format: <provider-namespace>/<type>
        :param str api-version:the API version of the resource provider
        :param str parent:the name of the parent resource (if needed) in <type>/<name> format'''
        rcf = _resource_client_factory()

        api_version = _resolve_api_version(rcf, resource_type, parent) \
            if not api_version else api_version
        parent_path = '{}/{}'.format(parent.type, parent.name) if parent else ''

        results = rcf.resources.get(
            resource_group_name=resource_group,
            resource_name=resource_name,
            resource_provider_namespace=resource_type.namespace,
            resource_type=resource_type.type,
            api_version=api_version,
            parent_resource_path=parent_path
        )
        return results

    def list(self, location=None, resource_type=None, tag=None, name=None):
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
        rcf = _resource_client_factory()
        odata_filter = _list_resources_odata_filter_builder(location, resource_type, str(tag), name)
        resources = rcf.resources.list(filter=odata_filter)
        return list(resources)
