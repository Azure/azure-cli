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
import re
import ssl

from urllib.request import urlopen
from urllib.parse import urlparse, unquote

from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id

from azure.mgmt.resource.resources.models import GenericResource
from azure.mgmt.resource.deployments.models import DeploymentMode

from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError, ResourceNotFoundError
from azure.cli.core.parser import IncorrectUsageError
from azure.cli.core.util import get_file_json, read_file_content, shell_safe_json_parse, sdk_no_wait
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import raise_subdivision_deployment_error
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.profiles import ResourceType, get_sdk, get_api_version, AZURE_API_PROFILES

from azure.cli.command_modules.resource._client_factory import (
    _resource_client_factory, _resource_deployments_client_factory, _resource_lock_client_factory,
    _resource_links_client_factory, _resource_deploymentscripts_client_factory, _resource_deploymentstacks_client_factory, _authorization_management_client, _resource_managedapps_client_factory, _resource_templatespecs_client_factory, _resource_privatelinks_client_factory)
from azure.cli.command_modules.resource._validators import _parse_lock_id
from azure.cli.command_modules.resource.parameters import StacksActionOnUnmanage

from azure.core.pipeline.policies import SansIOHTTPPolicy

from knack.log import get_logger
from knack.prompting import prompt, prompt_pass, prompt_t_f, prompt_choice_list, prompt_int, NoTTYException
from knack.util import CLIError

from ._formatters import format_what_if_operation_result
from ._bicep import (
    run_bicep_command,
    is_bicep_file,
    is_bicepparam_file,
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
    from azure.mgmt.core.tools import resource_id as resource_id_from_dict
    try:
        return resource_id_from_dict(**kwargs)
    except KeyError:
        return None


def _rfc6901_decode(encoded):
    return unquote(encoded).replace("~1", "/").replace("~0", "~")


def _get_json_pointer_segments(json_pointer):
    return [_rfc6901_decode(segment) for segment in json_pointer.split('/')]


def _resolve_parameter_type(parameter, template):
    current = parameter
    visited = set()
    while '$ref' in current:
        referenced = current.get('$ref')
        if referenced in visited:
            raise CLIError("Cycle detected with processing {}.".format(referenced))
        visited.add(referenced)

        segments = _get_json_pointer_segments(referenced)
        if len(segments) < 2 or segments[0] != "#" or not (segments[1] in ['definitions', 'parameters', 'outputs']):
            raise CLIError("Invalid $ref {}.".format(referenced))

        resolved = _resolve_type_from_path(referenced, segments[2:], template.get(segments[1])).copy()

        # it's possible to override some of these properties: the highest-level non-null value wins
        if current.get('nullable', None) is not None:
            resolved['nullable'] = current.get('nullable')
        if current.get('minLength', None) is not None:
            resolved['minLength'] = current.get('minLength')
        if current.get('maxLength', None) is not None:
            resolved['maxLength'] = current.get('maxLength')
        if current.get('allowedValues', None) is not None:
            resolved['allowedValues'] = current.get('allowedValues')

        current = resolved

    return current


def _resolve_type_from_path(current_ref, segments, definitions):
    current = definitions
    for segment in segments:
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit() and 0 <= int(segment) < len(current):
            current = current[int(segment)]
        else:
            raise CLIError("Failed to resolve path {}.".format(current_ref))

    return current


def _try_parse_key_value_object(parameters, template_obj, value):
    # support situation where empty JSON "{}" is provided
    if value == '{}' and not parameters:
        return True

    try:
        key, value = value.split('=', 1)
    except ValueError:
        return False

    param = template_obj.get('parameters', {}).get(key, None)
    if param is None:
        raise CLIError("unrecognized template parameter '{}'. Allowed parameters: {}"
                       .format(key, ', '.join(sorted(template_obj.get('parameters', {}).keys()))))

    param_type_data = _resolve_parameter_type(param, template_obj)
    param_type = param_type_data.get('type')

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


def _process_parameters(template_obj, parameter_lists):  # pylint: disable=too-many-statements

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
            elif not _try_parse_key_value_object(parameters, template_obj, item):
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
        param_type_data = _resolve_parameter_type(parameter, template)

        if 'defaultValue' in parameter:
            continue
        if param_type_data.get('nullable', False):
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


def _is_bicepparam_file_provided(parameters):
    if not parameters or len(parameters) < 1:
        return False

    for parameter_list in parameters:
        for parameter_item in parameter_list:
            if is_bicepparam_file(parameter_item):
                return True
    return False


def _ssl_context():
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
        template_for_deployment = None  # Use template_link for URI-based deployments
    else:
        # This function is resource-group-specific, so we hardcode 'resourceGroup' deployment scope
        template_content, template_obj = _process_template_file(cmd, template_file, 'resourceGroup')
        template_for_deployment = _get_template_for_deployment(template_uri, None, template_file, template_content, template_obj, None)

    if rollback_on_error == '':
        on_error_deployment = OnErrorDeployment(type='LastSuccessful')
    elif rollback_on_error:
        on_error_deployment = OnErrorDeployment(type='SpecificDeployment', deployment_name=rollback_on_error)

    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(template_obj, parameters) or {}
    parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters, no_prompt)

    parameters = json.loads(json.dumps(parameters))

    properties = DeploymentProperties(template=template_for_deployment, template_link=template_link,
                                      parameters=parameters, mode=mode, on_error_deployment=on_error_deployment)

    smc = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_DEPLOYMENTS,
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
    try:
        validation_poller = deployment_client.begin_validate(resource_group_name, deployment_name, deployment)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

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
        modified_data = json.loads(request_data)

        if modified_data.get('properties', {}).get('template'):
            template = modified_data["properties"]["template"]
            del modified_data["properties"]["template"]

            # templateLink and template cannot exist at the same time in deployment_dry_run mode
            if "templateLink" in modified_data["properties"].keys():
                del modified_data["properties"]["templateLink"]

            # The 'template' and other properties (such as 'parameters','mode'...) are spliced and encoded into the UTF-8 bytes as the request data
            # The format of the request data is: {"properties": {"parameters": {...}, "mode": "Incremental", template:{\r\n  "$schema": "...",\r\n  "contentVersion": "...",\r\n  "parameters": {...}}}
            # This is not an ordinary JSON format, but it is a JSONC format that service can deserialize
            # If not do this splicing, the request data generated by default serialization cannot be deserialized on the service side.
            # Because the service cannot deserialize the template element: "template": "{\r\n  \"$schema\": \"...\",\r\n  \"contentVersion\": \"...\",\r\n  \"parameters\": {...}}"
            partial_request = json.dumps(modified_data)
            json_data = partial_request[:-2] + ", template:" + template + r"}}"

            http_request.data = json_data.encode('utf-8')

            # This caused a very difficult-to-debug issue, because AzCLI's debug logs are written before this transformation.
            # This means the logs do not accurately represent the bytes being sent to the server.
            # If you see "The request content was invalid and could not be deserialized" in the response, this might be something to investigate.
            logger.debug("HTTP content is being overwritten to preserve template whitepace accurately. The request body logging may not accurately represent this.")


# pylint: disable=unused-argument
def deploy_arm_template_at_subscription_scope(cmd,
                                              template_file=None, template_uri=None, parameters=None,
                                              deployment_name=None, deployment_location=None,
                                              no_wait=False, handle_extended_json_format=None, no_prompt=False,
                                              confirm_with_what_if=None, what_if_result_format=None,
                                              what_if_exclude_change_types=None, template_spec=None, query_string=None,
                                              what_if=None, proceed_if_no_change=None, validation_level=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_subscription_scope_core(cmd,
                                                                                 template_file=template_file, template_uri=template_uri,
                                                                                 parameters=parameters, deployment_name=deployment_name,
                                                                                 deployment_location=deployment_location,
                                                                                 result_format=what_if_result_format,
                                                                                 exclude_change_types=what_if_exclude_change_types,
                                                                                 no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                                 return_result=True, validation_level=validation_level)
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
                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                      validation_level=validation_level)


# pylint: disable=unused-argument
def validate_arm_template_at_subscription_scope(cmd,
                                                template_file=None, template_uri=None, parameters=None,
                                                deployment_name=None, deployment_location=None,
                                                no_wait=False, handle_extended_json_format=None,
                                                no_prompt=False, template_spec=None, query_string=None,
                                                validation_level=None):
    return _deploy_arm_template_at_subscription_scope(cmd=cmd,
                                                      template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                      deployment_name=deployment_name, deployment_location=deployment_location,
                                                      validate_only=True, no_wait=no_wait,
                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                      validation_level=validation_level)


def _deploy_arm_template_at_subscription_scope(cmd,
                                               template_file=None, template_uri=None, parameters=None,
                                               deployment_name=None, deployment_location=None, validate_only=False,
                                               no_wait=False, no_prompt=False, template_spec=None, query_string=None,
                                               validation_level=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'subscription', template_file=template_file,
                                                                      template_uri=template_uri, parameters=parameters,
                                                                      mode='Incremental',
                                                                      no_prompt=no_prompt,
                                                                      template_spec=template_spec, query_string=query_string,
                                                                      validation_level=validation_level)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=(template_uri is None and template_spec is None))

    from azure.core.exceptions import HttpResponseError
    Deployment = cmd.get_models('Deployment')
    deployment = Deployment(properties=deployment_properties, location=deployment_location)
    try:
        validation_poller = mgmt_client.begin_validate_at_subscription_scope(deployment_name, deployment)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

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
                                          what_if=None, proceed_if_no_change=None, validation_level=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_resource_group_core(cmd,
                                                                             resource_group_name=resource_group_name,
                                                                             template_file=template_file, template_uri=template_uri,
                                                                             parameters=parameters, deployment_name=deployment_name, mode=mode,
                                                                             aux_tenants=aux_tenants, result_format=what_if_result_format,
                                                                             exclude_change_types=what_if_exclude_change_types,
                                                                             no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                             return_result=True, validation_level=validation_level)
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
                                                  no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                  validation_level=validation_level)


# pylint: disable=unused-argument
def validate_arm_template_at_resource_group(cmd,
                                            resource_group_name=None,
                                            template_file=None, template_uri=None, parameters=None,
                                            deployment_name=None, mode=None, rollback_on_error=None,
                                            no_wait=False, handle_extended_json_format=None, no_prompt=False, template_spec=None, query_string=None,
                                            validation_level=None):
    return _deploy_arm_template_at_resource_group(cmd,
                                                  resource_group_name=resource_group_name,
                                                  template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                  deployment_name=deployment_name, mode=mode, rollback_on_error=rollback_on_error,
                                                  validate_only=True, no_wait=no_wait,
                                                  no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                  validation_level=validation_level)


def _deploy_arm_template_at_resource_group(cmd,
                                           resource_group_name=None,
                                           template_file=None, template_uri=None, parameters=None,
                                           deployment_name=None, mode=None, rollback_on_error=None,
                                           validate_only=False, no_wait=False,
                                           aux_subscriptions=None, aux_tenants=None, no_prompt=False, template_spec=None, query_string=None,
                                           validation_level=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'resourceGroup', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode=mode,
                                                                      rollback_on_error=rollback_on_error,
                                                                      no_prompt=no_prompt, template_spec=template_spec,
                                                                      query_string=query_string, validation_level=validation_level)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, aux_subscriptions=aux_subscriptions,
                                                    aux_tenants=aux_tenants, plug_pipeline=deployment_properties.template_link is None)

    from azure.core.exceptions import HttpResponseError
    Deployment = cmd.get_models('Deployment')
    deployment = Deployment(properties=deployment_properties)
    try:
        validation_poller = mgmt_client.begin_validate(resource_group_name, deployment_name, deployment)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

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
                                            what_if=None, proceed_if_no_change=None, mode=None, validation_level=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_management_group_core(cmd,
                                                                               management_group_id=management_group_id,
                                                                               template_file=template_file, template_uri=template_uri,
                                                                               parameters=parameters, deployment_name=deployment_name,
                                                                               deployment_location=deployment_location,
                                                                               result_format=what_if_result_format,
                                                                               exclude_change_types=what_if_exclude_change_types,
                                                                               no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                               return_result=True, validation_level=validation_level)
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
                                                    no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                    mode=mode, validation_level=validation_level)


# pylint: disable=unused-argument
def validate_arm_template_at_management_group(cmd,
                                              management_group_id=None,
                                              template_file=None, template_uri=None, parameters=None,
                                              deployment_name=None, deployment_location=None,
                                              no_wait=False, handle_extended_json_format=None,
                                              no_prompt=False, template_spec=None, query_string=None,
                                              validation_level=None):
    return _deploy_arm_template_at_management_group(cmd=cmd,
                                                    management_group_id=management_group_id,
                                                    template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                    deployment_name=deployment_name, deployment_location=deployment_location,
                                                    validate_only=True, no_wait=no_wait,
                                                    no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                    mode='Incremental', validation_level=validation_level)


def _deploy_arm_template_at_management_group(cmd,
                                             management_group_id=None,
                                             template_file=None, template_uri=None, parameters=None,
                                             deployment_name=None, deployment_location=None, validate_only=False,
                                             no_wait=False, no_prompt=False, template_spec=None, query_string=None,
                                             mode=None, validation_level=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'managementGroup', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode=mode,
                                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                      validation_level=validation_level)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=deployment_properties.template_link is None)

    from azure.core.exceptions import HttpResponseError
    ScopedDeployment = cmd.get_models('ScopedDeployment')
    deployment = ScopedDeployment(properties=deployment_properties, location=deployment_location)
    try:
        validation_poller = mgmt_client.begin_validate_at_management_group_scope(management_group_id,
                                                                                 deployment_name, deployment)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

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
                                        what_if=None, proceed_if_no_change=None, validation_level=None):
    if confirm_with_what_if or what_if:
        what_if_result = _what_if_deploy_arm_template_at_tenant_scope_core(cmd,
                                                                           template_file=template_file, template_uri=template_uri,
                                                                           parameters=parameters, deployment_name=deployment_name,
                                                                           deployment_location=deployment_location,
                                                                           result_format=what_if_result_format,
                                                                           exclude_change_types=what_if_exclude_change_types,
                                                                           no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                           return_result=True, validation_level=validation_level)
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
                                                no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                validation_level=validation_level)


# pylint: disable=unused-argument
def validate_arm_template_at_tenant_scope(cmd,
                                          template_file=None, template_uri=None, parameters=None,
                                          deployment_name=None, deployment_location=None,
                                          no_wait=False, handle_extended_json_format=None, no_prompt=False,
                                          template_spec=None, query_string=None, validation_level=None):
    return _deploy_arm_template_at_tenant_scope(cmd=cmd,
                                                template_file=template_file, template_uri=template_uri, parameters=parameters,
                                                deployment_name=deployment_name, deployment_location=deployment_location,
                                                validate_only=True, no_wait=no_wait, no_prompt=no_prompt,
                                                template_spec=template_spec, query_string=query_string,
                                                validation_level=validation_level)


def _deploy_arm_template_at_tenant_scope(cmd,
                                         template_file=None, template_uri=None, parameters=None,
                                         deployment_name=None, deployment_location=None, validate_only=False,
                                         no_wait=False, no_prompt=False, template_spec=None, query_string=None,
                                         validation_level=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'tenant', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode='Incremental',
                                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                                      validation_level=validation_level)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=deployment_properties.template_link is None)

    from azure.core.exceptions import HttpResponseError
    ScopedDeployment = cmd.get_models('ScopedDeployment')
    deployment = ScopedDeployment(properties=deployment_properties, location=deployment_location)
    try:
        validation_poller = mgmt_client.begin_validate_at_tenant_scope(deployment_name=deployment_name,
                                                                       parameters=deployment)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)
    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)
    if validate_only:
        return validation_result

    return sdk_no_wait(no_wait, mgmt_client.begin_create_or_update_at_tenant_scope, deployment_name, deployment)


def what_if_deploy_arm_template_at_resource_group(cmd, resource_group_name,
                                                  template_file=None, template_uri=None, parameters=None,
                                                  deployment_name=None, mode=None,
                                                  aux_tenants=None, result_format=None,
                                                  no_pretty_print=None, no_prompt=False,
                                                  exclude_change_types=None, template_spec=None, query_string=None,
                                                  validation_level=None):
    return _what_if_deploy_arm_template_at_resource_group_core(cmd, resource_group_name,
                                                               template_file, template_uri, parameters,
                                                               deployment_name, mode,
                                                               aux_tenants, result_format,
                                                               no_pretty_print, no_prompt,
                                                               exclude_change_types, template_spec, query_string,
                                                               validation_level=validation_level)


def _what_if_deploy_arm_template_at_resource_group_core(cmd, resource_group_name,
                                                        template_file=None, template_uri=None, parameters=None,
                                                        deployment_name=None, mode=DeploymentMode.incremental,
                                                        aux_tenants=None, result_format=None,
                                                        no_pretty_print=None, no_prompt=False,
                                                        exclude_change_types=None, template_spec=None, query_string=None,
                                                        return_result=None, validation_level=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'resourceGroup', template_file, template_uri,
                                                                parameters, mode, result_format, no_prompt, template_spec, query_string,
                                                                validation_level=validation_level)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, aux_tenants=aux_tenants,
                                                    plug_pipeline=what_if_properties.template_link is None)
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
                                                      exclude_change_types=None, template_spec=None, query_string=None,
                                                      validation_level=None):
    return _what_if_deploy_arm_template_at_subscription_scope_core(cmd,
                                                                   template_file, template_uri, parameters,
                                                                   deployment_name, deployment_location,
                                                                   result_format, no_pretty_print, no_prompt,
                                                                   exclude_change_types, template_spec, query_string,
                                                                   validation_level=validation_level)


def _what_if_deploy_arm_template_at_subscription_scope_core(cmd,
                                                            template_file=None, template_uri=None, parameters=None,
                                                            deployment_name=None, deployment_location=None,
                                                            result_format=None, no_pretty_print=None, no_prompt=False,
                                                            exclude_change_types=None, template_spec=None, query_string=None,
                                                            return_result=None, validation_level=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'subscription', template_file, template_uri, parameters,
                                                                DeploymentMode.incremental, result_format, no_prompt, template_spec, query_string,
                                                                validation_level=validation_level)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=what_if_properties.template_link is None)
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
                                                    exclude_change_types=None, template_spec=None, query_string=None,
                                                    validation_level=None):
    return _what_if_deploy_arm_template_at_management_group_core(cmd, management_group_id,
                                                                 template_file, template_uri, parameters,
                                                                 deployment_name, deployment_location,
                                                                 result_format, no_pretty_print, no_prompt,
                                                                 exclude_change_types, template_spec, query_string,
                                                                 validation_level=validation_level)


def _what_if_deploy_arm_template_at_management_group_core(cmd, management_group_id=None,
                                                          template_file=None, template_uri=None, parameters=None,
                                                          deployment_name=None, deployment_location=None,
                                                          result_format=None, no_pretty_print=None, no_prompt=False,
                                                          exclude_change_types=None, template_spec=None, query_string=None,
                                                          return_result=None, validation_level=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'managementGroup', template_file, template_uri, parameters,
                                                                DeploymentMode.incremental, result_format, no_prompt, template_spec=template_spec,
                                                                query_string=query_string, validation_level=validation_level)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=what_if_properties.template_link is None)
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
                                                exclude_change_types=None, template_spec=None, query_string=None,
                                                validation_level=None):
    return _what_if_deploy_arm_template_at_tenant_scope_core(cmd,
                                                             template_file, template_uri, parameters,
                                                             deployment_name, deployment_location,
                                                             result_format, no_pretty_print, no_prompt,
                                                             exclude_change_types, template_spec, query_string,
                                                             validation_level=validation_level)


def _what_if_deploy_arm_template_at_tenant_scope_core(cmd,
                                                      template_file=None, template_uri=None, parameters=None,
                                                      deployment_name=None, deployment_location=None,
                                                      result_format=None, no_pretty_print=None, no_prompt=False,
                                                      exclude_change_types=None, template_spec=None, query_string=None,
                                                      return_result=None, validation_level=None):
    what_if_properties = _prepare_deployment_what_if_properties(cmd, 'tenant', template_file, template_uri, parameters,
                                                                DeploymentMode.incremental, result_format, no_prompt, template_spec, query_string,
                                                                validation_level=validation_level)
    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=what_if_properties.template_link is None)
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

    print(format_what_if_operation_result(what_if_result, cli_ctx.enable_color))
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


def _get_parameter_count(parameters):
    # parameters is a 2d array, because it's valid for a user to supply parameters in 2 formats:
    # '--parameters foo=1 --parameters bar=2' or '--parameters foo=1 bar=2'
    # if we try a simple len(parameters), this will return 1 for the latter case, which is incorrect
    count = 0
    for parameter_list in parameters:
        count += len(parameter_list)

    return count


def _get_bicepparam_file_path(parameters):
    bicepparam_file_path = None

    for parameter_list in parameters:
        for parameter_item in parameter_list:
            if is_bicepparam_file(parameter_item):
                if not bicepparam_file_path:
                    bicepparam_file_path = parameter_item
                else:
                    raise ArgumentUsageError("Only one .bicepparam file can be provided with --parameters argument")

    return bicepparam_file_path


def _parse_bicepparam_inline_params(parameters, template_obj):
    parsed_inline_params = {}

    for parameter_list in parameters:
        for parameter_item in parameter_list:
            if is_bicepparam_file(parameter_item):
                continue

            if not _try_parse_key_value_object(parsed_inline_params, template_obj, parameter_item):
                raise InvalidArgumentValueError(f"Unable to parse parameter: {parameter_item}. Only correctly formatted in-line parameters are allowed with a .bicepparam file")

    name_value_obj = {}
    for k, v in parsed_inline_params.items():
        name_value_obj[k] = v['value']

    return name_value_obj


def _build_bicepparam_file(cli_ctx, bicepparam_file, template_file, inline_params=None):
    custom_env = os.environ.copy()
    if inline_params:
        custom_env["BICEP_PARAMETERS_OVERRIDES"] = json.dumps(inline_params)

    if template_file:
        build_bicepparam_output = run_bicep_command(cli_ctx, ["build-params", bicepparam_file, "--bicep-file", template_file, "--stdout"], custom_env=custom_env)
    else:
        build_bicepparam_output = run_bicep_command(cli_ctx, ["build-params", bicepparam_file, "--stdout"], custom_env=custom_env)

    template_content = None
    template_spec_id = None

    build_bicepparam_output_json = json.loads(build_bicepparam_output)
    if "templateJson" in build_bicepparam_output_json:
        template_content = build_bicepparam_output_json["templateJson"]
    if "templateSpecId" in build_bicepparam_output_json:
        template_spec_id = build_bicepparam_output_json["templateSpecId"]
    parameters_content = build_bicepparam_output_json["parametersJson"]

    return template_content, template_spec_id, parameters_content


def _parse_bicepparam_file(cmd, template_file, parameters):
    ensure_bicep_installation(cmd.cli_ctx, stdout=False)

    minimum_supported_version_bicepparam_compilation = "0.14.85"
    if not bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version_bicepparam_compilation):
        raise ArgumentUsageError(f"Unable to compile .bicepparam file with the current version of Bicep CLI. Please upgrade Bicep CLI to {minimum_supported_version_bicepparam_compilation} or later.")

    minimum_supported_version_supplemental_param = "0.22.6"
    if _get_parameter_count(parameters) > 1 and not bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version_supplemental_param):
        raise ArgumentUsageError(f"Current version of Bicep CLI does not support supplemental parameters with .bicepparam file. Please upgrade Bicep CLI to {minimum_supported_version_supplemental_param} or later.")

    bicepparam_file = _get_bicepparam_file_path(parameters)

    if template_file and not is_bicep_file(template_file):
        raise ArgumentUsageError("Only a .bicep template is allowed with a .bicepparam file")

    template_content, template_spec_id, parameters_content = _build_bicepparam_file(cmd.cli_ctx, bicepparam_file, template_file)

    if _get_parameter_count(parameters) > 1:
        template_obj = None
        if template_spec_id:
            template_obj = _load_template_spec_template(cmd, template_spec_id)
        else:
            template_obj = _remove_comments_from_json(template_content)

        inline_params = _parse_bicepparam_inline_params(parameters, template_obj)

        # re-invoke build-params to process inline parameters
        template_content, template_spec_id, parameters_content = _build_bicepparam_file(cmd.cli_ctx, bicepparam_file, template_file, inline_params)

    return template_content, template_spec_id, parameters_content


def _load_template_spec_template(cmd, template_spec):
    # The api-version for ResourceType.MGMT_RESOURCE_RESOURCES may get updated and point to another (newer) version of the api version for
    # ResourceType.MGMT_RESOURCE_TEMPLATESPECS than our designated version. This ensures the api-version of all the rest requests for
    # template_spec are consistent in the same profile:
    api_version = get_api_version(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS)
    template_obj = show_resource(cmd=cmd, resource_ids=[template_spec], api_version=api_version).properties['mainTemplate']

    return template_obj


def _get_template_for_deployment(template_uri, template_spec, template_file, template_content, template_obj, parameters):
    """Determine what to use for template deployment based on the source"""
    if template_uri or template_spec:
        # For URI and template spec deployments, use None (template_link will be used)
        return None

    if _is_bicepparam_file_provided(parameters):
        # For bicepparam files, use the content
        return template_content

    if template_file and is_bicep_file(template_file):
        # For bicep files, convert the parsed object back to compact JSON string
        # This avoids the size inflation issue while maintaining compatibility
        # with the Azure SDK which expects string content
        return json.dumps(template_obj, separators=(',', ':'))

    # For ARM template files, use string content
    return template_content


def _process_template_file(cmd, template_file, deployment_scope):
    """Process template file and return template_content and template_obj"""
    if is_bicep_file(template_file):
        # Get compiled JSON from bicep
        template_content = run_bicep_command(cmd.cli_ctx, ["build", "--stdout", template_file])
        # For bicep files, parse JSON directly to avoid Azure SDK size inflation.
        # Bicep compilation outputs clean JSON without comments, so it's safe to
        # parse directly. This prevents the 4MB template size limit issue caused
        # by Azure SDK string escaping when using template content as string.
        template_obj = json.loads(template_content)
        template_schema = template_obj.get('$schema', '')
        validate_bicep_target_scope(template_schema, deployment_scope)
    else:
        # For ARM template files, read content and process comments
        template_content = read_file_content(template_file)
        template_obj = _remove_comments_from_json(template_content, file_path=template_file)

    return template_content, template_obj


def _prepare_deployment_properties_unmodified(cmd, deployment_scope, template_file=None, template_uri=None, parameters=None,
                                              mode=None, rollback_on_error=None, no_prompt=False, template_spec=None, query_string=None,
                                              validation_level=None):
    DeploymentProperties, TemplateLink, OnErrorDeployment = cmd.get_models('DeploymentProperties', 'TemplateLink', 'OnErrorDeployment')

    if template_file:
        pass
    elif template_spec:
        pass
    elif template_uri:
        pass
    elif _is_bicepparam_file_provided(parameters):
        pass
    else:
        raise InvalidArgumentValueError(
            "Please enter one of the following: template file, template spec, template url, or Bicep parameters file.")

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
        template_link = TemplateLink(id=template_spec)
        template_obj = _load_template_spec_template(cmd, template_spec)
    elif _is_bicepparam_file_provided(parameters):
        template_content, template_spec_id, bicepparam_json_content = _parse_bicepparam_file(cmd, template_file, parameters)
        if template_spec_id:
            template_link = TemplateLink(id=template_spec_id)
            template_obj = _load_template_spec_template(cmd, template_spec_id)
        else:
            template_obj = _remove_comments_from_json(template_content)

        template_schema = template_obj.get('$schema', '')
        validate_bicep_target_scope(template_schema, deployment_scope)
    else:
        template_content, template_obj = _process_template_file(cmd, template_file, deployment_scope)

    if rollback_on_error == '':
        on_error_deployment = OnErrorDeployment(type='LastSuccessful')
    elif rollback_on_error:
        on_error_deployment = OnErrorDeployment(type='SpecificDeployment', deployment_name=rollback_on_error)

    template_obj['resources'] = template_obj.get('resources', [])

    if _is_bicepparam_file_provided(parameters):
        parameters = json.loads(bicepparam_json_content).get('parameters', {})  # pylint: disable=used-before-assignment
    else:
        parameters = _process_parameters(template_obj, parameters) or {}
        parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters, no_prompt)
        parameters = json.loads(json.dumps(parameters))

    template_for_deployment = _get_template_for_deployment(template_uri, template_spec, template_file, template_content, template_obj, parameters)

    properties = DeploymentProperties(template=template_for_deployment, template_link=template_link,
                                      parameters=parameters, mode=mode, on_error_deployment=on_error_deployment,
                                      validation_level=validation_level)
    return properties


def _prepare_deployment_what_if_properties(cmd, deployment_scope, template_file, template_uri, parameters,
                                           mode, result_format, no_prompt, template_spec, query_string,
                                           validation_level):
    DeploymentWhatIfProperties, DeploymentWhatIfSettings = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_DEPLOYMENTS,
                                                                   'DeploymentWhatIfProperties', 'DeploymentWhatIfSettings',
                                                                   mod='models')

    deployment_properties = _prepare_deployment_properties_unmodified(cmd, deployment_scope, template_file=template_file, template_uri=template_uri,
                                                                      parameters=parameters, mode=mode, no_prompt=no_prompt, template_spec=template_spec,
                                                                      query_string=query_string, validation_level=validation_level)
    deployment_what_if_properties = DeploymentWhatIfProperties(template=deployment_properties.template, template_link=deployment_properties.template_link,
                                                               parameters=deployment_properties.parameters, mode=deployment_properties.mode,
                                                               what_if_settings=DeploymentWhatIfSettings(result_format=result_format),
                                                               validation_level=validation_level)

    return deployment_what_if_properties


# pylint: disable=protected-access
def _get_deployment_management_client(cli_ctx, aux_subscriptions=None, aux_tenants=None, plug_pipeline=True):

    smc = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_DEPLOYMENTS,
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


def _prepare_stacks_deny_settings(rcf, deny_settings_mode):
    deny_settings_mode = None if deny_settings_mode.lower() == "none" else deny_settings_mode
    deny_settings_enum = rcf.deployment_stacks.models.DenySettingsMode.none
    if deny_settings_mode:
        if deny_settings_mode.lower().replace(' ', '') == "denydelete":
            deny_settings_enum = rcf.deployment_stacks.models.DenySettingsMode.deny_delete
        elif deny_settings_mode.lower().replace(' ', '') == "denywriteanddelete":
            deny_settings_enum = rcf.deployment_stacks.models.DenySettingsMode.deny_write_and_delete
        else:
            raise InvalidArgumentValueError("Please enter only one of the following: denyDelete, or denyWriteAndDelete")

    return deny_settings_enum


def _prepare_stacks_excluded_principals(deny_settings_excluded_principals):
    excluded_principals_array = []
    if deny_settings_excluded_principals:
        for principal in deny_settings_excluded_principals.split(" "):
            excluded_principals_array.append(str(principal))
    else:
        excluded_principals_array = None

    return excluded_principals_array


def _prepare_stacks_delete_detach_models(rcf, action_on_unmanage):
    detach_model = rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Detach
    delete_model = rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = None, None, None

    if action_on_unmanage == StacksActionOnUnmanage.DETACH_ALL:
        aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = detach_model, detach_model, detach_model
    elif action_on_unmanage == StacksActionOnUnmanage.DELETE_RESOURCES:
        aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = delete_model, detach_model, detach_model
    elif action_on_unmanage == StacksActionOnUnmanage.DELETE_ALL:
        aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = delete_model, delete_model, delete_model

    return aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum


def _prepare_stacks_excluded_actions(deny_settings_excluded_actions):
    excluded_actions_array = []
    if deny_settings_excluded_actions:
        for action in deny_settings_excluded_actions.split(" "):
            excluded_actions_array.append(str(action))
    else:
        excluded_actions_array = None

    return excluded_actions_array


def _build_stacks_confirmation_string(rcf, yes, name, stack_scope, delete_resources_enum, delete_resource_groups_enum, delete_management_groups_enum):
    detach_model = rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Detach

    if not yes:
        from knack.prompting import prompt_y_n

        build_confirmation_string = f"The Deployment stack '{name}' you're trying to create already exists in the current {stack_scope}.\n"
        build_confirmation_string += "The following actions will be applied to any resources that are no longer managed by the Deployment stack after the template is applied:\n"

        detaching_entities = []
        deleting_entities = []

        if delete_resources_enum == detach_model:
            detaching_entities.append("resources")
        else:
            deleting_entities.append("resources")

        if delete_resource_groups_enum == detach_model:
            detaching_entities.append("resource groups")
        else:
            deleting_entities.append("resource groups")

        if delete_management_groups_enum == detach_model:
            detaching_entities.append("management groups")
        else:
            deleting_entities.append("management groups")

        if len(detaching_entities) > 0:
            build_confirmation_string += f"\nDetachment: {', '.join(detaching_entities)}\n"
        if len(deleting_entities) > 0:
            build_confirmation_string += f"\nDeletion: {', '.join(deleting_entities)}\n"

        build_confirmation_string += "\nAre you sure you want to continue?"

        confirmation = prompt_y_n(build_confirmation_string)
        if not confirmation:
            return None

    return build_confirmation_string


def _prepare_stacks_templates_and_parameters(cmd, rcf, deployment_scope, deployment_stack_model, template_file, template_spec, template_uri, parameters, query_string):
    t_spec, t_uri = None, None
    template_obj = None

    DeploymentStacksTemplateLink = cmd.get_models('DeploymentStacksTemplateLink')

    if template_file:
        pass
    elif template_spec:
        t_spec = template_spec
    elif template_uri:
        t_uri = template_uri
    elif _is_bicepparam_file_provided(parameters):
        pass
    else:
        raise InvalidArgumentValueError(
            "Please enter one of the following: template file, template spec, template url, or Bicep parameters file.")

    if t_spec:
        deployment_stack_model.template_link = DeploymentStacksTemplateLink(id=t_spec)
        template_obj = _load_template_spec_template(cmd, template_spec)
    elif t_uri:
        if query_string:
            deployment_stacks_template_link = DeploymentStacksTemplateLink(
                uri=t_uri, query_string=query_string)
            t_uri = _prepare_template_uri_with_query_string(
                template_uri=t_uri, input_query_string=query_string)
        else:
            deployment_stacks_template_link = DeploymentStacksTemplateLink(uri=t_uri)
        deployment_stack_model.template_link = deployment_stacks_template_link
        template_obj = _remove_comments_from_json(_urlretrieve(t_uri).decode('utf-8'), file_path=t_uri)
    elif _is_bicepparam_file_provided(parameters):
        template_content, template_spec_id, bicepparam_json_content = _parse_bicepparam_file(cmd, template_file, parameters)
        if template_spec_id:
            template_obj = _load_template_spec_template(cmd, template_spec_id)
            deployment_stack_model.template_link = DeploymentStacksTemplateLink(id=template_spec_id)
        else:
            template_obj = _remove_comments_from_json(template_content)
            deployment_stack_model.template = json.loads(json.dumps(template_obj))

        template_schema = template_obj.get('$schema', '')
        validate_bicep_target_scope(template_schema, deployment_scope)
    else:
        template_content = (
            run_bicep_command(cmd.cli_ctx, ["build", "--stdout", template_file])
            if is_bicep_file(template_file)
            else read_file_content(template_file)
        )

        template_obj = _remove_comments_from_json(template_content, file_path=template_file)

        if is_bicep_file(template_file):
            template_schema = template_obj.get('$schema', '')
            validate_bicep_target_scope(template_schema, deployment_scope)

            deployment_stack_model.template = json.loads(json.dumps(template_obj))
        else:
            deployment_stack_model.template = json.load(open(template_file))

    template_obj['resources'] = template_obj.get('resources', [])

    if _is_bicepparam_file_provided(parameters):
        parameters = json.loads(bicepparam_json_content).get('parameters', {})  # pylint: disable=used-before-assignment
    else:
        parameters = _process_parameters(template_obj, parameters) or {}
        parameters = _get_missing_parameters(parameters, template_obj, _prompt_for_parameters, False)
        parameters = json.loads(json.dumps(parameters))

    deployment_stack_model.parameters = parameters

    return deployment_stack_model


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
        cmd, resource_group_name, include_comments=False, include_parameter_default_value=False, resource_ids=None, skip_resource_name_params=False, skip_all_params=False, export_format=None):
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

    if export_format is None or export_format.lower() == "json" or export_format.lower() == "arm":
        export_template_request = ExportTemplateRequest(resources=resources, options=options, output_format="Json")
    elif export_format.lower() == "bicep":
        export_template_request = ExportTemplateRequest(resources=resources, options=options, output_format="Bicep")
    else:
        raise InvalidArgumentValueError('az resource: error: argument --export-format: invalid ExportFormat value: \'%s\'' % export_format)

    # Exporting a resource group as a template is async since API version 2019-08-01.
    if cmd.supported_api_version(min_api='2019-08-01'):
        if cmd.supported_api_version(min_api='2024-11-01'):
            result_poller = rcf.resource_groups.begin_export_template(resource_group_name,
                                                                      parameters=export_template_request,
                                                                      api_version='2024-11-01')
        else:
            if export_format.lower() == "bicep":
                raise CLIError("Bicep export is not supported in API version < 2024-11-01")

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

    return result.output if export_format and export_format.lower() == "bicep" else result.template


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
    Application, Plan = cmd.get_models('Application', 'Plan')
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
                                           main_template=None, location=None, deployment_mode=None, tags=None):
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
    ApplicationDefinition, ApplicationAuthorization, ApplicationDeploymentPolicy = \
        cmd.get_models('ApplicationDefinition',
                       'ApplicationAuthorization',
                       'ApplicationDeploymentPolicy')
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
        applicationAuth = ApplicationAuthorization(
            principal_id=principalId,
            role_definition_id=roleDefinitionId)
        applicationAuthList.append(applicationAuth)

    deployment_policy = ApplicationDeploymentPolicy(deployment_mode=deployment_mode) if deployment_mode is not None else None
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
    applicationDef.deployment_policy = deployment_policy

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
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_at_subscription_scope(filter=filter_string)


def list_deployments_at_resource_group(cmd, resource_group_name, filter_string=None):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_by_resource_group(resource_group_name, filter=filter_string)


def list_deployments_at_management_group(cmd, management_group_id, filter_string=None):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_at_management_group_scope(management_group_id, filter=filter_string)


def list_deployments_at_tenant_scope(cmd, filter_string=None):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.list_at_tenant_scope(filter=filter_string)


def get_deployment_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.get_at_subscription_scope(deployment_name)


def get_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.get(resource_group_name, deployment_name)


def get_deployment_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.get_at_management_group_scope(management_group_id, deployment_name)


def get_deployment_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.get_at_tenant_scope(deployment_name)


def delete_deployment_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete_at_subscription_scope(deployment_name)


def delete_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete(resource_group_name, deployment_name)


def delete_deployment_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete_at_management_group_scope(management_group_id, deployment_name)


def delete_deployment_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.begin_delete_at_tenant_scope(deployment_name)


def cancel_deployment_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel_at_subscription_scope(deployment_name)


def cancel_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel(resource_group_name, deployment_name)


def cancel_deployment_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployments.cancel_at_management_group_scope(management_group_id, deployment_name)


def cancel_deployment_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
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
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template_at_subscription_scope(deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template(resource_group_name, deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template_at_management_group_scope(management_group_id, deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    result = rcf.deployments.export_template_at_tenant_scope(deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_deployment_as_template(cmd, resource_group_name, deployment_name):
    smc = _resource_deployments_client_factory(cmd.cli_ctx)
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


def patch_resource(cmd, properties, resource_ids=None, resource_group_name=None,
                   resource_provider_namespace=None, parent_resource_path=None, resource_type=None,
                   resource_name=None, api_version=None, latest_include_preview=False, is_full_object=False):
    parsed_ids = _get_parsed_resource_ids(resource_ids) or [_create_parsed_id(cmd.cli_ctx,
                                                                              resource_group_name,
                                                                              resource_provider_namespace,
                                                                              parent_resource_path,
                                                                              resource_type,
                                                                              resource_name)]

    try:
        res = json.loads(properties)
    except json.decoder.JSONDecodeError as ex:
        raise CLIError('Error parsing JSON.\n{}\n{}'.format(properties, ex))

    if not is_full_object:
        res = GenericResource(properties=res)

    return _single_or_collection(
        [_get_rsrc_util_from_parsed_id(cmd.cli_ctx, id_dict, api_version, latest_include_preview)
         .patch(res) for id_dict in parsed_ids]
    )


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
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx, subscription_id=id_parts.get('subscription'))
    else:
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
                template_content = run_bicep_command(cmd.cli_ctx, ["build", "--stdout", template_file])
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
    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx, subscription_id=id_parts.get('subscription'))
    else:
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)

    existing_template, artifacts, input_ui_form_definition = None, None, None
    if template_file:
        from azure.cli.command_modules.resource._packing_engine import (pack)
        if is_bicep_file(template_file):
            template_content = run_bicep_command(cmd.cli_ctx, ["build", "--stdout", template_file])
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
    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx, subscription_id=id_parts.get('subscription'))
    else:
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
    if not version:
        raise IncorrectUsageError('Please specify the template spec version for export')
    exported_template = rcf.template_spec_versions.get(resource_group_name, name, version)
    from azure.cli.command_modules.resource._packing_engine import (unpack)
    return unpack(cmd, exported_template, output_folder, (str(name) + '.JSON'))


def delete_template_spec(cmd, resource_group_name=None, name=None, version=None, template_spec=None):
    if template_spec:
        id_parts = parse_resource_id(template_spec)
        resource_group_name = id_parts.get('resource_group')
        name = id_parts.get('name')
        version = id_parts.get('resource_name')
        if version == name:
            version = None
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx, subscription_id=id_parts.get('subscription'))
    else:
        rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
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


def create_deployment_stack_at_subscription(
    cmd, name, location, deny_settings_mode, action_on_unmanage, deployment_resource_group=None, template_file=None, template_spec=None,
    template_uri=None, query_string=None, parameters=None, description=None, deny_settings_excluded_principals=None,
    deny_settings_excluded_actions=None, deny_settings_apply_to_child_scopes=False, bypass_stack_out_of_sync_error=False, tags=None,
    yes=False, no_wait=False
):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)
    deny_settings_enum = _prepare_stacks_deny_settings(rcf, deny_settings_mode)

    excluded_principals_array = _prepare_stacks_excluded_principals(deny_settings_excluded_principals)
    excluded_actions_array = _prepare_stacks_excluded_actions(deny_settings_excluded_actions)

    tags = tags or {}

    if query_string and not template_uri:
        raise IncorrectUsageError('please provide --template-uri if --query-string is specified')

    if [template_file, template_spec, template_uri].count(None) < 2:
        raise InvalidArgumentValueError(
            "Please enter only one of the following: template file, template spec, or template url")
    try:
        get_subscription_response = rcf.deployment_stacks.get_at_subscription(name)
        if get_subscription_response:
            if get_subscription_response.location != location:
                raise CLIError("Cannot change location of an already existing stack at subscription scope.")
            # bypass if yes flag is true
            built_string = _build_stacks_confirmation_string(
                rcf, yes, name, "subscription", aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum)
            if not built_string:
                return
    except:  # pylint: disable=bare-except
        pass

    action_on_unmanage_model = rcf.deployment_stacks.models.ActionOnUnmanage(
        resources=aou_resources_action_enum, resource_groups=aou_resource_groups_action_enum,
        management_groups=aou_management_groups_action_enum)
    apply_to_child_scopes = deny_settings_apply_to_child_scopes
    deny_settings_model = rcf.deployment_stacks.models.DenySettings(
        mode=deny_settings_enum, excluded_principals=excluded_principals_array, excluded_actions=excluded_actions_array, apply_to_child_scopes=apply_to_child_scopes)
    deployment_stack_model = rcf.deployment_stacks.models.DeploymentStack(
        description=description, location=location, action_on_unmanage=action_on_unmanage_model, deny_settings=deny_settings_model,
        bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error, tags=tags)

    if deployment_resource_group:
        deployment_stack_model.deployment_scope = "/subscriptions/" + \
            get_subscription_id(cmd.cli_ctx) + "/resourceGroups/" + deployment_resource_group
        deployment_scope = 'resourceGroup'
    else:
        deployment_scope = 'subscription'

    deployment_stack_model = _prepare_stacks_templates_and_parameters(
        cmd, rcf, deployment_scope, deployment_stack_model, template_file, template_spec, template_uri, parameters, query_string)

    # run validate
    from azure.core.exceptions import HttpResponseError
    try:
        validation_poller = rcf.deployment_stacks.begin_validate_stack_at_subscription(name, deployment_stack_model)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)

    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)

    # run create
    return sdk_no_wait(no_wait, rcf.deployment_stacks.begin_create_or_update_at_subscription, name, deployment_stack_model)


def show_deployment_stack_at_subscription(cmd, name=None, id=None):  # pylint: disable=redefined-builtin
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    if name or id:
        if name:
            return rcf.deployment_stacks.get_at_subscription(name)
        return rcf.deployment_stacks.get_at_subscription(id.split('/')[-1])
    raise InvalidArgumentValueError("Please enter the stack name or stack resource id.")


def list_deployment_stack_at_subscription(cmd):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    return rcf.deployment_stacks.list_at_subscription()


def delete_deployment_stack_at_subscription(
    cmd, action_on_unmanage, name=None, id=None, bypass_stack_out_of_sync_error=False, yes=False
):  # pylint: disable=redefined-builtin
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    confirmation = "Are you sure you want to delete this stack"

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)

    delete_list = []
    if aou_resources_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("resources")
    if aou_resource_groups_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("resource groups")
    if aou_management_groups_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("management groups")

    # build confirmation string
    from knack.prompting import prompt_y_n
    if not yes:
        if not delete_list:
            response = prompt_y_n(confirmation + "?")
            if not response:
                return None
        else:
            confirmation += " and the specified resources: "
            response = prompt_y_n(confirmation + ", ".join(delete_list) + '?')
            if not response:
                return None

    if name or id:
        rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
        delete_name = None
        try:
            if name:
                delete_name = name
                rcf.deployment_stacks.get_at_subscription(name)
            else:
                name = id.split('/')[-1]
                delete_name = name
                rcf.deployment_stacks.get_at_subscription(name)
        except:
            raise ResourceNotFoundError("DeploymentStack " + delete_name + " not found in the current subscription scope.")
        return rcf.deployment_stacks.begin_delete_at_subscription(
            delete_name, unmanage_action_resources=aou_resources_action_enum,
            unmanage_action_resource_groups=aou_resource_groups_action_enum,
            unmanage_action_management_groups=aou_management_groups_action_enum,
            bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error)
    raise InvalidArgumentValueError("Please enter the stack name or stack resource id")


def export_template_deployment_stack_at_subscription(cmd, name=None, id=None):  # pylint: disable=redefined-builtin
    if name or id:
        rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
        if name:
            return rcf.deployment_stacks.export_template_at_subscription(name)
        return rcf.deployment_stacks.export_template_at_subscription(id.split('/')[-1])
    raise InvalidArgumentValueError("Please enter the stack name or stack resource id.")


def create_deployment_stack_at_resource_group(
    cmd, name, resource_group, deny_settings_mode, action_on_unmanage, template_file=None, template_spec=None, template_uri=None,
    query_string=None, parameters=None, description=None, deny_settings_excluded_principals=None, deny_settings_excluded_actions=None,
    deny_settings_apply_to_child_scopes=False, bypass_stack_out_of_sync_error=False, yes=False, tags=None, no_wait=False
):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)
    deny_settings_enum = _prepare_stacks_deny_settings(rcf, deny_settings_mode)

    excluded_principals_array = _prepare_stacks_excluded_principals(deny_settings_excluded_principals)
    excluded_actions_array = _prepare_stacks_excluded_actions(deny_settings_excluded_actions)

    tags = tags or {}

    if query_string and not template_uri:
        raise IncorrectUsageError('please provide --template-uri if --query-string is specified')

    if [template_file, template_spec, template_uri].count(None) < 2:
        raise InvalidArgumentValueError(
            "Please enter only one of the following: template file, template spec, or template url")

    # build confirmation string
    try:
        if rcf.deployment_stacks.get_at_resource_group(resource_group, name):
            built_string = _build_stacks_confirmation_string(
                rcf, yes, name, "resource group", aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum)
            if not built_string:
                return
    except:  # pylint: disable=bare-except
        pass

    action_on_unmanage_model = rcf.deployment_stacks.models.ActionOnUnmanage(
        resources=aou_resources_action_enum, resource_groups=aou_resource_groups_action_enum,
        management_groups=aou_management_groups_action_enum)
    apply_to_child_scopes = deny_settings_apply_to_child_scopes
    deny_settings_model = rcf.deployment_stacks.models.DenySettings(
        mode=deny_settings_enum, excluded_principals=excluded_principals_array, excluded_actions=excluded_actions_array, apply_to_child_scopes=apply_to_child_scopes)
    deployment_stack_model = rcf.deployment_stacks.models.DeploymentStack(
        description=description, action_on_unmanage=action_on_unmanage_model, deny_settings=deny_settings_model,
        bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error, tags=tags)

    # validate and prepare template & paramaters
    deployment_stack_model = _prepare_stacks_templates_and_parameters(
        cmd, rcf, 'resourceGroup', deployment_stack_model, template_file, template_spec, template_uri, parameters, query_string)

    # run validate
    from azure.core.exceptions import HttpResponseError
    try:
        validation_poller = rcf.deployment_stacks.begin_validate_stack_at_resource_group(resource_group, name, deployment_stack_model)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)

    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)

    # run create
    return sdk_no_wait(no_wait, rcf.deployment_stacks.begin_create_or_update_at_resource_group, resource_group, name, deployment_stack_model)


def show_deployment_stack_at_resource_group(cmd, name=None, resource_group=None, id=None):  # pylint: disable=redefined-builtin
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    if name and resource_group:
        return rcf.deployment_stacks.get_at_resource_group(resource_group, name)
    if id:
        stack_arr = id.split('/')
        if len(stack_arr) < 5:
            raise InvalidArgumentValueError("Please enter a valid id")
        return rcf.deployment_stacks.get_at_resource_group(stack_arr[4], stack_arr[-1])
    raise InvalidArgumentValueError("Please enter the (stack name and resource group) or stack resource id")


def list_deployment_stack_at_resource_group(cmd, resource_group):
    if resource_group:
        rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
        return rcf.deployment_stacks.list_at_resource_group(resource_group)
    raise InvalidArgumentValueError("Please enter the resource group")


def delete_deployment_stack_at_resource_group(
    cmd, action_on_unmanage, name=None, resource_group=None, id=None, bypass_stack_out_of_sync_error=False, yes=False
):  # pylint: disable=redefined-builtin
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    confirmation = "Are you sure you want to delete this stack"

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)

    delete_list = []
    if aou_resources_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("resources")
    if aou_resource_groups_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("resource groups")
    if aou_resource_groups_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("management groups")

    # build confirmation string
    from knack.prompting import prompt_y_n
    if not yes:
        if not delete_list:
            response = prompt_y_n(confirmation + "?")
            if not response:
                return None
        else:
            confirmation += " and the specified resources: "
            response = prompt_y_n(confirmation + ", ".join(delete_list) + '?')
            if not response:
                return None

    if name and resource_group:
        try:
            rcf.deployment_stacks.get_at_resource_group(resource_group, name)
        except:
            raise ResourceNotFoundError("DeploymentStack " + name + " not found in the current resource group scope.")
        return sdk_no_wait(
            False, rcf.deployment_stacks.begin_delete_at_resource_group, resource_group, name,
            unmanage_action_resources=aou_resources_action_enum, unmanage_action_resource_groups=aou_resource_groups_action_enum,
            unmanage_action_management_groups=aou_management_groups_action_enum,
            bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error)
    if id:
        stack_arr = id.split('/')
        if len(stack_arr) < 5:
            raise InvalidArgumentValueError("Please enter a valid id")
        name = stack_arr[-1]
        stack_rg = stack_arr[-5]
        try:
            rcf.deployment_stacks.get_at_resource_group(stack_rg, name)
        except:
            raise ResourceNotFoundError("DeploymentStack " + name + " not found in the current resource group scope.")
        return sdk_no_wait(
            False, rcf.deployment_stacks.begin_delete_at_resource_group, stack_rg, name,
            unmanage_action_resources=aou_resources_action_enum, unmanage_action_resource_groups=aou_resource_groups_action_enum,
            unmanage_action_management_groups=aou_management_groups_action_enum,
            bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error)
    raise InvalidArgumentValueError("Please enter the (stack name and resource group) or stack resource id")


def export_template_deployment_stack_at_resource_group(cmd, name=None, resource_group=None, id=None):  # pylint: disable=redefined-builtin
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    if name and resource_group:
        return rcf.deployment_stacks.export_template_at_resource_group(resource_group, name)
    if id:
        stack_arr = id.split('/')
        if len(stack_arr) < 5:
            raise InvalidArgumentValueError("Please enter a valid id")
        return rcf.deployment_stacks.export_template_at_resource_group(stack_arr[4], stack_arr[-1])
    raise InvalidArgumentValueError("Please enter the (stack name and resource group) or stack resource id")


def validate_deployment_stack_at_resource_group(
    cmd, name, resource_group, deny_settings_mode, action_on_unmanage, template_file=None, template_spec=None, template_uri=None,
    query_string=None, parameters=None, description=None, deny_settings_excluded_principals=None, deny_settings_excluded_actions=None,
    deny_settings_apply_to_child_scopes=False, bypass_stack_out_of_sync_error=False, tags=None
):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)

    deployment_stack_model = _prepare_validate_stack_at_scope(
        rcf=rcf, deployment_scope='resourceGroup', cmd=cmd, deny_settings_mode=deny_settings_mode, action_on_unmanage=action_on_unmanage,
        template_file=template_file, template_spec=template_spec, template_uri=template_uri, query_string=query_string,
        parameters=parameters, description=description, deny_settings_excluded_principals=deny_settings_excluded_principals,
        deny_settings_excluded_actions=deny_settings_excluded_actions,
        deny_settings_apply_to_child_scopes=deny_settings_apply_to_child_scopes,
        bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error, tags=tags)

    from azure.core.exceptions import HttpResponseError
    try:
        validation_poller = rcf.deployment_stacks.begin_validate_stack_at_resource_group(resource_group, name, deployment_stack_model)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)

    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)

    return validation_result


def validate_deployment_stack_at_subscription(
    cmd, name, location, deny_settings_mode, action_on_unmanage, deployment_resource_group=None, template_file=None, template_spec=None,
    template_uri=None, query_string=None, parameters=None, description=None, deny_settings_excluded_principals=None,
    deny_settings_excluded_actions=None, deny_settings_apply_to_child_scopes=False, bypass_stack_out_of_sync_error=False, tags=None
):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)

    deployment_stack_model = _prepare_validate_stack_at_scope(
        rcf=rcf, deployment_scope='subscription', cmd=cmd, location=location, deny_settings_mode=deny_settings_mode,
        action_on_unmanage=action_on_unmanage, deployment_resource_group=deployment_resource_group, template_file=template_file,
        template_spec=template_spec, template_uri=template_uri, query_string=query_string, parameters=parameters, description=description,
        deny_settings_excluded_principals=deny_settings_excluded_principals, deny_settings_excluded_actions=deny_settings_excluded_actions,
        deny_settings_apply_to_child_scopes=deny_settings_apply_to_child_scopes,
        bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error, tags=tags)

    from azure.core.exceptions import HttpResponseError
    try:
        validation_poller = rcf.deployment_stacks.begin_validate_stack_at_subscription(name, deployment_stack_model)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)

    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)

    return validation_result


def validate_deployment_stack_at_management_group(
    cmd, management_group_id, name, location, deny_settings_mode, action_on_unmanage, deployment_subscription=None,
    template_file=None, template_spec=None, template_uri=None, query_string=None, parameters=None, description=None,
    deny_settings_excluded_principals=None, deny_settings_excluded_actions=None, deny_settings_apply_to_child_scopes=False,
    bypass_stack_out_of_sync_error=False, tags=None
):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)

    deployment_stack_model = _prepare_validate_stack_at_scope(
        rcf=rcf, deployment_scope='managementGroup', cmd=cmd, location=location, deny_settings_mode=deny_settings_mode,
        action_on_unmanage=action_on_unmanage, deployment_subscription=deployment_subscription, template_file=template_file,
        template_spec=template_spec, template_uri=template_uri, query_string=query_string, parameters=parameters, description=description,
        deny_settings_excluded_principals=deny_settings_excluded_principals, deny_settings_excluded_actions=deny_settings_excluded_actions,
        deny_settings_apply_to_child_scopes=deny_settings_apply_to_child_scopes,
        bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error, tags=tags)

    from azure.core.exceptions import HttpResponseError
    try:
        validation_poller = rcf.deployment_stacks.begin_validate_stack_at_management_group(management_group_id, name, deployment_stack_model)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)

    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)

    return validation_result


def _prepare_validate_stack_at_scope(
    rcf, deployment_scope, cmd, deny_settings_mode, action_on_unmanage, location=None, deployment_subscription=None,
    deployment_resource_group=None, template_file=None, template_spec=None, template_uri=None, query_string=None, parameters=None,
    description=None, deny_settings_excluded_principals=None, deny_settings_excluded_actions=None,
    deny_settings_apply_to_child_scopes=False, bypass_stack_out_of_sync_error=False, tags=None
):
    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)
    deny_settings_enum = _prepare_stacks_deny_settings(rcf, deny_settings_mode)

    excluded_principals_array = _prepare_stacks_excluded_principals(deny_settings_excluded_principals)
    excluded_actions_array = _prepare_stacks_excluded_actions(deny_settings_excluded_actions)

    tags = tags or {}

    if query_string and not template_uri:
        raise IncorrectUsageError('please provide --template-uri if --query-string is specified')

    if [template_file, template_spec, template_uri].count(None) < 2:
        raise InvalidArgumentValueError(
            "Please enter only one of the following: template file, template spec, or template url")

    action_on_unmanage_model = rcf.deployment_stacks.models.ActionOnUnmanage(
        resources=aou_resources_action_enum, resource_groups=aou_resource_groups_action_enum,
        management_groups=aou_management_groups_action_enum)
    apply_to_child_scopes = deny_settings_apply_to_child_scopes
    deny_settings_model = rcf.deployment_stacks.models.DenySettings(
        mode=deny_settings_enum, excluded_principals=excluded_principals_array, excluded_actions=excluded_actions_array,
        apply_to_child_scopes=apply_to_child_scopes)
    deployment_stack_model = rcf.deployment_stacks.models.DeploymentStack(
        description=description, location=location, action_on_unmanage=action_on_unmanage_model, deny_settings=deny_settings_model,
        tags=tags, bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error)

    if deployment_scope == 'managementGroup' and deployment_subscription:
        deployment_stack_model.deployment_scope = f"/subscriptions/{deployment_subscription}"
        deployment_scope = 'subscription'
    elif deployment_scope == 'subscription' and deployment_resource_group:
        deployment_subscription_id = get_subscription_id(cmd.cli_ctx)

        deployment_stack_model.deployment_scope = f"/subscriptions/{deployment_subscription_id}/resourceGroups/{deployment_resource_group}"
        deployment_scope = 'resourceGroup'

    deployment_stack_model = _prepare_stacks_templates_and_parameters(
        cmd, rcf, deployment_scope, deployment_stack_model, template_file, template_spec, template_uri, parameters, query_string)

    return deployment_stack_model


def create_deployment_stack_at_management_group(
    cmd, management_group_id, name, location, deny_settings_mode, action_on_unmanage, deployment_subscription=None, template_file=None,
    template_spec=None, template_uri=None, query_string=None, parameters=None, description=None, deny_settings_excluded_principals=None,
    deny_settings_excluded_actions=None, deny_settings_apply_to_child_scopes=False, bypass_stack_out_of_sync_error=False, yes=False,
    tags=None, no_wait=False
):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)
    deny_settings_enum = _prepare_stacks_deny_settings(rcf, deny_settings_mode)

    excluded_principals_array = _prepare_stacks_excluded_principals(deny_settings_excluded_principals)
    excluded_actions_array = _prepare_stacks_excluded_actions(deny_settings_excluded_actions)

    tags = tags or {}

    if query_string and not template_uri:
        raise IncorrectUsageError('please provide --template-uri if --query-string is specified')

    if [template_file, template_spec, template_uri].count(None) < 2:
        raise InvalidArgumentValueError(
            "Please enter only one of the following: template file, template spec, or template url")
    try:
        get_mg_response = rcf.deployment_stacks.get_at_management_group(management_group_id, name)
        if get_mg_response:
            built_string = _build_stacks_confirmation_string(
                rcf, yes, name, "management group", aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum)
            if not built_string:
                return
    except:  # pylint: disable=bare-except
        pass

    action_on_unmanage_model = rcf.deployment_stacks.models.ActionOnUnmanage(
        resources=aou_resources_action_enum, resource_groups=aou_resource_groups_action_enum,
        management_groups=aou_management_groups_action_enum)
    apply_to_child_scopes = deny_settings_apply_to_child_scopes
    deny_settings_model = rcf.deployment_stacks.models.DenySettings(
        mode=deny_settings_enum, excluded_principals=excluded_principals_array, excluded_actions=excluded_actions_array, apply_to_child_scopes=apply_to_child_scopes)
    deployment_stack_model = rcf.deployment_stacks.models.DeploymentStack(
        description=description, location=location, action_on_unmanage=action_on_unmanage_model, deny_settings=deny_settings_model,
        bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error, tags=tags)

    if deployment_subscription:
        deployment_stack_model.deployment_scope = "/subscriptions/" + deployment_subscription
        deployment_scope = 'subscription'
    else:
        deployment_scope = 'managementGroup'

    deployment_stack_model = _prepare_stacks_templates_and_parameters(
        cmd, rcf, deployment_scope, deployment_stack_model, template_file, template_spec, template_uri, parameters, query_string)

    # run validate
    from azure.core.exceptions import HttpResponseError
    try:
        validation_poller = rcf.deployment_stacks.begin_validate_stack_at_management_group(
            management_group_id, name, deployment_stack_model)
    except HttpResponseError as err:
        err_message = _build_http_response_error_message(err)
        raise_subdivision_deployment_error(err_message, err.error.code if err.error else None)

    validation_result = LongRunningOperation(cmd.cli_ctx)(validation_poller)

    if validation_result and validation_result.error:
        err_message = _build_preflight_error_message(validation_result.error)
        raise_subdivision_deployment_error(err_message)

    # run create
    return sdk_no_wait(no_wait, rcf.deployment_stacks.begin_create_or_update_at_management_group, management_group_id, name, deployment_stack_model)


def show_deployment_stack_at_management_group(cmd, management_group_id, name=None, id=None):  # pylint: disable=redefined-builtin
    if name or id:
        rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
        if name:
            return rcf.deployment_stacks.get_at_management_group(management_group_id, name)
        return rcf.deployment_stacks.get_at_management_group(management_group_id, id.split('/')[-1])
    raise InvalidArgumentValueError("Please enter the stack name or stack resource id.")


def list_deployment_stack_at_management_group(cmd, management_group_id):
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    return rcf.deployment_stacks.list_at_management_group(management_group_id)


def delete_deployment_stack_at_management_group(
    cmd, management_group_id, action_on_unmanage, name=None, id=None, bypass_stack_out_of_sync_error=False, yes=False
):  # pylint: disable=redefined-builtin
    rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
    confirmation = "Are you sure you want to delete this stack"

    aou_resources_action_enum, aou_resource_groups_action_enum, aou_management_groups_action_enum = _prepare_stacks_delete_detach_models(
        rcf, action_on_unmanage)

    delete_list = []
    if aou_resources_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("resources")
    if aou_resource_groups_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("resource groups")
    if aou_management_groups_action_enum == rcf.deployment_stacks.models.DeploymentStacksDeleteDetachEnum.Delete:
        delete_list.append("management groups")

    # build confirmation string
    from knack.prompting import prompt_y_n
    if not yes:
        if not delete_list:
            response = prompt_y_n(confirmation + "?")
            if not response:
                return None
        else:
            confirmation += " and the specified resources: "
            response = prompt_y_n(confirmation + ", ".join(delete_list) + '?')
            if not response:
                return None

    if name or id:
        rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
        delete_name = None
        try:
            if name:
                delete_name = name
                rcf.deployment_stacks.get_at_management_group(management_group_id, name)
            else:
                name = id.split('/')[-1]
                delete_name = name
                rcf.deployment_stacks.get_at_management_group(management_group_id, name)
        except:
            raise ResourceNotFoundError("DeploymentStack " + delete_name +
                                        " not found in the current management group scope.")
        return rcf.deployment_stacks.begin_delete_at_management_group(
            management_group_id, delete_name, unmanage_action_resources=aou_resources_action_enum,
            unmanage_action_resource_groups=aou_resource_groups_action_enum,
            unmanage_action_management_groups=aou_management_groups_action_enum,
            bypass_stack_out_of_sync_error=bypass_stack_out_of_sync_error)
    raise InvalidArgumentValueError("Please enter the stack name or stack resource id")


def export_template_deployment_stack_at_management_group(cmd, management_group_id, name=None, id=None):  # pylint: disable=redefined-builtin
    if name or id:
        rcf = _resource_deploymentstacks_client_factory(cmd.cli_ctx)
        if name:
            return rcf.deployment_stacks.export_template_at_management_group(management_group_id, name)
        return rcf.deployment_stacks.export_template_at_management_group(management_group_id, id.split('/')[-1])
    raise InvalidArgumentValueError("Please enter the stack name or stack resource id.")


def list_deployment_operations_at_subscription_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list_at_subscription_scope(deployment_name)


def list_deployment_operations_at_resource_group(cmd, resource_group_name, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list(resource_group_name, deployment_name)


def list_deployment_operations_at_management_group(cmd, management_group_id, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list_at_management_group_scope(management_group_id, deployment_name)


def list_deployment_operations_at_tenant_scope(cmd, deployment_name):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.list_at_tenant_scope(deployment_name)


def get_deployment_operation_at_subscription_scope(cmd, deployment_name, op_id):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get_at_subscription_scope(deployment_name, op_id)


def get_deployment_operation_at_resource_group(cmd, resource_group_name, deployment_name, op_id):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get(resource_group_name, deployment_name, op_id)


def get_deployment_operation_at_management_group(cmd, management_group_id, deployment_name, op_id):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
    return rcf.deployment_operations.get_at_management_group_scope(management_group_id, deployment_name, op_id)


def get_deployment_operation_at_tenant_scope(cmd, deployment_name, op_id):
    rcf = _resource_deployments_client_factory(cmd.cli_ctx)
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


def _get_resource_id(cli_ctx, val, resource_group, resource_type, resource_namespace):
    from azure.mgmt.core.tools import resource_id
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
        if resource_group and resource_group.lower() != _resource_group.lower():
            raise CLIError(
                'Unexpected --resource-group for lock {}, expected {}'.format(
                    name, _resource_group))
        if _resource_namespace is None or _resource_namespace == 'Microsoft.Authorization':
            return
        if resource_provider_namespace and resource_provider_namespace.lower() != _resource_namespace.lower():
            raise CLIError(
                'Unexpected --namespace for lock {}, expected {}'.format(name, _resource_namespace))
        if resource.get('child_type_2', None) is None:
            _resource_type = resource.get('type', None)
            _resource_name = resource.get('name', None)
        else:
            if resource.get('child_type_3', None) is None:
                _resource_type = resource.get('child_type_1', None)
                _resource_name = resource.get('child_name_1', None)
                parent = resource['type'] + '/' + resource['name']
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
    parameters = ManagementLockObject(level=level, notes=notes)

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
        return rcf.tags.begin_create_or_update_at_scope(scope=resource_id, parameters=tags_resource)

    return rcf.tags.create_or_update(tag_name=tag_name)


def delete_tag_at_scope(cmd, resource_id=None, tag_name=None):
    rcf = _resource_client_factory(cmd.cli_ctx)
    if resource_id is not None:
        return rcf.tags.begin_delete_at_scope(scope=resource_id)

    return rcf.tags.delete(tag_name=tag_name)


def update_tag_at_scope(cmd, resource_id, tags, operation):
    rcf = _resource_client_factory(cmd.cli_ctx)
    if not tags:
        raise IncorrectUsageError("Tags could not be empty.")
    Tags = cmd.get_models('Tags')
    tag_obj = Tags(tags=tags)
    TagsPatchResource = cmd.get_models('TagsPatchResource')
    tags_resource = TagsPatchResource(properties=tag_obj, operation=operation)
    return rcf.tags.begin_update_at_scope(scope=resource_id, parameters=tags_resource)
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

    def patch(self, parameters):
        if self.resource_id:
            return self.rcf.resources.begin_update_by_id(self.resource_id,
                                                         self.api_version,
                                                         parameters)
        return self.rcf.resources.begin_update(self.resource_group_name,
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
                              'Microsoft.Network/publicIPAddresses', 'Microsoft.insights/workbooks']

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

        from azure.core.polling import LROPoller
        from azure.mgmt.core.polling.arm_polling import ARMPolling

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

        def deserialization_cb(pipeline_response):
            return json.loads(pipeline_response.http_response.text())

        request = client.post(url, query_parameters, header_parameters, **body_content_kwargs)
        pipeline_response = client._pipeline.run(request, stream=False)

        return LROPoller(client=client, initial_response=pipeline_response, deserialization_callback=deserialization_cb,
                         polling_method=ARMPolling())

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
    ensure_bicep_installation(cmd.cli_ctx, release_tag=version, target_platform=target_platform)


def uninstall_bicep_cli(cmd):
    remove_bicep_installation(cmd.cli_ctx)


def upgrade_bicep_cli(cmd, target_platform=None):
    latest_release_tag = get_bicep_latest_release_tag()
    ensure_bicep_installation(cmd.cli_ctx, release_tag=latest_release_tag, target_platform=target_platform)


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

    output = run_bicep_command(cmd.cli_ctx, args)

    if stdout:
        print(output)


def build_bicepparam_file(cmd, file, stdout=None, outdir=None, outfile=None, no_restore=None):
    args = ["build-params", file]
    if outdir:
        args += ["--outdir", outdir]
    if outfile:
        args += ["--outfile", outfile]
    if no_restore:
        args += ["--no-restore"]
    if stdout:
        args += ["--stdout"]

    output = run_bicep_command(cmd.cli_ctx, args)

    if stdout:
        print(output)


def format_bicep_file(cmd, file, stdout=None, outdir=None, outfile=None, newline=None, newline_kind=None, indent_kind=None, indent_size=None, insert_final_newline=None):
    ensure_bicep_installation(cmd.cli_ctx, stdout=False)

    minimum_supported_version = "0.12.1"
    kebab_case_params_supported_version = "0.26.54"

    if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version):
        args = ["format", file]
        use_kebab_case_params = bicep_version_greater_than_or_equal_to(cmd.cli_ctx, kebab_case_params_supported_version)
        newline_kind = newline_kind or newline

        # Auto is no longer supported by Bicep formatter v2. Use LF as default.
        if use_kebab_case_params and newline_kind == "Auto":
            newline_kind = "LF"

        if outdir:
            args += ["--outdir", outdir]
        if outfile:
            args += ["--outfile", outfile]
        if stdout:
            args += ["--stdout"]
        if newline_kind:
            args += ["--newline-kind" if use_kebab_case_params else "newline", newline_kind]
        if indent_kind:
            args += ["--indent-kind" if use_kebab_case_params else "indentKind", indent_kind]
        if indent_size:
            args += ["--indent-size" if use_kebab_case_params else "indentSize", indent_size]
        if insert_final_newline:
            args += ["--insert-final-newline" if use_kebab_case_params else "--insertFinalNewline"]

        output = run_bicep_command(cmd.cli_ctx, args)

        if stdout:
            print(output)
    else:
        logger.error("az bicep format could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def publish_bicep_file(cmd, file, target, documentationUri=None, documentation_uri=None, with_source=None, force=None):
    ensure_bicep_installation(cmd.cli_ctx)

    minimum_supported_version = "0.4.1008"
    kebab_case_param_supported_version = "0.26.54"

    if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version):
        args = ["publish", file, "--target", target]
        use_kebab_case_params = bicep_version_greater_than_or_equal_to(cmd.cli_ctx, kebab_case_param_supported_version)
        documentation_uri = documentation_uri or documentationUri

        if documentation_uri:
            minimum_supported_version_for_documentationUri_parameter = "0.14.46"
            if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version_for_documentationUri_parameter):
                args += ["--documentation-uri" if use_kebab_case_params else "--documentationUri", documentation_uri]
            else:
                logger.error("az bicep publish with --documentationUri/-d parameter could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version_for_documentationUri_parameter)
        if with_source:
            minimum_supported_version_for_publish_with_source = "0.23.1"
            if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version_for_publish_with_source):
                args += ["--with-source"]
            else:
                logger.error("az bicep publish with --with-source/-s parameter could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version_for_publish_with_source)
        if force:
            minimum_supported_version_for_publish_force = "0.17.1"
            if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version_for_publish_force):
                args += ["--force"]
            else:
                logger.error("az bicep publish with --force parameter could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version_for_publish_force)

        run_bicep_command(cmd.cli_ctx, args)
    else:
        logger.error("az bicep publish could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def restore_bicep_file(cmd, file, force=None):
    ensure_bicep_installation(cmd.cli_ctx)

    minimum_supported_version = "0.4.1008"
    if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version):
        args = ["restore", file]
        if force:
            args += ["--force"]
        run_bicep_command(cmd.cli_ctx, args)
    else:
        logger.error("az bicep restore could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def decompile_bicep_file(cmd, file, force=None):
    args = ["decompile", file]
    if force:
        args += ["--force"]
    run_bicep_command(cmd.cli_ctx, args)


def decompileparams_bicep_file(cmd, file, bicep_file=None, outdir=None, outfile=None, stdout=None):
    ensure_bicep_installation(cmd.cli_ctx)

    minimum_supported_version = "0.18.4"
    if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version):
        args = ["decompile-params", file]
        if bicep_file:
            args += ["--bicep-file", bicep_file]
        if outdir:
            args += ["--outdir", outdir]
        if outfile:
            args += ["--outfile", outfile]
        if stdout:
            args += ["--stdout"]

        output = run_bicep_command(cmd.cli_ctx, args)

        if stdout:
            print(output)
    else:
        logger.error("az bicep decompile-params could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def show_bicep_cli_version(cmd):
    print(run_bicep_command(cmd.cli_ctx, ["--version"], auto_install=False))


def list_bicep_cli_versions(cmd):
    return get_bicep_available_release_tags()


def generate_params_file(cmd, file, no_restore=None, outdir=None, outfile=None, stdout=None, output_format=None, include_params=None):
    ensure_bicep_installation(cmd.cli_ctx, stdout=False)

    minimum_supported_version = "0.7.4"
    if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version):
        args = ["generate-params", file]
        if no_restore:
            args += ["--no-restore"]
        if outdir:
            args += ["--outdir", outdir]
        if outfile:
            args += ["--outfile", outfile]
        if output_format:
            args += ["--output-format", output_format]
        if include_params:
            args += ["--include-params", include_params]
        if stdout:
            args += ["--stdout"]

        output = run_bicep_command(cmd.cli_ctx, args)

        if stdout:
            print(output)
    else:
        logger.error("az bicep generate-params could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


def lint_bicep_file(cmd, file, no_restore=None, diagnostics_format=None):
    ensure_bicep_installation(cmd.cli_ctx, stdout=False)

    minimum_supported_version = "0.7.4"
    if bicep_version_greater_than_or_equal_to(cmd.cli_ctx, minimum_supported_version):
        args = ["lint", file]
        if no_restore:
            args += ["--no-restore"]
        if diagnostics_format:
            args += ["--diagnostics-format", diagnostics_format]

        output = run_bicep_command(cmd.cli_ctx, args)

        print(output)
    else:
        logger.error("az bicep lint could not be executed with the current version of Bicep CLI. Please upgrade Bicep CLI to v%s or later.", minimum_supported_version)


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
