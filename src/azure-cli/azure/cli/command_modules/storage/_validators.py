# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import os
import argparse

from azure.cli.core.commands.validators import validate_key_value_pairs
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.util import get_file_json, shell_safe_json_parse

from azure.cli.command_modules.storage._client_factory import (get_storage_data_service_client,
                                                               blob_data_service_factory,
                                                               file_data_service_factory,
                                                               storage_client_factory,
                                                               cf_container_client,
                                                               cf_adls_file_system)
from azure.cli.command_modules.storage.util import glob_files_locally, guess_content_type
from azure.cli.command_modules.storage.sdkutil import get_table_data_type
from azure.cli.command_modules.storage.url_quote_util import encode_for_url
from azure.cli.command_modules.storage.oauth_token_util import TokenUpdater

from knack.log import get_logger
from knack.util import CLIError
from ._client_factory import cf_blob_service

storage_account_key_options = {'primary': 'key1', 'secondary': 'key2'}
logger = get_logger(__name__)


# Utilities


# pylint: disable=inconsistent-return-statements,too-many-lines
def _query_account_key(cli_ctx, account_name):
    """Query the storage account key. This is used when the customer doesn't offer account key but name."""
    rg, scf = _query_account_rg(cli_ctx, account_name)
    t_storage_account_keys = get_sdk(
        cli_ctx, ResourceType.MGMT_STORAGE, 'models.storage_account_keys#StorageAccountKeys')

    logger.debug('Disable HTTP logging to avoid having storage keys in debug logs')
    if t_storage_account_keys:
        return scf.storage_accounts.list_keys(rg, account_name, logging_enable=False).key1
    # of type: models.storage_account_list_keys_result#StorageAccountListKeysResult
    return scf.storage_accounts.list_keys(rg, account_name, logging_enable=False).keys[0].value  # pylint: disable=no-member


def _query_account_rg(cli_ctx, account_name):
    """Query the storage account's resource group, which the mgmt sdk requires."""
    scf = storage_client_factory(cli_ctx)
    acc = next((x for x in scf.storage_accounts.list() if x.name == account_name), None)
    if acc:
        from msrestazure.tools import parse_resource_id
        return parse_resource_id(acc.id)['resource_group'], scf
    raise ValueError("Storage account '{}' not found.".format(account_name))


def _create_token_credential(cli_ctx):
    from knack.cli import EVENT_CLI_POST_EXECUTE

    TokenCredential = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'common#TokenCredential')

    token_credential = TokenCredential()
    updater = TokenUpdater(token_credential, cli_ctx)

    def _cancel_timer_event_handler(_, **__):
        updater.cancel()
    cli_ctx.register_event(EVENT_CLI_POST_EXECUTE, _cancel_timer_event_handler)
    return token_credential


# region PARAMETER VALIDATORS
def parse_storage_account(cmd, namespace):
    """Parse storage account which can be either account name or account id"""
    from msrestazure.tools import parse_resource_id, is_valid_resource_id

    if namespace.account_name and is_valid_resource_id(namespace.account_name):
        namespace.resource_group_name = parse_resource_id(namespace.account_name)['resource_group']
        namespace.account_name = parse_resource_id(namespace.account_name)['name']
    elif namespace.account_name and not is_valid_resource_id(namespace.account_name) and \
            not namespace.resource_group_name:
        namespace.resource_group_name = _query_account_rg(cmd.cli_ctx, namespace.account_name)[0]


def process_resource_group(cmd, namespace):
    """Processes the resource group parameter from the account name"""
    if namespace.account_name and not namespace.resource_group_name:
        namespace.resource_group_name = _query_account_rg(cmd.cli_ctx, namespace.account_name)[0]


def validate_table_payload_format(cmd, namespace):
    t_table_payload = get_table_data_type(cmd.cli_ctx, 'table', 'TablePayloadFormat')
    if namespace.accept:
        formats = {
            'none': t_table_payload.JSON_NO_METADATA,
            'minimal': t_table_payload.JSON_MINIMAL_METADATA,
            'full': t_table_payload.JSON_FULL_METADATA
        }
        namespace.accept = formats[namespace.accept.lower()]


def validate_bypass(namespace):
    if namespace.bypass:
        namespace.bypass = ', '.join(namespace.bypass) if isinstance(namespace.bypass, list) else namespace.bypass


def validate_hns_migration_type(namespace):
    if namespace.request_type and namespace.request_type.lower() == 'validation':
        namespace.request_type = 'HnsOnValidationRequest'
    if namespace.request_type and namespace.request_type.lower() == 'upgrade':
        namespace.request_type = 'HnsOnHydrationRequest'


def get_config_value(cmd, section, key, default):
    logger.info("Try to get %s %s value from environment variables or config file.", section, key)
    return cmd.cli_ctx.config.get(section, key, default)


def is_storagev2(import_prefix):
    return import_prefix.startswith('azure.multiapi.storagev2.') or import_prefix.startswith('azure.data.tables')


# pylint: disable=too-many-branches, too-many-statements
def validate_client_parameters(cmd, namespace):
    """ Retrieves storage connection parameters from environment variables and parses out connection string into
    account name and key """
    n = namespace

    if hasattr(n, 'auth_mode'):
        auth_mode = n.auth_mode or get_config_value(cmd, 'storage', 'auth_mode', None)
        del n.auth_mode
        if not n.account_name:
            if hasattr(n, 'account_url') and not n.account_url:
                n.account_name = get_config_value(cmd, 'storage', 'account', None)
                n.account_url = get_config_value(cmd, 'storage', 'account_url', None)
            else:
                n.account_name = get_config_value(cmd, 'storage', 'account', None)
        if auth_mode == 'login':
            prefix = cmd.command_kwargs['resource_type'].value[0]
            # is_storagv2() is used to distinguish if the command is in track2 SDK
            # If yes, we will use get_login_credentials() as token credential
            if is_storagev2(prefix):
                from azure.cli.core._profile import Profile
                profile = Profile(cli_ctx=cmd.cli_ctx)
                n.token_credential, _, _ = profile.get_login_credentials(subscription_id=n._subscription)
            # Otherwise, we will assume it is in track1 and keep previous token updater
            else:
                n.token_credential = _create_token_credential(cmd.cli_ctx)

    if hasattr(n, 'token_credential') and n.token_credential:
        # give warning if there are account key args being ignored
        account_key_args = [n.account_key and "--account-key", n.sas_token and "--sas-token",
                            n.connection_string and "--connection-string"]
        account_key_args = [arg for arg in account_key_args if arg]

        if account_key_args:
            logger.warning('In "login" auth mode, the following arguments are ignored: %s',
                           ' ,'.join(account_key_args))
        return

    # When there is no input for credential, we will read environment variable
    if not n.connection_string and not n.account_key and not n.sas_token:
        n.connection_string = get_config_value(cmd, 'storage', 'connection_string', None)

    # if connection string supplied or in environment variables, extract account key and name
    if n.connection_string:
        conn_dict = validate_key_value_pairs(n.connection_string)
        n.account_name = conn_dict.get('AccountName')
        n.account_key = conn_dict.get('AccountKey')
        n.sas_token = conn_dict.get('SharedAccessSignature')

    # otherwise, simply try to retrieve the remaining variables from environment variables
    if not n.account_name:
        if hasattr(n, 'account_url') and not n.account_url:
            n.account_name = get_config_value(cmd, 'storage', 'account', None)
            n.account_url = get_config_value(cmd, 'storage', 'account_url', None)
        else:
            n.account_name = get_config_value(cmd, 'storage', 'account', None)
    if not n.account_key and not n.sas_token:
        n.account_key = get_config_value(cmd, 'storage', 'key', None)
    if not n.sas_token:
        n.sas_token = get_config_value(cmd, 'storage', 'sas_token', None)

    # strip the '?' from sas token. the portal and command line are returns sas token in different
    # forms
    if n.sas_token:
        n.sas_token = n.sas_token.lstrip('?')

    # account name with secondary
    if n.account_name and n.account_name.endswith('-secondary'):
        n.location_mode = 'secondary'
        n.account_name = n.account_name[:-10]

    # if account name is specified but no key, attempt to query
    if n.account_name and not n.account_key and not n.sas_token:
        message = """
There are no credentials provided in your command and environment, we will query for account key for your storage account.
It is recommended to provide --connection-string, --account-key or --sas-token in your command as credentials.
"""
        if 'auth_mode' in cmd.arguments:
            message += """
You also can add `--auth-mode login` in your command to use Azure Active Directory (Azure AD) for authorization if your login account is assigned required RBAC roles.
For more information about RBAC roles in storage, visit https://docs.microsoft.com/azure/storage/common/storage-auth-aad-rbac-cli.
"""
        logger.warning('%s\nIn addition, setting the corresponding environment variables can avoid inputting '
                       'credentials in your command. Please use --help to get more information about environment '
                       'variable usage.', message)
        try:
            n.account_key = _query_account_key(cmd.cli_ctx, n.account_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning("\nSkip querying account key due to failure: %s", ex)

    if hasattr(n, 'account_url') and n.account_url and not n.account_key and not n.sas_token:
        message = """
There are no credentials provided in your command and environment.
Please provide --connection-string, --account-key or --sas-token in your command as credentials.
        """

        if 'auth_mode' in cmd.arguments:
            message += """
You also can add `--auth-mode login` in your command to use Azure Active Directory (Azure AD) for authorization if your login account is assigned required RBAC roles.
For more information about RBAC roles in storage, visit https://docs.microsoft.com/azure/storage/common/storage-auth-aad-rbac-cli."
            """
        from azure.cli.core.azclierror import InvalidArgumentValueError
        raise InvalidArgumentValueError(message)


def validate_encryption_key(cmd, namespace):
    encryption_key_source = cmd.get_models('EncryptionScopeSource', resource_type=ResourceType.MGMT_STORAGE)
    if namespace.key_source == encryption_key_source.microsoft_key_vault and \
            not namespace.key_uri:
        raise CLIError("usage error: Please specify --key-uri when using {} as key source."
                       .format(encryption_key_source.microsoft_key_vault))
    if namespace.key_source != encryption_key_source.microsoft_key_vault and namespace.key_uri:
        raise CLIError("usage error: Specify `--key-source={}` and --key-uri to configure key vault properties."
                       .format(encryption_key_source.microsoft_key_vault))


def process_blob_source_uri(cmd, namespace):
    """
    Validate the parameters referenced to a blob source and create the source URI from them.
    """
    from .util import create_short_lived_blob_sas
    usage_string = \
        'Invalid usage: {}. Supply only one of the following argument sets to specify source:' \
        '\n\t   --source-uri' \
        '\n\tOR --source-container --source-blob --source-snapshot [--source-account-name & sas] ' \
        '\n\tOR --source-container --source-blob --source-snapshot [--source-account-name & key] '

    ns = vars(namespace)

    # source as blob
    container = ns.pop('source_container', None)
    blob = ns.pop('source_blob', None)
    snapshot = ns.pop('source_snapshot', None)

    # source credential clues
    source_account_name = ns.pop('source_account_name', None)
    source_account_key = ns.pop('source_account_key', None)
    sas = ns.pop('source_sas', None)

    # source in the form of an uri
    uri = ns.get('copy_source', None)
    if uri:
        if any([container, blob, sas, snapshot, source_account_name, source_account_key]):
            raise ValueError(usage_string.format('Unused parameters are given in addition to the '
                                                 'source URI'))
        # simplest scenario--no further processing necessary
        return

    validate_client_parameters(cmd, namespace)  # must run first to resolve storage account

    # determine if the copy will happen in the same storage account
    if not source_account_name and source_account_key:
        raise ValueError(usage_string.format('Source account key is given but account name is not'))
    if not source_account_name and not source_account_key:
        # neither source account name or key is given, assume that user intends to copy blob in
        # the same account
        source_account_name = ns.get('account_name', None)
        source_account_key = ns.get('account_key', None)
    elif source_account_name and not source_account_key:
        if source_account_name == ns.get('account_name', None):
            # the source account name is same as the destination account name
            source_account_key = ns.get('account_key', None)
        else:
            # the source account is different from destination account but the key is missing
            # try to query one.
            try:
                source_account_key = _query_account_key(cmd.cli_ctx, source_account_name)
            except ValueError:
                raise ValueError('Source storage account {} not found.'.format(source_account_name))
    # else: both source account name and key are given by user

    if not source_account_name:
        raise ValueError(usage_string.format('Storage account name not found'))

    if not sas:
        sas = create_short_lived_blob_sas(cmd, source_account_name, source_account_key, container, blob)

    query_params = []
    if sas:
        query_params.append(sas)
    if snapshot:
        query_params.append('snapshot={}'.format(snapshot))

    uri = 'https://{}.blob.{}/{}/{}{}{}'.format(source_account_name,
                                                cmd.cli_ctx.cloud.suffixes.storage_endpoint,
                                                container,
                                                blob,
                                                '?' if query_params else '',
                                                '&'.join(query_params))

    namespace.copy_source = uri


def validate_source_uri(cmd, namespace):  # pylint: disable=too-many-statements
    from .util import create_short_lived_blob_sas, create_short_lived_file_sas
    usage_string = \
        'Invalid usage: {}. Supply only one of the following argument sets to specify source:' \
        '\n\t   --source-uri [--source-sas]' \
        '\n\tOR --source-container --source-blob [--source-account-name & sas] [--source-snapshot]' \
        '\n\tOR --source-container --source-blob [--source-account-name & key] [--source-snapshot]' \
        '\n\tOR --source-share --source-path' \
        '\n\tOR --source-share --source-path [--source-account-name & sas]' \
        '\n\tOR --source-share --source-path [--source-account-name & key]'

    ns = vars(namespace)

    # source as blob
    container = ns.pop('source_container', None)
    blob = ns.pop('source_blob', None)
    snapshot = ns.pop('source_snapshot', None)

    # source as file
    share = ns.pop('source_share', None)
    path = ns.pop('source_path', None)
    file_snapshot = ns.pop('file_snapshot', None)

    # source credential clues
    source_account_name = ns.pop('source_account_name', None)
    source_account_key = ns.pop('source_account_key', None)
    source_sas = ns.pop('source_sas', None)

    # source in the form of an uri
    uri = ns.get('copy_source', None)
    if uri:
        if any([container, blob, snapshot, share, path, file_snapshot, source_account_name,
                source_account_key]):
            raise ValueError(usage_string.format('Unused parameters are given in addition to the '
                                                 'source URI'))
        if source_sas:
            source_sas = source_sas.lstrip('?')
            uri = '{}{}{}'.format(uri, '?', source_sas)
            namespace.copy_source = uri
        return

    # ensure either a file or blob source is specified
    valid_blob_source = container and blob and not share and not path and not file_snapshot
    valid_file_source = share and path and not container and not blob and not snapshot

    if not valid_blob_source and not valid_file_source:
        raise ValueError(usage_string.format('Neither a valid blob or file source is specified'))
    if valid_blob_source and valid_file_source:
        raise ValueError(usage_string.format('Ambiguous parameters, both blob and file sources are '
                                             'specified'))

    validate_client_parameters(cmd, namespace)  # must run first to resolve storage account

    if not source_account_name:
        if source_account_key:
            raise ValueError(usage_string.format('Source account key is given but account name is not'))
        # assume that user intends to copy blob in the same account
        source_account_name = ns.get('account_name', None)

    # determine if the copy will happen in the same storage account
    same_account = False

    if not source_account_key and not source_sas:
        if source_account_name == ns.get('account_name', None):
            same_account = True
            source_account_key = ns.get('account_key', None)
            source_sas = ns.get('sas_token', None)
        else:
            # the source account is different from destination account but the key is missing try to query one.
            try:
                source_account_key = _query_account_key(cmd.cli_ctx, source_account_name)
            except ValueError:
                raise ValueError('Source storage account {} not found.'.format(source_account_name))

    # Both source account name and either key or sas (or both) are now available
    if not source_sas:
        # generate a sas token even in the same account when the source and destination are not the same kind.
        if valid_file_source and (ns.get('container_name', None) or not same_account):
            dir_name, file_name = os.path.split(path) if path else (None, '')
            source_sas = create_short_lived_file_sas(cmd, source_account_name, source_account_key, share,
                                                     dir_name, file_name)
        elif valid_blob_source and (ns.get('share_name', None) or not same_account):
            source_sas = create_short_lived_blob_sas(cmd, source_account_name, source_account_key, container, blob)

    query_params = []
    if source_sas:
        query_params.append(source_sas.lstrip('?'))
    if snapshot:
        query_params.append('snapshot={}'.format(snapshot))
    if file_snapshot:
        query_params.append('sharesnapshot={}'.format(file_snapshot))

    uri = 'https://{0}.{1}.{6}/{2}/{3}{4}{5}'.format(
        source_account_name,
        'blob' if valid_blob_source else 'file',
        container if valid_blob_source else share,
        encode_for_url(blob if valid_blob_source else path),
        '?' if query_params else '',
        '&'.join(query_params),
        cmd.cli_ctx.cloud.suffixes.storage_endpoint)

    namespace.copy_source = uri


def validate_source_url(cmd, namespace):  # pylint: disable=too-many-statements, too-many-locals
    from .util import create_short_lived_blob_sas, create_short_lived_blob_sas_v2, create_short_lived_file_sas
    from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError, \
        MutuallyExclusiveArgumentError
    usage_string = \
        'Invalid usage: {}. Supply only one of the following argument sets to specify source:' \
        '\n\t   --source-uri [--source-sas]' \
        '\n\tOR --source-container --source-blob [--source-account-name & sas] [--source-snapshot]' \
        '\n\tOR --source-container --source-blob [--source-account-name & key] [--source-snapshot]' \
        '\n\tOR --source-share --source-path' \
        '\n\tOR --source-share --source-path [--source-account-name & sas]' \
        '\n\tOR --source-share --source-path [--source-account-name & key]'

    ns = vars(namespace)

    # source as blob
    container = ns.pop('source_container', None)
    blob = ns.pop('source_blob', None)
    snapshot = ns.pop('source_snapshot', None)

    # source as file
    share = ns.pop('source_share', None)
    path = ns.pop('source_path', None)
    file_snapshot = ns.pop('file_snapshot', None)

    # source credential clues
    source_account_name = ns.pop('source_account_name', None)
    source_account_key = ns.pop('source_account_key', None)
    source_sas = ns.pop('source_sas', None)

    # source in the form of an uri
    uri = ns.get('source_url', None)
    if uri:
        if any([container, blob, snapshot, share, path, file_snapshot, source_account_name,
                source_account_key]):
            raise InvalidArgumentValueError(usage_string.format(
                'Unused parameters are given in addition to the source URI'))
        if source_sas:
            source_sas = source_sas.lstrip('?')
            uri = '{}{}{}'.format(uri, '?', source_sas)
            namespace.copy_source = uri
        return

    # ensure either a file or blob source is specified
    valid_blob_source = container and blob and not share and not path and not file_snapshot
    valid_file_source = share and path and not container and not blob and not snapshot

    if not valid_blob_source and not valid_file_source:
        raise RequiredArgumentMissingError(usage_string.format('Neither a valid blob or file source is specified'))
    if valid_blob_source and valid_file_source:
        raise MutuallyExclusiveArgumentError(usage_string.format(
            'Ambiguous parameters, both blob and file sources are specified'))

    validate_client_parameters(cmd, namespace)  # must run first to resolve storage account

    if not source_account_name:
        if source_account_key:
            raise RequiredArgumentMissingError(usage_string.format(
                'Source account key is given but account name is not'))
        # assume that user intends to copy blob in the same account
        source_account_name = ns.get('account_name', None)

    # determine if the copy will happen in the same storage account
    same_account = False

    if not source_account_key and not source_sas:
        if source_account_name == ns.get('account_name', None):
            same_account = True
            source_account_key = ns.get('account_key', None)
            source_sas = ns.get('sas_token', None)
        else:
            # the source account is different from destination account but the key is missing try to query one.
            try:
                source_account_key = _query_account_key(cmd.cli_ctx, source_account_name)
            except ValueError:
                raise RequiredArgumentMissingError('Source storage account {} not found.'.format(source_account_name))

    # Both source account name and either key or sas (or both) are now available
    if not source_sas:
        # generate a sas token even in the same account when the source and destination are not the same kind.
        if valid_file_source and (ns.get('container_name', None) or not same_account):
            dir_name, file_name = os.path.split(path) if path else (None, '')
            source_sas = create_short_lived_file_sas(cmd, source_account_name, source_account_key, share,
                                                     dir_name, file_name)
        elif valid_blob_source and (ns.get('share_name', None) or not same_account):
            prefix = cmd.command_kwargs['resource_type'].value[0]
            # is_storagev2() is used to distinguish if the command is in track2 SDK
            # If yes, we will use get_login_credentials() as token credential
            if is_storagev2(prefix):
                source_sas = create_short_lived_blob_sas_v2(cmd, source_account_name, source_account_key, container,
                                                            blob)
            else:
                source_sas = create_short_lived_blob_sas(cmd, source_account_name, source_account_key, container, blob)

    query_params = []
    if source_sas:
        query_params.append(source_sas.lstrip('?'))
    if snapshot:
        query_params.append('snapshot={}'.format(snapshot))
    if file_snapshot:
        query_params.append('sharesnapshot={}'.format(file_snapshot))

    uri = 'https://{0}.{1}.{6}/{2}/{3}{4}{5}'.format(
        source_account_name,
        'blob' if valid_blob_source else 'file',
        container if valid_blob_source else share,
        encode_for_url(blob if valid_blob_source else path),
        '?' if query_params else '',
        '&'.join(query_params),
        cmd.cli_ctx.cloud.suffixes.storage_endpoint)

    namespace.source_url = uri


def validate_blob_type(namespace):
    if not namespace.blob_type:
        if namespace.file_path and namespace.file_path.endswith('.vhd'):
            namespace.blob_type = 'page'
        else:
            namespace.blob_type = 'block'


def validate_storage_data_plane_list(namespace):
    if namespace.num_results == '*':
        namespace.num_results = None
    else:
        namespace.num_results = int(namespace.num_results)


def get_content_setting_validator(settings_class, update, guess_from_file=None, process_md5=False):
    def _class_name(class_type):
        return class_type.__module__ + "." + class_type.__class__.__name__

    # pylint: disable=too-many-locals
    def validator(cmd, namespace):
        t_base_blob_service, t_file_service, t_blob_content_settings, t_file_content_settings = cmd.get_models(
            'blob.baseblobservice#BaseBlobService',
            'file#FileService',
            'blob.models#ContentSettings',
            'file.models#ContentSettings')

        prefix = cmd.command_kwargs['resource_type'].value[0]
        if is_storagev2(prefix):
            t_blob_content_settings = cmd.get_models('_models#ContentSettings',
                                                     resource_type=ResourceType.DATA_STORAGE_BLOB)

        # must run certain validators first for an update
        if update:
            validate_client_parameters(cmd, namespace)
        if not is_storagev2(prefix):
            if update and _class_name(settings_class) == _class_name(t_file_content_settings):
                get_file_path_validator()(namespace)

        ns = vars(namespace)
        clear_content_settings = ns.pop('clear_content_settings', False)

        # retrieve the existing object properties for an update
        if update and not clear_content_settings:
            account = ns.get('account_name')
            key = ns.get('account_key')
            cs = ns.get('connection_string')
            sas = ns.get('sas_token')
            token_credential = ns.get('token_credential')
            if _class_name(settings_class) == _class_name(t_blob_content_settings):
                container = ns.get('container_name')
                blob = ns.get('blob_name')
                lease_id = ns.get('lease_id')
                if is_storagev2(prefix):
                    account_kwargs = {'connection_string': cs,
                                      'account_name': account,
                                      'account_key': key,
                                      'token_credential': token_credential,
                                      'sas_token': sas}
                    client = cf_blob_service(cmd.cli_ctx, account_kwargs).get_blob_client(container=container,
                                                                                          blob=blob)
                    props = client.get_blob_properties(lease=lease_id).content_settings
                else:
                    client = get_storage_data_service_client(cmd.cli_ctx,
                                                             service=t_base_blob_service,
                                                             name=account,
                                                             key=key, connection_string=cs, sas_token=sas,
                                                             token_credential=token_credential)
                    props = client.get_blob_properties(container, blob, lease_id=lease_id).properties.content_settings

            elif _class_name(settings_class) == _class_name(t_file_content_settings):
                client = get_storage_data_service_client(cmd.cli_ctx, t_file_service, account, key, cs, sas)
                share = ns.get('share_name')
                directory = ns.get('directory_name')
                filename = ns.get('file_name')
                props = client.get_file_properties(share, directory, filename).properties.content_settings

        # create new properties
        new_props = settings_class(
            content_type=ns.pop('content_type', None),
            content_disposition=ns.pop('content_disposition', None),
            content_encoding=ns.pop('content_encoding', None),
            content_language=ns.pop('content_language', None),
            content_md5=ns.pop('content_md5', None),
            cache_control=ns.pop('content_cache_control', None)
        )

        # if update, fill in any None values with existing
        if update:
            if not clear_content_settings:
                for attr in ['content_type', 'content_disposition', 'content_encoding', 'content_language',
                             'content_md5', 'cache_control']:
                    if getattr(new_props, attr) is None:
                        setattr(new_props, attr, getattr(props, attr))
        else:
            if guess_from_file:
                new_props = guess_content_type(ns[guess_from_file], new_props, settings_class)

        # In track2 SDK, the content_md5 type should be bytearray. And then it will serialize to a string for request.
        # To keep consistent with track1 input and CLI will treat all parameter values as string. Here is to transform
        # content_md5 value to bytearray. And track2 SDK will serialize it into the right value with str type in header.
        if is_storagev2(prefix):
            if process_md5 and new_props.content_md5:
                from .track2_util import _str_to_bytearray
                new_props.content_md5 = _str_to_bytearray(new_props.content_md5)

        ns['content_settings'] = new_props

    return validator


def validate_custom_domain(namespace):
    if namespace.use_subdomain and not namespace.custom_domain:
        raise ValueError('usage error: --custom-domain DOMAIN [--use-subdomain]')


def validate_encryption_services(cmd, namespace):
    """
    Builds up the encryption services object for storage account operations based on the list of services passed in.
    """
    if namespace.encryption_services:
        t_encryption_services, t_encryption_service = get_sdk(cmd.cli_ctx, ResourceType.MGMT_STORAGE,
                                                              'EncryptionServices', 'EncryptionService', mod='models')
        services = {service: t_encryption_service(enabled=True) for service in namespace.encryption_services}

        namespace.encryption_services = t_encryption_services(**services)


def validate_encryption_source(namespace):
    if namespace.encryption_key_source == 'Microsoft.Keyvault' and \
            not (namespace.encryption_key_name and namespace.encryption_key_vault):
        raise ValueError('--encryption-key-name and --encryption-key-vault are required '
                         'when --encryption-key-source=Microsoft.Keyvault is specified.')

    if namespace.encryption_key_name or namespace.encryption_key_version is not None or namespace.encryption_key_vault:
        if namespace.encryption_key_source and namespace.encryption_key_source != 'Microsoft.Keyvault':
            raise ValueError('--encryption-key-name, --encryption-key-vault, and --encryption-key-version are not '
                             'applicable without Microsoft.Keyvault key-source.')


def validate_entity(namespace):
    """ Converts a list of key value pairs into a dictionary. Ensures that required
    RowKey and PartitionKey are converted to the correct case and included. """
    values = dict(x.split('=', 1) for x in namespace.entity)
    edm_types = {}
    keys = values.keys()
    for key in list(keys):
        if key.lower() == 'rowkey':
            val = values[key]
            del values[key]
            values['RowKey'] = val
        elif key.lower() == 'partitionkey':
            val = values[key]
            del values[key]
            values['PartitionKey'] = val
        elif key.endswith('@odata.type'):
            val = values[key]
            del values[key]
            real_key = key[0: key.index('@odata.type')]
            edm_types[real_key] = val

    keys = values.keys()
    missing_keys = 'RowKey ' if 'RowKey' not in keys else ''
    missing_keys = '{}PartitionKey'.format(missing_keys) \
        if 'PartitionKey' not in keys else missing_keys
    if missing_keys:
        raise argparse.ArgumentError(
            None, 'incorrect usage: entity requires: {}'.format(missing_keys))

    def cast_val(key, val):
        """ Attempts to cast numeric values (except RowKey and PartitionKey) to numbers so they
        can be queried correctly. """
        if key in ['PartitionKey', 'RowKey', 'DisplayVersion']:
            return val

        def try_cast(to_type):
            try:
                return to_type(val)
            except ValueError:
                return None

        return try_cast(int) or try_cast(float) or val

    for key, val in values.items():
        if edm_types.get(key, None):
            values[key] = (val, edm_types[key])
        else:
            # ensure numbers are converted from strings so querying will work correctly
            values[key] = cast_val(key, val)
    namespace.entity = values


def validate_marker(namespace):
    """ Converts a list of key value pairs into a dictionary. Ensures that required
    nextrowkey and nextpartitionkey are included. """
    if not namespace.marker:
        return
    marker = dict(x.split('=', 1) for x in namespace.marker)
    expected_keys = {'nextrowkey', 'nextpartitionkey'}

    for key in list(marker.keys()):
        new_key = key.lower()
        if new_key in expected_keys:
            expected_keys.remove(key.lower())
            val = marker[key]
            del marker[key]
            marker[new_key] = val
    if expected_keys:
        raise argparse.ArgumentError(
            None, 'incorrect usage: marker requires: {}'.format(' '.join(expected_keys)))

    namespace.marker = marker


def get_file_path_validator(default_file_param=None):
    """ Creates a namespace validator that splits out 'path' into 'directory_name' and 'file_name'.
    Allows another path-type parameter to be named which can supply a default filename. """

    def validator(namespace):
        if not hasattr(namespace, 'path'):
            return

        path = namespace.path
        dir_name, file_name = os.path.split(path) if path else (None, '')

        if default_file_param and '.' not in file_name:
            dir_name = path
            file_name = os.path.split(getattr(namespace, default_file_param))[1]
        dir_name = None if dir_name in ('', '.') else dir_name
        namespace.directory_name = dir_name
        namespace.file_name = file_name
        del namespace.path

    return validator


def validate_included_datasets(cmd, namespace):
    if namespace.include:
        include = namespace.include
        if set(include) - set('cmsd'):
            help_string = '(c)opy-info (m)etadata (s)napshots (d)eleted'
            raise ValueError('valid values are {} or a combination thereof.'.format(help_string))
        t_blob_include = cmd.get_models('blob#Include')
        namespace.include = t_blob_include('s' in include, 'm' in include, False, 'c' in include, 'd' in include)


def get_include_help_string(include_list):
    if include_list is None:
        return ''
    item = []
    for include in include_list:
        if include.value == 'uncommittedblobs':
            continue
        item.append('(' + include.value[0] + ')' + include[1:])
    return ', '.join(item)


def validate_included_datasets_validator(include_class):
    allowed_values = [x.lower() for x in dir(include_class) if not x.startswith('__')]
    allowed_string = ''.join(x[0] for x in allowed_values)

    def validator(namespace):
        if namespace.include:
            if set(namespace.include) - set(allowed_string):
                help_string = get_include_help_string(include_class)
                raise ValueError(
                    'valid values are {} or a combination thereof.'.format(help_string))
            include = []
            if 's' in namespace.include:
                include.append(include_class.snapshots)
            if 'm' in namespace.include:
                include.append(include_class.metadata)
            if 'c' in namespace.include:
                include.append(include_class.copy)
            if 'd' in namespace.include:
                include.append(include_class.deleted)
            if 'v' in namespace.include:
                include.append(include_class.versions)
            if 't' in namespace.include:
                include.append(include_class.tags)
            namespace.include = include

    return validator


def validate_key_name(namespace):
    key_options = {'primary': '1', 'secondary': '2'}
    if hasattr(namespace, 'key_type') and namespace.key_type:
        namespace.key_name = namespace.key_type + key_options[namespace.key_name]
    else:
        namespace.key_name = storage_account_key_options[namespace.key_name]
    if hasattr(namespace, 'key_type'):
        del namespace.key_type


def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)


def get_permission_help_string(permission_class):
    allowed_values = get_permission_allowed_values(permission_class)
    return ' '.join(['({}){}'.format(x[0], x[1:]) for x in allowed_values])


def get_permission_allowed_values(permission_class):
    if permission_class:
        instance = permission_class()

        allowed_values = [x.lower() for x in dir(instance) if not x.startswith('_')]
        if 'from_string' in allowed_values:
            allowed_values.remove('from_string')
        for i, item in enumerate(allowed_values):
            if item == 'delete_previous_version':
                allowed_values[i] = 'x' + item
            if item == 'permanent_delete':
                allowed_values[i] = 'y' + item
            if item == 'set_immutability_policy':
                allowed_values[i] = 'i' + item
            if item == 'manage_access_control':
                allowed_values[i] = 'permissions'
            if item == 'manage_ownership':
                allowed_values[i] = 'ownership'
        return sorted(allowed_values)
    return None


def get_permission_validator(permission_class):
    allowed_values = get_permission_allowed_values(permission_class)
    allowed_string = ''.join(x[0] for x in allowed_values)

    def validator(namespace):
        if namespace.permission:
            if set(namespace.permission) - set(allowed_string):
                help_string = get_permission_help_string(permission_class)
                raise ValueError(
                    'valid values are {} or a combination thereof.'.format(help_string))
            if hasattr(permission_class, 'from_string'):
                namespace.permission = permission_class.from_string(namespace.permission)
            else:
                namespace.permission = permission_class(_str=namespace.permission)

    return validator


def table_permission_validator(namespace):
    """ A special case for table because the SDK associates the QUERY permission with 'r' """
    from azure.data.tables._models import TableSasPermissions
    if namespace.permission:
        if set(namespace.permission) - set('raud'):
            help_string = '(r)ead/query (a)dd (u)pdate (d)elete'
            raise ValueError('valid values are {} or a combination thereof.'.format(help_string))
        namespace.permission = TableSasPermissions(_str=namespace.permission)


def validate_container_public_access(namespace):
    if namespace.public_access and namespace.public_access == 'off':
        namespace.public_access = None


def validate_container_nfsv3_squash(cmd, namespace):
    t_root_squash = cmd.get_models('RootSquashType', resource_type=ResourceType.MGMT_STORAGE)
    if namespace.root_squash and namespace.root_squash == t_root_squash.NO_ROOT_SQUASH:
        namespace.enable_nfs_v3_root_squash = False
        namespace.enable_nfs_v3_all_squash = False
    elif namespace.root_squash and namespace.root_squash == t_root_squash.ROOT_SQUASH:
        namespace.enable_nfs_v3_root_squash = True
        namespace.enable_nfs_v3_all_squash = False
    elif namespace.root_squash and namespace.root_squash == t_root_squash.ALL_SQUASH:
        namespace.enable_nfs_v3_all_squash = True

    del namespace.root_squash


def validate_fs_public_access(cmd, namespace):
    from .sdkutil import get_fs_access_type

    if namespace.public_access:
        namespace.public_access = get_fs_access_type(cmd.cli_ctx, namespace.public_access.lower())


def validate_select(namespace):
    if namespace.select:
        namespace.select = ','.join(namespace.select)


# pylint: disable=too-many-statements
def get_source_file_or_blob_service_client(cmd, namespace):
    """
    Create the second file service or blob service client for batch copy command, which is used to
    list the source files or blobs. If both the source account and source URI are omitted, it
    indicates that user want to copy files or blobs in the same storage account, therefore the
    destination client will be set None hence the command will use destination client.
    """
    t_file_svc, t_block_blob_svc = cmd.get_models('file#FileService', 'blob.blockblobservice#BlockBlobService')
    usage_string = 'invalid usage: supply only one of the following argument sets:' + \
                   '\n\t   --source-uri  [--source-sas]' + \
                   '\n\tOR --source-container' + \
                   '\n\tOR --source-container --source-account-name --source-account-key' + \
                   '\n\tOR --source-container --source-account-name --source-sas' + \
                   '\n\tOR --source-share --source-account-name --source-account-key' + \
                   '\n\tOR --source-share --source-account-name --source-account-sas'

    ns = vars(namespace)
    source_account = ns.pop('source_account_name', None)
    source_key = ns.pop('source_account_key', None)
    source_uri = ns.pop('source_uri', None)
    source_sas = ns.get('source_sas', None)
    source_container = ns.get('source_container', None)
    source_share = ns.get('source_share', None)

    if source_uri and source_account:
        raise ValueError(usage_string)
    if not source_uri and bool(source_container) == bool(source_share):  # must be container or share
        raise ValueError(usage_string)

    if (not source_account) and (not source_uri):
        # Set the source_client to None if neither source_account or source_uri is given. This
        # indicates the command that the source files share or blob container is in the same storage
        # account as the destination file share or blob container.
        #
        # The command itself should create the source service client since the validator can't
        # access the destination client through the namespace.
        #
        # A few arguments check will be made as well so as not to cause ambiguity.
        if source_key or source_sas:
            raise ValueError('invalid usage: --source-account-name is missing; the source account is assumed to be the'
                             ' same as the destination account. Do not provide --source-sas or --source-account-key')
        ns['source_client'] = None

        if 'token_credential' not in ns:  # not using oauth
            return
        # oauth is only possible through destination, must still get source creds
        source_account, source_key, source_sas = ns['account_name'], ns['account_key'], ns['sas_token']

    if source_account:
        if not (source_key or source_sas):
            # when neither storage account key or SAS is given, try to fetch the key in the current
            # subscription
            source_key = _query_account_key(cmd.cli_ctx, source_account)

        if source_container:
            ns['source_client'] = get_storage_data_service_client(
                cmd.cli_ctx, t_block_blob_svc, name=source_account, key=source_key, sas_token=source_sas)
        elif source_share:
            ns['source_client'] = get_storage_data_service_client(
                cmd.cli_ctx, t_file_svc, name=source_account, key=source_key, sas_token=source_sas)
    elif source_uri:
        if source_key or source_container or source_share:
            raise ValueError(usage_string)

        from .storage_url_helpers import StorageResourceIdentifier
        if source_sas:
            source_uri = '{}{}{}'.format(source_uri, '?', source_sas.lstrip('?'))
        identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, source_uri)
        nor_container_or_share = not identifier.container and not identifier.share
        if not identifier.is_url():
            raise ValueError('incorrect usage: --source-uri expects a URI')
        if identifier.blob or identifier.directory or identifier.filename or nor_container_or_share:
            raise ValueError('incorrect usage: --source-uri has to be blob container or file share')

        if identifier.sas_token:
            ns['source_sas'] = identifier.sas_token
        else:
            source_key = _query_account_key(cmd.cli_ctx, identifier.account_name)

        if identifier.container:
            ns['source_container'] = identifier.container
            if identifier.account_name != ns.get('account_name'):
                ns['source_client'] = get_storage_data_service_client(
                    cmd.cli_ctx, t_block_blob_svc, name=identifier.account_name, key=source_key,
                    sas_token=identifier.sas_token)
        elif identifier.share:
            ns['source_share'] = identifier.share
            if identifier.account_name != ns.get('account_name'):
                ns['source_client'] = get_storage_data_service_client(
                    cmd.cli_ctx, t_file_svc, name=identifier.account_name, key=source_key,
                    sas_token=identifier.sas_token)


def add_progress_callback(cmd, namespace):
    def _update_progress(current, total):
        message = getattr(_update_progress, 'message', 'Alive')
        reuse = getattr(_update_progress, 'reuse', False)

        if total:
            hook.add(message=message, value=current, total_val=total)
            if total == current and not reuse:
                hook.end()

    hook = cmd.cli_ctx.get_progress_controller(det=True)
    _update_progress.hook = hook

    if not namespace.no_progress:
        namespace.progress_callback = _update_progress
    del namespace.no_progress


def process_container_delete_parameters(cmd, namespace):
    """Process the parameters for storage container delete command"""
    # check whether to use mgmt or data-plane
    if namespace.bypass_immutability_policy:
        # use management-plane
        namespace.processed_account_name = namespace.account_name
        namespace.processed_resource_group, namespace.mgmt_client = _query_account_rg(
            cmd.cli_ctx, namespace.account_name)
        del namespace.auth_mode
    else:
        # use data-plane, like before
        validate_client_parameters(cmd, namespace)


def process_blob_download_batch_parameters(cmd, namespace):
    """Process the parameters for storage blob download command"""
    from azure.cli.core.azclierror import InvalidArgumentValueError
    # 1. quick check
    if not os.path.exists(namespace.destination) or not os.path.isdir(namespace.destination):
        raise InvalidArgumentValueError('incorrect usage: destination must be an existing directory')

    # 2. try to extract account name and container name from source string
    _process_blob_batch_container_parameters(cmd, namespace)

    # 3. Call validators
    add_download_progress_callback(cmd, namespace)


def process_blob_upload_batch_parameters(cmd, namespace):
    """Process the source and destination of storage blob upload command"""
    # 1. quick check
    if not os.path.exists(namespace.source) or not os.path.isdir(namespace.source):
        raise ValueError('incorrect usage: source must be an existing directory')

    # 2. try to extract account name and container name from destination string
    _process_blob_batch_container_parameters(cmd, namespace, source=False)

    # 3. collect the files to be uploaded
    namespace.source = os.path.realpath(namespace.source)
    namespace.source_files = list(glob_files_locally(namespace.source, namespace.pattern))

    # 4. determine blob type
    if namespace.blob_type is None:
        vhd_files = [f for f in namespace.source_files if f[0].endswith('.vhd')]
        if any(vhd_files) and len(vhd_files) == len(namespace.source_files):
            # when all the listed files are vhd files use page
            namespace.blob_type = 'page'
        elif any(vhd_files):
            from azure.cli.core.azclierror import ArgumentUsageError
            # source files contain vhd files but not all of them
            raise ArgumentUsageError("""Fail to guess the required blob type. Type of the files to be
            uploaded are not consistent. Default blob type for .vhd files is "page", while
            others are "block". You can solve this problem by either explicitly set the blob
            type or ensure the pattern matches a correct set of files.""")
        else:
            namespace.blob_type = 'block'

    # 5. Ignore content-md5 for batch upload
    namespace.content_md5 = None

    # 6. call other validators
    validate_metadata(namespace)
    t_blob_content_settings = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB, '_models#ContentSettings')
    get_content_setting_validator(t_blob_content_settings, update=False)(cmd, namespace)
    add_upload_progress_callback(cmd, namespace)
    blob_tier_validator_track2(cmd, namespace)


def process_blob_delete_batch_parameters(cmd, namespace):
    _process_blob_batch_container_parameters(cmd, namespace)


def _process_blob_batch_container_parameters(cmd, namespace, source=True):
    """Process the container parameters for storage blob batch commands before populating args from environment."""
    if source:
        container_arg, container_name_arg = 'source', 'source_container_name'
    else:
        # destination
        container_arg, container_name_arg = 'destination', 'destination_container_name'

    # try to extract account name and container name from source string
    from .storage_url_helpers import StorageResourceIdentifier
    container_arg_val = getattr(namespace, container_arg)  # either a url or name
    identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, container_arg_val)

    if not identifier.is_url():
        setattr(namespace, container_name_arg, container_arg_val)
    elif identifier.blob:
        raise ValueError('incorrect usage: {} should be either a container URL or name'.format(container_arg))
    else:
        setattr(namespace, container_name_arg, identifier.container)
        if namespace.account_name is None:
            namespace.account_name = identifier.account_name
        elif namespace.account_name != identifier.account_name:
            raise ValueError('The given storage account name is not consistent with the '
                             'account name in the destination URL')

        # if no sas-token is given and the container url contains one, use it
        if not namespace.sas_token and identifier.sas_token:
            namespace.sas_token = identifier.sas_token

    # Finally, grab missing storage connection parameters from environment variables
    validate_client_parameters(cmd, namespace)


def process_file_upload_batch_parameters(cmd, namespace):
    """Process the parameters of storage file batch upload command"""
    # 1. quick check
    if not os.path.exists(namespace.source):
        raise ValueError('incorrect usage: source {} does not exist'.format(namespace.source))

    if not os.path.isdir(namespace.source):
        raise ValueError('incorrect usage: source must be a directory')

    # 2. try to extract account name and container name from destination string
    from .storage_url_helpers import StorageResourceIdentifier
    identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, namespace.destination)
    if identifier.is_url():
        if identifier.filename or identifier.directory:
            raise ValueError('incorrect usage: destination must be a file share url')

        namespace.destination = identifier.share

        if not namespace.account_name:
            namespace.account_name = identifier.account_name

    namespace.source = os.path.realpath(namespace.source)


def process_file_download_batch_parameters(cmd, namespace):
    """Process the parameters for storage file batch download command"""
    # 1. quick check
    if not os.path.exists(namespace.destination) or not os.path.isdir(namespace.destination):
        raise ValueError('incorrect usage: destination must be an existing directory')

    # 2. try to extract account name and share name from source string
    process_file_batch_source_parameters(cmd, namespace)


def process_file_batch_source_parameters(cmd, namespace):
    from .storage_url_helpers import StorageResourceIdentifier
    identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, namespace.source)
    if identifier.is_url():
        if identifier.filename or identifier.directory:
            raise ValueError('incorrect usage: source should be either share URL or name')

        namespace.source = identifier.share

        if not namespace.account_name:
            namespace.account_name = identifier.account_name


def process_file_download_namespace(namespace):
    get_file_path_validator()(namespace)

    dest = namespace.file_path
    if not dest or os.path.isdir(dest):
        namespace.file_path = os.path.join(dest, namespace.file_name) \
            if dest else namespace.file_name


def process_metric_update_namespace(namespace):
    namespace.hour = namespace.hour == 'true'
    namespace.minute = namespace.minute == 'true'
    namespace.api = namespace.api == 'true' if namespace.api else None
    if namespace.hour is None and namespace.minute is None:
        raise argparse.ArgumentError(
            None, 'incorrect usage: must specify --hour and/or --minute')
    if (namespace.hour or namespace.minute) and namespace.api is None:
        raise argparse.ArgumentError(
            None, 'incorrect usage: specify --api when hour or minute metrics are enabled')


def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    subnet = namespace.subnet
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        return
    if subnet and not subnet_is_id and vnet:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        raise CLIError('incorrect usage: [--subnet ID | --subnet NAME --vnet-name NAME]')


def get_datetime_type(to_string):
    """ Validates UTC datetime. Examples of accepted forms:
    2017-12-31T01:11:59Z,2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
    from datetime import datetime

    def datetime_type(string):
        """ Validates UTC datetime. Examples of accepted forms:
        2017-12-31T01:11:59Z,2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
        accepted_date_formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%MZ',
                                 '%Y-%m-%dT%HZ', '%Y-%m-%d']
        for form in accepted_date_formats:
            try:
                if to_string:
                    return datetime.strptime(string, form).strftime(form)

                return datetime.strptime(string, form)
            except ValueError:
                continue
        raise ValueError("Input '{}' not valid. Valid example: 2000-12-31T12:59:59Z".format(string))

    return datetime_type


def get_api_version_type():
    """ Examples of accepted forms: 2017-12-31 """
    from datetime import datetime

    def api_version_type(string):
        """ Validates api version format. Examples of accepted form: 2017-12-31 """
        accepted_format = '%Y-%m-%d'
        try:
            return datetime.strptime(string, accepted_format).strftime(accepted_format)
        except ValueError:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            raise InvalidArgumentValueError("Input '{}' not valid. Valid example: 2008-10-27.".format(string))
    return api_version_type


def ipv4_range_type(string):
    """ Validates an IPv4 address or address range. """
    import re
    ip_format = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    if not re.match("^{}$".format(ip_format), string):
        if not re.match("^{ip_format}-{ip_format}$".format(ip_format=ip_format), string):
            raise CLIError("Please use the following format to specify ip range: '{ip1}-{ip2}'.")
    return string


def resource_type_type(loader):
    """ Returns a function which validates that resource types string contains only a combination of service,
    container, and object. Their shorthand representations are s, c, and o. """

    def impl(string):
        t_resources = loader.get_models('common.models#ResourceTypes')
        if set(string) - set("sco"):
            raise ValueError
        return t_resources(_str=''.join(set(string)))

    return impl


def resource_type_type_v2(loader):
    """ Returns a function which validates that resource types string contains only a combination of service,
    container, and object. Their shorthand representations are s, c, and o. """

    def impl(string):
        t_resources = loader.get_models('_shared.models#ResourceTypes', resource_type=ResourceType.DATA_STORAGE_BLOB)
        if set(string) - set("sco"):
            raise ValueError
        return t_resources.from_string(''.join(set(string)))

    return impl


def services_type(loader):
    """ Returns a function which validates that services string contains only a combination of blob, queue, table,
    and file. Their shorthand representations are b, q, t, and f. """

    def impl(string):
        t_services = loader.get_models('common.models#Services')
        if set(string) - set("bqtf"):
            raise ValueError
        return t_services(_str=''.join(set(string)))

    return impl


def services_type_v2():
    """ Returns a function which validates that services string contains only a combination of blob, queue, table,
    and file. Their shorthand representations are b, q, t, and f. """

    def impl(string):
        if set(string) - set("bqtf"):
            raise ValueError
        return ''.join(set(string))

    return impl


def get_char_options_validator(types, property_name):
    def _validator(namespace):
        service_types = set(getattr(namespace, property_name, []))

        if not service_types:
            raise ValueError('Missing options --{}.'.format(property_name.replace('_', '-')))

        if service_types - set(types):
            raise ValueError(
                '--{}: only valid values are: {}.'.format(property_name.replace('_', '-'), ', '.join(types)))

        setattr(namespace, property_name, service_types)

    return _validator


def page_blob_tier_validator(cmd, namespace):
    if not namespace.tier:
        return

    if namespace.blob_type != 'page' and namespace.tier:
        raise ValueError('Blob tier is only applicable to page blobs on premium storage accounts.')

    try:
        if is_storagev2(cmd.command_kwargs['resource_type'].value[0]):
            namespace.tier = getattr(cmd.get_models('_models#PremiumPageBlobTier'), namespace.tier)
        else:
            namespace.tier = getattr(cmd.get_models('blob.models#PremiumPageBlobTier'), namespace.tier)
    except AttributeError:
        from azure.cli.command_modules.storage.sdkutil import get_blob_tier_names
        raise ValueError('Unknown premium page blob tier name. Choose among {}'.format(', '.join(
            get_blob_tier_names(cmd.cli_ctx, 'PremiumPageBlobTier'))))


def block_blob_tier_validator(cmd, namespace):
    if not namespace.tier:
        return

    if namespace.blob_type != 'block' and namespace.tier:
        raise ValueError('Blob tier is only applicable to block blobs on standard storage accounts.')

    try:
        if is_storagev2(cmd.command_kwargs['resource_type'].value[0]):
            namespace.tier = getattr(cmd.get_models('_models#StandardBlobTier'), namespace.tier)
        else:
            namespace.tier = getattr(cmd.get_models('blob.models#StandardBlobTier'), namespace.tier)
    except AttributeError:
        from azure.cli.command_modules.storage.sdkutil import get_blob_tier_names
        raise ValueError('Unknown block blob tier name. Choose among {}'.format(', '.join(
            get_blob_tier_names(cmd.cli_ctx, 'StandardBlobTier'))))


def page_blob_tier_validator_track2(cmd, namespace):
    if not namespace.tier:
        return

    if namespace.blob_type != 'page' and namespace.tier:
        raise ValueError('Blob tier is only applicable to page blobs on premium storage accounts.')

    track2 = False
    try:
        if is_storagev2(cmd.command_kwargs['resource_type'].value[0]):
            track2 = True
            namespace.premium_page_blob_tier = getattr(cmd.get_models(
                '_generated.models._azure_blob_storage_enums#PremiumPageBlobAccessTier'), namespace.tier)
        else:
            namespace.premium_page_blob_tier = getattr(cmd.get_models('blob.models#PremiumPageBlobTier'),
                                                       namespace.tier)
    except AttributeError:
        from azure.cli.command_modules.storage.sdkutil import get_blob_tier_names_track2
        tier_names = get_blob_tier_names_track2(cmd.cli_ctx, 'blob.models#PremiumPageBlobTier', track2)
        if track2:
            tier_names = get_blob_tier_names_track2(
                cmd.cli_ctx, '_generated.models._azure_blob_storage_enums#PremiumPageBlobAccessTier', track2)
        raise ValueError('Unknown premium page blob tier name. Choose among {}'.format(', '.join(tier_names)))


def block_blob_tier_validator_track2(cmd, namespace):
    if not namespace.tier:
        return

    if namespace.blob_type != 'block' and namespace.tier:
        raise ValueError('Blob tier is only applicable to block blobs on standard storage accounts.')

    track2 = False
    try:
        if is_storagev2(cmd.command_kwargs['resource_type'].value[0]):
            track2 = True
            namespace.standard_blob_tier = getattr(cmd.get_models('_models#StandardBlobTier'), namespace.tier)
        else:
            namespace.standard_blob_tier = getattr(cmd.get_models('blob.models#StandardBlobTier'), namespace.tier)
    except AttributeError:
        from azure.cli.command_modules.storage.sdkutil import get_blob_tier_names_track2
        tier_names = get_blob_tier_names_track2(cmd.cli_ctx, 'blob.models#StandardBlobTier', track2)
        if track2:
            tier_names = get_blob_tier_names_track2(cmd.cli_ctx, '_models#StandardBlobTier', track2)
        raise ValueError('Unknown block blob tier name. Choose among {}'.format(', '.join(tier_names)))


def blob_tier_validator(cmd, namespace):
    if namespace.blob_type == 'page':
        page_blob_tier_validator(cmd, namespace)
    elif namespace.blob_type == 'block':
        block_blob_tier_validator(cmd, namespace)
    else:
        raise ValueError('Blob tier is only applicable to block or page blob.')


def blob_tier_validator_track2(cmd, namespace):
    if namespace.tier:
        if namespace.blob_type == 'page':
            page_blob_tier_validator_track2(cmd, namespace)
        elif namespace.blob_type == 'block':
            block_blob_tier_validator_track2(cmd, namespace)
        else:
            raise ValueError('Blob tier is only applicable to block or page blob.')
    del namespace.tier


def blob_download_file_path_validator(namespace):
    if os.path.isdir(namespace.file_path):
        from azure.cli.core.azclierror import FileOperationError
        raise FileOperationError('File is expected, not a directory: {}'.format(namespace.file_path))


def blob_rehydrate_priority_validator(namespace):
    if namespace.blob_type == 'page' and namespace.rehydrate_priority:
        raise ValueError('--rehydrate-priority is only applicable to block blob.')
    if namespace.tier == 'Archive' and namespace.rehydrate_priority:
        raise ValueError('--rehydrate-priority is only applicable to rehydrate blob data from the archive tier.')
    if namespace.rehydrate_priority is None:
        namespace.rehydrate_priority = 'Standard'


def validate_azcopy_upload_destination_url(cmd, namespace):
    client = blob_data_service_factory(cmd.cli_ctx, {
        'account_name': namespace.account_name, 'connection_string': namespace.connection_string})
    destination_path = namespace.destination_path
    if not destination_path:
        destination_path = ''
    url = client.make_blob_url(namespace.destination_container, destination_path)
    namespace.destination = url
    del namespace.destination_container
    del namespace.destination_path


def validate_azcopy_remove_arguments(cmd, namespace):
    usage_string = \
        'Invalid usage: {}. Supply only one of the following argument sets to specify source:' \
        '\n\t   --container-name  [--name]' \
        '\n\tOR --share-name [--path]'

    ns = vars(namespace)

    # source as blob
    container = ns.pop('container_name', None)
    blob = ns.pop('blob_name', None)

    # source as file
    share = ns.pop('share_name', None)
    path = ns.pop('path', None)

    # ensure either a file or blob source is specified
    valid_blob = container and not share
    valid_file = share and not container

    if not valid_blob and not valid_file:
        raise ValueError(usage_string.format('Neither a valid blob or file source is specified'))
    if valid_blob and valid_file:
        raise ValueError(usage_string.format('Ambiguous parameters, both blob and file sources are '
                                             'specified'))
    if valid_blob:
        client = blob_data_service_factory(cmd.cli_ctx, {
            'account_name': namespace.account_name})
        if not blob:
            blob = ''
        url = client.make_blob_url(container, blob)
        namespace.service = 'blob'
        namespace.target = url

    if valid_file:
        client = file_data_service_factory(cmd.cli_ctx, {
            'account_name': namespace.account_name,
            'account_key': namespace.account_key})
        dir_name, file_name = os.path.split(path) if path else (None, '')
        dir_name = None if dir_name in ('', '.') else dir_name
        url = client.make_file_url(share, dir_name, file_name)
        namespace.service = 'file'
        namespace.target = url


def as_user_validator(namespace):
    if hasattr(namespace, 'token_credential') and not namespace.as_user:
        raise CLIError('incorrect usage: specify --as-user when --auth-mode login is used to get user delegation key.')
    if namespace.as_user:
        if namespace.expiry is None:
            raise argparse.ArgumentError(
                None, 'incorrect usage: specify --expiry when as-user is enabled')

        expiry = get_datetime_type(False)(namespace.expiry)

        from datetime import datetime, timedelta
        if expiry > datetime.utcnow() + timedelta(days=7):
            raise argparse.ArgumentError(
                None, 'incorrect usage: --expiry should be within 7 days from now')

        if ((not hasattr(namespace, 'token_credential') or namespace.token_credential is None) and
                (not hasattr(namespace, 'auth_mode') or namespace.auth_mode != 'login')):
            raise argparse.ArgumentError(
                None, "incorrect usage: specify '--auth-mode login' when as-user is enabled")


def validator_change_feed_retention_days(namespace):
    enable = namespace.enable_change_feed
    days = namespace.change_feed_retention_days

    from azure.cli.core.azclierror import InvalidArgumentValueError
    if enable is False and days is not None:
        raise InvalidArgumentValueError("incorrect usage: "
                                        "'--change-feed-retention-days' is invalid "
                                        "when '--enable-change-feed' is set to false")
    if enable is None and days is not None:
        raise InvalidArgumentValueError("incorrect usage: "
                                        "please specify '--enable-change-feed true' if you "
                                        "want to set the value for '--change-feed-retention-days'")
    if days is not None:
        if days < 1:
            raise InvalidArgumentValueError("incorrect usage: "
                                            "'--change-feed-retention-days' must be greater than or equal to 1")
        if days > 146000:
            raise InvalidArgumentValueError("incorrect usage: "
                                            "'--change-feed-retention-days' must be less than or equal to 146000")


def validator_delete_retention_days(namespace, enable=None, days=None):
    enable_param = '--' + enable.replace('_', '-')
    days_param = '--' + enable.replace('_', '-')
    enable = getattr(namespace, enable)
    days = getattr(namespace, days)

    if enable is True and days is None:
        raise ValueError(
            "incorrect usage: you have to provide value for '{}' when '{}' "
            "is set to true".format(days_param, enable_param))

    if enable is False and days is not None:
        raise ValueError(
            "incorrect usage: '{}' is invalid when '{}' is set to false".format(days_param, enable_param))

    if enable is None and days is not None:
        raise ValueError(
            "incorrect usage: please specify '{} true' if you want to set the value for "
            "'{}'".format(enable_param, days_param))

    if days or days == 0:
        if days < 1:
            raise ValueError(
                "incorrect usage: '{}' must be greater than or equal to 1".format(days_param))
        if days > 365:
            raise ValueError(
                "incorrect usage: '{}' must be less than or equal to 365".format(days_param))


def validate_container_delete_retention_days(namespace):
    validator_delete_retention_days(namespace, enable='enable_container_delete_retention',
                                    days='container_delete_retention_days')


def validate_delete_retention_days(namespace):
    validator_delete_retention_days(namespace, enable='enable_delete_retention',
                                    days='delete_retention_days')


def validate_file_delete_retention_days(namespace):
    from azure.cli.core.azclierror import ValidationError
    if namespace.enable_delete_retention is True and namespace.delete_retention_days is None:
        raise ValidationError(
            "incorrect usage: you have to provide value for '--delete-retention-days' when '--enable-delete-retention' "
            "is set to true")

    if namespace.enable_delete_retention is False and namespace.delete_retention_days is not None:
        raise ValidationError(
            "incorrect usage: '--delete-retention-days' is invalid when '--enable-delete-retention' is set to false")


# pylint: disable=too-few-public-methods
class BlobRangeAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if not namespace.blob_ranges:
            namespace.blob_ranges = []
        if isinstance(values, list):
            values = ' '.join(values)
        BlobRange = namespace._cmd.get_models('BlobRestoreRange', resource_type=ResourceType.MGMT_STORAGE)
        try:
            start_range, end_range = values.split(' ')
        except (ValueError, TypeError):
            raise CLIError('usage error: --blob-range VARIABLE OPERATOR VALUE')
        namespace.blob_ranges.append(BlobRange(
            start_range=start_range,
            end_range=end_range
        ))


def validate_private_endpoint_connection_id(cmd, namespace):
    if namespace.connection_id:
        from azure.cli.core.util import parse_proxy_resource_id
        result = parse_proxy_resource_id(namespace.connection_id)
        namespace.resource_group_name = result['resource_group']
        namespace.account_name = result['name']
        namespace.private_endpoint_connection_name = result['child_name_1']

    if namespace.account_name and not namespace.resource_group_name:
        namespace.resource_group_name = _query_account_rg(cmd.cli_ctx, namespace.account_name)[0]

    if not all([namespace.account_name, namespace.resource_group_name, namespace.private_endpoint_connection_name]):
        raise CLIError('incorrect usage: [--id ID | --name NAME --account-name NAME]')

    del namespace.connection_id


def pop_data_client_auth(ns):
    del ns.auth_mode
    del ns.account_key
    del ns.connection_string
    del ns.sas_token


def validate_encryption_scope_parameter(cmd, ns):
    if (ns.default_encryption_scope and ns.prevent_encryption_scope_override is None) or \
         (not ns.default_encryption_scope and ns.prevent_encryption_scope_override is not None):
        raise CLIError("usage error: You need to specify both --default-encryption-scope and "
                       "--prevent-encryption-scope-override to set encryption scope information "
                       "when creating container.")


def validate_encryption_scope_client_params(ns):
    if ns.encryption_scope:
        # will use track2 client and socket_timeout is unused
        if 'socket_timeout' in ns:
            del ns.socket_timeout


def validate_access_control(namespace):
    if namespace.acl and namespace.permissions:
        raise CLIError('usage error: invalid when specifying both --acl and --permissions.')


def validate_service_type(services, service_type):
    if service_type == 'table':
        return 't' in services
    if service_type == 'blob':
        return 'b' in services
    if service_type == 'queue':
        return 'q' in services


def validate_logging_version(namespace):
    if validate_service_type(namespace.services, 'table') and namespace.version and namespace.version != 1.0:
        raise CLIError(
            'incorrect usage: for table service, the supported version for logging is `1.0`. For more information, '
            'please refer to https://docs.microsoft.com/rest/api/storageservices/storage-analytics-log-format.')


def validate_match_condition(namespace):
    from .track2_util import _if_match, _if_none_match
    if namespace.if_match:
        namespace = _if_match(if_match=namespace.if_match, **namespace)
        del namespace.if_match
    if namespace.if_none_match:
        namespace = _if_none_match(if_none_match=namespace.if_none_match, **namespace)
        del namespace.if_none_match


def validate_or_policy(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    error_elements = []
    if namespace.properties is None:
        error_msg = "Please provide --policy in JSON format or the following arguments: "
        if namespace.source_account is None:
            error_elements.append("--source-account")

        # Apply account name when there is no destination account provided
        if namespace.destination_account is None:
            namespace.destination_account = namespace.account_name

        if error_elements:
            error_msg += ", ".join(error_elements)
            error_msg += " to initialize Object Replication Policy for storage account."
            raise ValueError(error_msg)
    else:
        if os.path.exists(namespace.properties):
            or_policy = get_file_json(namespace.properties)
        else:
            or_policy = shell_safe_json_parse(namespace.properties)

        try:
            namespace.source_account = or_policy["sourceAccount"]
        except KeyError:
            namespace.source_account = or_policy["source_account"]
        if namespace.source_account is None:
            error_elements.append("source_account")

        try:
            namespace.destination_account = or_policy["destinationAccount"]
        except KeyError:
            namespace.destination_account = or_policy["destination_account"]

        if "rules" not in or_policy.keys() or not or_policy["rules"]:
            error_elements.append("rules")
        error_msg = "Missing input parameters: "
        if error_elements:
            error_msg += ", ".join(error_elements)
            error_msg += " in properties to initialize Object Replication Policy for storage account."
            raise ValueError(error_msg)
        namespace.properties = or_policy

        if "policyId" in or_policy.keys() and or_policy["policyId"]:
            namespace.policy_id = or_policy['policyId']

    if not is_valid_resource_id(namespace.source_account):
        namespace.source_account = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Storage', type='storageAccounts',
            name=namespace.source_account)
    if not is_valid_resource_id(namespace.destination_account):
        namespace.destination_account = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Storage', type='storageAccounts',
            name=namespace.destination_account)


def get_url_with_sas(cmd, namespace, url=None, container=None, blob=None, share=None, file_path=None):
    import re

    # usage check
    if not container and blob:
        raise CLIError('incorrect usage: please specify container information for your blob resource.')
    if not share and file_path:
        raise CLIError('incorrect usage: please specify share information for your file resource.')

    if url and container:
        raise CLIError('incorrect usage: you only can specify one between url and container information.')
    if url and share:
        raise CLIError('incorrect usage: you only can specify one between url and share information.')
    if share and container:
        raise CLIError('incorrect usage: you only can specify one between share and container information.')

    # get url
    storage_endpoint = cmd.cli_ctx.cloud.suffixes.storage_endpoint
    service = None
    if url is not None:
        # validate source is uri or local path
        storage_pattern = re.compile(r'https://(.*?)\.(blob|dfs|file).%s' % storage_endpoint)
        result = re.findall(storage_pattern, url)
        if result:  # source is URL
            storage_info = result[0]
            namespace.account_name = storage_info[0]
            if storage_info[1] in ['blob', 'dfs']:
                service = 'blob'
            elif storage_info[1] in ['file']:
                service = 'file'
            else:
                raise ValueError('{} is not valid storage endpoint.'.format(url))
        else:
            logger.info("%s is not Azure storage url.", url)
            return service, url
    # validate credential
    validate_client_parameters(cmd, namespace)
    kwargs = {'account_name': namespace.account_name,
              'account_key': namespace.account_key,
              'connection_string': namespace.connection_string,
              'sas_token': namespace.sas_token}
    if container:
        client = blob_data_service_factory(cmd.cli_ctx, kwargs)
        if blob is None:
            blob = ''
        url = client.make_blob_url(container, blob)

        service = 'blob'
    elif share:
        client = file_data_service_factory(cmd.cli_ctx, kwargs)
        dir_name, file_name = os.path.split(file_path) if file_path else (None, '')
        dir_name = None if dir_name in ('', '.') else dir_name
        url = client.make_file_url(share, dir_name, file_name)
        service = 'file'
    elif not any([url, container, share]):  # In account level, only blob service is supported
        service = 'blob'
        url = 'https://{}.{}.{}'.format(namespace.account_name, service, storage_endpoint)

    return service, url


def _is_valid_uri(uri):
    if not uri:
        return False
    if os.path.isdir(os.path.dirname(uri)) or os.path.isdir(uri):
        return uri
    if "?" in uri:  # sas token exists
        logger.debug("Find ? in %s. ", uri)
        return uri
    return False


def _add_sas_for_url(cmd, url, account_name, account_key, sas_token, service, resource_types, permissions):
    from azure.cli.command_modules.storage.azcopy.util import _generate_sas_token

    if sas_token:
        sas_token = sas_token.lstrip('?')
    else:
        try:
            sas_token = _generate_sas_token(cmd, account_name, account_key, service,
                                            resource_types=resource_types, permissions=permissions)
        except Exception as ex:  # pylint: disable=broad-except
            logger.info("Cannot generate sas token. %s", ex)
            sas_token = None
    if sas_token:
        return'{}?{}'.format(url, sas_token)
    return url


def validate_azcopy_credential(cmd, namespace):
    # Get destination uri
    if not _is_valid_uri(namespace.destination):
        namespace.url = namespace.destination
        service, namespace.destination = get_url_with_sas(
            cmd, namespace, url=namespace.destination,
            container=namespace.destination_container, blob=namespace.destination_blob,
            share=namespace.destination_share, file_path=namespace.destination_file_path)
        namespace.destination = _add_sas_for_url(cmd, url=namespace.destination, account_name=namespace.account_name,
                                                 account_key=namespace.account_key, sas_token=namespace.sas_token,
                                                 service=service, resource_types='co', permissions='wac')

    if not _is_valid_uri(namespace.source):
        # determine if source account is same with destination
        if not namespace.source_account_key and not namespace.source_sas and not namespace.source_connection_string:
            if namespace.source_account_name == namespace.account_name:
                namespace.source_account_key = namespace.account_key
                namespace.source_sas = namespace.sas_token
                namespace.source_connection_string = namespace.connection_string
        namespace.account_name = namespace.source_account_name
        namespace.account_key = namespace.source_account_key
        namespace.sas_token = namespace.source_sas
        namespace.connection_string = namespace.source_connection_string

        # Get source uri
        namespace.url = namespace.source
        service, namespace.source = get_url_with_sas(
            cmd, namespace, url=namespace.source,
            container=namespace.source_container, blob=namespace.source_blob,
            share=namespace.source_share, file_path=namespace.source_file_path)
        namespace.source = _add_sas_for_url(cmd, url=namespace.source, account_name=namespace.account_name,
                                            account_key=namespace.account_key, sas_token=namespace.sas_token,
                                            service=service, resource_types='sco', permissions='rl')


def is_directory(props):
    return 'hdi_isfolder' in props.metadata.keys() and props.metadata['hdi_isfolder'] == 'true'


def validate_fs_directory_upload_destination_url(cmd, namespace):
    kwargs = {'account_name': namespace.account_name,
              'account_key': namespace.account_key,
              'connection_string': namespace.connection_string,
              'sas_token': namespace.sas_token,
              'file_system_name': namespace.destination_fs}
    client = cf_adls_file_system(cmd.cli_ctx, kwargs)
    url = client.url
    if namespace.destination_path:
        from azure.core.exceptions import AzureError
        from azure.cli.core.azclierror import InvalidArgumentValueError
        file_client = client.get_file_client(file_path=namespace.destination_path)
        try:
            props = file_client.get_file_properties()
            if not is_directory(props):
                raise InvalidArgumentValueError('usage error: You are specifying --destination-path with a file name, '
                                                'not directory name. Please change to a valid directory name. '
                                                'If you want to upload to a file, please use '
                                                '`az storage fs file upload` command.')
        except AzureError:
            pass
        url = file_client.url

    if _is_valid_uri(url):
        namespace.destination = url
    else:
        namespace.destination = _add_sas_for_url(cmd, url=url, account_name=namespace.account_name,
                                                 account_key=namespace.account_key, sas_token=namespace.sas_token,
                                                 service='blob', resource_types='co', permissions='rwdlac')
    del namespace.destination_fs
    del namespace.destination_path


def validate_fs_directory_download_source_url(cmd, namespace):
    kwargs = {'account_name': namespace.account_name,
              'account_key': namespace.account_key,
              'connection_string': namespace.connection_string,
              'sas_token': namespace.sas_token,
              'file_system_name': namespace.source_fs}
    client = cf_adls_file_system(cmd.cli_ctx, kwargs)
    url = client.url
    if namespace.source_path:
        file_client = client.get_file_client(file_path=namespace.source_path)
        url = file_client.url
    if _is_valid_uri(url):
        namespace.source = url
    else:
        namespace.source = _add_sas_for_url(cmd, url=url, account_name=namespace.account_name,
                                            account_key=namespace.account_key, sas_token=namespace.sas_token,
                                            service='blob', resource_types='co', permissions='rl')
    del namespace.source_fs
    del namespace.source_path


def validate_text_configuration(cmd, ns):
    DelimitedTextDialect = cmd.get_models('_models#DelimitedTextDialect', resource_type=ResourceType.DATA_STORAGE_BLOB)
    DelimitedJsonDialect = cmd.get_models('_models#DelimitedJsonDialect', resource_type=ResourceType.DATA_STORAGE_BLOB)
    if ns.input_format == 'csv':
        ns.input_config = DelimitedTextDialect(
            delimiter=ns.in_column_separator,
            quotechar=ns.in_quote_char,
            lineterminator=ns.in_record_separator,
            escapechar=ns.in_escape_char,
            has_header=ns.in_has_header)
    if ns.input_format == 'json':
        ns.input_config = DelimitedJsonDialect(delimiter=ns.in_line_separator)

    if ns.output_format == 'csv':
        ns.output_config = DelimitedTextDialect(
            delimiter=ns.out_column_separator,
            quotechar=ns.out_quote_char,
            lineterminator=ns.out_record_separator,
            escapechar=ns.out_escape_char,
            has_header=ns.out_has_header)
    if ns.output_format == 'json':
        ns.output_config = DelimitedJsonDialect(delimiter=ns.out_line_separator)
    del ns.input_format, ns.in_line_separator, ns.in_column_separator, ns.in_quote_char, ns.in_record_separator, \
        ns.in_escape_char, ns.in_has_header
    del ns.output_format, ns.out_line_separator, ns.out_column_separator, ns.out_quote_char, ns.out_record_separator, \
        ns.out_escape_char, ns.out_has_header


def add_acl_progress_hook(namespace):
    if namespace.progress_hook:
        return

    failed_entries = []

    # the progress callback is invoked each time a batch is completed
    def progress_callback(acl_changes):
        # keep track of failed entries if there are any
        print(acl_changes.batch_failures)
        failed_entries.append(acl_changes.batch_failures)

    namespace.progress_hook = progress_callback


def get_not_none_validator(attribute_name):
    def validate_not_none(cmd, namespace):
        attribute = getattr(namespace, attribute_name, None)
        options_list = cmd.arguments[attribute_name].type.settings.get('options_list')
        if attribute in (None, ''):
            from azure.cli.core.azclierror import InvalidArgumentValueError
            raise InvalidArgumentValueError('Argument {} should be specified'.format('/'.join(options_list)))
    return validate_not_none


def validate_policy(namespace):
    if namespace.id is not None:
        logger.warning("\nPlease do not specify --expiry and --permissions if they are already specified in your "
                       "policy.")


def validate_immutability_arguments(namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    if not namespace.enable_alw:
        if any([namespace.immutability_period_since_creation_in_days,
                namespace.immutability_policy_state, namespace.allow_protected_append_writes is not None]):
            raise InvalidArgumentValueError("Incorrect usage: To enable account level immutability, "
                                            "need to specify --enable-alw true. "
                                            "Cannot set --enable_alw to false and specify "
                                            "--immutability-period --immutability-state "
                                            "--allow-append")


def validate_allow_protected_append_writes_all(namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    if namespace.allow_protected_append_writes_all and namespace.allow_protected_append_writes:
        raise InvalidArgumentValueError("usage error: The 'allow-protected-append-writes' "
                                        "and 'allow-protected-append-writes-all' "
                                        "properties are mutually exclusive. 'allow-protected-append-writes-all' allows "
                                        "new blocks to be written to both Append and Block Blobs, while "
                                        "'allow-protected-append-writes' allows new blocks to be written to "
                                        "Append Blobs only.")


def validate_blob_name_for_upload(namespace):
    if not namespace.blob_name:
        namespace.blob_name = os.path.basename(namespace.file_path)


def validate_share_close_handle(namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    if namespace.close_all and namespace.handle_id:
        raise InvalidArgumentValueError("usage error: Please only specify either --handle-id or --close-all, not both.")
    if not namespace.close_all and not namespace.handle_id:
        raise InvalidArgumentValueError("usage error: Please specify either --handle-id or --close-all.")


def validate_upload_blob(namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    if namespace.file_path and namespace.data:
        raise InvalidArgumentValueError("usage error: please only specify one of --file and --data to upload.")
    if not namespace.file_path and not namespace.data:
        raise InvalidArgumentValueError("usage error: please specify one of --file and --data to upload.")


def add_upload_progress_callback(cmd, namespace):
    def _update_progress(response):
        if response.http_response.status_code not in [200, 201]:
            return

        message = getattr(_update_progress, 'message', 'Alive')
        reuse = getattr(_update_progress, 'reuse', False)
        current = response.context['upload_stream_current']
        total = response.context['data_stream_total']

        if total:
            hook.add(message=message, value=current, total_val=total)
            if total == current and not reuse:
                hook.end()

    hook = cmd.cli_ctx.get_progress_controller(det=True)
    _update_progress.hook = hook

    if not namespace.no_progress:
        namespace.progress_callback = _update_progress
    del namespace.no_progress


def add_download_progress_callback(cmd, namespace):
    def _update_progress(response):
        if response.http_response.status_code not in [200, 201, 206]:
            return

        message = getattr(_update_progress, 'message', 'Alive')
        reuse = getattr(_update_progress, 'reuse', False)
        current = response.context['download_stream_current']
        total = response.context['data_stream_total']

        if total:
            hook.add(message=message, value=current, total_val=total)
            if total == current and not reuse:
                hook.end()

    hook = cmd.cli_ctx.get_progress_controller(det=True)
    _update_progress.hook = hook

    if not namespace.no_progress:
        namespace.progress_callback = _update_progress
    del namespace.no_progress


def validate_blob_arguments(namespace):
    from azure.cli.core.azclierror import RequiredArgumentMissingError
    if not namespace.blob_url and not all([namespace.blob_name, namespace.container_name]):
        raise RequiredArgumentMissingError(
            "Please specify --blob-url or combination of blob name, container name and storage account arguments.")
