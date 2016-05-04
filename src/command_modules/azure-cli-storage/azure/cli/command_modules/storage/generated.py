command_table = CommandTable()

# FACTORIES

def _storage_client_factory(_):
    return get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

def _file_data_service_factory(args):
    return get_data_service_client(
        FileService,
        args.pop('account_name', None),
        args.pop('account_key', None),
        connection_string=args.pop('connection_string', None),
        sas_token=args.pop('sas_token', None))

def _blob_data_service_factory(args):
    blob_type = args.get('type')
    blob_service = blob_types.get(blob_type, BlockBlobService)
    return get_data_service_client(
        blob_service,
        args.pop('account_name', None),
        args.pop('account_key', None),
        connection_string=args.pop('connection_string', None),
        sas_token=args.pop('sas_token', None))

def _cloud_storage_account_service_factory(args):
    account_name = args.pop('account_name', None)
    account_key = args.pop('account_key', None)
    sas_token = args.pop('sas_token', None)
    connection_string = args.pop('connection_string', None)
    if connection_string:
        # CloudStorageAccount doesn't accept connection string directly, so we must parse
        # out the account name and key manually
        conn_dict = validate_key_value_pairs(connection_string)
        account_name = conn_dict['AccountName']
        account_key = conn_dict['AccountKey']
    return CloudStorageAccount(account_name, account_key, sas_token)

# STORAGE ACCOUNT COMMANDS

build_operation(
    'storage account', 'storage_accounts', _storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.check_name_availability,
                              'Result', 'check-name'),
        AutoCommandDefinition(StorageAccountsOperations.delete, None),
        AutoCommandDefinition(StorageAccountsOperations.get_properties, 'StorageAccount', 'show')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'storage account', None, _cloud_storage_account_service_factory,
    [
        AutoCommandDefinition(CloudStorageAccount.generate_shared_access_signature,
                              'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage account keys', 'storage_accounts', _storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.list_keys, '[StorageAccountKeys]', 'list')
    ], command_table, PARAMETER_ALIASES)

# BLOB SERVICE COMMANDS

build_operation(
    'storage container', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_containers, '[Container]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_container, 'Bool', 'delete'),
        AutoCommandDefinition(BlockBlobService.get_container_properties,
                              'ContainerProperties', 'show'),
        AutoCommandDefinition(BlockBlobService.create_container, 'Bool', 'create'),
        AutoCommandDefinition(BlockBlobService.generate_container_shared_access_signature,
                              'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container acl', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_acl, 'StoredAccessPolicy', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_acl, '[StoredAccessPolicy]', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container metadata', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_metadata, 'Properties', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_metadata, 'Metadata', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container lease', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_container_lease, 'LeaseID', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_container_lease, 'LeaseID', 'renew'),
        AutoCommandDefinition(BlockBlobService.release_container_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_container_lease, None, 'change'),
        AutoCommandDefinition(BlockBlobService.break_container_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_blobs, '[Blob]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_blob, None, 'delete'),
        AutoCommandDefinition(BlockBlobService.generate_blob_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(BlockBlobService.make_blob_url, 'URL', 'url'),
        AutoCommandDefinition(BlockBlobService.snapshot_blob, 'SnapshotProperties', 'snapshot'),
        AutoCommandDefinition(BlockBlobService.get_blob_properties, 'Properties', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_properties, 'Propeties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob service-properties', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_service_properties,
                              '[ServiceProperties]', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_service_properties,
                              'ServiceProperties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob metadata', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob lease', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_blob_lease, 'LeaseID', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_blob_lease, 'LeaseID', 'renew'),
        AutoCommandDefinition(BlockBlobService.release_blob_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_blob_lease, None, 'change'),
        AutoCommandDefinition(BlockBlobService.break_blob_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob copy', None, _blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.copy_blob, 'CopyOperationProperties', 'start'),
        AutoCommandDefinition(BlockBlobService.abort_copy_blob, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# FILE SERVICE COMMANDS

build_operation(
    'storage share', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.list_shares, '[Share]', 'list'),
        AutoCommandDefinition(FileService.list_directories_and_files,
                              '[ShareContents]', 'contents'),
        AutoCommandDefinition(FileService.create_share, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_share, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.generate_share_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(FileService.get_share_stats, 'ShareStats', 'stats'),
        AutoCommandDefinition(FileService.get_share_properties, 'Properties', 'show'),
        AutoCommandDefinition(FileService.set_share_properties, 'Properties', 'set')

    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_share_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_share_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share acl', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.set_share_acl, '[StoredAccessPolicy]', 'set'),
        AutoCommandDefinition(FileService.get_share_acl, 'StoredAccessPolicy', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.create_directory, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_directory, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.get_directory_properties, 'Properties', 'show')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_directory_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_directory_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.delete_file, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.resize_file, 'Result', 'resize'),
        AutoCommandDefinition(FileService.make_file_url, 'URL', 'url'),
        AutoCommandDefinition(FileService.generate_file_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(FileService.get_file_properties, 'Properties', 'show'),
        AutoCommandDefinition(FileService.set_file_properties, 'Properties', 'set')
    ], command_table, FILE_PARAM_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file metadata', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_file_metadata, 'Metadata', 'set')
    ], command_table, FILE_PARAM_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file service-properties', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_service_properties, 'ServiceProperties', 'show'),
        AutoCommandDefinition(FileService.set_file_service_properties, 'ServiceProperties', 'set')
    ], command_table, FILE_PARAM_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file copy', None, _file_data_service_factory,
    [
        AutoCommandDefinition(FileService.copy_file, 'CopyOperationPropeties', 'start'),
        AutoCommandDefinition(FileService.abort_copy_file, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)
