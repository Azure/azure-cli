# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods

"""Constants in the Azure Configuration service.
"""


class HttpMethods:
    """Constants of http methods.
    """
    Head = 'HEAD'
    Get = 'GET'
    Put = 'PUT'
    Delete = 'DELETE'


class HttpHeaders:
    """Constants of http headers.
    """
    Accept = 'Accept'
    AcceptDateTime = 'Accept-Datetime'
    ClientRequestId = 'x-ms-client-request-id'
    CorrelationRequestId = 'x-ms-correlation-request-id'
    ContentType = 'Content-Type'
    IfMatch = 'If-Match'
    IfNoneMatch = 'If-None-Match'
    Link = 'link'
    UserAgent = 'User-Agent'
    RetryAfter = 'Retry-After'
    RetryAfterMs = 'retry-after-ms'


class HttpHeaderValues:
    MediaTypeApplication = 'application/json;'
    MediaTypeKeyValueApplication = "application/vnd.microsoft.appconfig.kv+json;"


class HttpResponseContent:
    Detail = 'detail'
    Title = 'title'


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


class Versions:
    """Constants of versions.
    """
    SDKVersion = '2.0.0'
    ApiVersion = '1.0'


class Validator:
    """Constants used in validator
    """
    MIN_POLL_INTERVAL = 0.5
