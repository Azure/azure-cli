# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=line-too-long

from __future__ import print_function
from collections import OrderedDict
import codecs
import json
import os
import re
import ssl
import sys
import uuid

from six.moves.urllib.request import urlopen  # pylint: disable=import-error
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

from knack.log import get_logger
from knack.prompting import prompt, prompt_pass, prompt_t_f, prompt_choice_list, prompt_int, NoTTYException
from knack.util import CLIError

from msrestazure.tools import is_valid_resource_id, parse_resource_id, resource_id as resource_dict_to_id

from azure.mgmt.resource.resources.models import GenericResource

from azure.mgmt.resource.locks.models import ManagementLockObject
from azure.mgmt.resource.links.models import ResourceLinkProperties

from azure.cli.core.parser import IncorrectUsageError
from azure.cli.core.util import get_file_json, shell_safe_json_parse, sdk_no_wait
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType, get_sdk

from azure.cli.command_modules.resource._client_factory import (
    _resource_client_factory, _resource_policy_client_factory, _resource_lock_client_factory,
    _resource_links_client_factory, _authorization_management_client, _resource_managedapps_client_factory)
from azure.cli.command_modules.resource._validators import _parse_lock_id

logger = get_logger(__name__)


def _process_parameters(template_param_defs, parameter_lists):

    def _try_parse_json_object(value):
        try:
            parsed = shell_safe_json_parse(value)
            return parsed.get('parameters', parsed)
        except CLIError:
            return None

    def _try_load_file_object(value):
        if os.path.isfile(value):
            parsed = get_file_json(value, throw_on_empty=False)
            return parsed.get('parameters', parsed)
        return None

    def _try_parse_key_value_object(template_param_defs, parameters, value):
        # support situation where empty JSON "{}" is provided
        if value == '{}' and not parameters:
            return True

        try:
            key, value = value.split('=', 1)
        except ValueError:
            return False

        param = template_param_defs.get(key, None)
        if param is None:
            raise CLIError("unrecognized template parameter '{}'. Allowed parameters: {}"
                           .format(key, ', '.join(sorted(template_param_defs.keys()))))

        param_type = param.get('type', None)
        if param_type:
            param_type = param_type.lower()
        if param_type in ['object', 'array']:
            parameters[key] = {'value': shell_safe_json_parse(value)}
        elif param_type in ['string', 'securestring']:
            parameters[key] = {'value': value}
        elif param_type == 'bool':
            parameters[key] = {'value': value.lower() == 'true'}
        elif param_type == 'int':
            parameters[key] = {'value': int(value)}
        else:
            logger.warning("Unrecognized type '%s' for parameter '%s'. Interpretting as string.", param_type, key)
            parameters[key] = {'value': value}

        return True

    parameters = {}
    for params in parameter_lists or []:
        for item in params:
            param_obj = _try_load_file_object(item) or _try_parse_json_object(item)
            if param_obj is not None:
                parameters.update(param_obj)
            elif not _try_parse_key_value_object(template_param_defs, parameters, item):
                raise CLIError('Unable to parse parameter: {}'.format(item))

    return parameters


def _find_missing_parameters(parameters, template):
    if template is None:
        return {}
    template_parameters = template.get('parameters', None)
    if template_parameters is None:
        return {}

    missing = OrderedDict()
    for parameter_name in template_parameters:
        parameter = template_parameters[parameter_name]
        if 'defaultValue' in parameter:
            continue
        if parameters is not None and parameters.get(parameter_name, None) is not None:
            continue
        missing[parameter_name] = parameter
    return missing


def _prompt_for_parameters(missing_parameters, fail_on_no_tty=True):  # pylint: disable=too-many-statements

    prompt_list = missing_parameters.keys() if isinstance(missing_parameters, OrderedDict) \
        else sorted(missing_parameters)
    result = OrderedDict()
    no_tty = False
    for param_name in prompt_list:
        param = missing_parameters[param_name]
        param_type = param.get('type', 'string')
        description = 'Missing description'
        metadata = param.get('metadata', None)
        if metadata is not None:
            description = metadata.get('description', description)
        allowed_values = param.get('allowedValues', None)

        prompt_str = "Please provide {} value for '{}' (? for help): ".format(param_type, param_name)
        while True:
            if allowed_values is not None:
                try:
                    ix = prompt_choice_list(prompt_str, allowed_values, help_string=description)
                    result[param_name] = allowed_values[ix]
                except NoTTYException:
                    result[param_name] = None
                    no_tty = True
                break
            elif param_type == 'securestring':
                try:
                    value = prompt_pass(prompt_str, help_string=description)
                except NoTTYException:
                    value = None
                    no_tty = True
                result[param_name] = value
                break
            elif param_type == 'int':
                try:
                    int_value = prompt_int(prompt_str, help_string=description)
                    result[param_name] = int_value
                except NoTTYException:
                    result[param_name] = 0
                    no_tty = True
                break
            elif param_type == 'bool':
                try:
                    value = prompt_t_f(prompt_str, help_string=description)
                    result[param_name] = value
                except NoTTYException:
                    result[param_name] = False
                    no_tty = True
                break
            elif param_type in ['object', 'array']:
                try:
                    value = prompt(prompt_str, help_string=description)
                except NoTTYException:
                    value = ''
                    no_tty = True

                if value == '':
                    value = {} if param_type == 'object' else []
                else:
                    try:
                        value = shell_safe_json_parse(value)
                    except Exception as ex:  # pylint: disable=broad-except
                        logger.error(ex)
                        continue
                result[param_name] = value
                break
            else:
                try:
                    result[param_name] = prompt(prompt_str, help_string=description)
                except NoTTYException:
                    result[param_name] = None
                    no_tty = True
                break
    if no_tty and fail_on_no_tty:
        raise NoTTYException
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


def _deploy_arm_template_core(cli_ctx, resource_group_name,  # pylint: disable=too-many-arguments
                              template_file=None, template_uri=None, deployment_name=None,
                              parameters=None, mode=None, rollback_on_error=None, validate_only=False,
                              no_wait=False):
    DeploymentProperties, TemplateLink, OnErrorDeployment = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                                                    'DeploymentProperties', 'TemplateLink',
                                                                    'OnErrorDeployment', mod='models')
    template = None
    template_link = None
    template_obj = None
    on_error_deployment = None

    if template_uri:
        template_link = TemplateLink(uri=template_uri)
        template_obj = shell_safe_json_parse(_urlretrieve(template_uri).decode('utf-8'), preserve_order=True)
    else:
        template = get_file_json(template_file, preserve_order=True)
        template_obj = template

    if rollback_on_error == '':
        on_error_deployment = OnErrorDeployment(type='LastSuccessful')
    elif rollback_on_error:
        on_error_deployment = OnErrorDeployment(type='SpecificDeployment', deployment_name=rollback_on_error)

    template_param_defs = template_obj.get('parameters', {})
    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(template_param_defs, parameters) or {}
    parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters)

    template = json.loads(json.dumps(template))
    parameters = json.loads(json.dumps(parameters))

    properties = DeploymentProperties(template=template, template_link=template_link,
                                      parameters=parameters, mode=mode, on_error_deployment=on_error_deployment)

    smc = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    if validate_only:
        return sdk_no_wait(no_wait, smc.deployments.validate, resource_group_name, deployment_name, properties)
    return sdk_no_wait(no_wait, smc.deployments.create_or_update, resource_group_name, deployment_name, properties)


def _deploy_arm_template_subscription_scope(cli_ctx,  # pylint: disable=too-many-arguments
                                            template_file=None, template_uri=None,
                                            deployment_name=None, deployment_location=None,
                                            parameters=None, mode=None, validate_only=False,
                                            no_wait=False):
    DeploymentProperties, TemplateLink = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                                 'DeploymentProperties', 'TemplateLink', mod='models')
    template = None
    template_link = None
    template_obj = None
    if template_uri:
        template_link = TemplateLink(uri=template_uri)
        template_obj = shell_safe_json_parse(_urlretrieve(template_uri).decode('utf-8'), preserve_order=True)
    else:
        template = get_file_json(template_file, preserve_order=True)
        template_obj = template

    template_param_defs = template_obj.get('parameters', {})
    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(template_param_defs, parameters) or {}
    parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters)

    template = json.loads(json.dumps(template))
    parameters = json.loads(json.dumps(parameters))

    properties = DeploymentProperties(template=template, template_link=template_link,
                                      parameters=parameters, mode=mode)

    smc = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    if validate_only:
        return sdk_no_wait(no_wait, smc.deployments.validate_at_subscription_scope,
                           deployment_name, properties, deployment_location)
    return sdk_no_wait(no_wait, smc.deployments.create_or_update_at_subscription_scope,
                       deployment_name, properties, deployment_location)


def _list_resources_odata_filter_builder(resource_group_name=None, resource_provider_namespace=None,
                                         resource_type=None, name=None, tag=None, location=None):
    """Build up OData filter string from parameters """
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


def _get_auth_provider_latest_api_version(cli_ctx):
    rcf = _resource_client_factory(cli_ctx)
    api_version = _ResourceUtils.resolve_api_version(rcf, 'Microsoft.Authorization', None, 'providerOperations')
    return api_version


def _update_provider(cli_ctx, namespace, registering, wait):
    import time
    rcf = _resource_client_factory(cli_ctx)
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


def _resolve_policy_id(cmd, policy, policy_set_definition, client):
    policy_id = policy or policy_set_definition
    if not is_valid_resource_id(policy_id):
        if policy:
            policy_def = _get_custom_or_builtin_policy(cmd, client, policy)
            policy_id = policy_def.id
        else:
            policy_set_def = _get_custom_or_builtin_policy(cmd, client, policy_set_definition, True)
            policy_id = policy_set_def.id
    return policy_id


def _get_custom_or_builtin_policy(cmd, client, name, for_policy_set=False):
    from msrest.exceptions import HttpOperationError
    from msrestazure.azure_exceptions import CloudError
    ErrorResponseException = cmd.get_models('ErrorResponseException')
    policy_operations = client.policy_set_definitions if for_policy_set else client.policy_definitions
    try:
        return policy_operations.get(name)
    except (CloudError, HttpOperationError, ErrorResponseException) as ex:
        status_code = ex.status_code if isinstance(ex, CloudError) else ex.response.status_code
        if status_code == 404:
            return policy_operations.get_built_in(name)
        raise


def _load_file_string_or_uri(file_or_string_or_uri, name, required=True):
    if file_or_string_or_uri is None:
        if required:
            raise CLIError('One of --{} or --{}-uri is required'.format(name, name))
        return None
    url = urlparse(file_or_string_or_uri)
    if url.scheme == 'http' or url.scheme == 'https' or url.scheme == 'file':
        response = urlopen(file_or_string_or_uri)
        reader = codecs.getreader('utf-8')
        result = json.load(reader(response))
        response.close()
        return result
    if os.path.exists(file_or_string_or_uri):
        return get_file_json(file_or_string_or_uri)
    return shell_safe_json_parse(file_or_string_or_uri)


def _call_subscription_get(cmd, lock_client, *args):
    if cmd.supported_api_version(max_api='2015-01-01'):
        return lock_client.management_locks.get(*args)
    return lock_client.management_locks.get_at_subscription_level(*args)


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


def _update_lock_parameters(parameters, level, notes):
    if level is not None:
        parameters.level = level
    if notes is not None:
        parameters.notes = notes


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


# region Custom Commands

def list_resource_groups(cmd, tag=None):  # pylint: disable=no-self-use
    """ List resource groups, optionally filtered by a tag.
    :param str tag:tag to filter by in 'key[=value]' format
    """
    rcf = _resource_client_factory(cmd.cli_ctx)

    filters = []
    if tag:
        key = list(tag.keys())[0]
        filters.append("tagname eq '{}'".format(key))
        filters.append("tagvalue eq '{}'".format(tag[key]))

    filter_text = ' and '.join(filters) if filters else None

    groups = rcf.resource_groups.list(filter=filter_text)
    return list(groups)


def create_resource_group(cmd, rg_name, location, tags=None):
    """ Create a new resource group.
    :param str resource_group_name:the desired resource group name
    :param str location:the resource group location
    :param str tags:tags in 'a=b c' format
    """
    rcf = _resource_client_factory(cmd.cli_ctx)

    ResourceGroup = cmd.get_models('ResourceGroup')
    parameters = ResourceGroup(
        location=location,
        tags=tags
    )
    return rcf.resource_groups.create_or_update(rg_name, parameters)


def update_resource_group(instance, tags=None):

    if tags is not None:
        instance.tags = tags

    return instance


def export_group_as_template(
        cmd, resource_group_name, include_comments=False, include_parameter_default_value=False):
    """Captures a resource group as a template.
    :param str resource_group_name:the name of the resoruce group.
    :param bool include_comments:export template with comments.
    :param bool include_parameter_default_value: export template parameter with default value.
    """
    rcf = _resource_client_factory(cmd.cli_ctx)

    export_options = []
    if include_comments:
        export_options.append('IncludeComments')
    if include_parameter_default_value:
        export_options.append('IncludeParameterDefaultValue')

    options = ','.join(export_options) if export_options else None

    result = rcf.resource_groups.export_template(resource_group_name, ['*'], options=options)

    print(json.dumps(result.template, indent=2))
    # pylint: disable=no-member
    # On error, server still returns 200, with details in the error attribute
    if result.error:
        error = result.error
        try:
            logger.warning(error.message)
        except AttributeError:
            logger.warning(str(error))
        for detail in getattr(error, 'details', None) or []:
            logger.error(detail.message)


def create_application(cmd, resource_group_name,
                       application_name, managedby_resource_group_id,
                       kind, managedapp_definition_id=None, location=None,
                       plan_name=None, plan_publisher=None, plan_product=None,
                       plan_version=None, tags=None, parameters=None):
    """ Create a new managed application.
    :param str resource_group_name:the desired resource group name
    :param str application_name:the managed application name
    :param str kind:the managed application kind. can be marketplace or servicecatalog
    :param str plan_name:the managed application package plan name
    :param str plan_publisher:the managed application package plan publisher
    :param str plan_product:the managed application package plan product
    :param str plan_version:the managed application package plan version
    :param str tags:tags in 'a=b c' format
    """
    from azure.mgmt.resource.managedapplications.models import Application, Plan
    racf = _resource_managedapps_client_factory(cmd.cli_ctx)
    rcf = _resource_client_factory(cmd.cli_ctx)
    if not location:
        location = rcf.resource_groups.get(resource_group_name).location
    application = Application(
        location=location,
        managed_resource_group_id=managedby_resource_group_id,
        kind=kind,
        tags=tags
    )

    if kind.lower() == 'servicecatalog':
        if managedapp_definition_id:
            application.application_definition_id = managedapp_definition_id
        else:
            raise CLIError('--managedapp-definition-id is required if kind is ServiceCatalog')
    elif kind.lower() == 'marketplace':
        if (plan_name is None and plan_product is None and
                plan_publisher is None and plan_version is None):
            raise CLIError('--plan-name, --plan-product, --plan-publisher and \
            --plan-version are all required if kind is MarketPlace')
        else:
            application.plan = Plan(plan_name, plan_publisher, plan_product, plan_version)

    applicationParameters = None

    if parameters:
        if os.path.exists(parameters):
            applicationParameters = get_file_json(parameters)
        else:
            applicationParameters = shell_safe_json_parse(parameters)

    application.parameters = applicationParameters

    return racf.applications.create_or_update(resource_group_name, application_name, application)


def show_application(cmd, resource_group_name=None, application_name=None):
    """ Gets a managed application.
    :param str resource_group_name:the resource group name
    :param str application_name:the managed application name
    """
    racf = _resource_managedapps_client_factory(cmd.cli_ctx)
    return racf.applications.get(resource_group_name, application_name)


def show_applicationdefinition(cmd, resource_group_name=None, application_definition_name=None):
    """ Gets a managed application definition.
    :param str resource_group_name:the resource group name
    :param str application_definition_name:the managed application definition name
    """
    racf = _resource_managedapps_client_factory(cmd.cli_ctx)
    return racf.application_definitions.get(resource_group_name, application_definition_name)


def create_applicationdefinition(cmd, resource_group_name,
                                 application_definition_name,
                                 lock_level, authorizations,
                                 description, display_name,
                                 package_file_uri=None, create_ui_definition=None,
                                 main_template=None, location=None, tags=None):
    """ Create a new managed application definition.
    :param str resource_group_name:the desired resource group name
    :param str application_definition_name:the managed application definition name
    :param str description:the managed application definition description
    :param str display_name:the managed application definition display name
    :param str package_file_uri:the managed application definition package file uri
    :param str create_ui_definition:the managed application definition create ui definition
    :param str main_template:the managed application definition main template
    :param str tags:tags in 'a=b c' format
    """
    from azure.mgmt.resource.managedapplications.models import ApplicationDefinition, ApplicationProviderAuthorization
    if not package_file_uri and not create_ui_definition and not main_template:
        raise CLIError('usage error: --package-file-uri <url> | --create-ui-definition --main-template')
    elif package_file_uri:
        if create_ui_definition or main_template:
            raise CLIError('usage error: must not specify \
            --create-ui-definition --main-template')
    elif not package_file_uri:
        if not create_ui_definition or not main_template:
            raise CLIError('usage error: must specify \
            --create-ui-definition --main-template')
    racf = _resource_managedapps_client_factory(cmd.cli_ctx)
    rcf = _resource_client_factory(cmd.cli_ctx)
    if not location:
        location = rcf.resource_groups.get(resource_group_name).location
    authorizations = authorizations or []
    applicationAuthList = []

    for name_value in authorizations:
        # split at the first ':', neither principalId nor roldeDefinitionId should have a ':'
        principalId, roleDefinitionId = name_value.split(':', 1)
        applicationAuth = ApplicationProviderAuthorization(
            principal_id=principalId,
            role_definition_id=roleDefinitionId)
        applicationAuthList.append(applicationAuth)

    applicationDef = ApplicationDefinition(lock_level=lock_level,
                                           authorizations=applicationAuthList,
                                           package_file_uri=package_file_uri)
    applicationDef.display_name = display_name
    applicationDef.description = description
    applicationDef.location = location
    applicationDef.package_file_uri = package_file_uri
    applicationDef.create_ui_definition = create_ui_definition
    applicationDef.main_template = main_template
    applicationDef.tags = tags

    return racf.application_definitions.create_or_update(resource_group_name,
                                                         application_definition_name, applicationDef)


def list_applications(cmd, resource_group_name=None):
    racf = _resource_managedapps_client_factory(cmd.cli_ctx)

    if resource_group_name:
        applications = racf.applications.list_by_resource_group(resource_group_name)
    else:
        applications = racf.applications.list_by_subscription()
    return list(applications)


def deploy_arm_template(cmd, resource_group_name,
                        template_file=None, template_uri=None, deployment_name=None,
                        parameters=None, mode=None, rollback_on_error=None, no_wait=False):
    return _deploy_arm_template_core(cmd.cli_ctx, resource_group_name, template_file, template_uri,
                                     deployment_name, parameters, mode, rollback_on_error, no_wait=no_wait)


def deploy_arm_template_at_subscription_scope(cmd, template_file=None, template_uri=None,
                                              deployment_name=None, deployment_location=None,
                                              parameters=None, no_wait=False):
    return _deploy_arm_template_subscription_scope(cmd.cli_ctx, template_file, template_uri,
                                                   deployment_name, deployment_location,
                                                   parameters, 'Incremental', no_wait=no_wait)


def validate_arm_template(cmd, resource_group_name, template_file=None, template_uri=None,
                          parameters=None, mode=None, rollback_on_error=None):
    return _deploy_arm_template_core(cmd.cli_ctx, resource_group_name, template_file, template_uri,
                                     'deployment_dry_run', parameters, mode, rollback_on_error, validate_only=True)


def validate_arm_template_at_subscription_scope(cmd, template_file=None, template_uri=None, deployment_location=None,
                                                parameters=None):
    return _deploy_arm_template_subscription_scope(cmd.cli_ctx, template_file, template_uri,
                                                   'deployment_dry_run', deployment_location,
                                                   parameters,
                                                   'Incremental',
                                                   validate_only=True)


def export_subscription_deployment_template(cmd, deployment_name):
    smc = _resource_client_factory(cmd.cli_ctx)
    result = smc.deployments.export_template_at_subscription_scope(deployment_name)
    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_deployment_as_template(cmd, resource_group_name, deployment_name):
    smc = _resource_client_factory(cmd.cli_ctx)
    result = smc.deployments.export_template(resource_group_name, deployment_name)
    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def create_resource(cmd, properties,
                    resource_group_name=None, resource_provider_namespace=None,
                    parent_resource_path=None, resource_type=None, resource_name=None,
                    resource_id=None, api_version=None, location=None, is_full_object=False):
    res = _ResourceUtils(cmd.cli_ctx, resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version)
    return res.create_resource(properties, location, is_full_object)


def _get_parsed_resource_ids(resource_ids):
    """
    Returns a generator of parsed resource ids. Raise when there is invalid resource id.
    """
    if not resource_ids:
        return None

    for rid in resource_ids:
        if not is_valid_resource_id(rid):
            raise CLIError('az resource: error: argument --ids: invalid ResourceId value: \'%s\'' % rid)

    return (parse_resource_id(rid) for rid in resource_ids)


def _get_rsrc_util_from_parsed_id(cli_ctx, parsed_id, api_version):
    return _ResourceUtils(cli_ctx,
                          parsed_id['resource_group'],
                          parsed_id['resource_namespace'],
                          parsed_id['resource_parent'],
                          parsed_id['resource_type'],
                          parsed_id['resource_name'],
                          None,
                          api_version)


def _create_parsed_id(resource_group_name=None, resource_provider_namespace=None, parent_resource_path=None,
                      resource_type=None, resource_name=None):
    return {
        'resource_group': resource_group_name,
        'resource_namespace': resource_provider_namespace,
        'resource_parent': parent_resource_path,
        'resource_type': resource_type,
        'resource_name': resource_name
    }


def _single_or_collection(obj, default=None):
    if not obj:
        return default

    if isinstance(obj, list) and len(obj) == 1:
        return obj[0]

    return obj


# pylint: unused-argument
def show_resource(cmd, resource_ids=None, resource_group_name=None,
                  resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                  resource_name=None, api_version=None, include_response_body=False):
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version).get_resource(
            include_response_body) for id_dict in parsed_ids])


# pylint: disable=unused-argument
def delete_resource(cmd, resource_ids=None, resource_group_name=None,
                    resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                    resource_name=None, api_version=None):
    """
    Deletes the given resource(s).
    This function allows deletion of ids with dependencies on one another.
    This is done with multiple passes through the given ids.
    """
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]
    to_be_deleted = [(_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version), id_dict)
                     for id_dict in parsed_ids]

    results = []
    from msrestazure.azure_exceptions import CloudError
    while to_be_deleted:
        logger.debug("Start new loop to delete resources.")
        operations = []
        failed_to_delete = []
        for rsrc_utils, id_dict in to_be_deleted:
            try:
                operations.append(rsrc_utils.delete())
                resource = resource_dict_to_id(**id_dict) if id_dict.get("subscription") else resource_name
                logger.debug("deleting %s", resource)
            except CloudError as e:
                # request to delete failed, add parsed id dict back to queue
                id_dict['exception'] = str(e)
                failed_to_delete.append((rsrc_utils, id_dict))
        to_be_deleted = failed_to_delete

        # stop deleting if none deletable
        if not operations:
            break

        # all operations return result before next pass
        for operation in operations:
            results.append(operation.result())

    if to_be_deleted:
        error_msg_builder = ['Some resources failed to be deleted:']
        for _, id_dict in to_be_deleted:
            logger.debug(id_dict['exception'])
            error_msg_builder.append(resource_dict_to_id(**id_dict))
        raise CLIError(os.linesep.join(error_msg_builder))

    return _single_or_collection(results)


# pylint: unused-argument
def update_resource(cmd, parameters, resource_ids=None,
                    resource_group_name=None, resource_provider_namespace=None,
                    parent_resource_path=None, resource_type=None, resource_name=None, api_version=None):
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version).update(parameters) for id_dict in parsed_ids])


# pylint: unused-argument
def tag_resource(cmd, tags, resource_ids=None,
                 resource_group_name=None, resource_provider_namespace=None,
                 parent_resource_path=None, resource_type=None, resource_name=None, api_version=None):
    """ Updates the tags on an existing resource. To clear tags, specify the --tag option
    without anything else. """
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version).tag(tags) for id_dict in parsed_ids])


# pylint: unused-argument
def invoke_resource_action(cmd, action, request_body=None, resource_ids=None,
                           resource_group_name=None, resource_provider_namespace=None,
                           parent_resource_path=None, resource_type=None, resource_name=None,
                           api_version=None):
    """ Invokes the provided action on an existing resource."""
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection([_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version)
                                  .invoke_action(action, request_body) for id_dict in parsed_ids])


def get_deployment_operations(client, resource_group_name, deployment_name, operation_ids):
    """get a deployment's operation."""
    result = []
    for op_id in operation_ids:
        dep = client.get(resource_group_name, deployment_name, op_id)
        result.append(dep)
    return result


def get_deployment_operations_at_subscription_scope(client, deployment_name, operation_ids):
    """get a deployment's operation."""
    result = []
    for op_id in operation_ids:
        dep = client.get_at_subscription_scope(deployment_name, op_id)
        result.append(dep)
    return result


def list_resources(cmd, resource_group_name=None,
                   resource_provider_namespace=None, resource_type=None, name=None, tag=None,
                   location=None):
    rcf = _resource_client_factory(cmd.cli_ctx)

    if resource_group_name is not None:
        rcf.resource_groups.get(resource_group_name)

    odata_filter = _list_resources_odata_filter_builder(resource_group_name,
                                                        resource_provider_namespace,
                                                        resource_type, name, tag, location)
    resources = rcf.resources.list(filter=odata_filter)
    return list(resources)


def register_provider(cmd, resource_provider_namespace, wait=False):
    _update_provider(cmd.cli_ctx, resource_provider_namespace, registering=True, wait=wait)


def unregister_provider(cmd, resource_provider_namespace, wait=False):
    _update_provider(cmd.cli_ctx, resource_provider_namespace, registering=False, wait=wait)


def list_provider_operations(cmd):
    auth_client = _authorization_management_client(cmd.cli_ctx)
    return auth_client.provider_operations_metadata.list()


def show_provider_operations(cmd, resource_provider_namespace):
    auth_client = _authorization_management_client(cmd.cli_ctx)
    return auth_client.provider_operations_metadata.get(resource_provider_namespace)


def move_resource(cmd, ids, destination_group, destination_subscription_id=None):
    """Moves resources from one resource group to another(can be under different subscription)

    :param ids: the space-separated resource ids to be moved
    :param destination_group: the destination resource group name
    :param destination_subscription_id: the destination subscription identifier
    """
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

    rcf = _resource_client_factory(cmd.cli_ctx)
    target = resource_dict_to_id(subscription=(destination_subscription_id or rcf.config.subscription_id),
                                 resource_group=destination_group)

    return rcf.resources.move_resources(resources[0]['resource_group'], ids, target)


def list_features(client, resource_provider_namespace=None):
    if resource_provider_namespace:
        return client.list(resource_provider_namespace=resource_provider_namespace)
    return client.list_all()


def register_feature(client, resource_provider_namespace, feature_name):
    logger.warning("Once the feature '%s' is registered, invoking 'az provider register -n %s' is required "
                   "to get the change propagated", feature_name, resource_provider_namespace)
    return client.register(resource_provider_namespace, feature_name)


# pylint: disable=inconsistent-return-statements
def create_policy_assignment(cmd, policy=None, policy_set_definition=None,
                             name=None, display_name=None, params=None,
                             resource_group_name=None, scope=None, sku=None,
                             not_scopes=None):
    """Creates a policy assignment
    :param not_scopes: Space-separated scopes where the policy assignment does not apply.
    """
    if bool(policy) == bool(policy_set_definition):
        raise CLIError('usage error: --policy NAME_OR_ID | '
                       '--policy-set-definition NAME_OR_ID')
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    scope = _build_policy_scope(policy_client.config.subscription_id,
                                resource_group_name, scope)
    policy_id = _resolve_policy_id(cmd, policy, policy_set_definition, policy_client)

    if params:
        if os.path.exists(params):
            params = get_file_json(params)
        else:
            params = shell_safe_json_parse(params)

    PolicyAssignment = cmd.get_models('PolicyAssignment')
    assignment = PolicyAssignment(display_name=display_name, policy_definition_id=policy_id, scope=scope)
    assignment.parameters = params if params else None

    if cmd.supported_api_version(min_api='2017-06-01-preview'):
        if not_scopes:
            kwargs_list = []
            for id_arg in not_scopes.split(' '):
                if parse_resource_id(id_arg):
                    kwargs_list.append(id_arg)
                else:
                    logger.error('az policy assignment create error: argument --not-scopes: \
                    invalid notscopes value: \'%s\'', id_arg)
                    return
            assignment.not_scopes = kwargs_list
        PolicySku = cmd.get_models('PolicySku')
        policySku = PolicySku(name='A0', tier='Free')
        if sku:
            policySku = policySku if sku.lower() == 'free' else PolicySku(name='A1', tier='Standard')
        assignment.sku = policySku

    return policy_client.policy_assignments.create(scope,
                                                   name or uuid.uuid4(),
                                                   assignment)


def delete_policy_assignment(cmd, name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    scope = _build_policy_scope(policy_client.config.subscription_id,
                                resource_group_name, scope)
    policy_client.policy_assignments.delete(scope, name)


def show_policy_assignment(cmd, name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    scope = _build_policy_scope(policy_client.config.subscription_id,
                                resource_group_name, scope)
    return policy_client.policy_assignments.get(scope, name)


def list_policy_assignment(cmd, disable_scope_strict_match=None, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
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
        parent_resource_path = '' if not id.get('child_name_1') else (id['type'] + '/' + id['name'])
        resource_type = id.get('child_type_1') or id['type']
        resource_name = id.get('child_name_1') or id['name']
        result = policy_client.policy_assignments.list_for_resource(
            id['resource_group'], id['namespace'],
            parent_resource_path, resource_type, resource_name)
    else:
        result = policy_client.policy_assignments.list()

    if not disable_scope_strict_match:
        result = [i for i in result if _scope.lower() == i.scope.lower()]

    return result


def create_policy_definition(cmd, name, rules=None, params=None, display_name=None, description=None, mode=None,
                             metadata=None):
    rules = _load_file_string_or_uri(rules, 'rules')
    params = _load_file_string_or_uri(params, 'params', False)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    PolicyDefinition = cmd.get_models('PolicyDefinition')
    parameters = PolicyDefinition(policy_rule=rules, parameters=params, description=description,
                                  display_name=display_name)
    if cmd.supported_api_version(min_api='2016-12-01'):
        parameters.mode = mode
    if cmd.supported_api_version(min_api='2017-06-01-preview'):
        parameters.metadata = metadata
    return policy_client.policy_definitions.create_or_update(name, parameters)


def create_policy_setdefinition(cmd, name, definitions, params=None, display_name=None, description=None):
    definitions = _load_file_string_or_uri(definitions, 'definitions')
    params = _load_file_string_or_uri(params, 'params', False)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    PolicySetDefinition = cmd.get_models('PolicySetDefinition')
    parameters = PolicySetDefinition(policy_definitions=definitions, parameters=params, description=description,
                                     display_name=display_name)
    return policy_client.policy_set_definitions.create_or_update(name, parameters)


def get_policy_definition(cmd, policy_definition_name):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return _get_custom_or_builtin_policy(cmd, policy_client, policy_definition_name)


def get_policy_setdefinition(cmd, policy_set_definition_name):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return _get_custom_or_builtin_policy(cmd, policy_client, policy_set_definition_name, True)


def update_policy_definition(instance, cmd, policy_definition_name, rules=None, params=None,
                             display_name=None, description=None, metadata=None):
    if rules:
        if os.path.exists(rules):
            rules = get_file_json(rules)
        else:
            rules = shell_safe_json_parse(rules)
        instance.policy_rule = rules

    if params:
        if os.path.exists(params):
            params = get_file_json(params)
        else:
            params = shell_safe_json_parse(params)
        instance.parameters = params

    if display_name is not None:
        instance.display_name = display_name

    if description is not None:
        instance.description = description

    if metadata:
        instance.metadata = metadata

    return instance


def update_policy_setdefinition(cmd, policy_set_definition_name, definitions=None, params=None,
                                display_name=None, description=None):
    if definitions:
        if os.path.exists(definitions):
            definitions = get_file_json(definitions)
        else:
            definitions = shell_safe_json_parse(definitions)

    if params:
        if os.path.exists(params):
            params = get_file_json(params)
        else:
            params = shell_safe_json_parse(params)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    definition = _get_custom_or_builtin_policy(cmd, policy_client, policy_set_definition_name, True)
    # pylint: disable=line-too-long,no-member
    PolicySetDefinition = cmd.get_models('PolicySetDefinition')
    parameters = PolicySetDefinition(
        policy_definitions=definitions if definitions is not None else definition.policy_definitions,
        description=description if description is not None else definition.description,
        display_name=display_name if display_name is not None else definition.display_name,
        parameters=params if params is not None else definition.parameters)
    return policy_client.policy_set_definitions.create_or_update(policy_set_definition_name, parameters)


def _register_rp(cli_ctx, subscription_id=None):
    rp = "Microsoft.Management"
    import time
    rcf = get_mgmt_service_client(
        cli_ctx,
        ResourceType.MGMT_RESOURCE_RESOURCES,
        subscription_id)
    rcf.providers.register(rp)
    while True:
        time.sleep(10)
        rp_info = rcf.providers.get(rp)
        if rp_info.registration_state == 'Registered':
            break


def _get_subscription_id_from_subscription(cli_ctx, subscription):  # pylint: disable=inconsistent-return-statements
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    subscriptions_list = profile.load_cached_subscriptions()
    for sub in subscriptions_list:
        if sub['id'] == subscription or sub['name'] == subscription:
            return sub['id']
    raise CLIError("Subscription not found in the current context.")


def _get_parent_id_from_parent(parent):
    if parent is None or parent.startswith("/providers/Microsoft.Management/managementGroups/"):
        return parent
    return "/providers/Microsoft.Management/managementGroups/" + parent


def cli_managementgroups_group_list(cmd, client):
    _register_rp(cmd.cli_ctx)
    return client.list()


def cli_managementgroups_group_show(
        cmd,
        client,
        group_name,
        expand=False,
        recurse=False):
    _register_rp(cmd.cli_ctx)
    if expand:
        return client.get(group_name, "children", recurse)
    return client.get(group_name)


def cli_managementgroups_group_create(
        cmd,
        client,
        group_name,
        display_name=None,
        parent=None):
    _register_rp(cmd.cli_ctx)
    parent_id = _get_parent_id_from_parent(parent)
    from azure.mgmt.managementgroups.models import (
        CreateManagementGroupRequest, CreateManagementGroupDetails, CreateParentGroupInfo)
    create_parent_grp_info = CreateParentGroupInfo(id=parent_id)
    create_mgmt_grp_details = CreateManagementGroupDetails(parent=create_parent_grp_info)
    create_mgmt_grp_request = CreateManagementGroupRequest(
        name=group_name,
        display_name=display_name,
        details=create_mgmt_grp_details)
    return client.create_or_update(group_name, create_mgmt_grp_request)


def cli_managementgroups_group_update_custom_func(
        instance,
        display_name=None,
        parent_id=None):
    parent_id = _get_parent_id_from_parent(parent_id)
    instance.display_name = display_name
    instance.parent_id = parent_id
    return instance


def cli_managementgroups_group_update_get():
    from azure.mgmt.managementgroups.models import PatchManagementGroupRequest
    update_parameters = PatchManagementGroupRequest(display_name=None, parent_id=None)
    return update_parameters


def cli_managementgroups_group_update_set(
        cmd, client, group_name, parameters=None):
    return client.update(group_name, parameters)


def cli_managementgroups_group_delete(cmd, client, group_name):
    _register_rp(cmd.cli_ctx)
    return client.delete(group_name)


def cli_managementgroups_subscription_add(
        cmd, client, group_name, subscription):
    subscription_id = _get_subscription_id_from_subscription(
        cmd.cli_ctx, subscription)
    _register_rp(cmd.cli_ctx)
    _register_rp(cmd.cli_ctx, subscription_id)
    return client.create(group_name, subscription_id)


def cli_managementgroups_subscription_remove(
        cmd, client, group_name, subscription):
    subscription_id = _get_subscription_id_from_subscription(
        cmd.cli_ctx, subscription)
    _register_rp(cmd.cli_ctx)
    _register_rp(cmd.cli_ctx, subscription_id)
    return client.delete(group_name, subscription_id)


# region Locks


def _validate_lock_params_match_lock(
        lock_client, name, resource_group, resource_provider_namespace, parent_resource_path,
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
        if resource_group != _resource_group:
            raise CLIError(
                'Unexpected --resource-group for lock {}, expected {}'.format(
                    name, _resource_group))
        if _resource_namespace is None or _resource_namespace == 'Microsoft.Authorization':
            return
        if resource_provider_namespace != _resource_namespace:
            raise CLIError(
                'Unexpected --namespace for lock {}, expected {}'.format(name, _resource_namespace))
        if resource.get('child_type_2', None) is None:
            _resource_type = resource.get('type', None)
            _resource_name = resource.get('name', None)
        else:
            _resource_type = resource.get('child_type_1', None)
            _resource_name = resource.get('child_name_1', None)
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


def list_locks(cmd, resource_group=None,
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
    lock_client = _resource_lock_client_factory(cmd.cli_ctx)
    lock_resource = _extract_lock_params(resource_group, resource_provider_namespace,
                                         resource_type, resource_name)
    resource_group = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    if resource_group is None:
        return lock_client.management_locks.list_at_subscription_level(filter=filter_string)
    if resource_name is None:
        return lock_client.management_locks.list_at_resource_group_level(
            resource_group, filter=filter_string)
    return lock_client.management_locks.list_at_resource_level(
        resource_group, resource_provider_namespace, parent_resource_path or '', resource_type,
        resource_name, filter=filter_string)


# pylint: disable=inconsistent-return-statements
def get_lock(cmd, lock_name=None, resource_group=None, resource_provider_namespace=None,
             parent_resource_path=None, resource_type=None, resource_name=None, ids=None):
    """
    :param name: The name of the lock.
    :type name: str
    """
    if ids:
        kwargs_list = []
        for id_arg in ids:
            try:
                kwargs_list.append(_parse_lock_id(id_arg))
            except AttributeError:
                logger.error('az lock show: error: argument --ids: invalid ResourceId value: \'%s\'', id_arg)
                return
        results = [get_lock(cmd, **kwargs) for kwargs in kwargs_list]
        return results[0] if len(results) == 1 else results

    lock_client = _resource_lock_client_factory(cmd.cli_ctx)

    lock_resource = _extract_lock_params(resource_group, resource_provider_namespace,
                                         resource_type, resource_name)

    resource_group = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    _validate_lock_params_match_lock(lock_client, lock_name, resource_group,
                                     resource_provider_namespace, parent_resource_path,
                                     resource_type, resource_name)

    if resource_group is None:
        return _call_subscription_get(cmd, lock_client, lock_name)
    if resource_name is None:
        return lock_client.management_locks.get_at_resource_group_level(resource_group, lock_name)
    if cmd.supported_api_version(max_api='2015-01-01'):
        lock_list = list_locks(resource_group, resource_provider_namespace, parent_resource_path,
                               resource_type, resource_name)
        return next((lock for lock in lock_list if lock.name == lock_name), None)
    return lock_client.management_locks.get_at_resource_level(
        resource_group, resource_provider_namespace,
        parent_resource_path or '', resource_type, resource_name, lock_name)


# pylint: disable=inconsistent-return-statements
def delete_lock(cmd, lock_name=None, resource_group=None, resource_provider_namespace=None,
                parent_resource_path=None, resource_type=None, resource_name=None, ids=None):
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
    if ids:
        kwargs_list = []
        for id_arg in ids:
            try:
                kwargs_list.append(_parse_lock_id(id_arg))
            except AttributeError:
                logger.error('az lock delete: error: argument --ids: invalid ResourceId value: \'%s\'', id_arg)
                return
        results = [delete_lock(cmd, **kwargs) for kwargs in kwargs_list]
        return results[0] if len(results) == 1 else results

    lock_client = _resource_lock_client_factory(cmd.cli_ctx)
    lock_resource = _extract_lock_params(resource_group, resource_provider_namespace,
                                         resource_type, resource_name)
    resource_group = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    _validate_lock_params_match_lock(lock_client, lock_name, resource_group,
                                     resource_provider_namespace, parent_resource_path,
                                     resource_type, resource_name)

    if resource_group is None:
        return lock_client.management_locks.delete_at_subscription_level(lock_name)
    if resource_name is None:
        return lock_client.management_locks.delete_at_resource_group_level(
            resource_group, lock_name)
    return lock_client.management_locks.delete_at_resource_level(
        resource_group, resource_provider_namespace, parent_resource_path or '', resource_type,
        resource_name, lock_name)


def create_lock(cmd, lock_name, level,
                resource_group=None, resource_provider_namespace=None, notes=None,
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
    :param notes: Notes about this lock.
    :type notes: str
    """
    parameters = ManagementLockObject(level=level, notes=notes, name=lock_name)

    lock_client = _resource_lock_client_factory(cmd.cli_ctx)
    lock_resource = _extract_lock_params(resource_group, resource_provider_namespace,
                                         resource_type, resource_name)
    resource_group = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    if resource_group is None:
        return lock_client.management_locks.create_or_update_at_subscription_level(lock_name, parameters)

    if resource_name is None:
        return lock_client.management_locks.create_or_update_at_resource_group_level(
            resource_group, lock_name, parameters)

    return lock_client.management_locks.create_or_update_at_resource_level(
        resource_group, resource_provider_namespace, parent_resource_path or '', resource_type,
        resource_name, lock_name, parameters)


# pylint: disable=inconsistent-return-statements
def update_lock(cmd, lock_name=None, resource_group=None, resource_provider_namespace=None, notes=None,
                parent_resource_path=None, resource_type=None, resource_name=None, level=None, ids=None):
    """
    Allows updates to the lock-type(level) and the notes of the lock
    """
    if ids:
        kwargs_list = []
        for id_arg in ids:
            try:
                kwargs_list.append(_parse_lock_id(id_arg))
            except AttributeError:
                logger.error('az lock update: error: argument --ids: invalid ResourceId value: \'%s\'', id_arg)
                return
        results = [update_lock(cmd, level=level, notes=notes, **kwargs) for kwargs in kwargs_list]
        return results[0] if len(results) == 1 else results

    lock_client = _resource_lock_client_factory(cmd.cli_ctx)

    lock_resource = _extract_lock_params(resource_group, resource_provider_namespace,
                                         resource_type, resource_name)

    resource_group = lock_resource[0]
    resource_name = lock_resource[1]
    resource_provider_namespace = lock_resource[2]
    resource_type = lock_resource[3]

    _validate_lock_params_match_lock(lock_client, lock_name, resource_group, resource_provider_namespace,
                                     parent_resource_path, resource_type, resource_name)

    if resource_group is None:
        params = _call_subscription_get(cmd, lock_client, lock_name)
        _update_lock_parameters(params, level, notes)
        return lock_client.management_locks.create_or_update_at_subscription_level(lock_name, params)
    if resource_name is None:
        params = lock_client.management_locks.get_at_resource_group_level(resource_group, lock_name)
        _update_lock_parameters(params, level, notes)
        return lock_client.management_locks.create_or_update_at_resource_group_level(
            resource_group, lock_name, params)
    if cmd.supported_api_version(max_api='2015-01-01'):
        lock_list = list_locks(resource_group, resource_provider_namespace, parent_resource_path,
                               resource_type, resource_name)
        return next((lock for lock in lock_list if lock.name == lock_name), None)
    else:
        params = lock_client.management_locks.get_at_resource_level(
            resource_group, resource_provider_namespace, parent_resource_path or '', resource_type,
            resource_name, lock_name)
    _update_lock_parameters(params, level, notes)
    return lock_client.management_locks.create_or_update_at_resource_level(
        resource_group, resource_provider_namespace, parent_resource_path or '', resource_type,
        resource_name, lock_name, params)

# endregion

# region ResourceLinks


def create_resource_link(cmd, link_id, target_id, notes=None):
    """
    :param target_id: The id of the resource link target.
    :type target_id: str
    :param notes: Notes for this link.
    :type notes: str
    """
    links_client = _resource_links_client_factory(cmd.cli_ctx).resource_links
    properties = ResourceLinkProperties(target_id, notes)
    links_client.create_or_update(link_id, properties)


def update_resource_link(cmd, link_id, target_id=None, notes=None):
    """
    :param target_id: The id of the resource link target.
    :type target_id: str
    :param notes: Notes for this link.
    :type notes: str
    """
    links_client = _resource_links_client_factory(cmd.cli_ctx).resource_links
    params = links_client.get(link_id)
    properties = ResourceLinkProperties(
        target_id if target_id is not None else params.properties.target_id,
        # pylint: disable=no-member
        notes=notes if notes is not None else params.properties.notes)  # pylint: disable=no-member
    links_client.create_or_update(link_id, properties)


def list_resource_links(cmd, scope=None, filter_string=None):
    """
    :param scope: The scope for the links
    :type scope: str
    :param filter_string: A filter for restricting the results
    :type filter_string: str
    """
    links_client = _resource_links_client_factory(cmd.cli_ctx).resource_links
    if scope is not None:
        return links_client.list_at_source_scope(scope, filter=filter_string)
    return links_client.list_at_subscription(filter=filter_string)

# endregion


class _ResourceUtils(object):  # pylint: disable=too-many-instance-attributes
    def __init__(self, cli_ctx,
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

        self.rcf = rcf or _resource_client_factory(cli_ctx)
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
        self.parent_resource_path = parent_resource_path if parent_resource_path else ''
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
                                                           self.parent_resource_path,
                                                           self.resource_type,
                                                           self.resource_name,
                                                           self.api_version,
                                                           res)
        return resource

    def get_resource(self, include_response_body=False):
        if self.resource_id:
            resource = self.rcf.resources.get_by_id(self.resource_id, self.api_version, raw=include_response_body)
        else:
            resource = self.rcf.resources.get(self.resource_group_name,
                                              self.resource_provider_namespace,
                                              self.parent_resource_path,
                                              self.resource_type,
                                              self.resource_name,
                                              self.api_version,
                                              raw=include_response_body)
        if include_response_body:
            temp = resource.output
            setattr(temp, 'response_body', json.loads(resource.response.content.decode()))
            resource = temp
        return resource

    def delete(self):
        if self.resource_id:
            return self.rcf.resources.delete_by_id(self.resource_id, self.api_version)
        return self.rcf.resources.delete(self.resource_group_name,
                                         self.resource_provider_namespace,
                                         self.parent_resource_path,
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
                                                   self.parent_resource_path,
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
                                                   self.parent_resource_path,
                                                   self.resource_type,
                                                   self.resource_name,
                                                   self.api_version,
                                                   parameters)

    def invoke_action(self, action, request_body):
        """
        Formats Url if none provided and sends the POST request with the url and request-body.
        """
        from msrestazure.azure_operation import AzureOperationPoller
        query_parameters = {}
        serialize = self.rcf.resources._serialize  # pylint: disable=protected-access
        client = self.rcf.resources._client  # pylint: disable=protected-access

        url = '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/' \
            '{resourceProviderNamespace}/{parentResourcePath}/{resourceType}/{resourceName}/{action}'

        url = client.format_url(
            url,
            resourceGroupName=serialize.url(
                "resource_group_name", self.resource_group_name, 'str',
                max_length=90, min_length=1, pattern=r'^[-\w\._\(\)]+$'),
            resourceProviderNamespace=serialize.url(
                "resource_provider_namespace", self.resource_provider_namespace, 'str'),
            parentResourcePath=serialize.url(
                "parent_resource_path", self.parent_resource_path, 'str', skip_quote=True),
            resourceType=serialize.url("resource_type", self.resource_type, 'str', skip_quote=True),
            resourceName=serialize.url("resource_name", self.resource_name, 'str'),
            subscriptionId=serialize.url(
                "self.config.subscription_id", self.rcf.resources.config.subscription_id, 'str'),
            action=serialize.url("action", action, 'str'))

        # Construct parameters
        query_parameters['api-version'] = serialize.query("api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if self.rcf.resources.config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid4())
        if self.rcf.resources.config.accept_language is not None:
            header_parameters['accept-language'] = serialize.header(
                "self.config.accept_language", self.rcf.resources.config.accept_language, 'str')

        # Construct and send request
        def long_running_send():
            request = client.post(url, query_parameters)
            return client.send(
                request, header_parameters, json.loads(request_body) if request_body else None)

        def get_long_running_status(status_link, headers=None):
            request = client.get(status_link)
            if headers:
                request.headers.update(headers)
            return client.send(request, header_parameters)

        def get_long_running_output(response):
            from msrestazure.azure_exceptions import CloudError
            if response.status_code not in [200, 202, 204]:
                exp = CloudError(response)
                exp.request_id = response.headers.get('x-ms-request-id')
                raise exp
            return response.text

        return AzureOperationPoller(long_running_send, get_long_running_output, get_long_running_status,
                                    self.rcf.resources.config.long_running_operation_timeout)

    @staticmethod
    def resolve_api_version(rcf, resource_provider_namespace, parent_resource_path, resource_type):
        provider = rcf.providers.get(resource_provider_namespace)

        # If available, we will use parent resource's api-version
        resource_type_str = (parent_resource_path.split('/')[0] if parent_resource_path else resource_type)

        rt = [t for t in provider.resource_types
              if t.resource_type.lower() == resource_type_str.lower()]
        if not rt:
            raise IncorrectUsageError('Resource type {} not found.'.format(resource_type_str))
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
        namespace = parts.get('child_namespace_1', parts['namespace'])
        if parts.get('child_type_2'):
            parent = (parts['type'] + '/' + parts['name'] + '/' +
                      parts['child_type_1'] + '/' + parts['child_name_1'])
            resource_type = parts['child_type_2']
        elif parts.get('child_type_1'):
            # if the child resource has a provider namespace it is independent of the
            # parent, so set the parent to empty
            if parts.get('child_namespace_1') is not None:
                parent = ''
            else:
                parent = parts['type'] + '/' + parts['name']
            resource_type = parts['child_type_1']
        else:
            parent = None
            resource_type = parts['type']

        return _ResourceUtils.resolve_api_version(rcf, namespace, parent, resource_type)
