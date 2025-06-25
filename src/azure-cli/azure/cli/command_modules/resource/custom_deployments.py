# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=line-too-long

from collections import OrderedDict
import json
import os
import re
import ssl

from urllib.request import urlopen
from urllib.parse import unquote

from azure.mgmt.core.tools import parse_resource_id

from azure.mgmt.resource.resources.models import DeploymentMode

from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError, ResourceNotFoundError
from azure.cli.core.parser import IncorrectUsageError
from azure.cli.core.util import read_file_content, shell_safe_json_parse, sdk_no_wait
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import raise_subdivision_deployment_error
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.profiles import ResourceType, get_sdk

from azure.cli.command_modules.resource._client_factory import (
    cf_deployments, cf_deployment_operations, cf_deploymentscripts, cf_resource_groups, _resource_deploymentstacks_client_factory, _resource_templatespecs_client_factory)
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
    else:
        template_content = (
            run_bicep_command(cmd.cli_ctx, ["build", "--stdout", template_file])
            if is_bicep_file(template_file)
            else read_file_content(template_file)
        )
        template_obj = _remove_comments_from_json(template_content, file_path=template_file)

    if rollback_on_error == '':
        on_error_deployment = OnErrorDeployment(type='LastSuccessful')
    elif rollback_on_error:
        on_error_deployment = OnErrorDeployment(type='SpecificDeployment', deployment_name=rollback_on_error)

    template_obj['resources'] = template_obj.get('resources', [])
    parameters = _process_parameters(template_obj, parameters) or {}
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
                                                    aux_tenants=aux_tenants, plug_pipeline=deployment_properties.template_link is None)

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
                                            what_if=None, proceed_if_no_change=None, mode=None):
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
                                                    no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                    mode=mode)


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
                                                    no_prompt=no_prompt, template_spec=template_spec, query_string=query_string,
                                                    mode='Incremental')


def _deploy_arm_template_at_management_group(cmd,
                                             management_group_id=None,
                                             template_file=None, template_uri=None, parameters=None,
                                             deployment_name=None, deployment_location=None, validate_only=False,
                                             no_wait=False, no_prompt=False, template_spec=None, query_string=None,
                                             mode=None):
    deployment_properties = _prepare_deployment_properties_unmodified(cmd, 'managementGroup', template_file=template_file,
                                                                      template_uri=template_uri,
                                                                      parameters=parameters, mode=mode,
                                                                      no_prompt=no_prompt, template_spec=template_spec, query_string=query_string)

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=deployment_properties.template_link is None)

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

    mgmt_client = _get_deployment_management_client(cmd.cli_ctx, plug_pipeline=deployment_properties.template_link is None)

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
                                                  deployment_name=None, mode=None,
                                                  aux_tenants=None, result_format=None,
                                                  no_pretty_print=None, no_prompt=False,
                                                  exclude_change_types=None, template_spec=None, query_string=None):
    return _what_if_deploy_arm_template_at_resource_group_core(cmd, resource_group_name,
                                                               template_file, template_uri, parameters,
                                                               deployment_name, mode,
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


def _load_template_spec_template(cmd, template_spec_id):
    rcf = _resource_templatespecs_client_factory(cmd.cli_ctx)
    id_parts = parse_resource_id(template_spec_id)
    resource_group_name = id_parts.get('resource_group')
    name = id_parts.get('name')
    version = id_parts.get('resource_name')

    template_spec = rcf.template_spec_versions.get(resource_group_name, name, version)

    return getattr(template_spec, 'main_template')


def _prepare_deployment_properties_unmodified(cmd, deployment_scope, template_file=None, template_uri=None, parameters=None,
                                              mode=None, rollback_on_error=None, no_prompt=False, template_spec=None, query_string=None):
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
        template_content = (
            run_bicep_command(cmd.cli_ctx, ["build", "--stdout", template_file])
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

    template_obj['resources'] = template_obj.get('resources', [])

    if _is_bicepparam_file_provided(parameters):
        parameters = json.loads(bicepparam_json_content).get('parameters', {})  # pylint: disable=used-before-assignment
    else:
        parameters = _process_parameters(template_obj, parameters) or {}
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


def list_deployments_at_subscription_scope(cmd, filter_string=None):
    client = cf_deployments(cmd.cli_ctx)
    return client.list_at_subscription_scope(filter=filter_string)


def list_deployments_at_resource_group(cmd, resource_group_name, filter_string=None):
    client = cf_deployments(cmd.cli_ctx)
    return client.list_by_resource_group(resource_group_name, filter=filter_string)


def list_deployments_at_management_group(cmd, management_group_id, filter_string=None):
    client = cf_deployments(cmd.cli_ctx)
    return client.list_at_management_group_scope(management_group_id, filter=filter_string)


def list_deployments_at_tenant_scope(cmd, filter_string=None):
    client = cf_deployments(cmd.cli_ctx)
    return client.list_at_tenant_scope(filter=filter_string)


def get_deployment_at_subscription_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.get_at_subscription_scope(deployment_name)


def get_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.get(resource_group_name, deployment_name)


def get_deployment_at_management_group(cmd, management_group_id, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.get_at_management_group_scope(management_group_id, deployment_name)


def get_deployment_at_tenant_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.get_at_tenant_scope(deployment_name)


def delete_deployment_at_subscription_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.begin_delete_at_subscription_scope(deployment_name)


def delete_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.begin_delete(resource_group_name, deployment_name)


def delete_deployment_at_management_group(cmd, management_group_id, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.begin_delete_at_management_group_scope(management_group_id, deployment_name)


def delete_deployment_at_tenant_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.begin_delete_at_tenant_scope(deployment_name)


def cancel_deployment_at_subscription_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.cancel_at_subscription_scope(deployment_name)


def cancel_deployment_at_resource_group(cmd, resource_group_name, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.cancel(resource_group_name, deployment_name)


def cancel_deployment_at_management_group(cmd, management_group_id, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.cancel_at_management_group_scope(management_group_id, deployment_name)


def cancel_deployment_at_tenant_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    return client.cancel_at_tenant_scope(deployment_name)


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
    client = cf_deployments(cmd.cli_ctx)
    result = client.export_template_at_subscription_scope(deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_resource_group(cmd, resource_group_name, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    result = client.export_template(resource_group_name, deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_management_group(cmd, management_group_id, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    result = client.export_template_at_management_group_scope(management_group_id, deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_template_at_tenant_scope(cmd, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    result = client.export_template_at_tenant_scope(deployment_name)

    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def export_deployment_as_template(cmd, resource_group_name, deployment_name):
    client = cf_deployments(cmd.cli_ctx)
    result = client.export_template(resource_group_name, deployment_name)
    print(json.dumps(result.template, indent=2))  # pylint: disable=no-member


def get_deployment_operations(client, resource_group_name, deployment_name, operation_ids):
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
    client = cf_deploymentscripts(cmd.cli_ctx)
    if resource_group_name is not None:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()


def get_deployment_script(cmd, resource_group_name, name):
    client = cf_deploymentscripts(cmd.cli_ctx)
    return client.get(resource_group_name, name)


def get_deployment_script_logs(cmd, resource_group_name, name):
    client = cf_deploymentscripts(cmd.cli_ctx)
    return client.get_logs(resource_group_name, name)


def delete_deployment_script(cmd, resource_group_name, name):
    client = cf_deploymentscripts(cmd.cli_ctx)
    client.delete(resource_group_name, name)


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
        rg_client = cf_resource_groups(cmd.cli_ctx)
        location = rg_client.get(resource_group_name).location
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
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.list_at_subscription_scope(deployment_name)


def list_deployment_operations_at_resource_group(cmd, resource_group_name, deployment_name):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.list(resource_group_name, deployment_name)


def list_deployment_operations_at_management_group(cmd, management_group_id, deployment_name):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.list_at_management_group_scope(management_group_id, deployment_name)


def list_deployment_operations_at_tenant_scope(cmd, deployment_name):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.list_at_tenant_scope(deployment_name)


def get_deployment_operation_at_subscription_scope(cmd, deployment_name, op_id):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.get_at_subscription_scope(deployment_name, op_id)


def get_deployment_operation_at_resource_group(cmd, resource_group_name, deployment_name, op_id):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.get(resource_group_name, deployment_name, op_id)


def get_deployment_operation_at_management_group(cmd, management_group_id, deployment_name, op_id):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.get_at_management_group_scope(management_group_id, deployment_name, op_id)


def get_deployment_operation_at_tenant_scope(cmd, deployment_name, op_id):
    client = cf_deployment_operations(cmd.cli_ctx)
    return client.get_at_tenant_scope(deployment_name, op_id)


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
