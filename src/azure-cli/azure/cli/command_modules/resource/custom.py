# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=line-too-long

from collections import OrderedDict
import codecs
import json
import os
import platform
import re
import ssl
import sys
import uuid
import base64

from urllib.request import urlopen
from urllib.parse import urlparse

from msrestazure.tools import is_valid_resource_id, parse_resource_id

from azure.mgmt.resource.resources.models import GenericResource, DeploymentMode

from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError, RequiredArgumentMissingError
from azure.cli.core.parser import IncorrectUsageError
from azure.cli.core.util import get_file_json, read_file_content, shell_safe_json_parse, sdk_no_wait
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import raise_subdivision_deployment_error
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.profiles import ResourceType, get_sdk, get_api_version, AZURE_API_PROFILES

from azure.cli.command_modules.resource._client_factory import (
    _resource_client_factory, _resource_policy_client_factory, _resource_lock_client_factory,
    _resource_links_client_factory, _resource_deploymentscripts_client_factory, _authorization_management_client, _resource_managedapps_client_factory, _resource_templatespecs_client_factory, _resource_privatelinks_client_factory)
from azure.cli.command_modules.resource._validators import _parse_lock_id

from azure.core.pipeline.policies import SansIOHTTPPolicy

from knack.log import get_logger
from knack.prompting import prompt, prompt_pass, prompt_t_f, prompt_choice_list, prompt_int, NoTTYException
from knack.util import CLIError

from ._validators import MSI_LOCAL_ID
from ._formatters import format_what_if_operation_result
from ._bicep import (
    run_bicep_command,
    is_bicep_file,
    ensure_bicep_installation,
    remove_bicep_installation,
    get_bicep_latest_release_tag,
    get_bicep_available_release_tags,
    validate_bicep_target_scope,
    bicep_version_greater_than_or_equal_to
)

from ._utils import _build_preflight_error_message, _build_http_response_error_message

logger = get_logger(__name__)

RPAAS_APIS = {'microsoft.datadog': '/subscriptions/{subscriptionId}/providers/Microsoft.Datadog/agreements/default?api-version=2020-02-01-preview',
              'microsoft.confluent': '/subscriptions/{subscriptionId}/providers/Microsoft.Confluent/agreements/default?api-version=2020-03-01-preview'}


def _build_resource_id(**kwargs):
    from msrestazure.tools import resource_id as resource_id_from_dict
    try:
        return resource_id_from_dict(**kwargs)
    except KeyError:
        return None


def _process_parameters(template_param_defs, parameter_lists):  # pylint: disable=too-many-statements

    def _try_parse_json_object(value):
        try:
            parsed = _remove_comments_from_json(value, False)
            return parsed.get('parameters', parsed)
        except Exception:  # pylint: disable=broad-except
            return None

    def _try_load_file_object(file_path):
        try:
            is_file = os.path.isfile(file_path)
        except ValueError:
            return None
        if is_file is True:
            try:
                content = read_file_content(file_path)
                if not content:
                    return None
                parsed = _remove_comments_from_json(content, False, file_path)
                return parsed.get('parameters', parsed)
            except Exception as ex:
                raise CLIError("Failed to parse {} with exception:\n    {}".format(file_path, ex))
        return None

    def _try_load_uri(uri):
        if "://" in uri:
            try:
                value = _urlretrieve(uri).decode('utf-8')
                parsed = _remove_comments_from_json(value, False)
                return parsed.get('parameters', parsed)
            except Exception:  # pylint: disable=broad-except
                pass
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
        if param_type in ['object', 'array', 'secureobject']:
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
            param_obj = _try_load_file_object(item)
            if param_obj is None:
                param_obj = _try_parse_json_object(item)
            if param_obj is None:
                param_obj = _try_load_uri(item)
            if param_obj is not None:
                parameters.update(param_obj)
            elif not _try_parse_key_value_object(template_param_defs, parameters, item):
                raise CLIError('Unable to parse parameter: {}'.format(item))

    return parameters


# pylint: disable=redefined-outer-name
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
        param_type = param.get('type', 'string').lower()
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
            if param_type == 'securestring':
                try:
                    value = prompt_pass(prompt_str, help_string=description)
                except NoTTYException:
                    value = None
                    no_tty = True
                result[param_name] = value
                break
            if param_type == 'int':
                try:
                    int_value = prompt_int(prompt_str, help_string=description)
                    result[param_name] = int_value
                except NoTTYException:
                    result[param_name] = 0
                    no_tty = True
                break
            if param_type == 'bool':
                try:
                    value = prompt_t_f(prompt_str, help_string=description)
                    result[param_name] = value
                except NoTTYException:
                    result[param_name] = False
                    no_tty = True
                break
            if param_type in ['object', 'array']:
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

            try:
                result[param_name] = prompt(prompt_str, help_string=description)
            except NoTTYException:
                result[param_name] = None
                no_tty = True
            break
    if no_tty and fail_on_no_tty:
        raise NoTTYException
    return result


# pylint: disable=redefined-outer-name
def _get_missing_parameters(parameters, template, prompt_fn, no_prompt=False):
    missing = _find_missing_parameters(parameters, template)
    if missing:
        if no_prompt is True:
            logger.warning("Missing input parameters: %s ", ', '.join(sorted(missing.keys())))
        else:
            try:
                prompt_parameters = prompt_fn(missing)
                for param_name in prompt_parameters:
                    parameters[param_name] = {
                        "value": prompt_parameters[param_name]
                    }
            except NoTTYException:
                raise CLIError("Missing input parameters: {}".format(', '.join(sorted(missing.keys()))))
    return parameters


def _ssl_context():
    if sys.version_info < (3, 4):
        return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url):
    try:
        req = urlopen(url, context=_ssl_context())
        return req.read()
    except Exception:  # pylint: disable=broad-except
        raise CLIError('Unable to retrieve url {}'.format(url))


# pylint: disable=redefined-outer-name
def _remove_comments_from_json(template, preserve_order=True, file_path=None):
    from ._json_handler import json_min

    # When commenting at the bottom of all elements in a JSON object, jsmin has a bug that will wrap lines.
    # It will affect the subsequent multi-line processing logic, so remove those comments in advance here.
    # Related issue: https://github.com/Azure/azure-cli/issues/11995, the sample is in the additional context of it.
    template = re.sub(r'(^[\t ]*//[\s\S]*?\n)|(^[\t ]*/\*{1,2}[\s\S]*?\*/)', '', template, flags=re.M)

    # In order to solve the package conflict introduced by jsmin, the jsmin code is referenced into json_min
    minified = json_min(template)
    try:
        return shell_safe_json_parse(minified, preserve_order, strict=False)  # use strict=False to allow multiline strings
    except CLIError:
        # Because the processing of removing comments and compression will lead to misplacement of error location,
        # so the error message should be wrapped.
        if file_path:
            raise CLIError("Failed to parse '{}', please check whether it is a valid JSON format".format(file_path))
        raise CLIError("Failed to parse the JSON data, please check whether it is a valid JSON format")


# pylint: disable=too-many-locals, too-many-statements, too-few-public-methods
def _deploy_arm_template_core_unmodified(cmd, resource_group_name, template_file=None,
                                         template_uri=None, deployment_name=None, parameters=None,
                                         mode=None, rollback_on_error=None, validate_only=False, no_wait=False,
                                         aux_subscriptions=None, aux_tenants=None, no_prompt=False):
    DeploymentProperties, TemplateLink, OnErrorDeployment = cmd.get_models('DeploymentProperties', 'TemplateLink',
                                                                           'OnErrorDeployment')
    template_link = None
    template_obj = None
    on_error_deployment = None
    template_content = None
    if template_uri:
        template_link = TemplateLink(uri=template_uri)
        template_obj = _remove_comments_from_json(_urlretrieve(template_uri).decode('utf-8'), file_path=template_uri)
    else:
        template_content = (
            run_bicep_command(["build", "--stdout", template_file])
            if is_bicep_file(template_file)
            else read_file_content(template_file)
        )
        template_obj = _remove_comments_from_json(template_content, file_path=template_file)

    if rollback_on_error == '':
        on_error_deployment = OnErrorDeployment(type='LastSuccessful')
    elif rollback_on_error:
        on_error_deployment = OnErrorDeployment(type='SpecificDeployment', deployment_name=rollback_on_error)

    template_param_defs = template_obj.get('parameters', {})
    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(template_param_defs, parameters) or {}
    parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters, no_prompt)

    parameters = json.loads(json.dumps(parameters))

    properties = DeploymentProperties(template=template_content, template_link=template_link,
                                      parameters=parameters, mode=mode, on_error_deployment=on_error_deployment)

    smc = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                  aux_subscriptions=aux_subscriptions, aux_tenants=aux_tenants)

    deployment_client = smc.deployments  # This solves the multi-api for you

    if not template_uri:
        # Plug this as default HTTP pipeline
        # pylint: disable=protected-access
        from azure.core.pipeline import Pipeline
        smc._client._pipeline._impl_policies.append(JsonCTemplatePolicy())
        # Because JsonCTemplatePolicy needs to be wrapped as _SansIOHTTPPolicyRunner, so a new Pipeline is built
        smc._client._pipeline = Pipeline(
            policies=smc._client._pipeline._impl_policies,
            transport=smc._client._pipeline._transport
        )

    from azure.core.exceptions import HttpResponseError
    Deployment = cmd.get_models('Deployment')
    deployment = Deployment(properties=properties)
    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        try:
            validation_poller = deployment_client.begin_validate(resource_group_name, deployment_name, deployment)
        except HttpResponseError as err:
            err_message = _build_http_response_error_message(err)
            raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
        validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)
    else:
        validation_result = deployment_client.validate(resource_group_name, deployment_name, deployment)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)
    if validate_only:
        return validation_result

    return sdk_no_wait(no_wait, deployment_client.begin_create_or_update, resource_group_name, deployment_name,
                       deployment)


class JsonCTemplatePolicy(SansIOHTTPPolicy):

    # Obtain the template data and then splice it with other properties into the JSONC format
    def on_request(self, request):
        http_request = request.http_request
        request_data = getattr(http_request, 'data', {}) or {}
        if not request_data:
            return

        # In the case of retry, because the first request has been processed and
        # converted the type of "request.http_request.data" from string to bytes,
        # so there is no need to process request object again during retry
        if isinstance(request_data, bytes):
            return

        # 'request_data' has been dumped into JSON string in set_json_body() when building HttpRequest in Python SDK.
        # In order to facilitate subsequent parsing, it is converted into a dict first
        http_request.data = json.loads(request_data)

        if http_request.data.get('properties', {}).get('template'):
            template = http_request.data["properties"]["template"]
            del http_request.data["properties"]["template"]

            # templateLink nad template cannot exist at the same time in deployment_dry_run mode
            if "templateLink" in http_request.data["properties"].keys():
                del http_request.data["properties"]["templateLink"]

            # The 'template' and other properties (such as 'parameters','mode'...) are spliced and encoded into the UTF-8 bytes as the request data
            # The format of the request data is: {"properties": {"parameters": {...}, "mode": "Incremental", template:{\r\n  "$schema": "...",\r\n  "contentVersion": "...",\r\n  "parameters": {...}}}
            # This is not an ordinary JSON format, but it is a JSONC format that service can deserialize
            # If not do this splicing, the request data generated by default serialization cannot be deserialized on the service side.
            # Because the service cannot deserialize the template element: "template": "{\r\n  \"$schema\": \"...\",\r\n  \"contentVersion\": \"...\",\r\n  \"parameters\": {...}}"
            partial_request = json.dumps(http_request.data)
            http_request.data = partial_request[:-2] + ", template:" + template + r"}}"
            http_request.data = http_request.data.encode('utf-8')


# pylint: disable=unused-argument
def deploy_arm_template_at_subscription_scope(cmd,
                                              template_file=None, template_uri=None, parameters=None,
                                              deployment_name=None, deployment_location=None,
                                              no_wait=False, handle_extended_json_format=None, no_prompt=False,
                                              confirm_with_what_if=None, what_if_result_format=None,
                                              what_if_exclude_change_types=None, template_spec=None, query_string=None,
                                              what_if=None, proceed_if_no_change=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_subscription_scope_core(cmd,
                                                                                 template_file=template_file, template_uri=template_uri,
                                                                                 parameters=parameters, deployment_name=deployment_name,
                                                                                 deployment_location=deployment_location,
                                                                                 result_format=what_if_result_format,
                                                                                 exclude_change_types=what_if_exclude_change_types,
                                                                                 no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                                 return_result=True)
        if what_if:
            return None

        ChangeType = cmd.get_models('ChangeType')
        has_change = any(change.change_type not in [ChangeType.no_change, ChangeType.ignore] for change in what_if_result.changes)

        if not proceed_if_no_change or has_change:
            from knack.prompting import prompt_y_n

            if not prompt_y_n("\nAre you sure you want to execute the deployment?"):
                return None

    return _deploy_arm_template_at_subscription_scope(cmd=cmd,
                                                      template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                      deployment_name=deployment_name, deployment_location=deployment_location,
                                                      validate_only=False, no_wait=no_wait,
                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


# pylint: disable=unused-argument
def validate_arm_template_at_subscription_scope(cmd,
                                                template_file=None, template_uri=None, parameters=None,
                                                deployment_name=None, deployment_location=None,
                                                no_wait=False, handle_extended_json_format=None,
                                                no_prompt=False, template_spec=None, query_string=None):
    return _deploy_arm_template_at_subscription_scope(cmd=cmd,
                                                      template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                      deployment_name=deployment_name, deployment_location=deployment_location,
                                                      validate_only=True, no_wait=no_wait,
                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,)


def _deploy_arm_template_at_subscription_scope(cmd,
                                               template_file=None, template_uri=None, parameters=None,
                                               deployment_name=None, deployment_location=None, validate_only=False,
                                               no_wait=False, no_prompt=False, template_spec=None, query_string=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'subscription', template_file=template_file,
                                                                      template_uri=template_uri, parameters=parameters,
                                                                      mode='Incremental',
                                                                      no_prompt=no_prompt,
                                                                      template_spec=template_spec, query_string=query_string)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))

    from azure.core.exceptions import HttpResponseError
    Deployment = cmd.get_models('Deployment')
    deployment = Deployment(properties=deployment_properties, location=deployment_location)
    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        try:
            validation_poller = mgmt_client.begin_validate_at_subscription_scope(deployment_name, deployment)
        except HttpResponseError as err:
            err_message = _build_http_response_error_message(err)
            raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
        validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)
    else:
        validation_result = mgmt_client.validate_at_subscription_scope(deployment_name, deployment)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)
    if validate_only:
        return validation_result

    return sdk_no_wait(no_wait, mgmt_client.begin_create_or_update_at_subscription_scope, deployment_name, deployment)


# pylint: disable=unused-argument
def deploy_arm_template_at_resource_group(cmd,
                                          resource_group_name=None,
                                          template_file=None, template_uri=None, parameters=None,
                                          deployment_name=None, mode=None, rollback_on_error=None,
                                          no_wait=False, handle_extended_json_format=None,
                                          aux_subscriptions=None, aux_tenants=None, no_prompt=False,
                                          confirm_with_what_if=None, what_if_result_format=None,
                                          what_if_exclude_change_types=None, template_spec=None, query_string=None,
                                          what_if=None, proceed_if_no_change=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_resource_group_core(cmd,
                                                                             resource_group_name=resource_group_name,
                                                                             template_file=template_file, template_uri=template_uri,
                                                                             parameters=parameters, deployment_name=deployment_name, mode=mode,
                                                                             aux_tenants=aux_tenants, result_format=what_if_result_format,
                                                                             exclude_change_types=what_if_exclude_change_types,
                                                                             no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                             return_result=True)
        if what_if:
            return None

        ChangeType = cmd.get_models('ChangeType')
        has_change = any(change.change_type not in [ChangeType.no_change, ChangeType.ignore] for change in what_if_result.changes)

        if not proceed_if_no_change or has_change:
            from knack.prompting import prompt_y_n

            if not prompt_y_n("\nAre you sure you want to execute the deployment?"):
                return None

    return _deploy_arm_template_at_resource_group(cmd=cmd,
                                                  resource_group_name=resource_group_name,
                                                  template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                  deployment_name=deployment_name, mode=mode, rollback_on_error=rollback_on_error,
                                                  validate_only=False, no_wait=no_wait,
                                                  aux_subscriptions=aux_subscriptions, aux_tenants=aux_tenants,
                                                  no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


# pylint: disable=unused-argument
def validate_arm_template_at_resource_group(cmd,
                                            resource_group_name=None,
                                            template_file=None, template_uri=None, parameters=None,
                                            deployment_name=None, mode=None, rollback_on_error=None,
                                            no_wait=False, handle_extended_json_format=None, no_prompt=False, template_spec=None, query_string=None):
    return _deploy_arm_template_at_resource_group(cmd,
                                                  resource_group_name=resource_group_name,
                                                  template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                  deployment_name=deployment_name, mode=mode, rollback_on_error=rollback_on_error,
                                                  validate_only=True, no_wait=no_wait,
                                                  no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


def _deploy_arm_template_at_resource_group(cmd,
                                           resource_group_name=None,
                                           template_file=None, template_uri=None, parameters=None,
                                           deployment_name=None, mode=None, rollback_on_error=None,
                                           validate_only=False, no_wait=False,
                                           aux_subscriptions=None, aux_tenants=None, no_prompt=False, template_spec=None, query_string=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'resourceGroup', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode=mode,
                                                                      rollback_on_error=rollback_on_error,
                                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, aux_subscriptions=aux_subscriptions,
                                                    aux_tenants=aux_tenants, plug_pipeline=(template_uri is None and template_spec is None))

    from azure.core.exceptions import HttpResponseError
    Deployment = cmd.get_models('Deployment')
    deployment = Deployment(properties=deployment_properties)
    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        try:
            validation_poller = mgmt_client.begin_validate(resource_group_name, deployment_name, deployment)
        except HttpResponseError as err:
            err_message = _build_http_response_error_message(err)
            raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
        validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)
    else:
        validation_result = mgmt_client.validate(resource_group_name, deployment_name, deployment)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)
    if validate_only:
        return validation_result

    return sdk_no_wait(no_wait, mgmt_client.begin_create_or_update, resource_group_name, deployment_name, deployment)


# pylint: disable=unused-argument
def deploy_arm_template_at_management_group(cmd,
                                            management_group_id=None,
                                            template_file=None, template_uri=None, parameters=None,
                                            deployment_name=None, deployment_location=None,
                                            no_wait=False, handle_extended_json_format=None, no_prompt=False,
                                            confirm_with_what_if=None, what_if_result_format=None,
                                            what_if_exclude_change_types=None, template_spec=None, query_string=None,
                                            what_if=None, proceed_if_no_change=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_management_group_core(cmd,
                                                                               management_group_id=management_group_id,
                                                                               template_file=template_file, template_uri=template_uri,
                                                                               parameters=parameters, deployment_name=deployment_name,
                                                                               deployment_location=deployment_location,
                                                                               result_format=what_if_result_format,
                                                                               exclude_change_types=what_if_exclude_change_types,
                                                                               no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                               return_result=True)
        if what_if:
            return None

        ChangeType = cmd.get_models('ChangeType')
        has_change = any(change.change_type not in [ChangeType.no_change, ChangeType.ignore] for change in what_if_result.changes)

        if not proceed_if_no_change or has_change:
            from knack.prompting import prompt_y_n

            if not prompt_y_n("\nAre you sure you want to execute the deployment?"):
                return None

    return _deploy_arm_template_at_management_group(cmd=cmd,
                                                    management_group_id=management_group_id,
                                                    template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                    deployment_name=deployment_name, deployment_location=deployment_location,
                                                    validate_only=False, no_wait=no_wait,
                                                    no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


# pylint: disable=unused-argument
def validate_arm_template_at_management_group(cmd,
                                              management_group_id=None,
                                              template_file=None, template_uri=None, parameters=None,
                                              deployment_name=None, deployment_location=None,
                                              no_wait=False, handle_extended_json_format=None,
                                              no_prompt=False, template_spec=None, query_string=None):
    return _deploy_arm_template_at_management_group(cmd=cmd,
                                                    management_group_id=management_group_id,
                                                    template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                    deployment_name=deployment_name, deployment_location=deployment_location,
                                                    validate_only=True, no_wait=no_wait,
                                                    no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


def _deploy_arm_template_at_management_group(cmd,
                                             management_group_id=None,
                                             template_file=None, template_uri=None, parameters=None,
                                             deployment_name=None, deployment_location=None, validate_only=False,
                                             no_wait=False, no_prompt=False, template_spec=None, query_string=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'managementGroup', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode='Incremental',
                                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))

    from azure.core.exceptions import HttpResponseError
    ScopedDeployment = cmd.get_models('ScopedDeployment')
    deployment = ScopedDeployment(properties=deployment_properties, location=deployment_location)
    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        try:
            validation_poller = mgmt_client.begin_validate_at_management_group_scope(management_group_id,
                                                                                     deployment_name, deployment)
        except HttpResponseError as err:
            err_message = _build_http_response_error_message(err)
            raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
        validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)
    else:
        validation_result = mgmt_client.validate_at_management_group_scope(management_group_id, deployment_name,
                                                                           deployment)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)
    if validate_only:
        return validation_result

    return sdk_no_wait(no_wait, mgmt_client.begin_create_or_update_at_management_group_scope, management_group_id,
                       deployment_name, deployment)


# pylint: disable=unused-argument
def deploy_arm_template_at_tenant_scope(cmd,
                                        template_file=None, template_uri=None, parameters=None,
                                        deployment_name=None, deployment_location=None,
                                        no_wait=False, handle_extended_json_format=None, no_prompt=False,
                                        confirm_with_what_if=None, what_if_result_format=None,
                                        what_if_exclude_change_types=None, template_spec=None, query_string=None,
                                        what_if=None, proceed_if_no_change=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_tenant_scope_core(cmd,
                                                                           template_file=template_file, template_uri=template_uri,
                                                                           parameters=parameters, deployment_name=deployment_name,
                                                                           deployment_location=deployment_location,
                                                                           result_format=what_if_result_format,
                                                                           exclude_change_types=what_if_exclude_change_types,
                                                                           no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                           return_result=True)
        if what_if:
            return None

        ChangeType = cmd.get_models('ChangeType')
        has_change = any(change.change_type not in [ChangeType.no_change, ChangeType.ignore] for change in what_if_result.changes)

        if not proceed_if_no_change or has_change:
            from knack.prompting import prompt_y_n

            if not prompt_y_n("\nAre you sure you want to execute the deployment?"):
                return None

    return _deploy_arm_template_at_tenant_scope(cmd=cmd,
                                                template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                deployment_name=deployment_name, deployment_location=deployment_location,
                                                validate_only=False, no_wait=no_wait,
                                                no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


# pylint: disable=unused-argument
def validate_arm_template_at_tenant_scope(cmd,
                                          template_file=None, template_uri=None, parameters=None,
                                          deployment_name=None, deployment_location=None,
                                          no_wait=False, handle_extended_json_format=None, no_prompt=False, template_spec=None, query_string=None):
    return _deploy_arm_template_at_tenant_scope(cmd=cmd,
                                                template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                deployment_name=deployment_name, deployment_location=deployment_location,
                                                validate_only=True, no_wait=no_wait,
                                                no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)


def _deploy_arm_template_at_tenant_scope(cmd,
                                         template_file=None, template_uri=None, parameters=None,
                                         deployment_name=None, deployment_location=None, validate_only=False,
                                         no_wait=False, no_prompt=False, template_spec=None, query_string=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'tenant', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode='Incremental',
                                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))

    from azure.core.exceptions import HttpResponseError
    ScopedDeployment = cmd.get_models('ScopedDeployment')
    deployment = ScopedDeployment(properties=deployment_properties, location=deployment_location)
    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        try:
            validation_poller = mgmt_client.begin_validate_at_tenant_scope(deployment_name=deployment_name,
                                                                           parameters=deployment)
        except HttpResponseError as err:
            err_message = _build_http_response_error_message(err)
            raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
        validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)
    else:
        validation_result = mgmt_client.validate_at_tenant_scope(deployment_name=deployment_name,
                                                                 parameters=deployment)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)
    if validate_only:
        return validation_result

    return sdk_no_wait(no_wait, mgmt_client.begin_create_or_update_at_tenant_scope, deployment_name, deployment)


def what_if_deploy_arm_template_at_resource_group(cmd, resource_group_name,
                                                  template_file=None, template_uri=None, parameters=None,
                                                  deployment_name=None, mode=DeploymentMode.incremental,
                                                  aux_tenants=None, result_format=None,
                                                  no_pretty_print=None, no_prompt=False,
                                                  exclude_change_types=None, template_spec=None, query_string=None):
    return _what_if_deploy_arm_template_at_resource_group_core(cmd, resource_group_name,
                                                               template_file, template_uri, parameters,
                                                               deployment_name, DeploymentMode.incremental,
                                                               aux_tenants, result_format,
                                                               no_pretty_print, no_prompt,
                                                               exclude_change_types, template_spec, query_string)


def _what_if_deploy_arm_template_at_resource_group_core(cmd, resource_group_name,
                                                        template_file=None, template_uri=None, parameters=None,
                                                        deployment_name=None, mode=DeploymentMode.incremental,
                                                        aux_tenants=None, result_format=None,
                                                        no_pretty_print=None, no_prompt=False,
                                                        exclude_change_types=None, template_spec=None, query_string=None,
                                                        return_result=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'resourceGroup', template_file, template_uri,
                                                                parameters, mode, result_format, no_prompt, template_spec, query_string)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, aux_tenants=aux_tenants,
                                                    plug_pipeline=(template_uri is None and template_spec is None))
    DeploymentWhatIf = cmd.get_models('DeploymentWhatIf')
    deployment_what_if = DeploymentWhatIf(properties=what_if_properties)
    what_if_poller = mgmt_client.begin_what_if(resource_group_name, deployment_name,
                                               parameters=deployment_what_if)
    what_if_result = _what_if_deploy_arm_template_core(cmd.cli_ctx, what_if_poller, no_pretty_print, exclude_change_types)

    return what_if_result if no_pretty_print or return_result else None


def what_if_deploy_arm_template_at_subscription_scope(cmd,
                                                      template_file=None, template_uri=None, parameters=None,
                                                      deployment_name=None, deployment_location=None,
                                                      result_format=None, no_pretty_print=None, no_prompt=False,
                                                      exclude_change_types=None, template_spec=None, query_string=None):
    return _what_if_deploy_arm_template_at_subscription_scope_core(cmd,
                                                                   template_file, template_uri, parameters,
                                                                   deployment_name, deployment_location,
                                                                   result_format, no_pretty_print, no_prompt,
                                                                   exclude_change_types, template_spec, query_string)


def _what_if_deploy_arm_template_at_subscription_scope_core(cmd,
                                                            template_file=None, template_uri=None, parameters=None,
                                                            deployment_name=None, deployment_location=None,
                                                            result_format=None, no_pretty_print=None, no_prompt=False,
                                                            exclude_change_types=None, template_spec=None, query_string=None,
                                                            return_result=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'subscription', template_file, template_uri, parameters,
                                                                DeploymentMode.incremental, result_format, no_prompt, template_spec, query_string)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))
    ScopedDeploymentWhatIf = cmd.get_models('ScopedDeploymentWhatIf')
    scoped_deployment_what_if = ScopedDeploymentWhatIf(location=deployment_location, properties=what_if_properties)
    what_if_poller = mgmt_client.begin_what_if_at_subscription_scope(deployment_name,
                                                                     parameters=scoped_deployment_what_if)
    what_if_result = _what_if_deploy_arm_template_core(cmd.cli_ctx, what_if_poller, no_pretty_print, exclude_change_types)

    return what_if_result if no_pretty_print or return_result else None


def what_if_deploy_arm_template_at_management_group(cmd, management_group_id=None,
                                                    template_file=None, template_uri=None, parameters=None,
                                                    deployment_name=None, deployment_location=None,
                                                    result_format=None, no_pretty_print=None, no_prompt=False,
                                                    exclude_change_types=None, template_spec=None, query_string=None):
    return _what_if_deploy_arm_template_at_management_group_core(cmd, management_group_id,
                                                                 template_file, template_uri, parameters,
                                                                 deployment_name, deployment_location,
                                                                 result_format, no_pretty_print, no_prompt,
                                                                 exclude_change_types, template_spec, query_string)


def _what_if_deploy_arm_template_at_management_group_core(cmd, management_group_id=None,
                                                          template_file=None, template_uri=None, parameters=None,
                                                          deployment_name=None, deployment_location=None,
                                                          result_format=None, no_pretty_print=None, no_prompt=False,
                                                          exclude_change_types=None, template_spec=None, query_string=None,
                                                          return_result=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'managementGroup', template_file, template_uri, parameters,
                                                                DeploymentMode.incremental, result_format, no_prompt, template_spec=template_spec, query_string=query_string)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))
    ScopedDeploymentWhatIf = cmd.get_models('ScopedDeploymentWhatIf')
    scoped_deployment_what_if = ScopedDeploymentWhatIf(location=deployment_location, properties=what_if_properties)
    what_if_poller = mgmt_client.begin_what_if_at_management_group_scope(management_group_id, deployment_name,
                                                                         parameters=scoped_deployment_what_if)
    what_if_result = _what_if_deploy_arm_template_core(cmd.cli_ctx, what_if_poller, no_pretty_print, exclude_change_types)

    return what_if_result if no_pretty_print or return_result else None


def what_if_deploy_arm_template_at_tenant_scope(cmd,
                                                template_file=None, template_uri=None, parameters=None,
                                                deployment_name=None, deployment_location=None,
                                                result_format=None, no_pretty_print=None, no_prompt=False,
                                                exclude_change_types=None, template_spec=None, query_string=None):
    return _what_if_deploy_arm_template_at_tenant_scope_core(cmd,
                                                             template_file, template_uri, parameters,
                                                             deployment_name, deployment_location,
                                                             result_format, no_pretty_print, no_prompt,
                                                             exclude_change_types, template_spec, query_string)


def _what_if_deploy_arm_template_at_tenant_scope_core(cmd,
                                                      template_file=None, template_uri=None, parameters=None,
                                                      deployment_name=None, deployment_location=None,
                                                      result_format=None, no_pretty_print=None, no_prompt=False,
                                                      exclude_change_types=None, template_spec=None, query_string=None,
                                                      return_result=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'tenant', template_file, template_uri, parameters,
                                                                DeploymentMode.incremental, result_format, no_prompt, template_spec, query_string)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))
    ScopedDeploymentWhatIf = cmd.get_models('ScopedDeploymentWhatIf')
    scoped_deployment_what_if = ScopedDeploymentWhatIf(location=deployment_location, properties=what_if_properties)
    what_if_poller = mgmt_client.begin_what_if_at_tenant_scope(deployment_name, parameters=scoped_deployment_what_if)
    what_if_result = _what_if_deploy_arm_template_core(cmd.cli_ctx, what_if_poller, no_pretty_print, exclude_change_types)

    return what_if_result if no_pretty_print or return_result else None


def _what_if_deploy_arm_template_core(cli_ctx, what_if_poller, no_pretty_print, exclude_change_types):
    what_if_result = LongRunningOperation(cli_ctx)(what_if_poller)

    if what_if_result.error:
        # The status code is 200 even when there's an error, because
        # it is technically a successful What-If operation. The error
        # is on the ARM template but not the operation.
        err_message = _build_preflight_error_message(what_if_result.error)
        raise CLIError(err_message)

    if exclude_change_types:
        exclude_change_types = set(map(lambda x: x.lower(), exclude_change_types))
        what_if_result.changes = list(
            filter(lambda x: x.change_type.lower() not in exclude_change_types, what_if_result.changes)
        )

    if no_pretty_print:
        return what_if_result

    try:
        if cli_ctx.enable_color:
            # Disabling colorama since it will silently strip out the Xterm 256 color codes the What-If formatter
            # is using. Unfortunately, the colors that colorama supports are very limited, which doesn't meet our needs.
            from colorama import deinit
            deinit()

            # Enable virtual terminal mode for Windows console so it processes color codes.
            if platform.system() == "Windows":
                from ._win_vt import enable_vt_mode
                enable_vt_mode()

        print(format_what_if_operation_result(what_if_result, cli_ctx.enable_color))
    finally:
        if cli_ctx.enable_color:
            from colorama import init
            init()

    return what_if_result


def _prepare_template_uri_with_query_string(template_uri, input_query_string):
    from urllib.parse import urlencode, parse_qs, urlsplit, urlunsplit

    try:
        scheme, netloc, path, query_string, fragment = urlsplit(template_uri)  # pylint: disable=unused-variable
        query_params = parse_qs(input_query_string)
        new_query_string = urlencode(query_params, doseq=True)

        return urlunsplit((scheme, netloc, path, new_query_string, fragment))
    except Exception:  # pylint: disable=broad-except
        raise InvalidArgumentValueError('Unable to parse parameter: {} .Make sure the value is formed correctly.'.format(input_query_string))


def _prepare_deployment_properties_unmodified(cmd, deployment_scope, template_file=None, template_uri=None, parameters=None,
                                              mode=None, rollback_on_error=None, no_prompt=False, template_spec=None, query_string=None):
    cli_ctx = cmd.cli_ctx
    DeploymentProperties, TemplateLink, OnErrorDeployment = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                                                    'DeploymentProperties', 'TemplateLink',
                                                                    'OnErrorDeployment', mod='models')
    template_link = None
    template_obj = None
    on_error_deployment = None
    template_content = None

    if query_string and not template_uri:
        raise IncorrectUsageError('please provide --template-uri if --query-string is specified')

    if template_uri:
        if query_string:
            template_link = TemplateLink(uri=template_uri, query_string=query_string)
            template_uri = _prepare_template_uri_with_query_string(template_uri=template_uri, input_query_string=query_string)
        else:
            template_link = TemplateLink(uri=template_uri)
        template_obj = _remove_comments_from_json(_urlretrieve(template_uri).decode('utf-8'), file_path=template_uri)
    elif template_spec:
        template_link = TemplateLink(id=template_spec, mode="Incremental")
        # The api-version for ResourceType.MGMT_RESOURCE_RESOURCES may get updated and point to another (newer) version of the api version for
        # ResourceType.MGMT_RESOURCE_TEMPLATESPECS than our designated version. This ensures the api-version of all the rest requests for
        # template_spec are consistent in the same profile:
        api_version = get_api_version(cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS)
        template_obj = show_resource(cmd=cmd, resource_ids=[template_spec], api_version=api_version).properties['mainTemplate']
    else:
        template_content = (
            run_bicep_command(["build", "--stdout", template_file])
            if is_bicep_file(template_file)
            else read_file_content(template_file)
        )
        template_obj = _remove_comments_from_json(template_content, file_path=template_file)

        if is_bicep_file(template_file):
            template_schema = template_obj.get('$schema', '')
            validate_bicep_target_scope(template_schema, deployment_scope)

    if rollback_on_error == '':
        on_error_deployment = OnErrorDeployment(type='LastSuccessful')
    elif rollback_on_error:
        on_error_deployment = OnErrorDeployment(type='SpecificDeployment', deployment_name=rollback_on_error)

    template_param_defs = template_obj.get('parameters', {})
    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(template_param_defs, parameters) or {}
    parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters, no_prompt)
    parameters = json.loads(json.dumps(parameters))

    properties = DeploymentProperties(template=template_content, template_link=template_link,
                                      parameters=parameters, mode=mode, on_error_deployment=on_error_deployment)
    return properties


def _prepare_deployment_what_if_properties(cmd, deployment_scope, template_file, template_uri, parameters,
                                           mode, result_format, no_prompt, template_spec, query_string):
    DeploymentWhatIfProperties, DeploymentWhatIfSettings = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                                                   'DeploymentWhatIfProperties', 'DeploymentWhatIfSettings',
                                                                   mod='models')

    deployment_properties = _prepare_deployment_properties_unmodified(cmd, deployment_scope, template_file=template_file, template_uri=template_uri,
                                                                      parameters=parameters, mode=mode, no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)
    deployment_what_if_properties = DeploymentWhatIfProperties(template=deployment_properties.template, template_link=deployment_properties.template_link,
                                                               parameters=deployment_properties.parameters, mode=deployment_properties.mode,
                                                               what_if_settings=DeploymentWhatIfSettings(result_format=result_format))

    return deployment_what_if_properties


# pylint: disable=protected-access
def _get_deployment_management_client(cli_ctx, aux_subscriptions=None, aux_tenants=None, plug_pipeline=True):

    smc = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                  aux_subscriptions=aux_subscriptions, aux_tenants=aux_tenants)

    deployment_client = smc.deployments  # This solves the multi-api for you

    if not plug_pipeline:
        return deployment_client

    # Plug this as default HTTP pipeline
    from azure.core.pipeline import Pipeline
    smc._client._pipeline._impl_policies.append(JsonCTemplatePolicy())
    # Because JsonCTemplatePolicy needs to be wrapped as _SansIOHTTPPolicyRunner, so a new Pipeline is built
    smc._client._pipeline = Pipeline(
        policies=smc._client._pipeline._impl_policies,
        transport=smc._client._pipeline._transport
    )

    return deployment_client


def _list_resources_odata_filter_builder(resource_group_name=None, resource_provider_namespace=None,
                                         resource_type=None, name=None, tag=None, location=None):
    """Build up OData filter string from parameters """
    if tag is not None:
        if resource_group_name:
            raise IncorrectUsageError('you cannot use \'--tag\' with \'--resource-group\''
                                      '(If the default value for resource group is set, please use \'az configure --defaults group=""\' command to clear it first)')
        if resource_provider_namespace:
            raise IncorrectUsageError('you cannot use \'--tag\' with \'--namespace\'')
        if resource_type:
            raise IncorrectUsageError('you cannot use \'--tag\' with \'--resource-type\'')
        if name:
            raise IncorrectUsageError('you cannot use \'--tag\' with \'--name\'')
        if location:
            raise IncorrectUsageError('you cannot use \'--tag\' with \'--location\''
                                      '(If the default value for location is set, please use \'az configure --defaults location=""\' command to clear it first)')

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


def _update_provider(cmd, namespace, registering, wait, properties=None, mg_id=None, accept_terms=None):
    import time
    target_state = 'Registered' if registering else 'Unregistered'
    rcf = _resource_client_factory(cmd.cli_ctx)
    is_rpaas = namespace.lower() in RPAAS_APIS
    if mg_id is None and registering:
        if is_rpaas and accept_terms:
            wait = True
        if cmd.supported_api_version(min_api='2021-04-01'):
            r = rcf.providers.register(namespace, properties=properties)
        else:
            r = rcf.providers.register(namespace)
    elif mg_id and registering:
        r = rcf.providers.register_at_management_group_scope(namespace, mg_id)
        if r is None:
            return
    else:
        r = rcf.providers.unregister(namespace)

    if r.registration_state == target_state:
        return

    if wait:
        while True:
            time.sleep(10)
            rp_info = rcf.providers.get(namespace)
            if rp_info.registration_state == target_state:
                break
        if is_rpaas and accept_terms and registering and mg_id is None:
            # call accept term API
            from azure.cli.core.util import send_raw_request
            send_raw_request(cmd.cli_ctx, 'put', RPAAS_APIS[namespace.lower()], body=json.dumps({"properties": {"accepted": True}}))
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
            policy_set_def = _get_custom_or_builtin_policy(cmd, client, policy_set_definition, None, None, True)
            policy_id = policy_set_def.id
    return policy_id


def _parse_management_group_reference(name):
    if _is_management_group_scope(name):
        parts = name.split('/')
        if len(parts) >= 9:
            return parts[4], parts[8]
    return None, name


def _parse_management_group_id(scope):
    if _is_management_group_scope(scope):
        parts = scope.split('/')
        if len(parts) >= 5:
            return parts[4]
    return None


def _get_custom_or_builtin_policy(cmd, client, name, subscription=None, management_group=None, for_policy_set=False):
    from azure.core.exceptions import HttpResponseError
    policy_operations = client.policy_set_definitions if for_policy_set else client.policy_definitions

    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                             subscription_id=subscription_id)
            policy_operations = client.policy_set_definitions if for_policy_set else client.policy_definitions
    try:
        if cmd.supported_api_version(min_api='2018-03-01'):
            if not management_group:
                management_group, name = _parse_management_group_reference(name)
            if management_group:
                return policy_operations.get_at_management_group(name, management_group)
        return policy_operations.get(name)
    except (HttpResponseError) as ex:
        status_code = ex.status_code if isinstance(ex, HttpResponseError) else ex.response.status_code
        if status_code == 404:
            try:
                return policy_operations.get_built_in(name)
            except HttpResponseError as ex2:
                # When the `--policy` parameter is neither a valid policy definition name nor conforms to the policy definition id format,
                # an exception of "AuthorizationFailed" will be reported to mislead customers.
                # So we need to modify the exception information thrown here.
                if ex2.status_code == 403 and ex2.error and ex2.error.code == 'AuthorizationFailed':
                    raise IncorrectUsageError('\'--policy\' should be a valid name or id of the policy definition')
                raise ex2
        raise


def _load_file_string_or_uri(file_or_string_or_uri, name, required=True):
    if file_or_string_or_uri is None:
        if required:
            raise CLIError('--{} is required'.format(name))
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
        if tag[key]:
            filters.append("tagvalue eq '{}'".format(tag[key]))

    filter_text = ' and '.join(filters) if filters else None

    groups = rcf.resource_groups.list(filter=filter_text)
    return list(groups)


def create_resource_group(cmd, rg_name, location, tags=None, managed_by=None):
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

    if cmd.supported_api_version(min_api='2016-09-01'):
        parameters.managed_by = managed_by

    return rcf.resource_groups.create_or_update(rg_name, parameters)


def update_resource_group(instance, tags=None):

    if tags is not None:
        instance.tags = tags

    return instance


def export_group_as_template(
        cmd, resource_group_name, include_comments=False, include_parameter_default_value=False, resource_ids=None, skip_resource_name_params=False, skip_all_params=False):
    """Captures a resource group as a template.
    :param str resource_group_name: the name of the resource group.
    :param resource_ids: space-separated resource ids to filter the export by. To export all resources, do not specify this argument or supply "*".
    :param bool include_comments: export template with comments.
    :param bool include_parameter_default_value: export template parameter with default value.
    :param bool skip_resource_name_params: export template and skip resource name parameterization.
    :param bool skip_all_params: export template parameter and skip all parameterization.
    """
    rcf = _resource_client_factory(cmd.cli_ctx)

    export_options = []
    if include_comments:
        export_options.append('IncludeComments')
    if include_parameter_default_value:
        export_options.append('IncludeParameterDefaultValue')
    if skip_resource_name_params:
        export_options.append('SkipResourceNameParameterization')
    if skip_all_params:
        export_options.append('SkipAllParameterization')

    resources = []
    if resource_ids is None or resource_ids[0] == "*":
        resources = ["*"]
    else:
        for i in resource_ids:
            if is_valid_resource_id(i):
                resources.append(i)
            else:
                raise CLIError('az resource: error: argument --resource-ids: invalid ResourceId value: \'%s\'' % i)

    options = ','.join(export_options) if export_options else None

    ExportTemplateRequest = cmd.get_models('ExportTemplateRequest')
    export_template_request = ExportTemplateRequest(resources=resources, options=options)

    # Exporting a resource group as a template is async since API version 2019-08-01.
    if cmd.supported_api_version(min_api='2019-08-01'):
        result_poller = rcf.resource_groups.begin_export_template(resource_group_name,
                                                                  parameters=export_template_request)
        result = LongRunningOperation(cmd.cli_ctx)(result_poller)
    else:
        result = rcf.resource_groups.begin_export_template(resource_group_name,
                                                           parameters=export_template_request)

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

    return result.template


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
        application.plan = Plan(name=plan_name, publisher=plan_publisher, product=plan_product, version=plan_version)

    applicationParameters = None

    if parameters:
        if os.path.exists(parameters):
            applicationParameters = get_file_json(parameters)
        else:
            applicationParameters = shell_safe_json_parse(parameters)

    application.parameters = applicationParameters

    return racf.applications.begin_create_or_update(resource_group_name, application_name, application)


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


def create_or_update_applicationdefinition(cmd, resource_group_name,
                                           application_definition_name,
                                           lock_level, authorizations,
                                           description, display_name,
                                           package_file_uri=None, create_ui_definition=None,
                                           main_template=None, location=None, tags=None):
    """ Create or update a new managed application definition.
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
    if package_file_uri:
        if create_ui_definition or main_template:
            raise CLIError('usage error: must not specify --create-ui-definition --main-template')
    if not package_file_uri:
        if not create_ui_definition or not main_template:
            raise CLIError('usage error: must specify --create-ui-definition --main-template')
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

    return racf.application_definitions.begin_create_or_update(resource_group_name,
                                                               application_definition_name, applicationDef)


def list_applications(cmd, resource_group_name=None):
    racf = _resource_managedapps_client_factory(cmd.cli_ctx)

    if resource_group_name:
        applications = racf.applications.list_by_resource_group(resource_group_name)
    else:
        applications = racf.applications.list_by_subscription()
    return list(applications)


def list_deployments_at_subscription_scope(cmd, filter_string=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_at_subscription_scope(filter=filter_string)


def list_deployments_at_resource_group(cmd, resource_group_name, filter_string=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_by_resource_group(resource_group_name, filter=filter_string)


def list_deployments_at_management_group(cmd, management_group_id, filter_string=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_at_management_group_scope(management_group_id, filter=filter_string)


def list_deployments_at_tenant_scope(cmd, filter_string=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_at_tenant_scope(filter=filter_string)


def get_deployment_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.get_at_subscription_scope(deployment_name)


def get_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.get(resource_group_name, deployment_name)


def get_deployment_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.get_at_management_group_scope(management_group_id, deployment_name)


def get_deployment_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.get_at_tenant_scope(deployment_name)


def delete_deployment_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete_at_subscription_scope(deployment_name)


def delete_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete(resource_group_name, deployment_name)


def delete_deployment_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete_at_management_group_scope(management_group_id, deployment_name)


def delete_deployment_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete_at_tenant_scope(deployment_name)


def cancel_deployment_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel_at_subscription_scope(deployment_name)


def cancel_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel(resource_group_name, deployment_name)


def cancel_deployment_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel_at_management_group_scope(management_group_id, deployment_name)


def cancel_deployment_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel_at_tenant_scope(deployment_name)


# pylint: disable=unused-argument
def deploy_arm_template(cmd, resource_group_name,
                        template_file=None, template_uri=None, deployment_name=None,
                        parameters=None, mode=None, rollback_on_error=None, no_wait=False,
                        handle_extended_json_format=None, aux_subscriptions=None, aux_tenants=None,
                        no_prompt=False):
    return _deploy_arm_template_core_unmodified(cmd, resource_group_name=resource_group_name,
                                                template_file=template_file, template_uri=template_uri,
                                                deployment_name=deployment_name, parameters=parameters, mode=mode,
                                                rollback_on_error=rollback_on_error, no_wait=no_wait,
                                                aux_subscriptions=aux_subscriptions, aux_tenants=aux_tenants,
                                                no_prompt=no_prompt)


# pylint: disable=unused-argument
def validate_arm_template(cmd, resource_group_name, template_file=None, template_uri=None,
                          parameters=None, mode=None, rollback_on_error=None, handle_extended_json_format=None,
                          no_prompt=False):
    return _deploy_arm_template_core_unmodified(cmd, resource_group_name, template_file, template_uri,
                                                'deployment_dry_run', parameters, mode, rollback_on_error,
                                                validate_only=True, no_prompt=no_prompt)


def export_template_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template_at_subscription_scope(deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template(resource_group_name, deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template_at_management_group_scope(management_group_id, deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template_at_tenant_scope(deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_deployment_as_template(cmd, resource_group_name, deployment_name):
    smc = _resource_client_factory(cmd.cli_ctx)
    result = smc.deployments.export_template(resource_group_name, deployment_name)
    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def create_resource(cmd, properties,
                    resource_group_name=None, resource_provider_namespace=None,
                    parent_resource_path=None, resource_type=None, resource_name=None,
                    resource_id=None, api_version=None, location=None, is_full_object=False,
                    latest_include_preview=False):
    res = _ResourceUtils(cmd.cli_ctx, resource_group_name, resource_provider_namespace,
                         parent_resource_path, resource_type, resource_name,
                         resource_id, api_version, latest_include_preview=latest_include_preview)
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

    return ({'resource_id': rid} for rid in resource_ids)


def _get_rsrc_util_from_parsed_id(cli_ctx, parsed_id, api_version, latest_include_preview=False):
    return _ResourceUtils(cli_ctx,
                          parsed_id.get('resource_group', None),
                          parsed_id.get('resource_namespace', None),
                          parsed_id.get('resource_parent', None),
                          parsed_id.get('resource_type', None),
                          parsed_id.get('resource_name', None),
                          parsed_id.get('resource_id', None),
                          api_version,
                          latest_include_preview=latest_include_preview)


def _create_parsed_id(cli_ctx, resource_group_name=None, resource_provider_namespace=None, parent_resource_path=None,
                      resource_type=None, resource_name=None):
    subscription = get_subscription_id(cli_ctx)
    return {
        'resource_group': resource_group_name,
        'resource_namespace': resource_provider_namespace,
        'resource_parent': parent_resource_path,
        'resource_type': resource_type,
        'resource_name': resource_name,
        'subscription': subscription
    }


def _single_or_collection(obj, default=None):
    if not obj:
        return default

    if isinstance(obj, list) and len(obj) == 1:
        return obj[0]

    return obj


def show_resource(cmd, resource_ids=None, resource_group_name=None,
                  resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                  resource_name=None, api_version=None, include_response_body=False, latest_include_preview=False):
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(cmd.cli_ctx,
                                                                              resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version, latest_include_preview).get_resource(
            include_response_body) for id_dict in parsed_ids])


# pylint: disable=unused-argument
def delete_resource(cmd, resource_ids=None, resource_group_name=None,
                    resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                    resource_name=None, api_version=None, latest_include_preview=False):
    """
    Deletes the given resource(s).
    This function allows deletion of ids with dependencies on one another.
    This is done with multiple passes through the given ids.
    """
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(cmd.cli_ctx,
                                                                              resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]
    to_be_deleted = [(_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version, latest_include_preview), id_dict)
                     for id_dict in parsed_ids]

    results = []
    from azure.core.exceptions import HttpResponseError
    while to_be_deleted:
        logger.debug("Start new loop to delete resources.")
        operations = []
        failed_to_delete = []
        for rsrc_utils, id_dict in to_be_deleted:
            try:
                operations.append(rsrc_utils.delete())
                resource = _build_resource_id(**id_dict) or resource_name
                logger.debug("deleting %s", resource)
            except HttpResponseError as e:
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
        error_msg_builder = ['Some resources failed to be deleted (run with `--verbose` for more information):']
        for _, id_dict in to_be_deleted:
            logger.info(id_dict['exception'])
            resource_id = _build_resource_id(**id_dict) or id_dict['resource_id']
            error_msg_builder.append(resource_id)
        raise CLIError(os.linesep.join(error_msg_builder))

    return _single_or_collection(results)


def update_resource(cmd, parameters, resource_ids=None,
                    resource_group_name=None, resource_provider_namespace=None,
                    parent_resource_path=None, resource_type=None, resource_name=None, api_version=None,
                    latest_include_preview=False):
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(cmd.cli_ctx,
                                                                              resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version, latest_include_preview).update(parameters)
         for id_dict in parsed_ids])


def tag_resource(cmd, tags, resource_ids=None, resource_group_name=None, resource_provider_namespace=None,
                 parent_resource_path=None, resource_type=None, resource_name=None, api_version=None,
                 is_incremental=None, latest_include_preview=False):
    """ Updates the tags on an existing resource. To clear tags, specify the --tag option
    without anything else. """
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(cmd.cli_ctx,
                                                                              resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection([LongRunningOperation(cmd.cli_ctx)(
        _get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version, latest_include_preview).tag(
            tags, is_incremental)) for id_dict in parsed_ids])


def invoke_resource_action(cmd, action, request_body=None, resource_ids=None,
                           resource_group_name=None, resource_provider_namespace=None,
                           parent_resource_path=None, resource_type=None, resource_name=None,
                           api_version=None, latest_include_preview=False):
    """ Invokes the provided action on an existing resource."""
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(cmd.cli_ctx,
                                                                              resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version, latest_include_preview).invoke_action(
            action, request_body) for id_dict in parsed_ids])


def get_deployment_operations(client, resource_group_name, deployment_name, operation_ids):
    """get a deployment's operation."""
    result = []
    for op_id in operation_ids:
        dep = client.get(resource_group_name, deployment_name, op_id)
        result.append(dep)
    return result


def get_deployment_operations_at_subscription_scope(client, deployment_name, operation_ids):
    result = []
    for op_id in operation_ids:
        deployment = client.get_at_subscription_scope(deployment_name, op_id)
        result.append(deployment)
    return result


def get_deployment_operations_at_resource_group(client, resource_group_name, deployment_name, operation_ids):
    result = []
    for op_id in operation_ids:
        dep = client.get(resource_group_name, deployment_name, op_id)
        result.append(dep)
    return result


def get_deployment_operations_at_management_group(client, management_group_id, deployment_name, operation_ids):
    result = []
    for op_id in operation_ids:
        dep = client.get_at_management_group_scope(management_group_id, deployment_name, op_id)
        result.append(dep)
    return result


def get_deployment_operations_at_tenant_scope(client, deployment_name, operation_ids):
    result = []
    for op_id in operation_ids:
        dep = client.get_at_tenant_scope(deployment_name, op_id)
        result.append(dep)
    return result


def list_deployment_scripts(cmd, resource_group_name=None):
    rcf = _resource_deploymentscripts_client_factory(cmd.cli_ctx)
    if resource_group_name is not None:
        return rcf.deployment_scripts.list_by_resource_group(resource_group_name)
    return rcf.deployment_scripts.list_by_subscription()


def get_deployment_script(cmd, resource_group_name, name):
    rcf = _resource_deploymentscripts_client_factory(cmd.cli_ctx)
    return rcf.deployment_scripts.get(resource_group_name, name)


def get_deployment_script_logs(cmd, resource_group_name, name):
    rcf = _resource_deploymentscripts_client_factory(cmd.cli_ctx)
    return rcf.deployment_scripts.get_logs(resource_group_name, name)


def delete_deployment_script(cmd, resource_group_name, name):
    rcf = _resource_deploymentscripts_client_factory(cmd.cli_ctx)
    rcf.deployment_scripts.delete(resource_group_name, name)


def get_template_spec(cmd, resource_group_name=None, name=None, version=None, template_spec=None):
    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
    if version:
        return rcf.template_spec_versions.get(resource_group_name, name, version)
    retrieved_template = rcf.template_specs.get(resource_group_name, name, expand="versions")
    version_names = list(retrieved_template.versions.keys())
    retrieved_template.versions = version_names
    return retrieved_template


def create_template_spec(cmd, resource_group_name, name, template_file=None, location=None, display_name=None,
                         description=None, version=None, version_description=None, tags=None, no_prompt=False, ui_form_definition_file=None):
    if location is None:
        rcf = _resource_client_factory(cmd.cli_ctx)
        location = rcf.resource_groups.get(resource_group_name).location
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)

    if template_file and not version:
        raise IncorrectUsageError('please provide --version if --template-file is specified')

    if version:
        input_template, artifacts, input_ui_form_definition = None, None, None
        exists = False
        if no_prompt is False:
            try:  # Check if child template spec already exists.
                rcf.template_spec_versions.get(resource_group_name=resource_group_name, template_spec_name=name, template_spec_version=version)
                from knack.prompting import prompt_y_n
                confirmation = prompt_y_n("This will override template spec {} version {}. Proceed?".format(name, version))
                if not confirmation:
                    return None
                exists = True
            except Exception:  # pylint: disable=broad-except
                pass

        if template_file:
            from azure.cli.command_modules.resource._packing_engine import (pack)
            if is_bicep_file(template_file):
                template_content = run_bicep_command(["build", "--stdout", template_file])
                input_content = _remove_comments_from_json(template_content, file_path=template_file)
                input_template = json.loads(json.dumps(input_content))
                artifacts = []
            else:
                packed_template = pack(cmd, template_file)
                input_template = getattr(packed_template, 'RootTemplate')
                artifacts = getattr(packed_template, 'Artifacts')

        if ui_form_definition_file:
            ui_form_definition_content = _remove_comments_from_json(read_file_content(ui_form_definition_file))
            input_ui_form_definition = json.loads(json.dumps(ui_form_definition_content))

        if not exists:
            try:  # Check if parent template spec already exists.
                existing_parent = rcf.template_specs.get(resource_group_name=resource_group_name, template_spec_name=name)
                if tags is None:  # New version should inherit tags from parent if none are provided.
                    tags = getattr(existing_parent, 'tags')
            except Exception:  # pylint: disable=broad-except
                tags = tags or {}
                TemplateSpec = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS, 'TemplateSpec', mod='models')
                template_spec_parent = TemplateSpec(location=location, description=description, display_name=display_name, tags=tags)
                rcf.template_specs.create_or_update(resource_group_name, name, template_spec_parent)

        TemplateSpecVersion = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS, 'TemplateSpecVersion', mod='models')
        template_spec_version = TemplateSpecVersion(location=location, linked_templates=artifacts, description=version_description, main_template=input_template, tags=tags, ui_form_definition=input_ui_form_definition)
        return rcf.template_spec_versions.create_or_update(resource_group_name, name, version, template_spec_version)

    tags = tags or {}
    TemplateSpec = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS, 'TemplateSpec', mod='models')
    template_spec_parent = TemplateSpec(location=location, description=description, display_name=display_name, tags=tags)
    return rcf.template_specs.create_or_update(resource_group_name, name, template_spec_parent)


def update_template_spec(cmd, resource_group_name=None, name=None, template_spec=None, template_file=None, display_name=None,
                         description=None, version=None, version_description=None, tags=None, ui_form_definition_file=None):
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)

    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None

    existing_template, artifacts, input_ui_form_definition = None, None, None
    if template_file:
        from azure.cli.command_modules.resource._packing_engine import (pack)
        if is_bicep_file(template_file):
            template_content = run_bicep_command(["build", "--stdout", template_file])
            input_content = _remove_comments_from_json(template_content, file_path=template_file)
            input_template = json.loads(json.dumps(input_content))
            artifacts = []
        else:
            packed_template = pack(cmd, template_file)
            input_template = getattr(packed_template, 'RootTemplate')
            artifacts = getattr(packed_template, 'Artifacts')

    if ui_form_definition_file:
        ui_form_definition_content = _remove_comments_from_json(read_file_content(ui_form_definition_file))
        input_ui_form_definition = json.loads(json.dumps(ui_form_definition_content))

    if version:
        existing_template = rcf.template_spec_versions.get(resource_group_name=resource_group_name, template_spec_name=name, template_spec_version=version)

        location = getattr(existing_template, 'location')

        # Do not remove tags if not explicitly empty.
        if tags is None:
            tags = getattr(existing_template, 'tags')
        if version_description is None:
            version_description = getattr(existing_template, 'description')
        if template_file is None:
            input_template = getattr(existing_template, 'main_template')
        if ui_form_definition_file is None:
            input_ui_form_definition = getattr(existing_template, 'ui_form_definition')
        TemplateSpecVersion = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS, 'TemplateSpecVersion', mod='models')

        updated_template_spec = TemplateSpecVersion(location=location, linked_templates=artifacts, description=version_description, main_template=input_template, tags=tags, ui_form_definition=input_ui_form_definition)
        return rcf.template_spec_versions.create_or_update(resource_group_name, name, version, updated_template_spec)

    existing_template = rcf.template_specs.get(resource_group_name=resource_group_name, template_spec_name=name)

    location = getattr(existing_template, 'location')
    # Do not remove tags if not explicitly empty.
    if tags is None:
        tags = getattr(existing_template, 'tags')
    if display_name is None:
        display_name = getattr(existing_template, 'display_name')
    if description is None:
        description = getattr(existing_template, 'description')

    TemplateSpec = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS, 'TemplateSpec', mod='models')

    root_template = TemplateSpec(location=location, description=description, display_name=display_name, tags=tags)
    return rcf.template_specs.create_or_update(resource_group_name, name, root_template)


def export_template_spec(cmd, output_folder, resource_group_name=None, name=None, version=None, template_spec=None):
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None
    if not version:
        raise IncorrectUsageError('Please specify the template spec version for export')
    exported_template = rcf.template_spec_versions.get(resource_group_name, name, version)
    from azure.cli.command_modules.resource._packing_engine import (unpack)
    return unpack(cmd, exported_template, output_folder, (str(name) + '.JSON'))


def delete_template_spec(cmd, resource_group_name=None, name=None, version=None, template_spec=None):
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None
    if version:
        return rcf.template_spec_versions.delete(resource_group_name=resource_group_name, template_spec_name=name, template_spec_version=version)
    return rcf.template_specs.delete(resource_group_name=resource_group_name, template_spec_name=name)


def list_template_specs(cmd, resource_group_name=None, name=None):
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
    if resource_group_name is not None:
        if name is not None:
            return rcf.template_spec_versions.list(resource_group_name=resource_group_name, template_spec_name=name)
        return rcf.template_specs.list_by_resource_group(resource_group_name)
    return rcf.template_specs.list_by_subscription()


def list_deployment_operations_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list_at_subscription_scope(deployment_name)


def list_deployment_operations_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list(resource_group_name, deployment_name)


def list_deployment_operations_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list_at_management_group_scope(management_group_id, deployment_name)


def list_deployment_operations_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list_at_tenant_scope(deployment_name)


def get_deployment_operation_at_subscription_scope(cmd, deployment_name, op_id):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get_at_subscription_scope(deployment_name, op_id)


def get_deployment_operation_at_resource_group(cmd, resource_group_name, deployment_name, op_id):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get(resource_group_name, deployment_name, op_id)


def get_deployment_operation_at_management_group(cmd, management_group_id, deployment_name, op_id):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get_at_management_group_scope(management_group_id, deployment_name, op_id)


def get_deployment_operation_at_tenant_scope(cmd, deployment_name, op_id):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get_at_tenant_scope(deployment_name, op_id)


def list_resources(cmd, resource_group_name=None,
                   resource_provider_namespace=None, resource_type=None, name=None, tag=None,
                   location=None):
    rcf = _resource_client_factory(cmd.cli_ctx)

    if resource_group_name is not None:
        rcf.resource_groups.get(resource_group_name)

    odata_filter = _list_resources_odata_filter_builder(resource_group_name,
                                                        resource_provider_namespace,
                                                        resource_type, name, tag, location)

    expand = "createdTime,changedTime,provisioningState"
    resources = rcf.resources.list(filter=odata_filter, expand=expand)
    return list(resources)


def register_provider(cmd, resource_provider_namespace, consent_to_permissions=False, mg=None, wait=False, accept_terms=None):
    properties = None
    if cmd.supported_api_version(min_api='2021-04-01') and consent_to_permissions:
        ProviderRegistrationRequest, ProviderConsentDefinition = cmd.get_models('ProviderRegistrationRequest', 'ProviderConsentDefinition')
        properties = ProviderRegistrationRequest(third_party_provider_consent=ProviderConsentDefinition(consent_to_authorization=consent_to_permissions))
    _update_provider(cmd, resource_provider_namespace, registering=True, wait=wait, properties=properties, mg_id=mg, accept_terms=accept_terms)


def unregister_provider(cmd, resource_provider_namespace, wait=False):
    _update_provider(cmd, resource_provider_namespace, registering=False, wait=wait)


def list_provider_operations(cmd):
    auth_client = _authorization_management_client(cmd.cli_ctx)
    return auth_client.provider_operations_metadata.list()


def list_provider_permissions(cmd, resource_provider_namespace):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.providers.provider_permissions(resource_provider_namespace)


def show_provider_operations(cmd, resource_provider_namespace):
    version = getattr(get_api_version(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION), 'provider_operations_metadata')
    auth_client = _authorization_management_client(cmd.cli_ctx)
    if version == '2015-07-01':
        return auth_client.provider_operations_metadata.get(resource_provider_namespace, version)
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

    if len({r['subscription'] for r in resources}) > 1:
        raise CLIError('All resources should be under the same subscription')
    if len({r['resource_group'] for r in resources}) > 1:
        raise CLIError('All resources should be under the same group')

    rcf = _resource_client_factory(cmd.cli_ctx)
    default_subscription_id = get_subscription_id(cmd.cli_ctx)
    target = _build_resource_id(subscription=(destination_subscription_id or default_subscription_id),
                                resource_group=destination_group)

    ResourcesMoveInfo = cmd.get_models('ResourcesMoveInfo')
    resources_move_info = ResourcesMoveInfo(resources=ids, target_resource_group=target)
    return rcf.resources.begin_move_resources(resources[0]['resource_group'], parameters=resources_move_info)


def list_features(client, resource_provider_namespace=None):
    if resource_provider_namespace:
        return client.list(resource_provider_namespace=resource_provider_namespace)
    return client.list_all()


def register_feature(client, resource_provider_namespace, feature_name):
    logger.warning("Once the feature '%s' is registered, invoking 'az provider register -n %s' is required "
                   "to get the change propagated", feature_name, resource_provider_namespace)
    return client.register(resource_provider_namespace, feature_name)


def unregister_feature(client, resource_provider_namespace, feature_name):
    logger.warning("Once the feature '%s' is unregistered, invoking 'az provider register -n %s' is required "
                   "to get the change propagated", feature_name, resource_provider_namespace)
    return client.unregister(resource_provider_namespace, feature_name)


def list_feature_registrations(client, resource_provider_namespace=None):
    if resource_provider_namespace:
        return client.list_by_subscription(provider_namespace=resource_provider_namespace)
    return client.list_all_by_subscription()


def create_feature_registration(client, resource_provider_namespace, feature_name):
    return client.create_or_update(resource_provider_namespace, feature_name, {})


def delete_feature_registration(client, resource_provider_namespace, feature_name):
    return client.delete(resource_provider_namespace, feature_name)


# pylint: disable=inconsistent-return-statements,too-many-locals
def create_policy_assignment(cmd, policy=None, policy_set_definition=None,
                             name=None, display_name=None, params=None,
                             resource_group_name=None, scope=None, sku=None,
                             not_scopes=None, location=None, assign_identity=None,
                             mi_system_assigned=None, mi_user_assigned=None,
                             identity_scope=None, identity_role='Contributor', enforcement_mode='Default',
                             description=None):
    """Creates a policy assignment
    :param not_scopes: Space-separated scopes where the policy assignment does not apply.
    """
    if bool(policy) == bool(policy_set_definition):
        raise ArgumentUsageError('usage error: --policy NAME_OR_ID | '
                                 '--policy-set-definition NAME_OR_ID')
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    policy_id = _resolve_policy_id(cmd, policy, policy_set_definition, policy_client)
    params = _load_file_string_or_uri(params, 'params', False)

    PolicyAssignment = cmd.get_models('PolicyAssignment')
    assignment = PolicyAssignment(display_name=display_name, policy_definition_id=policy_id, scope=scope, enforcement_mode=enforcement_mode, description=description)
    assignment.parameters = params if params else None

    if cmd.supported_api_version(min_api='2017-06-01-preview'):
        if not_scopes:
            kwargs_list = []
            for id_arg in not_scopes.split(' '):
                id_parts = parse_resource_id(id_arg)
                if id_parts.get('subscription') or _is_management_group_scope(id_arg):
                    kwargs_list.append(id_arg)
                else:
                    raise InvalidArgumentValueError("Invalid resource ID value in --not-scopes: '%s'" % id_arg)
            assignment.not_scopes = kwargs_list

    identities = None
    if cmd.supported_api_version(min_api='2018-05-01'):
        if location:
            assignment.location = location
        if mi_system_assigned is not None or assign_identity is not None:
            identities = [MSI_LOCAL_ID]
        elif mi_user_assigned is not None:
            identities = [mi_user_assigned]

        identity = None
        if identities is not None:
            identity = _build_identities_info(cmd, identities, resource_group_name)
        assignment.identity = identity

    if name is None:
        name = (base64.urlsafe_b64encode(uuid.uuid4().bytes).decode())[:-2]

    createdAssignment = policy_client.policy_assignments.create(scope, name, assignment)

    # Create the identity's role assignment if requested
    if identities is not None and identity_scope:
        from azure.cli.core.commands.arm import assign_identity as _assign_identity_helper
        _assign_identity_helper(cmd.cli_ctx, lambda: createdAssignment, lambda resource: createdAssignment, identity_role, identity_scope)

    return createdAssignment


def _get_resource_id(cli_ctx, val, resource_group, resource_type, resource_namespace):
    from msrestazure.tools import resource_id
    if is_valid_resource_id(val):
        return val

    kwargs = {
        'name': val,
        'resource_group': resource_group,
        'namespace': resource_namespace,
        'type': resource_type,
        'subscription': get_subscription_id(cli_ctx)
    }
    missing_kwargs = {k: v for k, v in kwargs.items() if not v}

    return resource_id(**kwargs) if not missing_kwargs else None


def _build_identities_info(cmd, identities, resourceGroupName):
    identities = identities or []
    ResourceIdentityType = cmd.get_models('ResourceIdentityType')
    ResourceIdentity = cmd.get_models('Identity')
    identity_type = ResourceIdentityType.none
    if not identities or MSI_LOCAL_ID in identities:
        return ResourceIdentity(type=ResourceIdentityType.system_assigned)

    user_assigned_identities = [x for x in identities if x != MSI_LOCAL_ID]
    if user_assigned_identities:
        msiId = _get_resource_id(cmd.cli_ctx, user_assigned_identities[0], resourceGroupName,
                                 'userAssignedIdentities', 'Microsoft.ManagedIdentity')

        UserAssignedIdentitiesValue = cmd.get_models('UserAssignedIdentitiesValue')
        userAssignedIdentity = {msiId: UserAssignedIdentitiesValue()}
        return ResourceIdentity(type=ResourceIdentityType.user_assigned, user_assigned_identities=userAssignedIdentity)

    return ResourceIdentity(type=identity_type)


def update_policy_assignment(cmd, name=None, display_name=None, params=None,
                             resource_group_name=None, scope=None, sku=None,
                             not_scopes=None, enforcement_mode=None, description=None):
    """Updates a policy assignment
    :param not_scopes: Space-separated scopes where the policy assignment does not apply.
    """
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    params = _load_file_string_or_uri(params, 'params', False)

    existing_assignment = policy_client.policy_assignments.get(scope, name)
    PolicyAssignment = cmd.get_models('PolicyAssignment')
    assignment = PolicyAssignment(
        display_name=display_name if display_name is not None else existing_assignment.display_name,
        policy_definition_id=existing_assignment.policy_definition_id,
        scope=existing_assignment.scope,
        enforcement_mode=enforcement_mode if enforcement_mode is not None else existing_assignment.enforcement_mode,
        metadata=existing_assignment.metadata,
        parameters=params if params is not None else existing_assignment.parameters,
        description=description if description is not None else existing_assignment.description)

    if cmd.supported_api_version(min_api='2017-06-01-preview'):
        kwargs_list = existing_assignment.not_scopes
        if not_scopes:
            kwargs_list = []
            for id_arg in not_scopes.split(' '):
                id_parts = parse_resource_id(id_arg)
                if id_parts.get('subscription') or _is_management_group_scope(id_arg):
                    kwargs_list.append(id_arg)
                else:
                    raise InvalidArgumentValueError("Invalid resource ID value in --not-scopes: '%s'" % id_arg)
        assignment.not_scopes = kwargs_list

    if cmd.supported_api_version(min_api='2018-05-01'):
        assignment.location = existing_assignment.location
        assignment.identity = existing_assignment.identity

    if cmd.supported_api_version(min_api='2020-09-01'):
        assignment.non_compliance_messages = existing_assignment.non_compliance_messages

    return policy_client.policy_assignments.create(scope, name, assignment)


def delete_policy_assignment(cmd, name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    policy_client.policy_assignments.delete(scope, name)


def show_policy_assignment(cmd, name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    return policy_client.policy_assignments.get(scope, name)


def list_policy_assignment(cmd, disable_scope_strict_match=None, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    _scope = _build_policy_scope(get_subscription_id(cmd.cli_ctx),
                                 resource_group_name, scope)
    id_parts = parse_resource_id(_scope)
    subscription = id_parts.get('subscription')
    resource_group = id_parts.get('resource_group')
    resource_type = id_parts.get('child_type_1') or id_parts.get('type')
    resource_name = id_parts.get('child_name_1') or id_parts.get('name')
    management_group = _parse_management_group_id(scope)

    if management_group:
        result = policy_client.policy_assignments.list_for_management_group(management_group_id=management_group, filter='atScope()')
    elif all([resource_type, resource_group, subscription]):
        namespace = id_parts.get('namespace')
        parent_resource_path = '' if not id_parts.get('child_name_1') else (id_parts['type'] + '/' + id_parts['name'])
        result = policy_client.policy_assignments.list_for_resource(
            resource_group, namespace,
            parent_resource_path, resource_type, resource_name)
    elif resource_group:
        result = policy_client.policy_assignments.list_for_resource_group(resource_group)
    elif subscription:
        result = policy_client.policy_assignments.list()
    elif scope:
        raise InvalidArgumentValueError('usage error `--scope`: must be a fully qualified ARM ID.')
    else:
        raise ArgumentUsageError('usage error: --scope ARM_ID | --resource-group NAME')

    if not disable_scope_strict_match:
        result = [i for i in result if _scope.lower().strip('/') == i.scope.lower().strip('/')]

    return result


def list_policy_non_compliance_message(cmd, name, scope=None, resource_group_name=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    return policy_client.policy_assignments.get(scope, name).non_compliance_messages


def create_policy_non_compliance_message(cmd, name, message, scope=None, resource_group_name=None,
                                         policy_definition_reference_id=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)

    assignment = policy_client.policy_assignments.get(scope, name)

    NonComplianceMessage = cmd.get_models('NonComplianceMessage')
    created_message = NonComplianceMessage(message=message, policy_definition_reference_id=policy_definition_reference_id)
    if not assignment.non_compliance_messages:
        assignment.non_compliance_messages = []
    assignment.non_compliance_messages.append(created_message)

    return policy_client.policy_assignments.create(scope, name, assignment).non_compliance_messages


def delete_policy_non_compliance_message(cmd, name, message, scope=None, resource_group_name=None,
                                         policy_definition_reference_id=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)

    assignment = policy_client.policy_assignments.get(scope, name)

    NonComplianceMessage = cmd.get_models('NonComplianceMessage')
    message_to_remove = NonComplianceMessage(message=message, policy_definition_reference_id=policy_definition_reference_id)
    if assignment.non_compliance_messages:
        assignment.non_compliance_messages = [existingMessage for existingMessage in assignment.non_compliance_messages if not _is_non_compliance_message_equivalent(existingMessage, message_to_remove)]

    return policy_client.policy_assignments.create(scope, name, assignment).non_compliance_messages


def _is_non_compliance_message_equivalent(first, second):
    first_message = '' if first.message is None else first.message
    seccond_message = '' if second.message is None else second.message
    first_reference_id = '' if first.policy_definition_reference_id is None else first.policy_definition_reference_id
    second_reference_id = '' if second.policy_definition_reference_id is None else second.policy_definition_reference_id

    return first_message.lower() == seccond_message.lower() and first_reference_id.lower() == second_reference_id.lower()


def set_identity(cmd, name, scope=None, resource_group_name=None,
                 mi_system_assigned=None, mi_user_assigned=None,
                 identity_role='Contributor', identity_scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    # Backward compatibility that assign system assigned MSI when none specified.
    identities = None
    if mi_system_assigned is not None or mi_user_assigned is None:
        identities = [MSI_LOCAL_ID]
    else:
        identities = [mi_user_assigned]

    def getter():
        return policy_client.policy_assignments.get(scope, name)

    def setter(policyAssignment):
        policyAssignment.identity = _build_identities_info(cmd, identities, resource_group_name)
        return policy_client.policy_assignments.create(scope, name, policyAssignment)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity_helper
    updatedAssignment = _assign_identity_helper(cmd.cli_ctx, getter, setter, identity_role, identity_scope)
    return updatedAssignment.identity


def show_identity(cmd, name, scope=None, resource_group_name=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    return policy_client.policy_assignments.get(scope, name).identity


def remove_identity(cmd, name, scope=None, resource_group_name=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    policyAssignment = policy_client.policy_assignments.get(scope, name)

    ResourceIdentityType = cmd.get_models('ResourceIdentityType')
    ResourceIdentity = cmd.get_models('Identity')
    policyAssignment.identity = ResourceIdentity(type=ResourceIdentityType.none)
    policyAssignment = policy_client.policy_assignments.create(scope, name, policyAssignment)
    return policyAssignment.identity


def enforce_mutually_exclusive(subscription, management_group):
    if subscription and management_group:
        raise IncorrectUsageError('cannot provide both --subscription and --management-group')


def create_policy_definition(cmd, name, rules=None, params=None, display_name=None, description=None, mode=None,
                             metadata=None, subscription=None, management_group=None):
    rules = _load_file_string_or_uri(rules, 'rules')
    params = _load_file_string_or_uri(params, 'params', False)

    PolicyDefinition = cmd.get_models('PolicyDefinition')
    parameters = PolicyDefinition(policy_rule=rules, parameters=params, description=description,
                                  display_name=display_name)
    if cmd.supported_api_version(min_api='2016-12-01'):
        parameters.mode = mode
    if cmd.supported_api_version(min_api='2017-06-01-preview'):
        parameters.metadata = metadata
    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            policy_client = _resource_policy_client_factory(cmd.cli_ctx)
            return policy_client.policy_definitions.create_or_update_at_management_group(name, management_group, parameters)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_definitions.create_or_update(name, parameters)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return policy_client.policy_definitions.create_or_update(name, parameters)


def create_policy_setdefinition(cmd, name, definitions, params=None, display_name=None, description=None,
                                subscription=None, management_group=None, definition_groups=None, metadata=None):

    definitions = _load_file_string_or_uri(definitions, 'definitions')
    params = _load_file_string_or_uri(params, 'params', False)
    definition_groups = _load_file_string_or_uri(definition_groups, 'definition_groups', False)

    PolicySetDefinition = cmd.get_models('PolicySetDefinition')
    parameters = PolicySetDefinition(policy_definitions=definitions, parameters=params, description=description,
                                     display_name=display_name, policy_definition_groups=definition_groups)

    if cmd.supported_api_version(min_api='2017-06-01-preview'):
        parameters.metadata = metadata
    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            policy_client = _resource_policy_client_factory(cmd.cli_ctx)
            return policy_client.policy_set_definitions.create_or_update_at_management_group(name, management_group, parameters)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_set_definitions.create_or_update(name, parameters)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return policy_client.policy_set_definitions.create_or_update(name, parameters)


def get_policy_definition(cmd, policy_definition_name, subscription=None, management_group=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return _get_custom_or_builtin_policy(cmd, policy_client, policy_definition_name, subscription, management_group)


def get_policy_setdefinition(cmd, policy_set_definition_name, subscription=None, management_group=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return _get_custom_or_builtin_policy(cmd, policy_client, policy_set_definition_name, subscription, management_group, True)


def list_policy_definition(cmd, subscription=None, management_group=None):

    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            policy_client = _resource_policy_client_factory(cmd.cli_ctx)
            return policy_client.policy_definitions.list_by_management_group(management_group)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_definitions.list()

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return policy_client.policy_definitions.list()


def list_policy_setdefinition(cmd, subscription=None, management_group=None):
    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            policy_client = _resource_policy_client_factory(cmd.cli_ctx)
            return policy_client.policy_set_definitions.list_by_management_group(management_group)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_set_definitions.list()

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return policy_client.policy_set_definitions.list()


def delete_policy_definition(cmd, policy_definition_name, subscription=None, management_group=None):
    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            policy_client = _resource_policy_client_factory(cmd.cli_ctx)
            return policy_client.policy_definitions.delete_at_management_group(policy_definition_name, management_group)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_definitions.delete(policy_definition_name)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return policy_client.policy_definitions.delete(policy_definition_name)


def delete_policy_setdefinition(cmd, policy_set_definition_name, subscription=None, management_group=None):
    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            policy_client = _resource_policy_client_factory(cmd.cli_ctx)
            return policy_client.policy_set_definitions.delete_at_management_group(policy_set_definition_name,
                                                                                   management_group)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_set_definitions.delete(policy_set_definition_name)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    return policy_client.policy_set_definitions.delete(policy_set_definition_name)


def update_policy_definition(cmd, policy_definition_name, rules=None, params=None,
                             display_name=None, description=None, metadata=None, mode=None,
                             subscription=None, management_group=None):

    rules = _load_file_string_or_uri(rules, 'rules', False)
    params = _load_file_string_or_uri(params, 'params', False)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    definition = _get_custom_or_builtin_policy(cmd, policy_client, policy_definition_name, subscription, management_group)
    # pylint: disable=line-too-long,no-member

    PolicyDefinition = cmd.get_models('PolicyDefinition')
    parameters = PolicyDefinition(
        policy_rule=rules if rules is not None else definition.policy_rule,
        parameters=params if params is not None else definition.parameters,
        display_name=display_name if display_name is not None else definition.display_name,
        description=description if description is not None else definition.description,
        metadata=metadata if metadata is not None else definition.metadata)

    if cmd.supported_api_version(min_api='2016-12-01'):
        parameters.mode = mode
    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            return policy_client.policy_definitions.create_or_update_at_management_group(policy_definition_name, management_group, parameters)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_definitions.create_or_update(policy_definition_name, parameters)

    return policy_client.policy_definitions.create_or_update(policy_definition_name, parameters)


def update_policy_setdefinition(cmd, policy_set_definition_name, definitions=None, params=None,
                                display_name=None, description=None,
                                subscription=None, management_group=None, definition_groups=None, metadata=None):

    definitions = _load_file_string_or_uri(definitions, 'definitions', False)
    params = _load_file_string_or_uri(params, 'params', False)
    definition_groups = _load_file_string_or_uri(definition_groups, 'definition_groups', False)

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    definition = _get_custom_or_builtin_policy(cmd, policy_client, policy_set_definition_name, subscription, management_group, True)
    # pylint: disable=line-too-long,no-member
    PolicySetDefinition = cmd.get_models('PolicySetDefinition')
    parameters = PolicySetDefinition(
        policy_definitions=definitions if definitions is not None else definition.policy_definitions,
        description=description if description is not None else definition.description,
        display_name=display_name if display_name is not None else definition.display_name,
        parameters=params if params is not None else definition.parameters,
        policy_definition_groups=definition_groups if definition_groups is not None else definition.policy_definition_groups,
        metadata=metadata if metadata is not None else definition.metadata)

    if cmd.supported_api_version(min_api='2018-03-01'):
        enforce_mutually_exclusive(subscription, management_group)
        if management_group:
            return policy_client.policy_set_definitions.create_or_update_at_management_group(policy_set_definition_name, management_group, parameters)
        if subscription:
            subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
            policy_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_POLICY,
                                                    subscription_id=subscription_id)
            return policy_client.policy_set_definitions.create_or_update(policy_set_definition_name, parameters)

    return policy_client.policy_set_definitions.create_or_update(policy_set_definition_name, parameters)


def create_policy_exemption(cmd, name, policy_assignment=None, exemption_category=None,
                            policy_definition_reference_ids=None, expires_on=None,
                            display_name=None, description=None, resource_group_name=None, scope=None,
                            metadata=None):
    if policy_assignment is None:
        raise RequiredArgumentMissingError('--policy_assignment is required')
    if exemption_category is None:
        raise RequiredArgumentMissingError('--exemption_category is required')

    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    PolicyExemption = cmd.get_models('PolicyExemption')
    exemption = PolicyExemption(policy_assignment_id=policy_assignment, policy_definition_reference_ids=policy_definition_reference_ids,
                                exemption_category=exemption_category, expires_on=expires_on,
                                display_name=display_name, description=description, metadata=metadata)
    createdExemption = policy_client.policy_exemptions.create_or_update(scope, name, exemption)
    return createdExemption


def update_policy_exemption(cmd, name, exemption_category=None,
                            policy_definition_reference_ids=None, expires_on=None,
                            display_name=None, description=None, resource_group_name=None, scope=None,
                            metadata=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    PolicyExemption = cmd.get_models('PolicyExemption')
    exemption = policy_client.policy_exemptions.get(scope, name)
    parameters = PolicyExemption(
        policy_assignment_id=exemption.policy_assignment_id,
        policy_definition_reference_ids=policy_definition_reference_ids if policy_definition_reference_ids is not None else exemption.policy_definition_reference_ids,
        exemption_category=exemption_category if exemption_category is not None else exemption.exemption_category,
        expires_on=expires_on if expires_on is not None else exemption.expires_on,
        display_name=display_name if display_name is not None else exemption.display_name,
        description=description if description is not None else exemption.description,
        metadata=metadata if metadata is not None else exemption.metadata)
    updatedExemption = policy_client.policy_exemptions.create_or_update(scope, name, parameters)
    return updatedExemption


def delete_policy_exemption(cmd, name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    policy_client.policy_exemptions.delete(scope, name)


def get_policy_exemption(cmd, name, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = _build_policy_scope(subscription_id, resource_group_name, scope)
    return policy_client.policy_exemptions.get(scope, name)


def list_policy_exemption(cmd, disable_scope_strict_match=None, resource_group_name=None, scope=None):
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    _scope = _build_policy_scope(get_subscription_id(cmd.cli_ctx),
                                 resource_group_name, scope)
    id_parts = parse_resource_id(_scope)
    subscription = id_parts.get('subscription')
    resource_group = id_parts.get('resource_group')
    resource_type = id_parts.get('child_type_1') or id_parts.get('type')
    resource_name = id_parts.get('child_name_1') or id_parts.get('name')
    management_group = _parse_management_group_id(scope)

    if management_group:
        result = policy_client.policy_exemptions.list_for_management_group(management_group_id=management_group, filter='atScope()')
    elif all([resource_type, resource_group, subscription]):
        namespace = id_parts.get('namespace')
        parent_resource_path = '' if not id_parts.get('child_name_1') else (id_parts['type'] + '/' + id_parts['name'])
        result = policy_client.policy_exemptions.list_for_resource(
            resource_group, namespace,
            parent_resource_path, resource_type, resource_name)
    elif resource_group:
        result = policy_client.policy_exemptions.list_for_resource_group(resource_group)
    elif subscription:
        result = policy_client.policy_exemptions.list()
    elif scope:
        raise InvalidArgumentValueError('usage error `--scope`: must be a fully qualified ARM ID.')
    else:
        raise ArgumentUsageError('usage error: --scope ARM_ID | --resource-group NAME')

    if not disable_scope_strict_match:
        result = [i for i in result if i.id.lower().strip('/').startswith(_scope.lower().strip('/') + "/providers/microsoft.authorization/policyexemptions")]

    return result


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
        if subscription in (sub['id'], sub['name']):
            return sub['id']
    raise CLIError("Subscription not found in the current context.")


def _get_parent_id_from_parent(parent):
    if parent is None or _is_management_group_scope(parent):
        return parent
    return "/providers/Microsoft.Management/managementGroups/" + parent


def _is_management_group_scope(scope):
    return scope is not None and scope.lower().startswith("/providers/microsoft.management/managementgroups")


def cli_managementgroups_get_tenant_backfill_status(
        cmd,
        client):
    return client.tenant_backfill_status()


def cli_managementgroups_start_tenant_backfill(
        cmd,
        client):
    return client.start_tenant_backfill()


def cli_managementgroups_get_name_availability(cmd, client, group_name):
    from azure.mgmt.managementgroups.models import CheckNameAvailabilityRequest
    checkNameAvailabilityRequest = CheckNameAvailabilityRequest(name=group_name)
    return client.check_name_availability(checkNameAvailabilityRequest)


def cli_managementgroups_group_list(cmd, client, no_register=False):
    if not no_register:
        _register_rp(cmd.cli_ctx)
    return client.list()


def cli_managementgroups_group_show(
        cmd,
        client,
        group_name,
        expand=False,
        recurse=False,
        no_register=False):
    if not no_register:
        _register_rp(cmd.cli_ctx)
    if expand:
        return client.get(group_name, "children", recurse)
    return client.get(group_name)


def cli_managementgroups_group_create(
        cmd,
        client,
        group_name,
        display_name=None,
        parent=None,
        no_register=False):
    if not no_register:
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
    return client.begin_create_or_update(group_name, create_mgmt_grp_request)


def cli_managementgroups_group_update_custom_func(
        instance,
        display_name=None,
        parent_id=None):
    parent_group_id = _get_parent_id_from_parent(parent_id)
    instance.display_name = display_name
    instance.parent_group_id = parent_group_id
    return instance


def cli_managementgroups_group_update_get():
    from azure.mgmt.managementgroups.models import PatchManagementGroupRequest
    update_parameters = PatchManagementGroupRequest(display_name=None, parent_group_id=None)
    return update_parameters


def cli_managementgroups_group_update_set(
        cmd, client, group_name, parameters=None):
    return client.update(group_name, parameters)


def cli_managementgroups_group_delete(cmd, client, group_name, no_register=False):
    if not no_register:
        _register_rp(cmd.cli_ctx)
    return client.begin_delete(group_name)


def cli_managementgroups_subscription_add(
        cmd, client, group_name, subscription):
    subscription_id = _get_subscription_id_from_subscription(
        cmd.cli_ctx, subscription)
    return client.create(group_name, subscription_id)


def cli_managementgroups_subscription_show(
        cmd,
        client,
        group_name,
        subscription):
    subscription_id = _get_subscription_id_from_subscription(cmd.cli_ctx, subscription)
    return client.get_subscription(group_name, subscription_id)


def cli_managementgroups_subscription_show_sub_under_mg(
        cmd,
        client,
        group_name):
    return client.get_subscriptions_under_management_group(group_name)


def cli_managementgroups_subscription_remove(
        cmd, client, group_name, subscription):
    subscription_id = _get_subscription_id_from_subscription(
        cmd.cli_ctx, subscription)
    return client.delete(group_name, subscription_id)


def cli_managementgroups_entities_list(
        cmd,
        client):
    return client.list()


def cli_hierarchy_settings_list(
        cmd,
        client,
        group_name):
    return client.list(group_name)


def cli_hierarchy_settings_create(
        cmd,
        client,
        group_name,
        require_authorization_for_group_creation=None,
        default_management_group=None):
    from azure.mgmt.managementgroups.models import CreateOrUpdateSettingsRequest
    create_or_update_parameters = CreateOrUpdateSettingsRequest(require_authorization_for_group_creation=require_authorization_for_group_creation, default_management_group=default_management_group)
    return client.create_or_update(group_name, create_or_update_parameters)


def cli_hierarchy_settings_delete(
        cmd,
        client,
        group_name):
    return client.delete(group_name)


def cli_hierarchysettings_group_update_custom_func(
        instance,
        require_authorization_for_group_creation=None,
        default_management_group=None):
    instance.require_authorization_for_group_creation = require_authorization_for_group_creation
    instance.default_management_group = default_management_group
    return instance


def cli_hierarchysettings_group_update_get():
    from azure.mgmt.managementgroups.models import CreateOrUpdateSettingsRequest
    update_parameters = CreateOrUpdateSettingsRequest(require_authorization_for_group_creation=None, default_management_group=None)
    return update_parameters


def cli_hierarchysettings_group_update_set(
        cmd, client, group_name, parameters=None):
    return client.update(group_name, parameters)


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
            if resource.get('child_type_3', None) is None:
                _resource_type = resource.get('child_type_1', None)
                _resource_name = resource.get('child_name_1', None)
                parent = (resource['type'] + '/' + resource['name'])
            else:
                _resource_type = resource.get('child_type_2', None)
                _resource_name = resource.get('child_name_2', None)
                parent = (resource['type'] + '/' + resource['name'] + '/' +
                          resource['child_type_1'] + '/' + resource['child_name_1'])
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
    ManagementLockObject = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_LOCKS, 'ManagementLockObject', mod='models')
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
    links_client = _resource_links_client_factory(cmd.cli_ctx).resource_links

    ResourceLink = cmd.get_models('ResourceLink')
    ResourceLinkProperties = cmd.get_models('ResourceLinkProperties')
    properties = ResourceLinkProperties(target_id=target_id, notes=notes)
    resource_link = ResourceLink(properties=properties)
    links_client.create_or_update(link_id, resource_link)


def update_resource_link(cmd, link_id, target_id=None, notes=None):
    links_client = _resource_links_client_factory(cmd.cli_ctx).resource_links
    params = links_client.get(link_id)

    ResourceLink = cmd.get_models('ResourceLink')
    ResourceLinkProperties = cmd.get_models('ResourceLinkProperties')
    # pylint: disable=no-member
    properties = ResourceLinkProperties(
        target_id=target_id if target_id is not None else params.properties.target_id,
        notes=notes if notes is not None else params.properties.notes)
    resource_link = ResourceLink(properties=properties)
    links_client.create_or_update(link_id, resource_link)


def list_resource_links(cmd, scope=None, filter_string=None):
    links_client = _resource_links_client_factory(cmd.cli_ctx).resource_links
    if scope is not None:
        return links_client.list_at_source_scope(scope, filter=filter_string)
    return links_client.list_at_subscription(filter=filter_string)
# endregion


# region tags
def get_tag_at_scope(cmd, resource_id=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    if resource_id is not None:
        return rcf.tags.get_at_scope(scope=resource_id)

    return rcf.tags.list()


def create_or_update_tag_at_scope(cmd, resource_id=None, tags=None, tag_name=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    if resource_id is not None:
        if not tags:
            raise IncorrectUsageError("Tags could not be empty.")
        Tags = cmd.get_models('Tags')
        tag_obj = Tags(tags=tags)
        TagsResource = cmd.get_models('TagsResource')
        tags_resource = TagsResource(properties=tag_obj)
        return rcf.tags.create_or_update_at_scope(scope=resource_id, parameters=tags_resource)

    return rcf.tags.create_or_update(tag_name=tag_name)


def delete_tag_at_scope(cmd, resource_id=None, tag_name=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    if resource_id is not None:
        return rcf.tags.delete_at_scope(scope=resource_id)

    return rcf.tags.delete(tag_name=tag_name)


def update_tag_at_scope(cmd, resource_id, tags, operation):
    rcf = _resource_client_factory(cmd.cli_ctx)
    if not tags:
        raise IncorrectUsageError("Tags could not be empty.")
    Tags = cmd.get_models('Tags')
    tag_obj = Tags(tags=tags)
    TagsPatchResource = cmd.get_models('TagsPatchResource')
    tags_resource = TagsPatchResource(properties=tag_obj, operation=operation)
    return rcf.tags.update_at_scope(scope=resource_id, parameters=tags_resource)
# endregion


class _ResourceUtils:  # pylint: disable=too-many-instance-attributes
    def __init__(self, cli_ctx,
                 resource_group_name=None, resource_provider_namespace=None,
                 parent_resource_path=None, resource_type=None, resource_name=None,
                 resource_id=None, api_version=None, rcf=None, latest_include_preview=False):
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
                api_version = _ResourceUtils._resolve_api_version_by_id(self.rcf, resource_id,
                                                                        latest_include_preview=latest_include_preview)
            else:
                _validate_resource_inputs(resource_group_name, resource_provider_namespace,
                                          resource_type, resource_name)
                api_version = _ResourceUtils.resolve_api_version(self.rcf,
                                                                 resource_provider_namespace,
                                                                 parent_resource_path,
                                                                 resource_type,
                                                                 latest_include_preview=latest_include_preview)

        self.resource_group_name = resource_group_name
        self.resource_provider_namespace = resource_provider_namespace
        self.parent_resource_path = parent_resource_path if parent_resource_path else ''
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.resource_id = resource_id
        self.api_version = api_version

    def create_resource(self, properties, location, is_full_object):
        try:
            res = json.loads(properties)
        except json.decoder.JSONDecodeError as ex:
            raise CLIError('Error parsing JSON.\n{}\n{}'.format(properties, ex))

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
            resource = self.rcf.resources.begin_create_or_update_by_id(self.resource_id,
                                                                       self.api_version,
                                                                       res)
        else:
            resource = self.rcf.resources.begin_create_or_update(self.resource_group_name,
                                                                 self.resource_provider_namespace,
                                                                 self.parent_resource_path,
                                                                 self.resource_type,
                                                                 self.resource_name,
                                                                 self.api_version,
                                                                 res)
        return resource

    def get_resource(self, include_response_body=False):

        def add_response_body(pipeline_response, deserialized, *kwargs):
            resource = deserialized
            response_body = {}
            try:
                response_body = pipeline_response.http_response.internal_response.content.decode()
            except AttributeError:
                pass
            setattr(resource, 'response_body', json.loads(response_body))
            return resource

        cls = None
        if include_response_body:
            cls = add_response_body

        if self.resource_id:
            resource = self.rcf.resources.get_by_id(self.resource_id, self.api_version, cls=cls)
        else:
            resource = self.rcf.resources.get(self.resource_group_name,
                                              self.resource_provider_namespace,
                                              self.parent_resource_path,
                                              self.resource_type,
                                              self.resource_name,
                                              self.api_version,
                                              cls=cls)

        return resource

    def delete(self):
        if self.resource_id:
            return self.rcf.resources.begin_delete_by_id(self.resource_id, self.api_version)
        return self.rcf.resources.begin_delete(self.resource_group_name,
                                               self.resource_provider_namespace,
                                               self.parent_resource_path,
                                               self.resource_type,
                                               self.resource_name,
                                               self.api_version)

    def update(self, parameters):
        if self.resource_id:
            return self.rcf.resources.begin_create_or_update_by_id(self.resource_id,
                                                                   self.api_version,
                                                                   parameters)
        return self.rcf.resources.begin_create_or_update(self.resource_group_name,
                                                         self.resource_provider_namespace,
                                                         self.parent_resource_path,
                                                         self.resource_type,
                                                         self.resource_name,
                                                         self.api_version,
                                                         parameters)

    def tag(self, tags, is_incremental=False):
        resource = self.get_resource()

        if is_incremental is True:
            if not tags:
                raise CLIError("When modifying tag incrementally, the parameters of tag must have specific values.")
            if resource.tags:
                resource.tags.update(tags)
                tags = resource.tags

        # please add the service type that needs to be requested with PATCH type here
        # for example: the properties of RecoveryServices/vaults must be filled, and a PUT request that passes back
        # to properties will fail due to the lack of properties, so the PATCH type should be used
        need_patch_service = ['Microsoft.RecoveryServices/vaults', 'Microsoft.Resources/resourceGroups',
                              'Microsoft.ContainerRegistry/registries/webhooks',
                              'Microsoft.ContainerInstance/containerGroups',
                              'Microsoft.Network/publicIPAddresses']

        if resource is not None and resource.type in need_patch_service:
            parameters = GenericResource(tags=tags)
            if self.resource_id:
                return self.rcf.resources.begin_update_by_id(self.resource_id, self.api_version, parameters)
            return self.rcf.resources.begin_update(self.resource_group_name,
                                                   self.resource_provider_namespace,
                                                   self.parent_resource_path,
                                                   self.resource_type,
                                                   self.resource_name,
                                                   self.api_version,
                                                   parameters)

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
            return self.rcf.resources.begin_create_or_update_by_id(self.resource_id, self.api_version,
                                                                   parameters)
        return self.rcf.resources.begin_create_or_update(self.resource_group_name,
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

        if self.resource_id:
            url = client.format_url(
                '{resource_id}/{action}',
                resource_id=self.resource_id,
                action=serialize.url("action", action, 'str'))
        else:
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
                    "self._config.subscription_id", self.rcf.resources._config.subscription_id, 'str'),
                action=serialize.url("action", action, 'str'))

        # Construct parameters
        query_parameters['api-version'] = serialize.query("api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        # This value of accept_language comes from the fixed configuration in the AzureConfiguration in track 1.
        header_parameters['accept-language'] = 'en-US'

        body_content_kwargs = {}
        body_content_kwargs['content'] = json.loads(request_body) if request_body else None

        # Construct and send request
        def long_running_send():
            request = client.post(url, query_parameters, header_parameters, **body_content_kwargs)
            pipeline_response = client._pipeline.run(request, stream=False)
            return pipeline_response.http_response.internal_response

        def get_long_running_status(status_link, headers=None):
            request = client.get(status_link, query_parameters, header_parameters)
            if headers:
                request.headers.update(headers)
            pipeline_response = client._pipeline.run(request, stream=False)
            return pipeline_response.http_response.internal_response

        def get_long_running_output(response):
            from azure.core.exceptions import HttpResponseError
            if response.status_code not in [200, 202, 204]:
                exp = HttpResponseError(response)
                exp.request_id = response.headers.get('x-ms-request-id')
                raise exp
            return response.text

        return AzureOperationPoller(long_running_send, get_long_running_output, get_long_running_status)

    @staticmethod
    def resolve_api_version(rcf, resource_provider_namespace, parent_resource_path, resource_type,
                            latest_include_preview=False):
        provider = rcf.providers.get(resource_provider_namespace)

        # If available, we will use parent resource's api-version
        resource_type_str = (parent_resource_path.split('/')[0] if parent_resource_path else resource_type)

        rt = [t for t in provider.resource_types
              if t.resource_type.lower() == resource_type_str.lower()]
        if not rt:
            raise IncorrectUsageError('Resource type {} not found.'.format(resource_type_str))
        if len(rt) == 1 and rt[0].api_versions:
            # If latest_include_preview is true,
            # the last api-version will be taken regardless of whether it is preview version or not
            if latest_include_preview:
                return rt[0].api_versions[0]
            # Take the latest stable version first.
            # if there is no stable version, the latest preview version will be taken.
            npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
            return npv[0] if npv else rt[0].api_versions[0]
        raise IncorrectUsageError(
            'API version is required and could not be resolved for resource {}'
            .format(resource_type))

    @staticmethod
    def _resolve_api_version_by_id(rcf, resource_id, latest_include_preview=False):
        parts = parse_resource_id(resource_id)

        if len(parts) == 2 and parts['subscription'] is not None and parts['resource_group'] is not None:
            return AZURE_API_PROFILES['latest'][ResourceType.MGMT_RESOURCE_RESOURCES]

        if 'namespace' not in parts:
            raise CLIError('The type of value entered by --ids parameter is not supported.')

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

        return _ResourceUtils.resolve_api_version(rcf, namespace, parent, resource_type,
                                                  latest_include_preview=latest_include_preview)


def install_bicep_cli(cmd, version=None, target_platform=None):
    # The parameter version is actually a git tag here.
    ensure_bicep_installation(release_tag=version, target_platform=target_platform)


def uninstall_bicep_cli(cmd):
    remove_bicep_installation()


def upgrade_bicep_cli(cmd, target_platform=None):
    latest_release_tag = get_bicep_latest_release_tag()
    ensure_bicep_installation(release_tag=latest_release_tag, target_platform=target_platform)


def build_bicep_file(cmd, file, stdout=None, outdir=None, outfile=None, no_restore=None):
    args = ["build", file]
    if outdir:
        args += ["--outdir", outdir]
    if outfile:
        args += ["--outfile", outfile]
    if no_restore:
        args += ["--no-restore"]
    if stdout:
        args += ["--stdout"]

    output = run_bicep_command(args)

    if stdout:
        print(output)


def publish_bicep_file(cmd, file, target):
    ensure_bicep_installation()

    minimum_supported_version = "0.4.1008"
    if bicep_version_greater_than_or_equal_to(minimum_supported_version):
        run_bicep_command(["publish", file, "--target", target])
    else:
        logger.error("az bicep publish could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def restore_bicep_file(cmd, file, force=None):
    ensure_bicep_installation()

    minimum_supported_version = "0.4.1008"
    if bicep_version_greater_than_or_equal_to(minimum_supported_version):
        args = ["restore", file]
        if force:
            args += ["--force"]
        run_bicep_command(args)
    else:
        logger.error("az bicep restore could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def decompile_bicep_file(cmd, file, force=None):
    args = ["decompile", file]
    if force:
        args += ["--force"]
    run_bicep_command(args)


def show_bicep_cli_version(cmd):
    print(run_bicep_command(["--version"], auto_install=False))


def list_bicep_cli_versions(cmd):
    return get_bicep_available_release_tags()

def generate_params_file(cmd, file, no_restore=None, outdir=None, outfile=None, stdout=None):
    ensure_bicep_installation()

    minimum_supported_version = "0.7.4"
    if bicep_version_greater_than_or_equal_to(minimum_supported_version):
        args = ["generate-params", file]
        if no_restore:
            args += ["--no-restore"]
        if outdir:
            args += ["--outdir", outdir]
        if outfile:
            args += ["--outfile", outfile]
        if stdout:
            args += ["--stdout"]

        output = run_bicep_command(args)

        if stdout:
            print(output)
    else:
        logger.error("az bicep generate-params could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def create_resourcemanager_privatelink(
        cmd, resource_group, name, location):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    ResourceManagementPrivateLinkLocation = cmd.get_models(
        'ResourceManagementPrivateLinkLocation')
    resource_management_private_link_location = ResourceManagementPrivateLinkLocation(
        location=location)
    return rcf.resource_management_private_link.put(resource_group, name, resource_management_private_link_location)


def get_resourcemanager_privatelink(cmd, resource_group, name):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    return rcf.resource_management_private_link.get(resource_group, name)


def list_resourcemanager_privatelink(cmd, resource_group=None):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    if resource_group:
        return rcf.resource_management_private_link.list_by_resource_group(resource_group)
    return rcf.resource_management_private_link.list()


def delete_resourcemanager_privatelink(cmd, resource_group, name):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    return rcf.resource_management_private_link.delete(resource_group, name)


def create_private_link_association(cmd, management_group_id, name, privatelink, public_network_access):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    PrivateLinkProperties, PrivateLinkObject = cmd.get_models(
        'PrivateLinkAssociationProperties', 'PrivateLinkAssociationObject')
    pl = PrivateLinkObject(properties=PrivateLinkProperties(
        private_link=privatelink, public_network_access=public_network_access))
    return rcf.private_link_association.put(group_id=management_group_id, pla_id=name, parameters=pl)


def get_private_link_association(cmd, management_group_id, name):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    return rcf.private_link_association.get(group_id=management_group_id, pla_id=name)


def delete_private_link_association(cmd, management_group_id, name):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    return rcf.private_link_association.delete(group_id=management_group_id, pla_id=name)


def list_private_link_association(cmd, management_group_id):
    rcf = _resource_privatelinks_client_factory(cmd.cli_ctx)
    return rcf.private_link_association.list(group_id=management_group_id)
