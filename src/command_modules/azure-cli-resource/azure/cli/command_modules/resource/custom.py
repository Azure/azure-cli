# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from __future__ import print_function
import json
import os
import re
import ssl
import sys
import uuid

from six.moves.urllib.request import urlopen  # pylint: disable=import-error

from azure.mgmt.resource.resources.models import GenericResource

from azure.mgmt.resource.locks.models import ManagementLockObject
from azure.mgmt.resource.links.models import ResourceLinkProperties

from azure.mgmt.resource.managedapplications.models import Appliance
from azure.mgmt.resource.managedapplications.models import Plan
from azure.mgmt.resource.managedapplications.models import ApplianceDefinition
from azure.mgmt.resource.managedapplications.models import ApplianceProviderAuthorization

from azure.cli.core.parser import IncorrectUsageError
from azure.cli.core.prompting import prompt, prompt_pass, prompt_t_f, prompt_choice_list, prompt_int
from azure.cli.core.util import CLIError, get_file_json, shell_safe_json_parse
import azure.cli.core.azlogging as azlogging
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import is_valid_resource_id, parse_resource_id
from azure.cli.core.profiles import get_sdk, ResourceType

from ._client_factory import (_resource_client_factory,
                              _resource_policy_client_factory,
                              _resource_lock_client_factory,
                              _resource_links_client_factory,
                              _authorization_management_client,
                              _resource_managedapps_client_factory)

logger = azlogging.get_az_logger(__name__)


def list_resource_groups(tag=None):  # pylint: disable=no-self-use
    """ List resource groups, optionally filtered by a tag.
    :param str tag:tag to filter by in 'key[=value]' format
    """
    rcf = _resource_client_factory()

    filters = []
    if tag:
        key = list(tag.keys())[0]
        filters.append("tagname eq '{}'".format(key))
        filters.append("tagvalue eq '{}'".format(tag[key]))

    filter_text = ' and '.join(filters) if filters else None

    groups = rcf.resource_groups.list(filter=filter_text)
    return list(groups)


def create_resource_group(rg_name, location, tags=None):
    """ Create a new resource group.
    :param str resource_group_name:the desired resource group name
    :param str location:the resource group location
    :param str tags:tags in 'a=b c' format
    """
    rcf = _resource_client_factory()

    ResourceGroup = get_sdk(ResourceType.MGMT_RESOURCE_RESOURCES, 'ResourceGroup', mod='models')
    parameters = ResourceGroup(
        location=location,
        tags=tags
    )
    return rcf.resource_groups.create_or_update(rg_name, parameters)


def create_appliance(resource_group_name,
                     appliance_name, managedby_resource_group_id,
                     location, kind, managedapp_definition_id=None,
                     plan_name=None, plan_publisher=None, plan_product=None,
                     plan_version=None, tags=None, parameters=None):
    """ Create a new managed application.
    :param str resource_group_name:the desired resource group name
    :param str appliance_name:the managed application name
    :param str kind:the managed application kind. can be marketplace or servicecatalog
    :param str plan_name:the managed application package plan name
    :param str plan_publisher:the managed application package plan publisher
    :param str plan_product:the managed application package plan product
    :param str plan_version:the managed application package plan version
    :param str tags:tags in 'a=b c' format
    """
    racf = _resource_managedapps_client_factory()
    appliance = Appliance(
        location=location,
        managed_resource_group_id=managedby_resource_group_id,
        kind=kind,
        tags=tags
    )

    if kind.lower() == 'servicecatalog':
        if managedapp_definition_id:
            appliance.appliance_definition_id = managedapp_definition_id
        else:
            raise CLIError('--managedapp-definition-id is required if kind is ServiceCatalog')
    elif kind.lower() == 'marketplace':
        if (plan_name is None and plan_product is None and
                plan_publisher is None and plan_version is None):
            raise CLIError('--plan-name, --plan-product, --plan-publisher and \
            --plan-version are all required if kind is MarketPlace')
        else:
            appliance.plan = Plan(plan_name, plan_publisher, plan_product, plan_version)

    applianceParameters = None

    if parameters:
        if os.path.exists(parameters):
            applianceParameters = get_file_json(parameters)
        else:
            applianceParameters = shell_safe_json_parse(parameters)

    appliance.parameters = applianceParameters

    return racf.appliances.create_or_update(resource_group_name, appliance_name, appliance)


def show_appliance(resource_group_name=None, appliance_name=None, managedapp_id=None):
    """ Gets a managed application.
    :param str resource_group_name:the resource group name
    :param str appliance_name:the managed application name
    """
    racf = _resource_managedapps_client_factory()
    if managedapp_id:
        appliance = racf.appliances.get_by_id(managedapp_id)
    else:
        appliance = racf.appliances.get(resource_group_name, appliance_name)
    return appliance


def show_appliancedefinition(resource_group_name=None, appliance_definition_name=None,
                             managedapp_definition_id=None):
    """ Gets a managed application definition.
    :param str resource_group_name:the resource group name
    :param str appliance_definition_name:the managed application definition name
    """
    racf = _resource_managedapps_client_factory()
    if managedapp_definition_id:
        appliancedef = racf.appliance_definitions.get_by_id(managedapp_definition_id)
    else:
        appliancedef = racf.appliance_definitions.get(resource_group_name,
                                                      appliance_definition_name)
    return appliancedef


def create_appliancedefinition(resource_group_name,
                               appliance_definition_name, location,
                               lock_level, package_file_uri, authorizations,
                               description, display_name, tags=None):
    """ Create a new managed application definition.
    :param str resource_group_name:the desired resource group name
    :param str appliance_definition_name:the managed application definition name
    :param str description:the managed application definition description
    :param str display_name:the managed application definition display name
    :param str package_file_uri:the managed application definition package file uri
    :param str tags:tags in 'a=b c' format
    """
    racf = _resource_managedapps_client_factory()
    authorizations = authorizations or []
    applianceAuthList = []

    for name_value in authorizations:
        # split at the first ':', neither principalId nor roldeDefinitionId should have a ':'
        principalId, roleDefinitionId = name_value.split(':', 1)
        applianceAuth = ApplianceProviderAuthorization(principalId, roleDefinitionId)
        applianceAuthList.append(applianceAuth)

    applianceDef = ApplianceDefinition(lock_level, applianceAuthList, package_file_uri)
    applianceDef.display_name = display_name
    applianceDef.description = description
    applianceDef.location = location
    applianceDef.tags = tags

    return racf.appliance_definitions.create_or_update(resource_group_name,
                                                       appliance_definition_name, applianceDef)


def list_appliances(resource_group_name=None):
    racf = _resource_managedapps_client_factory()

    if resource_group_name:
        appliances = racf.appliances.list_by_resource_group(resource_group_name)
    else:
        appliances = racf.appliances.list_by_subscription()
    return list(appliances)


def export_group_as_template(
        resource_group_name, include_comments=False, include_parameter_default_value=False):
    """Captures a resource group as a template.
    :param str resource_group_name:the name of the resoruce group.
    :param bool include_comments:export template with comments.
    :param bool include_parameter_default_value: export template parameter with default value.
    """
    rcf = _resource_client_factory()

    export_options = []
    if include_comments:
        export_options.append('IncludeComments')
    if include_parameter_default_value:
        export_options.append('IncludeParameterDefaultValue')

    options = ','.join(export_options) if export_options else None

    result = rcf.resource_groups.export_template(resource_group_name, '*', options=options)
    # pylint: disable=no-member
    # On error, server still returns 200, with details in the error attribute
    if result.error:
        error = result.error
        if (hasattr(error, 'details') and error.details and
                hasattr(error.details[0], 'message')):
            error = error.details[0].message
        raise CLIError(error)

    print(json.dumps(result.template, indent=2))


def deploy_arm_template(resource_group_name,
                        template_file=None, template_uri=None, deployment_name=None,
                        parameters=None, mode='incremental', no_wait=False):
    return _deploy_arm_template_core(resource_group_name, template_file, template_uri,
                                     deployment_name, parameters, mode, no_wait=no_wait)


def validate_arm_template(resource_group_name, template_file=None, template_uri=None,
                          parameters=None, mode='incremental'):
    return _deploy_arm_template_core(resource_group_name, template_file, template_uri,
                                     'deployment_dry_run', parameters, mode, validate_only=True)


def _find_missing_parameters(parameters, template):
    if template is None:
        return {}
    template_parameters = template.get('parameters', None)
    if template_parameters is None:
        return {}

    missing = {}
    for parameter_name in template_parameters:
        parameter = template_parameters[parameter_name]
        if parameter.get('defaultValue', None) is not None:
            continue
        if parameters is not None and parameters.get(parameter_name, None) is not None:
            continue
        missing[parameter_name] = parameter
    return missing


def _prompt_for_parameters(missing_parameters):
    result = {}
    for param_name in missing_parameters:
        prompt_str = 'Please provide a value for \'{}\' (? for help): '.format(param_name)
        param = missing_parameters[param_name]
        param_type = param.get('type', 'string')
        description = 'Missing description'
        metadata = param.get('metadata', None)
        if metadata is not None:
            description = metadata.get('description', description)
        allowed_values = param.get('allowedValues', None)

        while True:
            if allowed_values is not None:
                ix = prompt_choice_list(prompt_str, allowed_values, help_string=description)
                result[param_name] = allowed_values[ix]
                break
            elif param_type == 'securestring':
                value = prompt_pass(prompt_str, help_string=description)
                result[param_name] = value
            elif param_type == 'int':
                int_value = prompt_int(prompt_str, help_string=description)
                result[param_name] = int_value
                break
            elif param_type == 'bool':
                value = prompt_t_f(prompt_str, help_string=description)
                result[param_name] = value
                break
            else:
                value = prompt(prompt_str, help_string=description)
                result[param_name] = value
            if value:
                break
    return result


def _get_missing_parameters(parameters, template, prompt_fn):
    missing = _find_missing_parameters(parameters, template)
    if missing:
        prompt_parameters = prompt_fn(missing)
        for param_name in prompt_parameters:
            parameters[param_name] = {
                "value": prompt_parameters[param_name]
            }
    return parameters


def _ssl_context():
    if sys.version_info < (3, 4):
        return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url):
    req = urlopen(url, context=_ssl_context())
    return req.read()


def _deploy_arm_template_core(resource_group_name,  # pylint: disable=too-many-arguments
                              template_file=None, template_uri=None, deployment_name=None,
                              parameters=None, mode='incremental', validate_only=False,
                              no_wait=False):
    DeploymentProperties, TemplateLink = get_sdk(ResourceType.MGMT_RESOURCE_RESOURCES,
                                                 'DeploymentProperties',
                                                 'TemplateLink',
                                                 mod='models')
    parameters = parameters or {}
    template = None
    template_link = None
    template_obj = None
    if template_uri:
        template_link = TemplateLink(uri=template_uri)
        template_obj = shell_safe_json_parse(_urlretrieve(template_uri).decode('utf-8'))
    else:
        template = get_file_json(template_file)
        template_obj = template

    parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters)

    properties = DeploymentProperties(template=template, template_link=template_link,
                                      parameters=parameters, mode=mode)

    smc = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
    if validate_only:
        return smc.deployments.validate(resource_group_name, deployment_name, properties, raw=no_wait)
    return smc.deployments.create_or_update(resource_group_name, deployment_name, properties, raw=no_wait)


def export_deployment_as_template(resource_group_name, deployment_name):
    smc = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
    result = smc.deployments.export_template(resource_group_name, deployment_name)
    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def create_resource(properties,
                    resource_group_name=None, resource_provider_namespace=None,
                    parent_resource_path=None, resource_type=None, resource_name=None,
                    resource_id=None, api_version=None, location=None, is_full_object=False):
    res = _ResourceUtils(resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version)
    return res.create_resource(properties, location, is_full_object)


def show_resource(resource_group_name=None,
                  resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                  resource_name=None, resource_id=None, api_version=None):
    res = _ResourceUtils(resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version)
    return res.get_resource()


def delete_resource(resource_group_name=None,
                    resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                    resource_name=None, resource_id=None, api_version=None):
    res = _ResourceUtils(resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version)
    return res.delete()


def update_resource(parameters,
                    resource_group_name=None, resource_provider_namespace=None,
                    parent_resource_path=None, resource_type=None, resource_name=None,
                    resource_id=None, api_version=None):
    res = _ResourceUtils(resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version)
    return res.update(parameters)


def tag_resource(tags,
                 resource_group_name=None, resource_provider_namespace=None,
                 parent_resource_path=None, resource_type=None, resource_name=None,
                 resource_id=None, api_version=None):
    """ Updates the tags on an existing resource. To clear tags, specify the --tag option
    without anything else. """
    res = _ResourceUtils(resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version)
    return res.tag(tags)


def get_deployment_operations(client, resource_group_name, deployment_name, operation_ids):
    """get a deployment's operation.
    """
    result = []
    for op_id in operation_ids:
        dep = client.get(resource_group_name, deployment_name, op_id)
        result.append(dep)
    return result


def list_resources(resource_group_name=None,
                   resource_provider_namespace=None, resource_type=None, name=None, tag=None,
                   location=None):
    rcf = _resource_client_factory()

    if resource_group_name is not None:
        rcf.resource_groups.get(resource_group_name)

    odata_filter = _list_resources_odata_filter_builder(resource_group_name,
                                                        resource_provider_namespace,
                                                        resource_type, name, tag, location)
    resources = rcf.resources.list(filter=odata_filter)
    return list(resources)


def _list_resources_odata_filter_builder(resource_group_name=None,
                                         resource_provider_namespace=None,
                                         resource_type=None, name=None, tag=None, location=None):
    """Build up OData filter string from parameters
    """
    filters = []

    if resource_group_name:
        filters.append("resourceGroup eq '{}'".format(resource_group_name))

    if name:
        filters.append("name eq '{}'".format(name))

    if location:
        filters.append("location eq '{}'".format(location))

    if resource_type:
        if resource_provider_namespace:
            f = "'{}/{}'".format(resource_provider_namespace, resource_type)
        else:
            if not re.match('[^/]+/[^/]+', resource_type):
                raise CLIError(
                    'Malformed resource-type: '
                    '--resource-type=<namespace>/<resource-type> expected.')
            # assume resource_type is <namespace>/<type>. The worst is to get a server error
            f = "'{}'".format(resource_type)
        filters.append("resourceType eq " + f)
    else:
        if resource_provider_namespace:
            raise CLIError('--namespace also requires --resource-type')

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


def get_providers_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    rcf = _resource_client_factory()
    result = rcf.providers.list()
    return [r.namespace for r in result]


def get_resource_types_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    rcf = _resource_client_factory()
    result = rcf.providers.list()
    types = []
    for p in list(result):
        for r in p.resource_types:
            types.append(p.namespace + '/' + r.resource_type)
    return types


def register_provider(resource_provider_namespace, wait=False):
    _update_provider(resource_provider_namespace, registering=True, wait=wait)


def unregister_provider(resource_provider_namespace, wait=False):
    _update_provider(resource_provider_namespace, registering=False, wait=wait)


def _update_provider(namespace, registering, wait):
    import time
    rcf = _resource_client_factory()
    if registering:
        rcf.providers.register(namespace)
    else:
        rcf.providers.unregister(namespace)

    if wait:
        while True:
            time.sleep(10)
            rp_info = rcf.providers.get(namespace)
            if rp_info.registration_state == ('Registered' if registering else 'Unregistered'):
                break
    else:
        action = 'Registering' if registering else 'Unregistering'
        msg_template = '%s is still on-going. You can monitor using \'az provider show -n %s\''
        logger.warning(msg_template, action, namespace)


def list_provider_operations(api_version=None):
    api_version = api_version or _get_auth_provider_latest_api_version()
    auth_client = _authorization_management_client()
    return auth_client.provider_operations_metadata.list(api_version)


def show_provider_operations(resource_provider_namespace, api_version=None):
    api_version = api_version or _get_auth_provider_latest_api_version()
    auth_client = _authorization_management_client()
    return auth_client.provider_operations_metadata.get(resource_provider_namespace, api_version)


def _get_auth_provider_latest_api_version():
    rcf = _resource_client_factory()
    api_version = _ResourceUtils.resolve_api_version(rcf, 'Microsoft.Authorization',
                                                     None, 'providerOperations')
    return api_version


def move_resource(ids, destination_group, destination_subscription_id=None):
    """Moves resources from one resource group to another(can be under different subscription)

    :param ids: the space separated resource ids to be moved
    :param destination_group: the destination resource group name
    :param destination_subscription_id: the destination subscription identifier
    """
    from azure.cli.core.commands.arm import resource_id

    # verify all resource ids are valid and under the same group
    resources = []
    for i in ids:
        if is_valid_resource_id(i):
            resources.append(parse_resource_id(i))
        else:
            raise CLIError('Invalid id "{}", as it has no group or subscription field'.format(i))

    if len(set([r['subscription'] for r in resources])) > 1:
        raise CLIError('All resources should be under the same subscription')
    if len(set([r['resource_group'] for r in resources])) > 1:
        raise CLIError('All resources should be under the same group')

    rcf = _resource_client_factory()
    target = resource_id(subscription=(destination_subscription_id or rcf.config.subscription_id),
                         resource_group=destination_group)

    return rcf.resources.move_resources(resources[0]['resource_group'], ids, target)


def list_features(client, resource_provider_namespace=None):
    if resource_provider_namespace:
        return client.list(resource_provider_namespace=resource_provider_namespace)
    return client.list_all()


def create_policy_assignment(policy, name=None, display_name=None,
                             resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory()
    scope = _build_policy_scope(policy_client.config.subscription_id,
                                resource_group_name, scope)
    policy_id = _resolve_policy_id(policy, policy_client)
    PolicyAssignment = get_sdk(ResourceType.MGMT_RESOURCE_POLICY, 'PolicyAssignment', mod='models')
    assignment = PolicyAssignment(display_name, policy_id, scope)
    return policy_client.policy_assignments.create(scope,
                                                   name or uuid.uuid4(),
                                                   assignment)


def delete_policy_assignment(name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory()
    scope = _build_policy_scope(policy_client.config.subscription_id,
                                resource_group_name, scope)
    policy_client.policy_assignments.delete(scope, name)


def show_policy_assignment(name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory()
    scope = _build_policy_scope(policy_client.config.subscription_id,
                                resource_group_name, scope)
    return policy_client.policy_assignments.get(scope, name)


def list_policy_assignment(disable_scope_strict_match=None, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory()
    if scope and not is_valid_resource_id(scope):
        parts = scope.strip('/').split('/')
        if len(parts) == 4:
            resource_group_name = parts[3]
        elif len(parts) == 2:
            # rarely used, but still verify
            if parts[1].lower() != policy_client.config.subscription_id.lower():
                raise CLIError("Please use current active subscription's id")
        else:
            err = "Invalid scope '{}', it should point to a resource group or a resource"
            raise CLIError(err.format(scope))
        scope = None

    _scope = _build_policy_scope(policy_client.config.subscription_id,
                                 resource_group_name, scope)
    if resource_group_name:
        result = policy_client.policy_assignments.list_for_resource_group(resource_group_name)
    elif scope:
        # pylint: disable=redefined-builtin
        id = parse_resource_id(scope)
        parent_resource_path = '' if not id.get('child_name') else (id['type'] + '/' + id['name'])
        resource_type = id.get('child_type') or id['type']
        resource_name = id.get('child_name') or id['name']
        result = policy_client.policy_assignments.list_for_resource(
            id['resource_group'], id['namespace'],
            parent_resource_path, resource_type, resource_name)
    else:
        result = policy_client.policy_assignments.list()

    if not disable_scope_strict_match:
        result = [i for i in result if _scope.lower() == i.scope.lower()]

    return result


def _build_policy_scope(subscription_id, resource_group_name, scope):
    subscription_scope = '/subscriptions/' + subscription_id
    if scope:
        if resource_group_name:
            err = "Resource group '{}' is redundant because 'scope' is supplied"
            raise CLIError(err.format(resource_group_name))
    elif resource_group_name:
        scope = subscription_scope + '/resourceGroups/' + resource_group_name
    else:
        scope = subscription_scope
    return scope


def _resolve_policy_id(policy, client):
    policy_id = policy
    if not is_valid_resource_id(policy):
        policy_def = client.policy_definitions.get(policy)
        policy_id = policy_def.id
    return policy_id


def create_policy_definition(name, rules, display_name=None, description=None):
    if os.path.exists(rules):
        rules = get_file_json(rules)
    else:
        rules = shell_safe_json_parse(rules)

    policy_client = _resource_policy_client_factory()
    PolicyDefinition = get_sdk(ResourceType.MGMT_RESOURCE_POLICY, 'PolicyDefinition', mod='models')
    parameters = PolicyDefinition(policy_rule=rules, description=description,
                                  display_name=display_name)
    return policy_client.policy_definitions.create_or_update(name, parameters)


def update_policy_definition(policy_definition_name, rules=None,
                             display_name=None, description=None):
    if rules is not None:
        if os.path.exists(rules):
            rules = get_file_json(rules)
        else:
            rules = shell_safe_json_parse(rules)

    policy_client = _resource_policy_client_factory()
    definition = policy_client.policy_definitions.get(policy_definition_name)
    # pylint: disable=line-too-long,no-member
    PolicyDefinition = get_sdk(ResourceType.MGMT_RESOURCE_POLICY, 'PolicyDefinition', mod='models')
    parameters = PolicyDefinition(
        policy_rule=rules if rules is not None else definition.policy_rule,
        description=description if description is not None else definition.description,
        display_name=display_name if display_name is not None else definition.display_name)
    return policy_client.policy_definitions.create_or_update(policy_definition_name, parameters)


def get_policy_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory()
    result = policy_client.policy_definitions.list()
    return [i.name for i in result]


def get_policy_assignment_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory()
    result = policy_client.policy_assignments.list()
    return [i.name for i in result]


def list_locks(resource_group_name=None,
               resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
               resource_name=None, filter_string=None):
    """
    :param resource_provider_namespace: Name of a resource provider.
    :type resource_provider_namespace: str
    :param parent_resource_path: Path to a parent resource
    :type parent_resource_path: str
    :param resource_type: The type for the resource with the lock.
    :type resource_type: str
    :param resource_name: Name of a resource that has a lock.
    :type resource_name: str
    :param filter_string: A query filter to use to restrict the results.
    :type filter_string: str
    """
    lock_client = _resource_lock_client_factory()
    lock_resource = _extract_lock_params(resource_group_name, resource_provider_namespace,
                                         resource_type, resource_name)
    resource_group_name = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    if resource_group_name is None:
        return lock_client.management_locks.list_at_subscription_level(filter=filter_string)
    if resource_name is None:
        return lock_client.management_locks.list_at_resource_group_level(
            resource_group_name, filter=filter_string)
    return lock_client.management_locks.list_at_resource_level(
        resource_group_name, resource_provider_namespace, parent_resource_path, resource_type,
        resource_name, filter=filter_string)


def _validate_lock_params_match_lock(
        lock_client, name, resource_group_name, resource_provider_namespace, parent_resource_path,
        resource_type, resource_name):
    """
    Locks are scoped to subscription, resource group or resource.
    However, the az list command returns all locks for the current scopes
    and all lower scopes (e.g. resource group level also includes resource locks).
    This can lead to a confusing user experience where the user specifies a lock
    name and assumes that it will work, even if they haven't given the right
    scope. This function attempts to validate the parameters and help the
    user find the right scope, by first finding the lock, and then infering
    what it's parameters should be.
    """
    locks = lock_client.management_locks.list_at_subscription_level()
    found_count = 0  # locks at different levels can have the same name
    lock_resource_id = None
    for lock in locks:
        if lock.name == name:
            found_count = found_count + 1
            lock_resource_id = lock.id
    if found_count == 1:
        # If we only found one lock, let's validate that the parameters are correct,
        # if we found more than one, we'll assume the user knows what they're doing
        # TODO: Add validation for that case too?
        resource = parse_resource_id(lock_resource_id)
        _resource_group = resource.get('resource_group', None)
        _resource_namespace = resource.get('namespace', None)
        if _resource_group is None:
            return
        if resource_group_name != _resource_group:
            raise CLIError(
                'Unexpected --resource-group for lock {}, expected {}'.format(
                    name, _resource_group))
        if _resource_namespace is None:
            return
        if resource_provider_namespace != _resource_namespace:
            raise CLIError(
                'Unexpected --namespace for lock {}, expected {}'.format(name, _resource_namespace))
        if resource.get('grandchild_type', None) is None:
            _resource_type = resource.get('type', None)
            _resource_name = resource.get('name', None)
        else:
            _resource_type = resource.get('child_type', None)
            _resource_name = resource.get('child_name', None)
            parent = (resource['type'] + '/' + resource['name'])
            if parent != parent_resource_path:
                raise CLIError(
                    'Unexpected --parent for lock {}, expected {}'.format(
                        name, parent))
        if resource_type != _resource_type:
            raise CLIError('Unexpected --resource-type for lock {}, expected {}'.format(
                name, _resource_type))
        if resource_name != _resource_name:
            raise CLIError('Unexpected --resource-name for lock {}, expected {}'.format(
                name, _resource_name))


def get_lock(name, resource_group_name=None):
    """
    :param name: Name of the lock.
    :type name: str
    """
    lock_client = _resource_lock_client_factory()
    if resource_group_name is None:
        return lock_client.management_locks.get_at_subscription_level(name)
    return lock_client.management_locks.get_at_resource_group_level(resource_group_name, name)


def delete_lock(name,
                resource_group_name=None, resource_provider_namespace=None,
                parent_resource_path=None, resource_type=None, resource_name=None):
    """
    :param name: The name of the lock.
    :type name: str
    :param resource_provider_namespace: Name of a resource provider.
    :type resource_provider_namespace: str
    :param parent_resource_path: Path to a parent resource
    :type parent_resource_path: str
    :param resource_type: The type for the resource with the lock.
    :type resource_type: str
    :param resource_name: Name of a resource that has a lock.
    :type resource_name: str
    """
    lock_client = _resource_lock_client_factory()
    lock_resource = _extract_lock_params(resource_group_name, resource_provider_namespace,
                                         resource_type, resource_name)
    resource_group_name = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    _validate_lock_params_match_lock(lock_client, name, resource_group_name,
                                     resource_provider_namespace, parent_resource_path,
                                     resource_type, resource_name)

    if resource_group_name is None:
        return lock_client.management_locks.delete_at_subscription_level(name)
    if resource_name is None:
        return lock_client.management_locks.delete_at_resource_group_level(
            resource_group_name, name)
    return lock_client.management_locks.delete_at_resource_level(
        resource_group_name, resource_provider_namespace, parent_resource_path or '', resource_type,
        resource_name, name)


def _extract_lock_params(resource_group_name, resource_provider_namespace,
                         resource_type, resource_name):
    if resource_group_name is None:
        return (None, None, None, None)

    if resource_name is None:
        return (resource_group_name, None, None, None)

    parts = resource_type.split('/', 2)
    if resource_provider_namespace is None and len(parts) == 2:
        resource_provider_namespace = parts[0]
        resource_type = parts[1]
    return (resource_group_name, resource_name, resource_provider_namespace, resource_type)


def create_lock(name,
                resource_group_name=None, resource_provider_namespace=None, notes=None,
                parent_resource_path=None, resource_type=None, resource_name=None, level=None):
    """
    :param name: The name of the lock.
    :type name: str
    :param resource_provider_namespace: Name of a resource provider.
    :type resource_provider_namespace: str
    :param parent_resource_path: Path to a parent resource
    :type parent_resource_path: str
    :param resource_type: The type for the resource with the lock.
    :type resource_type: str
    :param resource_name: Name of a resource that has a lock.
    :type resource_name: str
    :param notes: Notes about this lock.
    :type notes: str
    """
    if level != 'ReadOnly' and level != 'CanNotDelete':
        raise CLIError('--lock-type must be one of "ReadOnly" or "CanNotDelete"')
    parameters = ManagementLockObject(level=level, notes=notes, name=name)

    lock_client = _resource_lock_client_factory()
    lock_resource = _extract_lock_params(resource_group_name, resource_provider_namespace,
                                         resource_type, resource_name)
    resource_group_name = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    if resource_group_name is None:
        return lock_client.management_locks.create_or_update_at_subscription_level(name, parameters)

    if resource_name is None:
        return lock_client.management_locks.create_or_update_at_resource_group_level(
            resource_group_name, name, parameters)

    return lock_client.management_locks.create_or_update_at_resource_level(
        resource_group_name, resource_provider_namespace, parent_resource_path or '', resource_type,
        resource_name, name, parameters)


def _update_lock_parameters(parameters, level, notes, lock_id, lock_type):
    if level is not None:
        parameters.level = level
    if notes is not None:
        parameters.nodes = notes
    if lock_id is not None:
        parameters.id = lock_id
    if lock_type is not None:
        parameters.type = lock_type


def update_lock(name, resource_group_name=None, level=None, notes=None):
    lock_client = _resource_lock_client_factory()
    if resource_group_name is None:
        params = lock_client.management_locks.get(name)
        _update_lock_parameters(params, level, notes, None, None)
        return lock_client.management_locks.create_or_update_at_subscription_level(name, params)
    params = lock_client.management_locks.get_at_resource_group_level(resource_group_name, name)
    _update_lock_parameters(params, level, notes, None, None)
    return lock_client.management_locks.create_or_update_at_resource_group_level(
        resource_group_name, name, params)


def create_resource_link(link_id, target_id, notes=None):
    """
    :param target_id: The id of the resource link target.
    :type target_id: str
    :param notes: Notes for this link.
    :type notes: str
    """
    links_client = _resource_links_client_factory().resource_links
    properties = ResourceLinkProperties(target_id, notes)
    links_client.create_or_update(link_id, properties)


def update_resource_link(link_id, target_id=None, notes=None):
    """
    :param target_id: The id of the resource link target.
    :type target_id: str
    :param notes: Notes for this link.
    :type notes: str
    """
    links_client = _resource_links_client_factory().resource_links
    params = links_client.get(link_id)
    properties = ResourceLinkProperties(
        target_id if target_id is not None else params.properties.target_id,
        # pylint: disable=no-member
        notes=notes if notes is not None else params.properties.notes)  # pylint: disable=no-member
    links_client.create_or_update(link_id, properties)


def list_resource_links(scope=None, filter_string=None):
    """
    :param scope: The scope for the links
    :type scope: str
    :param filter_string: A filter for restricting the results
    :type filter_string: str
    """
    links_client = _resource_links_client_factory().resource_links
    if scope is not None:
        return links_client.list_at_source_scope(scope, filter=filter_string)
    return links_client.list_at_subscription(filter=filter_string)


def _validate_resource_inputs(resource_group_name, resource_provider_namespace,
                              resource_type, resource_name):
    if resource_group_name is None:
        raise CLIError('--resource-group/-g is required.')
    if resource_type is None:
        raise CLIError('--resource-type is required')
    if resource_name is None:
        raise CLIError('--name/-n is required')
    if resource_provider_namespace is None:
        raise CLIError('--namespace is required')


class _ResourceUtils(object):  # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 resource_group_name=None, resource_provider_namespace=None,
                 parent_resource_path=None, resource_type=None, resource_name=None,
                 resource_id=None, api_version=None, rcf=None):
        # if the resouce_type is in format 'namespace/type' split it.
        # (we don't have to do this, but commands like 'vm show' returns such values)
        if resource_type and not resource_provider_namespace and not parent_resource_path:
            parts = resource_type.split('/')
            if len(parts) > 1:
                resource_provider_namespace = parts[0]
                resource_type = parts[1]

        self.rcf = rcf or _resource_client_factory()
        if api_version is None:
            if resource_id:
                api_version = _ResourceUtils._resolve_api_version_by_id(self.rcf, resource_id)
            else:
                _validate_resource_inputs(resource_group_name, resource_provider_namespace,
                                          resource_type, resource_name)
                api_version = _ResourceUtils.resolve_api_version(self.rcf,
                                                                 resource_provider_namespace,
                                                                 parent_resource_path,
                                                                 resource_type)

        self.resource_group_name = resource_group_name
        self.resource_provider_namespace = resource_provider_namespace
        self.parent_resource_path = parent_resource_path
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.resource_id = resource_id
        self.api_version = api_version

    def create_resource(self, properties, location, is_full_object):
        res = json.loads(properties)
        if not is_full_object:
            if not location:
                if self.resource_id:
                    rg_name = parse_resource_id(self.resource_id)['resource_group']
                else:
                    rg_name = self.resource_group_name
                location = self.rcf.resource_groups.get(rg_name).location

            res = GenericResource(location=location, properties=res)
        elif res.get('location', None) is None:
            raise IncorrectUsageError("location of the resource is required")

        if self.resource_id:
            resource = self.rcf.resources.create_or_update_by_id(self.resource_id,
                                                                 self.api_version,
                                                                 res)
        else:
            resource = self.rcf.resources.create_or_update(self.resource_group_name,
                                                           self.resource_provider_namespace,
                                                           self.parent_resource_path or '',
                                                           self.resource_type,
                                                           self.resource_name,
                                                           self.api_version,
                                                           res)
        return resource

    def get_resource(self):
        if self.resource_id:
            resource = self.rcf.resources.get_by_id(self.resource_id, self.api_version)
        else:
            resource = self.rcf.resources.get(self.resource_group_name,
                                              self.resource_provider_namespace,
                                              self.parent_resource_path or '',
                                              self.resource_type,
                                              self.resource_name,
                                              self.api_version)
        return resource

    def delete(self):
        if self.resource_id:
            return self.rcf.resources.delete_by_id(self.resource_id, self.api_version)
        return self.rcf.resources.delete(self.resource_group_name,
                                         self.resource_provider_namespace,
                                         self.parent_resource_path or '',
                                         self.resource_type,
                                         self.resource_name,
                                         self.api_version)

    def update(self, parameters):
        if self.resource_id:
            return self.rcf.resources.create_or_update_by_id(self.resource_id,
                                                             self.api_version,
                                                             parameters)
        return self.rcf.resources.create_or_update(self.resource_group_name,
                                                   self.resource_provider_namespace,
                                                   self.parent_resource_path or '',
                                                   self.resource_type,
                                                   self.resource_name,
                                                   self.api_version,
                                                   parameters)

    def tag(self, tags):
        resource = self.get_resource()
        # pylint: disable=no-member
        parameters = GenericResource(
            location=resource.location,
            tags=tags,
            plan=resource.plan,
            properties=resource.properties,
            kind=resource.kind,
            managed_by=resource.managed_by,
            sku=resource.sku,
            identity=resource.identity)

        if self.resource_id:
            return self.rcf.resources.create_or_update_by_id(self.resource_id, self.api_version,
                                                             parameters)
        return self.rcf.resources.create_or_update(self.resource_group_name,
                                                   self.resource_provider_namespace,
                                                   self.parent_resource_path or '',
                                                   self.resource_type,
                                                   self.resource_name,
                                                   self.api_version,
                                                   parameters)

    @staticmethod
    def resolve_api_version(rcf, resource_provider_namespace, parent_resource_path, resource_type):
        provider = rcf.providers.get(resource_provider_namespace)

        # If available, we will use parent resource's api-version
        resource_type_str = (parent_resource_path.split('/')[0]
                             if parent_resource_path else resource_type)

        rt = [t for t in provider.resource_types
              if t.resource_type.lower() == resource_type_str.lower()]
        if not rt:
            raise IncorrectUsageError('Resource type {} not found.'
                                      .format(resource_type_str))
        if len(rt) == 1 and rt[0].api_versions:
            npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
            return npv[0] if npv else rt[0].api_versions[0]
        else:
            raise IncorrectUsageError(
                'API version is required and could not be resolved for resource {}'
                .format(resource_type))

    @staticmethod
    def _resolve_api_version_by_id(rcf, resource_id):
        parts = parse_resource_id(resource_id)
        namespace = parts.get('child_namespace', parts['namespace'])
        if parts.get('grandchild_type'):
            parent = (parts['type'] + '/' + parts['name'] + '/' +
                      parts['child_type'] + '/' + parts['child_name'])
            resource_type = parts['grandchild_type']
        elif parts.get('child_type'):
            # if the child resource has a provider namespace it is independent of the
            # parent, so set the parent to empty
            if parts.get('child_namespace') is not None:
                parent = ''
            else:
                parent = parts['type'] + '/' + parts['name']
            resource_type = parts['child_type']
        else:
            parent = None
            resource_type = parts['type']

        return _ResourceUtils.resolve_api_version(rcf, namespace, parent, resource_type)
