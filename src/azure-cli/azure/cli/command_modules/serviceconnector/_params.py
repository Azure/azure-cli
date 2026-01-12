# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_location_type,
    get_three_state_flag
)
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from ._validators import (
    validate_connstr_props,
    validate_params,
    validate_kafka_params,
    validate_local_params,
    get_default_object_id_of_current_user
)
from ._resource_config import (
    AUTH_TYPE,
    RESOURCE,
    SOURCE_RESOURCES_PARAMS,
    SOURCE_RESOURCES_CREATE_PARAMS,
    TARGET_RESOURCES_PARAMS,
    SOURCE_RESOURCES_OPTIONAL_PARAMS,
    TARGET_RESOURCES_CONNECTION_STRING,
    AUTH_TYPE_PARAMS,
    SUPPORTED_AUTH_TYPE,
    SUPPORTED_CLIENT_TYPE,
    TARGET_SUPPORT_SERVICE_ENDPOINT,
    TARGET_SUPPORT_PRIVATE_ENDPOINT,
    LOCAL_CONNECTION_PARAMS,
    OPT_OUT_OPTION
)
from ._addon_factory import AddonFactory
from knack.arguments import CLIArgumentType
from .action import AddAdditionalConnectionStringProperties, AddCustomizedKeys


def add_source_resource_block(context, source, enable_id=True, target=None):
    source_args = SOURCE_RESOURCES_PARAMS.get(source)
    for resource, args in SOURCE_RESOURCES_PARAMS.items():
        if resource != source:
            for arg in args:
                if arg not in source_args:
                    context.ignore(arg)

    required_args = []
    for arg, content in SOURCE_RESOURCES_PARAMS.get(source).items():
        id_arg = '\'--id\'' if enable_id else '\'--source-id\''
        deprecate_info = content.get('deprecate_info')
        context.argument(arg, configured_default=content.get('configured_default'),
                         options_list=content.get('options'), type=str,
                         deprecate_info=context.deprecate() if deprecate_info else None,
                         help='{}. Required if {} is not specified.{}'.format(
                             content.get('help'), id_arg, deprecate_info))
        required_args.append(content.get('options')[0])

    validator_kwargs = {
        'validator': validate_params}
    if not enable_id:
        context.argument('source_id', options_list=['--source-id'], type=str,
                         help="The resource id of a {source}. Required if {required_args} "
                         "are not specified.".format(
            source=source.value, required_args=str(required_args)),
            **validator_kwargs)
    else:
        required_args.append('--connection')
        context.argument('indentifier', options_list=['--id'], type=str,
                         help="The resource id of the connection. {required_args} are required "
                         "if '--id' is not specified.".format(required_args=str(required_args)))
        context.ignore('source_id')

    # scope parameter
    if source == RESOURCE.KubernetesCluster:
        context.argument('scope', options_list=['--kube-namespace'], type=str, default='default',
                         help="The kubernetes namespace where the connection information "
                         "will be saved into (as kubernetes secret).")
        context.argument('enable_csi', options_list=['--enable-csi'], arg_type=get_three_state_flag(),
                         help="Use keyvault as a secrets store via a CSI volume. "
                         "If specified, AuthType Arguments are not needed.")
        if target == RESOURCE.AppConfig:
            context.argument('enable_appconfig_extension', options_list=['--use-appconfig-extension', '-e'],
                             arg_type=get_three_state_flag(),
                             help="Install Azure App Configuration extension in the Kubernetes cluster.")
        else:
            context.ignore('enable_appconfig_extension')
    elif source == RESOURCE.ContainerApp:
        for arg, content in SOURCE_RESOURCES_CREATE_PARAMS.get(source).items():
            context.argument(arg, options_list=content.get(
                'options'), type=str, help=content.get('help'))
        context.ignore('enable_csi')
        context.ignore('enable_appconfig_extension')
    else:
        context.ignore('scope')
        context.ignore('enable_csi')
        context.ignore('enable_appconfig_extension')

    # slot parameter
    for resource, args in SOURCE_RESOURCES_OPTIONAL_PARAMS.items():
        for arg in args:
            if resource == source:
                deprecate_info = args.get(arg).get('deprecate_info')
                context.argument(arg, options_list=args.get(arg).get(
                    'options'), type=str,
                    deprecate_info=context.deprecate() if deprecate_info else None,
                    help=args.get(arg).get('help'))
            else:
                context.ignore(arg)


def add_auth_block(context, source, target):
    support_auth_types = SUPPORTED_AUTH_TYPE.get(
        source, {}).get(target, [])
    for auth_type in AUTH_TYPE_PARAMS:
        if auth_type in support_auth_types:
            validator = None
            if auth_type == AUTH_TYPE.UserAccount:
                validator = get_default_object_id_of_current_user
            for arg, params in AUTH_TYPE_PARAMS.get(auth_type).items():
                context.argument(arg, options_list=params.get('options'), action=params.get('action'), nargs='*',
                                 help=params.get('help'), arg_group='AuthType', validator=validator)
        else:
            for arg in AUTH_TYPE_PARAMS.get(auth_type):
                context.ignore(arg)


def add_local_connection_block(context, show_id=True):
    context.argument('location', arg_type=CLIArgumentType(
        arg_type=get_location_type(context),
        required=False,
        validator=get_default_location_from_resource_group))

    if show_id:
        context.argument('id', options_list=[
            '--id'], type=str, help='The id of connection.', validator=validate_local_params)
        params = LOCAL_CONNECTION_PARAMS.get('connection_name')
        context.argument('connection_name', options_list=params.get('options'), type=params.get('type'),
                         help=params.get('help'), validator=validate_local_params)


def add_target_resource_block(context, target):
    target_args = TARGET_RESOURCES_PARAMS.get(target)
    for resource, args in TARGET_RESOURCES_PARAMS.items():
        if resource != target:
            for arg in args:
                if arg not in target_args:
                    context.ignore(arg)

    required_args = []
    if target in TARGET_RESOURCES_PARAMS:
        for arg, content in TARGET_RESOURCES_PARAMS.get(target).items():
            context.argument(arg, options_list=content.get('options'), type=str,
                             help='{}. Required if \'--target-id\' is not specified.'.format(content.get('help')))
            required_args.append(content.get('options')[0])
        if target == RESOURCE.NeonPostgres or target == RESOURCE.MongoDbAtlas:
            context.ignore('target_id')
        else:
            context.argument('target_id', type=str,
                             help='The resource id of target service. Required if {required_args} '
                             'are not specified.'.format(required_args=str(required_args)))

    if target != RESOURCE.KeyVault:
        context.ignore('enable_csi')


def add_connection_name_argument(context, source):
    context.argument('connection_name', options_list=['--connection'], type=str,
                     help='Name of the {} connection.'.format(source.value), validator=validate_params)


def add_client_type_argument(context, source, target):
    client_types = SUPPORTED_CLIENT_TYPE.get(source).get(target, [])
    client_types = [item.value for item in client_types]
    context.argument('client_type', options_list=['--client-type'], arg_type=get_enum_type(client_types),
                     help='The client type used on the {}'.format(source.value))


def add_customized_keys_argument(context):
    context.argument('customized_keys', options_list=['--customized-keys'], action=AddCustomizedKeys, nargs='*',
                     help='The customized keys used to change default configuration names. Key is the original '
                     'name, value is the customized name.')


def add_connstr_props_argument(context):
    # linter: length '--additional-connection-string-properties' longer than 22, so use abbreviation
    context.argument('connstr_props', options_list=['--connstr-props'],
                     action=AddAdditionalConnectionStringProperties, nargs='*',
                     help='The additional connection string properties used to build connection string.',
                     validator=validate_connstr_props)


def add_no_recreate_arguments(context):
    context.argument('no_recreate', options_list=['--no-recreate'],
                     arg_type=get_three_state_flag(), default=False,
                     help='Skip executing creation operation when no updates to an existing connection.')


def add_target_type_argument(context, source):
    TARGET_TYPES = [
        elem.value for elem in SUPPORTED_AUTH_TYPE.get(source).keys()]
    context.argument('target_resource_type', options_list=['--target-type', '-t'],
                     arg_type=get_enum_type(TARGET_TYPES), help='The target resource type')


def add_new_addon_argument(context, source, target):
    if AddonFactory.get(target, None):
        context.argument('new_addon', options_list=['--new'], arg_type=get_three_state_flag(), default=False,
                         help='Indicates whether to create a new {} when '
                         'creating the {} connection'.format(target.value, source.value))
    else:
        context.ignore('new_addon')


def add_secret_store_argument(context, source=""):
    if source == RESOURCE.KubernetesCluster:
        context.ignore('key_vault_id')
    else:
        context.argument('key_vault_id', options_list=[
            '--vault-id'], help='The id of key vault to store secret value')


def add_configuration_store_argument(context):
    context.argument('app_config_id', options_list=[
        '--appconfig-id'], help='The app configuration id to store configuration')


def add_vnet_block(context, target):
    if target not in TARGET_SUPPORT_SERVICE_ENDPOINT:
        context.ignore('service_endpoint')
    else:
        context.argument('service_endpoint', options_list=['--service-endpoint'], arg_type=get_three_state_flag(),
                         default=None, arg_group='NetworkSolution',
                         help='Connect target service by service endpoint. Source resource must be in the VNet'
                         ' and target SKU must support service endpoint feature.')

    if target not in TARGET_SUPPORT_PRIVATE_ENDPOINT:
        context.ignore('private_endpoint')
    else:
        context.argument('private_endpoint', options_list=['--private-endpoint'], arg_type=get_three_state_flag(),
                         default=None, arg_group='NetworkSolution',
                         help='Connect target service by private endpoint. '
                         'The private endpoint in source virtual network must be created ahead.')


def add_connection_string_argument(context, source, target):
    if source == RESOURCE.WebApp and target in TARGET_RESOURCES_CONNECTION_STRING:
        context.argument('store_in_connection_string', options_list=['--config-connstr'],
                         arg_type=get_three_state_flag(), default=False, is_preview=True,
                         help='Store configuration into connection strings, '
                         'only could be used together with dotnet client_type')
    else:
        context.ignore('store_in_connection_string')


def add_confluent_kafka_argument(context):
    context.argument('bootstrap_server', options_list=[
        '--bootstrap-server'], help='Kafka bootstrap server url')
    context.argument('kafka_key', options_list=[
        '--kafka-key'], help='Kafka API-Key (key)')
    context.argument('kafka_secret', options_list=[
        '--kafka-secret'], help='Kafka API-Key (secret)')
    context.argument('schema_registry', options_list=[
        '--schema-registry'], help='Schema registry url')
    context.argument('schema_key', options_list=[
        '--schema-key'], help='Schema registry API-Key (key)')
    context.argument('schema_secret', options_list=[
        '--schema-secret'], help='Schema registry API-Key (secret)')
    context.argument('connection_name', options_list=['--connection'],
                     help='Name of the connection', validator=validate_kafka_params)


def add_opt_out_argument(context):
    context.argument('opt_out_list', options_list=['--opt-out'],
                     default=None, nargs='+',
                     arg_type=get_enum_type(OPT_OUT_OPTION),
                     help='Whether to disable some configuration steps. '
                     'Use configinfo to disbale configuration information changes on source. '
                     'Use publicnetwork to disable public network access configuration.'
                     'Use auth to skip auth configuration such as enabling managed identity and granting RBAC roles.'
                     )


def load_arguments(self, _):  # pylint: disable=too-many-statements

    for source in SOURCE_RESOURCES_PARAMS:

        with self.argument_context('{} connection list'.format(source.value)) as c:
            add_source_resource_block(
                c, source, enable_id=False)

        with self.argument_context('{} connection show'.format(source.value)) as c:
            add_source_resource_block(c, source)
            add_connection_name_argument(c, source)

        with self.argument_context('{} connection delete'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)

        with self.argument_context('{} connection list-configuration'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)
        with self.argument_context('{} connection validate'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)

        with self.argument_context('{} connection list-support-types'.format(source.value)) as c:
            add_target_type_argument(c, source)

        with self.argument_context('{} connection wait'.format(source.value)) as c:
            add_connection_name_argument(c, source)
            add_source_resource_block(c, source)

        for target in TARGET_RESOURCES_PARAMS:
            with self.argument_context('{} connection create {}'.format(source.value, target.value)) as c:
                add_client_type_argument(c, source, target)
                add_connection_name_argument(c, source)
                add_source_resource_block(c, source, enable_id=False, target=target)
                add_target_resource_block(c, target)
                add_auth_block(c, source, target)
                add_new_addon_argument(c, source, target)
                add_configuration_store_argument(c)
                add_secret_store_argument(c, source)
                add_vnet_block(c, target)
                add_connection_string_argument(c, source, target)
                add_customized_keys_argument(c)
                add_opt_out_argument(c)
                add_connstr_props_argument(c)
                add_no_recreate_arguments(c)

            with self.argument_context('{} connection update {}'.format(source.value, target.value)) as c:
                add_client_type_argument(c, source, target)
                add_connection_name_argument(c, source)
                add_source_resource_block(c, source, enable_id=True, target=target)
                add_auth_block(c, source, target)
                add_configuration_store_argument(c)
                add_secret_store_argument(c, source)
                add_vnet_block(c, target)
                add_connection_string_argument(c, source, target)
                add_customized_keys_argument(c)
                add_opt_out_argument(c)
                add_connstr_props_argument(c)

        # special target resource: independent implementation
        target = RESOURCE.ConfluentKafka
        with self.argument_context('{} connection create {}'.format(source.value, target.value)) as c:
            add_client_type_argument(c, source, target)
            add_source_resource_block(c, source, enable_id=False)
            add_confluent_kafka_argument(c)
            add_configuration_store_argument(c)
            add_secret_store_argument(c, source)
            add_customized_keys_argument(c)
            add_opt_out_argument(c)
        with self.argument_context('{} connection update {}'.format(source.value, target.value)) as c:
            add_client_type_argument(c, source, target)
            add_source_resource_block(c, source, enable_id=False)
            add_confluent_kafka_argument(c)
            add_configuration_store_argument(c)
            add_secret_store_argument(c, source)
            add_customized_keys_argument(c)
            add_opt_out_argument(c)

    # local connection
    with self.argument_context('connection list') as c:
        add_local_connection_block(c, show_id=False)

    with self.argument_context('connection show') as c:
        add_local_connection_block(c)

    with self.argument_context('connection delete') as c:
        add_local_connection_block(c)

    with self.argument_context('connection generate-configuration') as c:
        add_local_connection_block(c)

    with self.argument_context('connection validate') as c:
        add_local_connection_block(c)

    with self.argument_context('connection list-support-types') as c:
        add_target_type_argument(c, source)

    with self.argument_context('connection wait') as c:
        add_local_connection_block(c)

    source = RESOURCE.Local
    for target in TARGET_RESOURCES_PARAMS:
        with self.argument_context('connection preview-configuration {}'.format(target.value)) as c:
            add_auth_block(c, source, target)
            add_client_type_argument(c, source, target)

        with self.argument_context('connection create {}'.format(target.value)) as c:
            add_client_type_argument(c, source, target)
            add_target_resource_block(c, target)
            add_auth_block(c, source, target)
            add_new_addon_argument(c, source, target)
            add_configuration_store_argument(c)
            add_secret_store_argument(c, source)
            add_vnet_block(c, target)
            add_local_connection_block(c)
            add_customized_keys_argument(c)
        with self.argument_context('connection update {}'.format(target.value)) as c:
            add_client_type_argument(c, source, target)
            add_auth_block(c, source, target)
            add_configuration_store_argument(c)
            add_secret_store_argument(c, source)
            add_vnet_block(c, target)
            add_local_connection_block(c)
            add_customized_keys_argument(c)

    # special target resource: independent implementation
    target = RESOURCE.ConfluentKafka
    with self.argument_context('connection create {}'.format(target.value)) as c:
        add_client_type_argument(c, source, target)
        add_confluent_kafka_argument(c)
        add_configuration_store_argument(c)
        add_secret_store_argument(c, source)
        add_local_connection_block(c, show_id=False)
        add_customized_keys_argument(c)
    with self.argument_context('connection update {}'.format(target.value)) as c:
        add_client_type_argument(c, source, target)
        add_confluent_kafka_argument(c)
        add_configuration_store_argument(c)
        add_secret_store_argument(c, source)
        add_local_connection_block(c, show_id=False)
        add_customized_keys_argument(c)
    with self.argument_context('connection preview-configuration {}'.format(target.value)) as c:
        add_auth_block(c, source, target)
        add_client_type_argument(c, source, target)
