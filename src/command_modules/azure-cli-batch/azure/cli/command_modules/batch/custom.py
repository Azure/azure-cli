# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit # pylint: disable=import-error

from azure.mgmt.batch.models import (BatchAccountCreateParameters,
                                     AutoStorageBaseProperties,
                                     UpdateApplicationParameters)
from azure.mgmt.batch.operations import (ApplicationPackageOperations)
from azure.storage.blob import BlockBlobService

import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)

def list_accounts(client, resource_group_name=None):
    acct_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(acct_list)

def create_account(client, resource_group_name, account_name, location, #pylint:disable=too-many-arguments
                   tags=None, storage_account_id=None):
    # TODO: get storage_account_id by search storage account name
    if storage_account_id:
        properties = AutoStorageBaseProperties(storage_account_id=storage_account_id)
    else:
        properties = None

    parameters = BatchAccountCreateParameters(location=location,
                                              tags=tags,
                                              auto_storage=properties)

    return client.create(resource_group_name=resource_group_name,
                         account_name=account_name,
                         parameters=parameters)

create_account.__doc__ = AutoStorageBaseProperties.__doc__

def update_account(client, resource_group_name, account_name,  #pylint:disable=too-many-arguments
                   tags=None, storage_account_id=None):
    if storage_account_id:
        properties = AutoStorageBaseProperties(storage_account_id=storage_account_id)
    else:
        properties = None

    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         tags=tags,
                         auto_storage=properties)

update_account.__doc__ = AutoStorageBaseProperties.__doc__

def update_application(client, resource_group_name, account_name, application_id, #pylint:disable=too-many-arguments
                       allow_updates=None, display_name=None, default_version=None):
    parameters = UpdateApplicationParameters(allow_updates=allow_updates,
                                             display_name=display_name,
                                             default_version=default_version)
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         application_id=application_id,
                         parameters=parameters)

update_application.__doc__ = UpdateApplicationParameters.__doc__

def _upload_package_blob(package_file, url):
    """Upload the location file to storage url provided by autostorage"""

    uri = urlsplit(url)
    # in uri path, it always start with '/', so container name is at second block
    pathParts = uri.path.split('/', 2)
    container_name = pathParts[1]
    blob_name = pathParts[2]
    # we need handle the scenario storage account not in public Azure
    hostParts = uri.netloc.split('.', 2)
    account_name = hostParts[0]
    # endpoint suffix needs to ignore the 'blob' part in the host name
    endpoint_suffix = hostParts[2]

    sas_service = BlockBlobService(account_name=account_name,
                                   sas_token=uri.query,
                                   endpoint_suffix=endpoint_suffix)
    sas_service.create_blob_from_path(
        container_name=container_name,
        blob_name=blob_name,
        file_path=package_file,
    )

def create_application_package(client, resource_group_name, account_name, #pylint:disable=too-many-arguments
                               application_id, version, package_file):
    result = client.create(resource_group_name, account_name, application_id, version)
    logger.info('Uploading %s to storage blob %s...', package_file, result.storage_url)
    _upload_package_blob(package_file, result.storage_url)
    return result

create_application_package.__doc__ = ApplicationPackageOperations.create.__doc__
