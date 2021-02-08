# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods

"""Reserved keywords in the AppConfiguration service.
"""


class FeatureFlagConstants:
    FEATURE_FLAG_PREFIX = ".appconfig.featureflag/"
    FEATURE_FLAG_CONTENT_TYPE = "application/vnd.microsoft.appconfig.ff+json;charset=utf-8"


class KeyVaultConstants:
    KEYVAULT_CONTENT_TYPE = "application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8"
    APPSVC_KEYVAULT_PREFIX = "@Microsoft.KeyVault"


class SearchFilterOptions:
    ANY_KEY = '*'
    ANY_LABEL = '*'
    EMPTY_LABEL = '\\0'


class StatusCodes:
    """HTTP status codes returned by the REST operations
    """
    # Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    PARTIAL_CONTENT = 206
    NOT_MODIFIED = 304

    # Client Error
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    PRECONDITION_FAILED = 412
    REQUEST_ENTITY_TOO_LARGE = 413
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    RETRY_WITH = 449

    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class HttpHeaders:
    from azure.cli.core import __version__ as core_version
    USER_AGENT = "AZURECLI.APPCONFIG/{0}".format(core_version)
