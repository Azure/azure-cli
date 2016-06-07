# pylint: disable=too-few-public-methods,no-self-use,too-many-arguments

from __future__ import print_function
import json
from codecs import open as codecs_open

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.resource.resources.models.resource_group import ResourceGroup
from azure.mgmt.resource.resources.models import GenericResource

from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError
import azure.cli._logging as _logging
from azure.cli.commands.client_factory import get_mgmt_service_client

from ._factory import _resource_client_factory

logger = _logging.get_az_logger(__name__)

def _list_resources_odata_filter_builder(location=None, resource_type=None,
                                         resource_group_name=None, tag=None, name=None):
    '''Build up OData filter string from parameters
    '''

    filters = []

    if resource_group_name:
        filters.append("resourceGroup eq '{}'".format(resource_group_name))

    if name:
        filters.append("name eq '{}'".format(name))

    if location:
        filters.append("location eq '{}'".format(location))

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

def list_resource_groups(tag=None): # pylint: disable=no-self-use
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

def create_resource_group(resource_group_name, location, tags=None):
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

def export_group_as_template(
        resource_group_name, include_comments=False, include_parameter_default_value=False):
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

def list_resources(
        location=None, resource_type=None, resource_group_name=None, tag=None, name=None):
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
    odata_filter = _list_resources_odata_filter_builder(
        location, resource_type, resource_group_name, tag, name)
    resources = rcf.resources.list(filter=odata_filter)
    return list(resources)

def deploy_arm_template(
        resource_group, deployment_name, template_file_path,
        parameters_file_path, mode='incremental'):
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

    properties = DeploymentProperties(template=template, parameters=parameters, mode=mode)

    smc = get_mgmt_service_client(ResourceManagementClient,
                                  ResourceManagementClientConfiguration)
    return smc.deployments.create_or_update(resource_group, deployment_name, properties)

def tag_resource(
        resource_group_name, resource_name, resource_type, tags, parent_resource_path=None,
        api_version=None, resource_provider_namespace=None):
    ''' Updates the tags on an existing resource. To clear tags, specify the --tag option
    without anything else. '''
    rcf = _resource_client_factory()
    resource = rcf.resources.get(
        resource_group_name,
        resource_provider_namespace,
        parent_resource_path,
        resource_type,
        resource_name,
        api_version)
    parameters = GenericResource(resource.location, tags, None, None) # pylint: disable=no-member
    try:
        rcf.resources.create_or_update(
            resource_group_name,
            resource_provider_namespace,
            parent_resource_path,
            resource_type,
            resource_name,
            api_version,
            parameters)
    except CloudError as ex:
        # TODO: Remove workaround once Swagger and SDK fix is implemented (#120123723)
        if '202' not in str(ex):
            raise ex

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
