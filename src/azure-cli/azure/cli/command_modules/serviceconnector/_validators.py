# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import random
import string

from knack.log import get_logger
from knack.prompting import (
    prompt,
    prompt_pass
)
from msrestazure.tools import (
    parse_resource_id,
    is_valid_resource_id
)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.azclierror import (
    ValidationError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError
)

from ._utils import run_cli_cmd
from ._resource_config import (
    CLIENT_TYPE,
    RESOURCE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES,
    SOURCE_RESOURCES_PARAMS,
    SOURCE_RESOURCES_CREATE_PARAMS,
    TARGET_RESOURCES_PARAMS,
    AUTH_TYPE_PARAMS,
    SUPPORTED_AUTH_TYPE
)


logger = get_logger(__name__)


def get_source_resource_name(cmd):
    '''Get source resource name
    e.g, az webapp connection list: => RESOURCE.WebApp
    '''
    source = None
    source_name = cmd.name.split(' ')[0]
    for item in SOURCE_RESOURCES:
        if item.value.lower() == source_name.lower():
            source = item
    return source


def get_target_resource_name(cmd):
    '''Get target resource name
    e.g, az webapp connection create postgres: => RESOURCE.Postgres
    '''
    target = None
    target_name = cmd.name.split(' ')[-1]
    for item in TARGET_RESOURCES:
        if item.value.lower() == target_name.lower():
            target = item
    return target


def get_resource_type_by_id(resource_id):
    '''Get source or target resource type by resource id
    '''
    target_type = None
    all_resources = dict()
    all_resources.update(SOURCE_RESOURCES)
    all_resources.update(TARGET_RESOURCES)
    for _type, _id in all_resources.items():
        matched = re.match(get_resource_regex(_id), resource_id, re.IGNORECASE)
        if matched:
            target_type = _type
    return target_type


def get_resource_regex(resource):
    '''Replace '{...}' with '[^/]*' for regex matching
    '''
    regex = resource
    for item in re.findall(r'(\{[^\{\}]*\})', resource):
        regex = regex.replace(item, '[^/]*')
    return regex


def check_required_args(resource, cmd_arg_values):
    '''Check whether a resource's required arguments are in cmd_arg_values
    '''
    args = re.findall(r'\{([^\{\}]*)\}', resource)
    args.remove('subscription')
    for arg in args:
        if not cmd_arg_values.get(arg, None):
            return False
    return True


def generate_connection_name(cmd):
    '''Generate connection name for users if not provided
    '''
    target = get_target_resource_name(cmd).value.replace('-', '')
    randstr = ''.join(random.sample(string.ascii_lowercase + string.digits, 5))
    name = '{}_{}'.format(target, randstr)

    logger.warning('Connection name is not specified, use generated one: --connection %s', name)
    return name


def get_client_type(cmd, namespace):
    '''Infer client type from source resource
    '''

    def _infer_webapp(source_id):
        value_type_map = {
            'python': CLIENT_TYPE.Python,
            'dotnet': CLIENT_TYPE.Dotnet,
            'dotnetcore': CLIENT_TYPE.Dotnet,
            'php': CLIENT_TYPE.Php,
            'java': CLIENT_TYPE.Java,
            'nodejs': CLIENT_TYPE.Nodejs,
            'node': CLIENT_TYPE.Nodejs,
            'ruby': CLIENT_TYPE.Ruby,
        }

        prop_type_map = {
            'javaVersion': CLIENT_TYPE.Java,
            'netFrameworkVersion': CLIENT_TYPE.Dotnet,
            'pythonVersion': CLIENT_TYPE.Python,
            'nodeVersion': CLIENT_TYPE.Nodejs,
            'phpVersion': CLIENT_TYPE.Php,
        }

        client_type = None
        try:
            output = run_cli_cmd('az webapp show --id {} -o json'.format(source_id))
            prop = output.get('siteConfig').get('linuxFxVersion', None) or\
                output.get('siteConfig').get('windowsFxVersion', None)
            # use 'linuxFxVersion' and 'windowsFxVersion' property to decide
            if prop:
                language = prop.split('|')[0].lower()
                client_type = value_type_map.get(language, None)
            # use '*Version' property to decide
            if client_type is None:
                for prop, _type in prop_type_map.items():
                    if output.get('siteConfig', dict()).get(prop, None) is not None:
                        client_type = _type
                        break
        except Exception:  # pylint: disable=broad-except
            pass

        return client_type

    def _infer_springcloud(source_id):
        client_type = None
        try:
            segments = parse_resource_id(source_id)
            output = run_cli_cmd('az spring-cloud app show -g {} -s {} -n {}'
                                 ' -o json'.format(segments.get('resource_group'), segments.get('name'),
                                                   segments.get('child_name_1')))
            prop_val = output.get('properties')\
                             .get('activeDeployment')\
                             .get('properties')\
                             .get('deploymentSettings')\
                             .get('runtimeVersion')

            language = prop_val.split('_')[0].lower()
            if language == 'java':
                client_type = CLIENT_TYPE.Java
            elif language == 'netcore':
                client_type = CLIENT_TYPE.Dotnet
        except Exception:   # pylint: disable=broad-except
            pass

        return client_type

    # fallback to use None as client type
    client_type = None
    if 'webapp' in cmd.name:
        client_type = _infer_webapp(namespace.source_id)
    elif 'spring-cloud' in cmd.name:
        client_type = _infer_springcloud(namespace.source_id)

    method = 'detected'
    if client_type is None:
        client_type = CLIENT_TYPE.Blank
        method = 'default'

    logger.warning('Client type is not specified, use %s one: --client-type %s', method, client_type.value)
    return client_type.value


def interactive_input(arg, hint):
    '''Get interactive inputs from users
    '''
    value = None
    cmd_value = None
    if arg == 'secret_auth_info':
        name = prompt('User name of database (--secret name=): ')
        secret = prompt_pass('Password of database (--secret secret=): ')
        value = {
            'name': name,
            'secret_info': {
                'secret_type': 'rawValue',
                'value': secret
            },
            'auth_type': 'secret'
        }
        cmd_value = 'name={} secret={}'.format(name, '*' * len(secret))
    elif arg == 'service_principal_auth_info_secret':
        client_id = prompt('ServicePrincipal client-id (--service-principal client_id=): ')
        object_id = prompt('Enterprise Application object-id (--service-principal object-id=): ')
        secret = prompt_pass('ServicePrincipal secret (--service-principal secret=): ')
        value = {
            'client_id': client_id,
            'object-id': object_id,
            'secret': secret,
            'auth_type': 'servicePrincipalSecret'
        }
        cmd_value = 'client-id={} principal-id={} secret={}'.format(client_id, object_id, '*' * len(secret))
    elif arg == 'user_identity_auth_info':
        client_id = prompt('UserAssignedIdentity client-id (--user-identity client_id=): ')
        subscription_id = prompt('UserAssignedIdentity subscription-id (--user-identity subs_id=): ')
        value = {
            'client_id': client_id,
            'subscription_id': subscription_id,
            'auth_type': 'userAssignedIdentity'
        }
        cmd_value = 'client-id={} subscription-id={}'.format(client_id, subscription_id)
    else:
        value = prompt('{}: '.format(hint))
        cmd_value = value

    # check blank value
    if isinstance(value, dict):
        for sub_val in value.values():
            if not sub_val:
                raise RequiredArgumentMissingError('{} should not be blank'.format(hint))
    elif not value:
        raise RequiredArgumentMissingError('{} should not be blank'.format(hint))

    return value, cmd_value


def get_local_context_value(cmd, arg):
    '''Get local context values
    '''
    groups = ['all', 'cupertino', 'serviceconnector']
    arg_map = {
        'source_resource_group': ['resource_group_name'],
        'target_resource_group': ['resource_group_name'],
        'server': ['postgres_server_name'],
        'database': ['postgres_database_name'],
        'site': ['webapp_name']
    }
    for group in groups:
        possible_args = arg_map.get(arg, [arg])
        for item in possible_args:
            if cmd.cli_ctx.local_context.get(group, item):
                return cmd.cli_ctx.local_context.get(group, item)
    return None


def intelligent_experience(cmd, namespace, missing_args):
    '''Use local context and interactive inputs to get arg values
    '''
    cmd_arg_values = dict()

    # use commandline source/target resource args
    for arg in missing_args:
        if getattr(namespace, arg, None) is not None:
            cmd_arg_values[arg] = getattr(namespace, arg)

    # for auth info without additional parameters
    if 'secret_auth_info_auto' in missing_args:
        cmd_arg_values['secret_auth_info_auto'] = {
            'auth_type': 'secret'
        }
        logger.warning('Auth info is not specified, use default one: --secret')
    elif 'system_identity_auth_info' in missing_args:
        cmd_arg_values['system_identity_auth_info'] = {
            'auth_type': 'systemAssignedIdentity'
        }
        logger.warning('Auth info is not specified, use default one: --system-identity')

    if cmd.cli_ctx.local_context.is_on:
        # arguments found in local context
        context_arg_values = dict()
        for arg in missing_args:
            if arg not in cmd_arg_values:
                if get_local_context_value(cmd, arg):
                    context_arg_values[arg] = get_local_context_value(cmd, arg)

        # apply local context arguments
        param_str = ''
        for arg in context_arg_values:
            option = missing_args[arg].get('options')[0]
            value = context_arg_values[arg]
            param_str += '{} {} '.format(option, value)
        if param_str:
            logger.warning('Apply local context arguments: %s', param_str.strip())
            cmd_arg_values.update(context_arg_values)

    # arguments from interactive inputs
    param_str = ''
    for arg in missing_args:
        if arg not in cmd_arg_values:
            hint = '{} ({})'.format(missing_args[arg].get('help'), '/'.join(missing_args[arg].get('options')))
            value, cmd_value = interactive_input(arg, hint)
            cmd_arg_values[arg] = value

            # show applied params
            option = missing_args[arg].get('options')[0]
            param_str += '{} {} '.format(option, cmd_value)
    if param_str:
        logger.warning('Apply interactive input arguments: %s', param_str.strip())

    return cmd_arg_values


def validate_source_resource_id(namespace):
    '''Validate resource id of a source resource
    '''
    if getattr(namespace, 'source_id', None):
        if not is_valid_resource_id(namespace.source_id):
            raise InvalidArgumentValueError('Resource id is invalid: {}'.format(namespace.source_id))
        matched = False
        for resource in SOURCE_RESOURCES.values():
            matched = re.match(get_resource_regex(resource), namespace.source_id)
            if matched:
                namespace.source_id = matched.group()
                return True
        if not matched:
            raise InvalidArgumentValueError('Unsupported source resource id: {}'.format(namespace.source_id))

    return False


def validate_connection_id(namespace):
    '''Validate resource id of a connection
    '''
    if getattr(namespace, 'indentifier', None):
        matched = False
        for resource in SOURCE_RESOURCES.values():
            regex = '({})/providers/Microsoft.ServiceLinker/linkers/([^/]*)'.format(get_resource_regex(resource))
            matched = re.match(regex, namespace.indentifier, re.IGNORECASE)
            if matched:
                namespace.source_id = matched.group(1)
                namespace.connection_name = matched.group(2)
                return True
        if not matched:
            raise InvalidArgumentValueError('Connection id is invalid: {}'.format(namespace.indentifier))

    return False


def validate_target_resource_id(namespace):
    '''Validate resource id of a target resource
    '''
    if getattr(namespace, 'target_id', None):
        if not is_valid_resource_id(namespace.target_id):
            raise InvalidArgumentValueError('Resource id is invalid: {}'.format(namespace.target_id))
        matched = False
        for resource in TARGET_RESOURCES.values():
            matched = re.match(get_resource_regex(resource), namespace.target_id, re.IGNORECASE)
            if matched:
                namespace.target_id = matched.group()
                return True
        if not matched:
            raise InvalidArgumentValueError('Unsupported target resource id is invalid: {}'.format(namespace.target_id))

    return False


def get_missing_source_args(cmd):
    '''Get source resource related args
    '''
    source = get_source_resource_name(cmd)
    missing_args = dict()

    for arg, content in SOURCE_RESOURCES_PARAMS.get(source).items():
        missing_args[arg] = content

    return missing_args


def get_missing_source_create_args(cmd, namespace):
    '''Get source resource related args in create
    '''
    source = get_source_resource_name(cmd)
    missing_args = dict()

    args = SOURCE_RESOURCES_CREATE_PARAMS.get(source)
    if args:
        for arg, content in args.items():
            if not getattr(namespace, arg, None):
                missing_args[arg] = content

    return missing_args


def get_missing_target_args(cmd):
    '''Get target resource related args
    '''
    target = get_target_resource_name(cmd)
    missing_args = dict()

    for arg, content in TARGET_RESOURCES_PARAMS.get(target).items():
        missing_args[arg] = content

    return missing_args


def get_missing_auth_args(cmd, namespace):
    '''Get auth info related args user didn't provide in command line
    '''
    source = get_source_resource_name(cmd)
    target = get_target_resource_name(cmd)
    missing_args = dict()

    # when keyvault csi is enabled, auth_type is userIdentity without subs_id and client_id
    if source == RESOURCE.KubernetesCluster and target == RESOURCE.KeyVault\
            and getattr(namespace, 'enable_csi', None):
        setattr(namespace, 'user_identity_auth_info', {
            'auth_type': 'userAssignedIdentity'
        })
        return missing_args

    # check if there are auth_info related params
    auth_param_exist = False
    for _, params in AUTH_TYPE_PARAMS.items():
        for arg in params:
            if getattr(namespace, arg, None):
                auth_param_exist = True
                break

    if source and target and not auth_param_exist:
        default_auth_type = SUPPORTED_AUTH_TYPE.get(source, {}).get(target, {})[0]

        for arg, content in AUTH_TYPE_PARAMS.get(default_auth_type).items():
            if getattr(namespace, arg, None) is None:
                missing_args[arg] = content

    return missing_args


def get_missing_connection_name(namespace):
    '''Get connection_name arg if user didn't provide it in command line
    '''
    missing_args = dict()
    if getattr(namespace, 'connection_name', None) is None:
        missing_args['connection_name'] = {
            'help': 'The connection name',
            'options': ['--connection']
        }

    return missing_args


def get_missing_client_type(namespace):
    '''Get client_type arg if user didn't provide it in command line
    '''
    missing_args = dict()
    if getattr(namespace, 'client_type', None) is None:
        missing_args['client_type'] = {
            'help': 'Client type of the connection',
            'options': ['--client-type']
        }

    return missing_args


def validate_list_params(cmd, namespace):
    '''Get missing args of list command
    '''
    missing_args = dict()
    if not validate_source_resource_id(namespace):
        missing_args.update(get_missing_source_args(cmd))
    return missing_args


def validate_create_params(cmd, namespace):
    '''Get missing args of create command
    '''
    missing_args = dict()
    if not validate_source_resource_id(namespace):
        missing_args.update(get_missing_source_args(cmd))
    missing_args.update(get_missing_source_create_args(cmd, namespace))
    if not validate_target_resource_id(namespace):
        missing_args.update(get_missing_target_args(cmd))
    missing_args.update(get_missing_auth_args(cmd, namespace))
    return missing_args


def validate_addon_params(cmd, namespace):
    '''Get missing args of add command with '--new'
    '''
    missing_args = dict()
    if not validate_source_resource_id(namespace):
        missing_args.update(get_missing_source_args(cmd))
    return missing_args


def validate_update_params(cmd, namespace):
    '''Get missing args of update command
    '''
    missing_args = dict()
    if not validate_connection_id(namespace):
        missing_args.update(get_missing_source_args(cmd))
    missing_args.update(get_missing_auth_args(cmd, namespace))
    missing_args.update(get_missing_connection_name(namespace))
    return missing_args


def validate_default_params(cmd, namespace):
    '''Get missing args of commands except for list, create
    '''
    missing_args = dict()
    if not validate_connection_id(namespace):
        missing_args.update(get_missing_source_args(cmd))
    missing_args.update(get_missing_connection_name(namespace))
    return missing_args


def apply_source_args(cmd, namespace, arg_values):
    '''Set source resource id by arg_values
    '''
    source = get_source_resource_name(cmd)
    resource = SOURCE_RESOURCES.get(source)
    if check_required_args(resource, arg_values):
        namespace.source_id = resource.format(
            subscription=get_subscription_id(cmd.cli_ctx),
            **arg_values
        )


def apply_source_create_args(cmd, namespace, arg_values):
    '''Set source resource related args in create by arg_values
    '''
    source = get_source_resource_name(cmd)
    for arg in SOURCE_RESOURCES_CREATE_PARAMS.get(source, {}):
        if arg in arg_values:
            setattr(namespace, arg, arg_values.get(arg, None))


def apply_target_args(cmd, namespace, arg_values):
    '''Set target resource id by arg_values
    '''
    target = get_target_resource_name(cmd)
    resource = TARGET_RESOURCES.get(target)
    if check_required_args(resource, arg_values):
        namespace.target_id = resource.format(
            subscription=get_subscription_id(cmd.cli_ctx),
            **arg_values
        )


def apply_auth_args(cmd, namespace, arg_values):
    '''Set auth info by arg_values
    '''
    source = get_source_resource_name(cmd)
    target = get_target_resource_name(cmd)
    if source and target:
        auth_types = SUPPORTED_AUTH_TYPE.get(source, {}).get(target, {})
        for auth_type in auth_types:
            for arg in AUTH_TYPE_PARAMS.get(auth_type):
                if arg in arg_values:
                    setattr(namespace, arg, arg_values.get(arg, None))


def apply_connection_name(namespace, arg_values):
    '''Set connection_name by arg_values
    '''
    if getattr(namespace, 'connection_name', None) is None:
        namespace.connection_name = arg_values.get('connection_name', None)


def apply_client_type(namespace, arg_values):
    '''Set client_type by arg_values
    '''
    if getattr(namespace, 'client_type', None) is None:
        namespace.client_type = arg_values.get('client_type', None)


def apply_list_params(cmd, namespace, arg_values):
    '''Set list command missing args
    '''
    apply_source_args(cmd, namespace, arg_values)


def apply_create_params(cmd, namespace, arg_values):
    '''Set create command missing args
    '''
    apply_source_args(cmd, namespace, arg_values)
    apply_source_create_args(cmd, namespace, arg_values)
    apply_target_args(cmd, namespace, arg_values)
    apply_auth_args(cmd, namespace, arg_values)


def apply_addon_params(cmd, namespace, arg_values):
    '''Set addon command missing args
    '''
    apply_source_args(cmd, namespace, arg_values)


def apply_update_params(cmd, namespace, arg_values):
    '''Set update command missing args
    '''
    apply_source_args(cmd, namespace, arg_values)
    apply_connection_name(namespace, arg_values)
    apply_auth_args(cmd, namespace, arg_values)


def apply_default_params(cmd, namespace, arg_values):
    '''Set missing args of commands except for list, create
    '''
    apply_source_args(cmd, namespace, arg_values)
    apply_connection_name(namespace, arg_values)


def validate_params(cmd, namespace):
    '''Validate command parameters
    '''
    def _validate_and_apply(validate, apply):
        missing_args = validate(cmd, namespace)
        if missing_args:
            arg_values = intelligent_experience(cmd, namespace, missing_args)
            apply(cmd, namespace, arg_values)

    # for command: 'list'
    if cmd.name.endswith(' list'):
        _validate_and_apply(validate_list_params, apply_list_params)
    # for command: 'create'
    elif 'create' in cmd.name:
        # if --new is specified
        if getattr(namespace, 'new_addon'):
            _validate_and_apply(validate_addon_params, apply_addon_params)
        else:
            _validate_and_apply(validate_create_params, apply_create_params)
        if getattr(namespace, 'connection_name', None) is None:
            namespace.connection_name = generate_connection_name(cmd)
        if getattr(namespace, 'client_type', None) is None:
            namespace.client_type = get_client_type(cmd, namespace)
    # for command: update
    elif 'update' in cmd.name:
        _validate_and_apply(validate_update_params, apply_update_params)
    # for command: all others
    else:
        _validate_and_apply(validate_default_params, apply_default_params)


def validate_kafka_params(cmd, namespace):
    def _validate_and_apply(validate, apply):
        missing_args = validate(cmd, namespace)
        if missing_args:
            arg_values = intelligent_experience(cmd, namespace, missing_args)
            apply(cmd, namespace, arg_values)

    _validate_and_apply(validate_list_params, apply_list_params)
    if 'create {}'.format(RESOURCE.ConfluentKafka.value) in cmd.name:
        if getattr(namespace, 'connection_name', None) is None:
            namespace.connection_name = generate_connection_name(cmd)
        elif namespace.connection_name.endswith('_schema'):
            raise InvalidArgumentValueError("Connection name of {} can not end with "
                                            "'_schema'".format(RESOURCE.ConfluentKafka.value))

        if getattr(namespace, 'client_type', None) is None:
            namespace.client_type = get_client_type(cmd, namespace)


def validate_service_state(linker_parameters):
    '''Validate whether user provided params are applicable to service state
    '''
    target_type = None
    target_id = linker_parameters.get('target_service', dict()).get('id')
    for target, resource_id in TARGET_RESOURCES.items():
        matched = re.match(get_resource_regex(resource_id), target_id, re.IGNORECASE)
        if matched:
            target_type = target

    if target_type == RESOURCE.AppConfig and linker_parameters.get('auth_info', dict()).get('auth_type') == 'secret':
        segments = parse_resource_id(target_id)
        rg = segments.get('resource_group')
        name = segments.get('name')
        if not rg or not name:
            return

        output = run_cli_cmd('az appconfig show -g {} -n {}'.format(rg, name))
        if output and output.get('disableLocalAuth') is True:
            raise ValidationError('Secret as auth type is not allowed when local auth is disabled for the '
                                  'specified appconfig, you may use service principal or managed identity.')
