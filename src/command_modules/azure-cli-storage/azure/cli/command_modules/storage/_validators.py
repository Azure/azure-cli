# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import validate_key_value_pairs
from azure.cli.core.profiles import ResourceType, get_sdk

from azure.cli.command_modules.storage._client_factory import get_storage_data_service_client
from azure.cli.command_modules.storage.util import glob_files_locally, guess_content_type
from azure.cli.command_modules.storage.sdkutil import get_table_data_type
from azure.cli.command_modules.storage.url_quote_util import encode_for_url

storage_account_key_options = {'primary': 'key1', 'secondary': 'key2'}


# Utilities


# pylint: disable=inconsistent-return-statements
def _query_account_key(cli_ctx, account_name):
    """Query the storage account key. This is used when the customer doesn't offer account key but name."""
    scf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)
    acc = next((x for x in scf.storage_accounts.list() if x.name == account_name), None)
    if acc:
        from msrestazure.tools import parse_resource_id
        rg = parse_resource_id(acc.id)['resource_group']

        t_storage_account_keys, t_storage_account_list_keys_results = get_sdk(
            cli_ctx,
            ResourceType.MGMT_STORAGE,
            'models.storage_account_keys#StorageAccountKeys',
            'models.storage_account_list_keys_result#StorageAccountListKeysResult')

        if t_storage_account_keys:
            return scf.storage_accounts.list_keys(rg, account_name).key1
        elif t_storage_account_list_keys_results:
            return scf.storage_accounts.list_keys(rg, account_name).keys[0].value  # pylint: disable=no-member
    else:
        raise ValueError("Storage account '{}' not found.".format(account_name))


# region PARAMETER VALIDATORS

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


def validate_client_parameters(cmd, namespace):
    """ Retrieves storage connection parameters from environment variables and parses out connection string into
    account name and key """
    n = namespace

    def get_config_value(section, key, default):
        return cmd.cli_ctx.config.get(section, key, default)

    if not n.connection_string:
        n.connection_string = get_config_value('storage', 'connection_string', None)

    # if connection string supplied or in environment variables, extract account key and name
    if n.connection_string:
        conn_dict = validate_key_value_pairs(n.connection_string)
        n.account_name = conn_dict.get('AccountName')
        n.account_key = conn_dict.get('AccountKey')
        if not n.account_name or not n.account_key:
            from knack.util import CLIError
            raise CLIError('Connection-string: %s, is malformed. Some shell environments require the '
                           'connection string to be surrounded by quotes.' % n.connection_string)

    # otherwise, simply try to retrieve the remaining variables from environment variables
    if not n.account_name:
        n.account_name = get_config_value('storage', 'account', None)
    if not n.account_key:
        n.account_key = get_config_value('storage', 'key', None)
    if not n.sas_token:
        n.sas_token = get_config_value('storage', 'sas_token', None)

    # strip the '?' from sas token. the portal and command line are returns sas token in different
    # forms
    if n.sas_token:
        n.sas_token = n.sas_token.lstrip('?')

    # if account name is specified but no key, attempt to query
    if n.account_name and not n.account_key and not n.sas_token:
        n.account_key = _query_account_key(cmd.cli_ctx, n.account_name)


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
        else:
            # simplest scenario--no further processing necessary
            return

    validate_client_parameters(cmd, namespace)  # must run first to resolve storage account

    # determine if the copy will happen in the same storage account
    if not source_account_name and source_account_key:
        raise ValueError(usage_string.format('Source account key is given but account name is not'))
    elif not source_account_name and not source_account_key:
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
        '\n\t   --source-uri' \
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

    # source credential clues
    source_account_name = ns.pop('source_account_name', None)
    source_account_key = ns.pop('source_account_key', None)
    source_sas = ns.pop('source_sas', None)

    # source in the form of an uri
    uri = ns.get('copy_source', None)
    if uri:
        if any([container, blob, source_sas, snapshot, share, path, source_account_name,
                source_account_key]):
            raise ValueError(usage_string.format('Unused parameters are given in addition to the '
                                                 'source URI'))
        else:
            # simplest scenario--no further processing necessary
            return

    # ensure either a file or blob source is specified
    valid_blob_source = container and blob and not share and not path
    valid_file_source = share and path and not container and not blob and not snapshot

    if not valid_blob_source and not valid_file_source:
        raise ValueError(usage_string.format('Neither a valid blob or file source is specified'))
    elif valid_blob_source and valid_file_source:
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
            import os
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

    uri = 'https://{0}.{1}.{6}/{2}/{3}{4}{5}'.format(
        source_account_name,
        'blob' if valid_blob_source else 'file',
        container if valid_blob_source else share,
        encode_for_url(blob if valid_blob_source else path),
        '?' if query_params else '',
        '&'.join(query_params),
        cmd.cli_ctx.cloud.suffixes.storage_endpoint)

    namespace.copy_source = uri


def validate_blob_type(namespace):
    if not namespace.blob_type:
        namespace.blob_type = 'page' if namespace.file_path.endswith('.vhd') else 'block'


def get_content_setting_validator(settings_class, update, guess_from_file=None):
    def _class_name(class_type):
        return class_type.__module__ + "." + class_type.__class__.__name__

    def validator(cmd, namespace):
        t_base_blob_service, t_file_service, t_blob_content_settings, t_file_content_settings = cmd.get_models(
            'blob.baseblobservice#BaseBlobService',
            'file#FileService',
            'blob.models#ContentSettings',
            'file.models#ContentSettings')

        # must run certain validators first for an update
        if update:
            validate_client_parameters(cmd, namespace)
        if update and _class_name(settings_class) == _class_name(t_file_content_settings):
            get_file_path_validator()(namespace)
        ns = vars(namespace)

        # retrieve the existing object properties for an update
        if update:
            account = ns.get('account_name')
            key = ns.get('account_key')
            cs = ns.get('connection_string')
            sas = ns.get('sas_token')
            if _class_name(settings_class) == _class_name(t_blob_content_settings):
                client = get_storage_data_service_client(cmd.cli_ctx,
                                                         t_base_blob_service,
                                                         account,
                                                         key,
                                                         cs,
                                                         sas)
                container = ns.get('container_name')
                blob = ns.get('blob_name')
                lease_id = ns.get('lease_id')
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
            new_props.content_type = new_props.content_type or props.content_type
            new_props.content_disposition = new_props.content_disposition or props.content_disposition
            new_props.content_encoding = new_props.content_encoding or props.content_encoding
            new_props.content_language = new_props.content_language or props.content_language
            new_props.content_md5 = new_props.content_md5 or props.content_md5
            new_props.cache_control = new_props.cache_control or props.cache_control
        else:
            if guess_from_file:
                new_props = guess_content_type(ns[guess_from_file], new_props, settings_class)

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


def validate_encryption_source(cmd, namespace):
    ns = vars(namespace)

    key_name = ns.pop('encryption_key_name', None)
    key_version = ns.pop('encryption_key_version', None)
    key_vault_uri = ns.pop('encryption_key_vault', None)

    if namespace.encryption_key_source == 'Microsoft.Keyvault' and not (key_name and key_version and key_vault_uri):
        raise ValueError('--encryption-key-name, --encryption-key-vault, and --encryption-key-version are required '
                         'when --encryption-key-source=Microsoft.Keyvault is specified.')

    if key_name or key_version or key_vault_uri:
        if namespace.encryption_key_source != 'Microsoft.Keyvault':
            raise ValueError('--encryption-key-name, --encryption-key-vault, and --encryption-key-version are not '
                             'applicable when --encryption-key-source=Microsoft.Keyvault is not specified.')
        KeyVaultProperties = get_sdk(cmd.cli_ctx, ResourceType.MGMT_STORAGE, 'KeyVaultProperties',
                                     mod='models')
        if not KeyVaultProperties:
            return

        kv_prop = KeyVaultProperties(key_name=key_name, key_version=key_version, key_vault_uri=key_vault_uri)
        namespace.encryption_key_vault_properties = kv_prop


def validate_entity(namespace):
    """ Converts a list of key value pairs into a dictionary. Ensures that required
    RowKey and PartitionKey are converted to the correct case and included. """
    values = dict(x.split('=', 1) for x in namespace.entity)
    keys = values.keys()
    for key in keys:
        if key.lower() == 'rowkey':
            val = values[key]
            del values[key]
            values['RowKey'] = val
        elif key.lower() == 'partitionkey':
            val = values[key]
            del values[key]
            values['PartitionKey'] = val
    keys = values.keys()
    missing_keys = 'RowKey ' if 'RowKey' not in keys else ''
    missing_keys = '{}PartitionKey'.format(missing_keys) \
        if 'PartitionKey' not in keys else missing_keys
    if missing_keys:
        import argparse
        raise argparse.ArgumentError(
            None, 'incorrect usage: entity requires: {}'.format(missing_keys))

    def cast_val(key, val):
        """ Attempts to cast numeric values (except RowKey and PartitionKey) to numbers so they
        can be queried correctly. """
        if key in ['PartitionKey', 'RowKey']:
            return val

        def try_cast(to_type):
            try:
                return to_type(val)
            except ValueError:
                return None

        return try_cast(int) or try_cast(float) or val

    # ensure numbers are converted from strings so querying will work correctly
    values = {key: cast_val(key, val) for key, val in values.items()}
    namespace.entity = values


def validate_marker(namespace):
    """ Converts a list of key value pairs into a dictionary. Ensures that required
    nextrowkey and nextpartitionkey are included. """
    if not namespace.marker:
        return
    marker = dict(x.split('=', 1) for x in namespace.marker)
    expected_keys = {'nextrowkey', 'nextpartitionkey'}

    for key in marker:
        new_key = key.lower()
        if new_key in expected_keys:
            expected_keys.remove(key.lower())
            val = marker[key]
            del marker[key]
            marker[new_key] = val
    if expected_keys:
        import argparse
        raise argparse.ArgumentError(
            None, 'incorrect usage: marker requires: {}'.format(' '.join(expected_keys)))

    namespace.marker = marker


def get_file_path_validator(default_file_param=None):
    """ Creates a namespace validator that splits out 'path' into 'directory_name' and 'file_name'.
    Allows another path-type parameter to be named which can supply a default filename. """

    def validator(namespace):
        import os
        if not hasattr(namespace, 'path'):
            return

        path = namespace.path
        dir_name, file_name = os.path.split(path) if path else (None, '')

        if default_file_param and '.' not in file_name:
            dir_name = path
            file_name = os.path.split(getattr(namespace, default_file_param))[1]
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


def validate_key(namespace):
    namespace.key_name = storage_account_key_options[namespace.key_name]


def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)


def get_permission_help_string(permission_class):
    allowed_values = [x.lower() for x in dir(permission_class) if not x.startswith('__')]
    return ' '.join(['({}){}'.format(x[0], x[1:]) for x in allowed_values])


def get_permission_validator(permission_class):
    allowed_values = [x.lower() for x in dir(permission_class) if not x.startswith('__')]
    allowed_string = ''.join(x[0] for x in allowed_values)

    def validator(namespace):
        if namespace.permission:
            if set(namespace.permission) - set(allowed_string):
                help_string = get_permission_help_string(permission_class)
                raise ValueError(
                    'valid values are {} or a combination thereof.'.format(help_string))
            namespace.permission = permission_class(_str=namespace.permission)

    return validator


def table_permission_validator(cmd, namespace):
    """ A special case for table because the SDK associates the QUERY permission with 'r' """
    t_table_permissions = get_table_data_type(cmd.cli_ctx, 'table', 'TablePermissions')
    if namespace.permission:
        if set(namespace.permission) - set('raud'):
            help_string = '(r)ead/query (a)dd (u)pdate (d)elete'
            raise ValueError('valid values are {} or a combination thereof.'.format(help_string))
        namespace.permission = t_table_permissions(_str=namespace.permission)


def validate_container_public_access(cmd, namespace):
    from .sdkutil import get_container_access_type
    t_base_blob_svc = cmd.get_models('blob.baseblobservice#BaseBlobService')

    if namespace.public_access:
        namespace.public_access = get_container_access_type(cmd.cli_ctx, namespace.public_access.lower())

        if hasattr(namespace, 'signed_identifiers'):
            # must retrieve the existing ACL to simulate a patch operation because these calls
            # are needlessly conflated
            ns = vars(namespace)
            validate_client_parameters(cmd, namespace)
            account = ns.get('account_name')
            key = ns.get('account_key')
            cs = ns.get('connection_string')
            sas = ns.get('sas_token')
            client = get_storage_data_service_client(cmd.cli_ctx, t_base_blob_svc, account, key, cs, sas)
            container = ns.get('container_name')
            lease_id = ns.get('lease_id')
            ns['signed_identifiers'] = client.get_container_acl(container, lease_id=lease_id)


def validate_select(namespace):
    if namespace.select:
        namespace.select = ','.join(namespace.select)


def get_source_file_or_blob_service_client(cmd, namespace):
    """
    Create the second file service or blob service client for batch copy command, which is used to
    list the source files or blobs. If both the source account and source URI are omitted, it
    indicates that user want to copy files or blobs in the same storage account, therefore the
    destination client will be set None hence the command will use destination client.
    """
    t_file_svc, t_block_blob_svc = cmd.get_models('file#FileService', 'blob.blockblobservice#BlockBlobService')
    usage_string = 'invalid usage: supply only one of the following argument sets:' + \
                   '\n\t   --source-uri' + \
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

    elif (not source_account) and (not source_uri):
        # Set the source_client to None if neither source_account or source_uri is given. This
        # indicates the command that the source files share or blob container is in the same storage
        # account as the destination file share.
        #
        # The command itself should create the source service client since the validator can't
        # access the destination client through the namespace.
        #
        # A few arguments check will be made as well so as not to cause ambiguity.

        if source_key:
            raise ValueError('invalid usage: --source-account-key is set but --source-account-name'
                             ' is missing.')

        if source_container and source_share:
            raise ValueError(usage_string)

        if not source_container and not source_share:
            raise ValueError(usage_string)

        ns['source_client'] = None

    elif source_account:
        if source_container and source_share:
            raise ValueError(usage_string)

        if not (source_key or source_sas):
            # when either storage account key or SAS is given, try to fetch the key in the current
            # subscription
            source_key = _query_account_key(cmd.cli_ctx, source_account)

        if source_container:
            ns['source_client'] = get_storage_data_service_client(cmd.cli_ctx,
                                                                  t_block_blob_svc,
                                                                  name=source_account,
                                                                  key=source_key,
                                                                  sas_token=source_sas)
        elif source_share:
            ns['source_client'] = get_storage_data_service_client(cmd.cli_ctx,
                                                                  t_file_svc,
                                                                  name=source_account,
                                                                  key=source_key,
                                                                  sas_token=source_sas)
        else:
            raise ValueError(usage_string)

    elif source_uri:
        if source_sas or source_key or source_container or source_share:
            raise ValueError(usage_string)

        from .storage_url_helpers import StorageResourceIdentifier
        identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, source_uri)
        nor_container_or_share = not identifier.container and not identifier.share
        if not identifier.is_url():
            raise ValueError('incorrect usage: --source-uri expects a URI')
        elif identifier.blob or identifier.directory or \
                identifier.filename or nor_container_or_share:
            raise ValueError('incorrect usage: --source-uri has to be blob container or file share')
        elif identifier.container:
            ns['source_container'] = identifier.container
            if identifier.account_name != ns.get('account_name'):
                ns['source_client'] = get_storage_data_service_client(cmd.cli_ctx, t_block_blob_svc,
                                                                      name=identifier.account_name,
                                                                      sas_token=identifier.sas_token)
        elif identifier.share:
            ns['source_share'] = identifier.share
            if identifier.account_name != ns.get('account_name'):
                ns['source_client'] = get_storage_data_service_client(cmd.cli_ctx,
                                                                      t_file_svc,
                                                                      name=identifier.account_name,
                                                                      sas_token=identifier.sas_token)


def add_progress_callback(cmd, namespace):
    def _update_progress(current, total):
        hook = cmd.cli_ctx.get_progress_controller(det=True)

        if total:
            hook.add(message='Alive', value=current, total_val=total)
            if total == current:
                hook.end()

    if not namespace.no_progress:
        namespace.progress_callback = _update_progress
    del namespace.no_progress


def process_blob_download_batch_parameters(namespace, cmd):
    """Process the parameters for storage blob download command"""
    import os

    # 1. quick check
    if not os.path.exists(namespace.destination) or not os.path.isdir(namespace.destination):
        raise ValueError('incorrect usage: destination must be an existing directory')

    # 2. try to extract account name and container name from source string
    process_blob_batch_source_parameters(cmd, namespace)


def process_blob_batch_source_parameters(cmd, namespace):
    """Process the parameters for storage blob download command"""

    # try to extract account name and container name from source string
    from .storage_url_helpers import StorageResourceIdentifier
    identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, namespace.source)

    if not identifier.is_url():
        namespace.source_container_name = namespace.source
    elif identifier.blob:
        raise ValueError('incorrect usage: source should be either container URL or name')
    else:
        namespace.source_container_name = identifier.container
        if namespace.account_name is None:
            namespace.account_name = identifier.account_name


def process_blob_upload_batch_parameters(cmd, namespace):
    """Process the source and destination of storage blob upload command"""
    import os

    # 1. quick check
    if not os.path.exists(namespace.source):
        raise ValueError('incorrect usage: source {} does not exist'.format(namespace.source))

    if not os.path.isdir(namespace.source):
        raise ValueError('incorrect usage: source must be a directory')

    # 2. try to extract account name and container name from destination string
    from .storage_url_helpers import StorageResourceIdentifier
    identifier = StorageResourceIdentifier(cmd.cli_ctx.cloud, namespace.destination)

    if not identifier.is_url():
        namespace.destination_container_name = namespace.destination
    elif identifier.blob is not None:
        raise ValueError('incorrect usage: destination cannot be a blob url')
    else:
        namespace.destination_container_name = identifier.container

        if namespace.account_name:
            if namespace.account_name != identifier.account_name:
                raise ValueError(
                    'The given storage account name is not consistent with the account name in the destination URI')
        else:
            namespace.account_name = identifier.account_name

        if not (namespace.account_key or namespace.sas_token or namespace.connection_string):
            validate_client_parameters(cmd, namespace)

        # it is possible the account name be overwritten by the connection string
        if namespace.account_name != identifier.account_name:
            raise ValueError(
                'The given storage account name is not consistent with the account name in the destination URI')

        if not (namespace.account_key or namespace.sas_token or namespace.connection_string):
            raise ValueError('Missing storage account credential information.')

    # 3. collect the files to be uploaded
    namespace.source = os.path.realpath(namespace.source)
    namespace.source_files = [c for c in glob_files_locally(namespace.source, namespace.pattern)]

    # 4. determine blob type
    if namespace.blob_type is None:
        vhd_files = [f for f in namespace.source_files if f[0].endswith('.vhd')]
        if any(vhd_files) and len(vhd_files) == len(namespace.source_files):
            # when all the listed files are vhd files use page
            namespace.blob_type = 'page'
        elif any(vhd_files):
            # source files contain vhd files but not all of them
            from knack.util import CLIError
            raise CLIError("""Fail to guess the required blob type. Type of the files to be
            uploaded are not consistent. Default blob type for .vhd files is "page", while
            others are "block". You can solve this problem by either explicitly set the blob
            type or ensure the pattern matches a correct set of files.""")
        else:
            namespace.blob_type = 'block'


def process_blob_copy_batch_namespace(namespace):
    if namespace.prefix is None and not namespace.recursive:
        raise ValueError('incorrect usage: --recursive | --pattern PATTERN')


def process_file_upload_batch_parameters(cmd, namespace):
    """Process the parameters of storage file batch upload command"""
    import os

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
    import os

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
    import os

    get_file_path_validator()(namespace)

    dest = namespace.file_path
    if not dest or os.path.isdir(dest):
        namespace.file_path = os.path.join(dest, namespace.file_name) \
            if dest else namespace.file_name


def process_metric_update_namespace(namespace):
    import argparse
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
    elif subnet and not subnet_is_id and vnet:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        from knack.util import CLIError
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


def ipv4_range_type(string):
    """ Validates an IPv4 address or address range. """
    import re
    ip_format = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    if not re.match("^{}$".format(ip_format), string):
        if not re.match("^{}-{}$".format(ip_format, ip_format), string):
            raise ValueError
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


def services_type(loader):
    """ Returns a function which validates that services string contains only a combination of blob, queue, table,
    and file. Their shorthand representations are b, q, t, and f. """

    def impl(string):
        t_services = loader.get_models('common.models#Services')
        if set(string) - set("bqtf"):
            raise ValueError
        return t_services(_str=''.join(set(string)))

    return impl


def get_char_options_validator(types, property_name):
    def _validator(namespace):
        service_types = set(getattr(namespace, property_name, list()))

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
        namespace.tier = getattr(cmd.get_models('blob.models#StandardBlobTier'), namespace.tier)
    except AttributeError:
        from azure.cli.command_modules.storage.sdkutil import get_blob_tier_names
        raise ValueError('Unknown block blob tier name. Choose among {}'.format(', '.join(
            get_blob_tier_names(cmd.cli_ctx, 'StandardBlobTier'))))


def blob_tier_validator(cmd, namespace):
    if namespace.blob_type == 'page':
        page_blob_tier_validator(cmd, namespace)
    elif namespace.blob_type == 'block':
        block_blob_tier_validator(cmd, namespace)
    else:
        raise ValueError('Blob tier is only applicable to block or page blob.')
