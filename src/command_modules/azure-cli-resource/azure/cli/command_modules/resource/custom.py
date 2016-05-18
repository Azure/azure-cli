# pylint: disable=too-few-public-methods,no-self-use,too-many-arguments

from __future__ import print_function
import json
from codecs import open as codecs_open

from azure.mgmt.resource.resources.models.resource_group import ResourceGroup

from azure.cli.parser import IncorrectUsageError
from azure.cli.commands import CommandTable
from azure.cli._locale import L
from azure.cli._util import CLIError
import azure.cli._logging as _logging
from azure.cli.commands import LongRunningOperation
from azure.cli.commands._command_creation import get_mgmt_service_client

from ._params import _resource_client_factory

logger = _logging.get_az_logger(__name__)

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
        filters.append("resourceType eq '{}/{}'".format(
            resource_type.namespace, resource_type.type))

    if tag:
        if name or location:
            raise IncorrectUsageError('you cannot use the tag filter with other filters')

        tag_name = list(tag.keys())[0] if isinstance(tag, dict) else tag
        tag_value = tag[tag_name] if isinstance(tag, dict) else ''
        if tag_name:
            if tag_name[-1] == '*':
                filters.append("startswith(tagname, '%s')" % tag_name[0:-1])
            else:
                filters.append("tagname eq '%s'" % tag_name)
                if tag_value != '':
                    filters.append("tagvalue eq '%s'" % tag_value)
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

    def export_group_as_template(self,
                                 resource_group_name,
                                 include_comments=False,
                                 include_parameter_default_value=False):
        '''Captures a resource group as a template.
        :param str resource_group_name:the name of the resoruce group.
        :param bool include_comments:export template with comments.
        :param bool include_parameter_default_value: export template parameter with default value.
        '''
        rcf = _resource_client_factory()

        export_options = []
        if include_comments:
            export_options.append('IncludeComments')
        if include_parameter_default_value:
            export_options.append('IncludeParameterDefaultValue')

        options = ','.join(export_options) if export_options else None

        result = rcf.resource_groups.export_template(resource_group_name, '*', options=options)
        #pylint: disable=no-member
        # On error, server still returns 200, with details in the error attribute
        if result.error:
            raise CLIError(result.error)

        print(json.dumps(result.template, indent=2))


class ConvenienceResourceCommands(object):

    def __init__(self, **_):
        pass

    def show(self, resource_group, resource_name, resource_type, api_version=None, parent=None):
        ''' Show details of a specific resource in a resource group or subscription
        :param str resource_group:the containing resource group name
        :param str resource_name:the resource name
        :param str resource_type:the resource type in format: <provider-namespace>/<type>
        :param str api_version:the API version of the resource provider
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
            :param str resource_type:filter by resource type
            :param str tag:filter by tag in 'a=b;c' format
            :param str name:filter by resource name
        '''
        rcf = _resource_client_factory()
        odata_filter = _list_resources_odata_filter_builder(location, resource_type, tag, name)
        resources = rcf.resources.list(filter=odata_filter)
        return list(resources)

    def deploy(self, resource_group, deployment_name, template_file_path,
               parameters_file_path, mode='Incremental'):
        ''' Deploy resources with an ARM template.
            :param str resource_group:resource group for deployment
            :param str location:location for deployment
            :param str deployment_name:name for deployment
            (use different values for simultaneous deployments)
            :param str template_file_path:path to deployment template JSON file
            :param str parameters_file_path:path to deployment parameters JSON file
        '''
        from azure.mgmt.resource.resources import (ResourceManagementClientConfiguration,
                                                   ResourceManagementClient)
        from azure.mgmt.resource.resources.models import DeploymentProperties

        parameters = _get_file_json(parameters_file_path)
        parameters = parameters.get('parameters', parameters)

        template = _get_file_json(template_file_path)

        properties = DeploymentProperties(template=template,
                                          parameters=parameters,
                                          mode=mode)

        op = LongRunningOperation('Deployment started', 'Deployment complete')
        smc = get_mgmt_service_client(ResourceManagementClient,
                                      ResourceManagementClientConfiguration)
        poller = smc.deployments.create_or_update(resource_group, deployment_name, properties)
        return op(poller)

def _get_file_json(file_path):
    return _load_json(file_path, 'utf-8') \
        or _load_json(file_path, 'utf-8-sig') \
        or _load_json(file_path, 'utf-16') \
        or _load_json(file_path, 'utf-16le') \
        or _load_json(file_path, 'utf-16be')

def _load_json(file_path, encoding):
    try:
        with codecs_open(file_path, encoding=encoding) as f:
            text = f.read()
        return json.loads(text)
    except ValueError:
        pass
