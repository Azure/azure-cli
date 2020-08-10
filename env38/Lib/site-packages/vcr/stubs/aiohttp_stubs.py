"""Stubs for aiohttp HTTP clients"""
import asyncio
import functools
import logging
import json

from aiohttp import ClientConnectionError, ClientResponse, RequestInfo, streams
from aiohttp import hdrs, CookieJar
from http.cookies import CookieError, Morsel, SimpleCookie
from aiohttp.helpers import strip_auth_from_url
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from vcr.errors import CannotOverwriteExistingCassetteException
from vcr.request import Request

log = logging.getLogger(__name__)


class MockStream(asyncio.StreamReader, streams.AsyncStreamReaderMixin):
    pass


class MockClientResponse(ClientResponse):
    def __init__(self, method, url, request_info=None):
        super().__init__(
            method=method,
            url=url,
            writer=None,
            continue100=None,
            timer=None,
            request_info=request_info,
            traces=None,
            loop=asyncio.get_event_loop(),
            session=None,
        )

    async def json(self, *, encoding="utf-8", loads=json.loads, **kwargs):  # NOQA: E999
        stripped = self._body.strip()
        if not stripped:
            return None

        return loads(stripped.decode(encoding))

    async def text(self, encoding="utf-8", errors="strict"):
        return self._body.decode(encoding, errors=errors)

    async def read(self):
        return self._body

    def release(self):
        pass

    @property
    def content(self):
        s = MockStream()
        s.feed_data(self._body)
        s.feed_eof()
        return s


def build_response(vcr_request, vcr_response, history):
    request_info = RequestInfo(
        url=URL(vcr_request.url),
        method=vcr_request.method,
        headers=_deserialize_headers(vcr_request.headers),
        real_url=URL(vcr_request.url),
    )
    response = MockClientResponse(vcr_request.method, URL(vcr_response.get("url")), request_info=request_info)
    response.status = vcr_response["status"]["code"]
    response._body = vcr_response["body"].get("string", b"")
    response.reason = vcr_response["status"]["message"]
    response._headers = _deserialize_headers(vcr_response["headers"])
    response._history = tuple(history)
    # cookies
    for hdr in response.headers.getall(hdrs.SET_COOKIE, ()):
        try:
            cookies = SimpleCookie(hdr)
            for cookie_name, cookie in cookies.items():
                expires = cookie.get("expires", "").strip()
                if expires:
                    log.debug('Ignoring expiration date: %s="%s"', cookie_name, expires)
                cookie["expires"] = ""
                response.cookies.load(cookie.output(header="").strip())
        except CookieError as exc:
            log.warning("Can not load response cookies: %s", exc)

    response.close()
    return response


def _serialize_headers(headers):
    """Serialize CIMultiDictProxy to a pickle-able dict because proxy
        objects forbid pickling:

        https://github.com/aio-libs/multidict/issues/340
    """
    # Mark strings as keys so 'istr' types don't show up in
    # the cassettes as comments.
    serialized_headers = {}
    for k, v in headers.items():
        serialized_headers.setdefault(str(k), []).append(v)

    return serialized_headers


def _deserialize_headers(headers):
    deserialized_headers = CIMultiDict()
    for k, vs in headers.items():
        if isinstance(vs, list):
            for v in vs:
                deserialized_headers.add(k, v)
        else:
            deserialized_headers.add(k, vs)

    return CIMultiDictProxy(deserialized_headers)


def play_responses(cassette, vcr_request):
    history = []
    vcr_response = cassette.play_response(vcr_request)
    response = build_response(vcr_request, vcr_response, history)

    # If we're following redirects, continue playing until we reach
    # our final destination.
    while 300 <= response.status <= 399:
        if "location" not in response.headers:
            break

        next_url = URL(response.url).join(URL(response.headers["location"]))

        # Make a stub VCR request that we can then use to look up the recorded
        # VCR request saved to the cassette. This feels a little hacky and
        # may have edge cases based on the headers we're providing (e.g. if
        # there's a matcher that is used to filter by headers).
        vcr_request = Request("GET", str(next_url), None, _serialize_headers(response.request_info.headers))
        vcr_requests = cassette.find_requests_with_most_matches(vcr_request)
        for vcr_request, *_ in vcr_requests:
            if cassette.can_play_response_for(vcr_request):
                break

        # Tack on the response we saw from the redirect into the history
        # list that is added on to the final response.
        history.append(response)
        vcr_response = cassette.play_response(vcr_request)
        response = build_response(vcr_request, vcr_response, history)

    return response


async def record_response(cassette, vcr_request, response):
    """Record a VCR request-response chain to the cassette."""

    try:
        body = {"string": (await response.read())}
    # aiohttp raises a ClientConnectionError on reads when
    # there is no body. We can use this to know to not write one.
    except ClientConnectionError:
        body = {}

    vcr_response = {
        "status": {"code": response.status, "message": response.reason},
        "headers": _serialize_headers(response.headers),
        "body": body,  # NOQA: E999
        "url": str(response.url),
    }

    cassette.append(vcr_request, vcr_response)


async def record_responses(cassette, vcr_request, response):
    """Because aiohttp follows redirects by default, we must support
        them by default. This method is used to write individual
        request-response chains that were implicitly followed to get
        to the final destination.
    """

    for past_response in response.history:
        aiohttp_request = past_response.request_info

        # No data because it's following a redirect.
        past_request = Request(
            aiohttp_request.method,
            str(aiohttp_request.url),
            None,
            _serialize_headers(aiohttp_request.headers),
        )
        await record_response(cassette, past_request, past_response)

    # If we're following redirects, then the last request-response
    # we record is the one attached to the `response`.
    if response.history:
        aiohttp_request = response.request_info
        vcr_request = Request(
            aiohttp_request.method,
            str(aiohttp_request.url),
            None,
            _serialize_headers(aiohttp_request.headers),
        )

    await record_response(cassette, vcr_request, response)


def _build_cookie_header(session, cookies, cookie_header, url):
    url, _ = strip_auth_from_url(url)
    all_cookies = session._cookie_jar.filter_cookies(url)
    if cookies is not None:
        tmp_cookie_jar = CookieJar()
        tmp_cookie_jar.update_cookies(cookies)
        req_cookies = tmp_cookie_jar.filter_cookies(url)
        if req_cookies:
            all_cookies.load(req_cookies)

    if not all_cookies and not cookie_header:
        return None

    c = SimpleCookie()
    if cookie_header:
        c.load(cookie_header)
    for name, value in all_cookies.items():
        if isinstance(value, Morsel):
            mrsl_val = value.get(value.key, Morsel())
            mrsl_val.set(value.key, value.value, value.coded_value)
            c[name] = mrsl_val
        else:
            c[name] = value

    return c.output(header="", sep=";").strip()


def vcr_request(cassette, real_request):
    @functools.wraps(real_request)
    async def new_request(self, method, url, **kwargs):
        headers = kwargs.get("headers")
        auth = kwargs.get("auth")
        headers = self._prepare_headers(headers)
        data = kwargs.get("data", kwargs.get("json"))
        params = kwargs.get("params")
        cookies = kwargs.get("cookies")

        if auth is not None:
            headers["AUTHORIZATION"] = auth.encode()

        request_url = URL(url)
        if params:
            for k, v in params.items():
                params[k] = str(v)
            request_url = URL(url).with_query(params)

        c_header = headers.pop(hdrs.COOKIE, None)
        cookie_header = _build_cookie_header(self, cookies, c_header, request_url)
        if cookie_header:
            headers[hdrs.COOKIE] = cookie_header

        vcr_request = Request(method, str(request_url), data, _serialize_headers(headers))

        if cassette.can_play_response_for(vcr_request):
            log.info("Playing response for {} from cassette".format(vcr_request))
            response = play_responses(cassette, vcr_request)
            for redirect in response.history:
                self._cookie_jar.update_cookies(redirect.cookies, redirect.url)
            self._cookie_jar.update_cookies(response.cookies, response.url)
            return response

        if cassette.write_protected and cassette.filter_request(vcr_request):
            raise CannotOverwriteExistingCassetteException(cassette=cassette, failed_request=vcr_request)

        log.info("%s not in cassette, sending to real server", vcr_request)

        response = await real_request(self, method, url, **kwargs)  # NOQA: E999
        await record_responses(cassette, vcr_request, response)
        return response

    return new_request
