import functools
import logging
from unittest.mock import patch, MagicMock

import httpx
from vcr.request import Request as VcrRequest
from vcr.errors import CannotOverwriteExistingCassetteException


_logger = logging.getLogger(__name__)


def _transform_headers(httpx_reponse):
    """
    Some headers can appear multiple times, like "Set-Cookie".
    Therefore transform to every header key to list of values.
    """

    out = {}
    for key, var in httpx_reponse.headers.raw:
        decoded_key = key.decode("utf-8")
        out.setdefault(decoded_key, [])
        out[decoded_key].append(var.decode("utf-8"))
    return out


def _to_serialized_response(httpx_reponse):
    return {
        "status_code": httpx_reponse.status_code,
        "http_version": httpx_reponse.http_version,
        "headers": _transform_headers(httpx_reponse),
        "content": httpx_reponse.content.decode("utf-8", "ignore"),
    }


def _from_serialized_headers(headers):
    """
    httpx accepts headers as list of tuples of header key and value.
    """

    header_list = []
    for key, values in headers.items():
        for v in values:
            header_list.append((key, v))
    return header_list


@patch("httpx.Response.close", MagicMock())
@patch("httpx.Response.read", MagicMock())
def _from_serialized_response(request, serialized_response, history=None):
    content = serialized_response.get("content").encode()
    response = httpx.Response(
        status_code=serialized_response.get("status_code"),
        request=request,
        http_version=serialized_response.get("http_version"),
        headers=_from_serialized_headers(serialized_response.get("headers")),
        content=content,
        history=history or [],
    )
    response._content = content
    return response


def _make_vcr_request(httpx_request, **kwargs):
    body = httpx_request.read().decode("utf-8")
    uri = str(httpx_request.url)
    headers = dict(httpx_request.headers)
    return VcrRequest(httpx_request.method, uri, body, headers)


def _shared_vcr_send(cassette, real_send, *args, **kwargs):
    real_request = args[1]

    vcr_request = _make_vcr_request(real_request, **kwargs)

    if cassette.can_play_response_for(vcr_request):
        return vcr_request, _play_responses(cassette, real_request, vcr_request, args[0], kwargs)

    if cassette.write_protected and cassette.filter_request(vcr_request):
        raise CannotOverwriteExistingCassetteException(cassette=cassette, failed_request=vcr_request)

    _logger.info("%s not in cassette, sending to real server", vcr_request)
    return vcr_request, None


def _record_responses(cassette, vcr_request, real_response):
    for past_real_response in real_response.history:
        past_vcr_request = _make_vcr_request(past_real_response.request)
        cassette.append(past_vcr_request, _to_serialized_response(past_real_response))

    if real_response.history:
        # If there was a redirection keep we want the request which will hold the
        # final redirect value
        vcr_request = _make_vcr_request(real_response.request)

    cassette.append(vcr_request, _to_serialized_response(real_response))
    return real_response


def _play_responses(cassette, request, vcr_request, client, kwargs):
    history = []
    allow_redirects = kwargs.get("allow_redirects", True)
    vcr_response = cassette.play_response(vcr_request)
    response = _from_serialized_response(request, vcr_response)

    while allow_redirects and 300 <= response.status_code <= 399:
        next_url = response.headers.get("location")
        if not next_url:
            break

        vcr_request = VcrRequest("GET", next_url, None, dict(response.headers))
        vcr_request = cassette.find_requests_with_most_matches(vcr_request)[0][0]

        history.append(response)
        # add cookies from response to session cookie store
        client.cookies.extract_cookies(response)

        vcr_response = cassette.play_response(vcr_request)
        response = _from_serialized_response(vcr_request, vcr_response, history)

    return response


async def _async_vcr_send(cassette, real_send, *args, **kwargs):
    vcr_request, response = _shared_vcr_send(cassette, real_send, *args, **kwargs)
    if response:
        # add cookies from response to session cookie store
        args[0].cookies.extract_cookies(response)
        return response

    real_response = await real_send(*args, **kwargs)
    return _record_responses(cassette, vcr_request, real_response)


def async_vcr_send(cassette, real_send):
    @functools.wraps(real_send)
    def _inner_send(*args, **kwargs):
        return _async_vcr_send(cassette, real_send, *args, **kwargs)

    return _inner_send


def _sync_vcr_send(cassette, real_send, *args, **kwargs):
    vcr_request, response = _shared_vcr_send(cassette, real_send, *args, **kwargs)
    if response:
        # add cookies from response to session cookie store
        args[0].cookies.extract_cookies(response)
        return response

    real_response = real_send(*args, **kwargs)
    return _record_responses(cassette, vcr_request, real_response)


def sync_vcr_send(cassette, real_send):
    @functools.wraps(real_send)
    def _inner_send(*args, **kwargs):
        return _sync_vcr_send(cassette, real_send, *args, **kwargs)

    return _inner_send
