# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""User-level agent selection and bounded retrieval for optional Azure skills installation."""

import io
import json
import os
import re
import ssl
import time
from dataclasses import dataclass
from http.client import HTTPException, HTTPResponse, HTTPSConnection
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from knack.util import CLIError
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)


AGENT_IDS = ('claude-code', 'codex', 'github-copilot', 'pi')
API_ROOT = 'https://api.github.com/repos/microsoft/azure-skills'
ARCHIVE_ROOT = 'https://codeload.github.com/microsoft/azure-skills/zip/'
METADATA_LIMIT = 1024 * 1024
ARCHIVE_LIMIT = 64 * 1024 * 1024
_SOCKET_TIMEOUT = 30
_RESPONSE_TIMEOUT = 120


@dataclass(frozen=True)
class Release:
    tag: str
    commit: str


class _DeadlineReader(io.RawIOBase):
    def __init__(self, sock, raw):
        self._socket = sock
        self._raw = raw
        self._deadline = time.monotonic() + _RESPONSE_TIMEOUT

    def readable(self):
        return True

    def readinto(self, buffer):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise CLIError('Azure skills response exceeded the read deadline.')
        # Buffered body reads and chunk framing can each perform many receives.
        self._socket.settimeout(min(_SOCKET_TIMEOUT, remaining))
        try:
            return self._raw.readinto(buffer)
        except TimeoutError:
            if time.monotonic() >= self._deadline:
                raise CLIError('Azure skills response exceeded the read deadline.') from None
            raise

    def close(self):
        try:
            self._raw.close()
        finally:
            super().close()


class _DeadlineHTTPResponse(HTTPResponse):
    def __init__(self, sock, *args, **kwargs):
        super().__init__(sock, *args, **kwargs)
        # Install below buffering before headers are read; error bodies share this deadline.
        self.fp = io.BufferedReader(_DeadlineReader(sock, self.fp.detach()))


class _DeadlineHTTPSConnection(HTTPSConnection):
    response_class = _DeadlineHTTPResponse


class _DeadlineHTTPSHandler(HTTPSHandler):
    def do_open(self, http_class, req, **http_conn_args):
        return super().do_open(_DeadlineHTTPSConnection, req, **http_conn_args)


class _MetadataRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CLIError('Unexpected redirect while resolving Azure skills metadata.')

    def http_error_302(self, req, fp, code, msg, headers):
        # urllib otherwise retains the response when redirect_request raises.
        try:
            return self.redirect_request(req, fp, code, msg, headers, '')
        finally:
            fp.close()

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


class _ArchiveRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            parsed = urlsplit(newurl)
            allowed = (parsed.scheme == 'https' and parsed.hostname == 'codeload.github.com' and
                       parsed.port in (None, 443) and parsed.username is None and parsed.password is None)
        except ValueError:
            allowed = False
        if not allowed:
            raise CLIError('Unexpected redirect while downloading the Azure skills archive.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

    def http_error_302(self, req, fp, code, msg, headers):
        try:
            location = headers.get('Location') or headers.get('URI')
            if not location:
                raise CLIError('Missing redirect location while downloading the Azure skills archive.')
            new = self.redirect_request(req, fp, code, msg, headers, urljoin(req.full_url, location))
            count = getattr(req, '_azure_skills_redirects', 0)
            if count >= self.max_redirections:
                raise CLIError('Too many redirects while downloading the Azure skills archive.')
            new._azure_skills_redirects = count + 1  # pylint: disable=protected-access
        finally:
            # Do not use urllib's unbounded drain of a redirect response body.
            fp.close()
        return self.parent.open(new, timeout=req.timeout)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


def _copy_bounded(source, destination, limit: int) -> int:
    deadline = time.monotonic() + _RESPONSE_TIMEOUT
    written = 0
    while True:
        if time.monotonic() > deadline:
            raise CLIError('Azure skills response exceeded the read deadline.')
        chunk = source.read(min(65536, limit - written + 1))
        if not chunk:
            return written
        written += len(chunk)
        if written > limit:
            raise CLIError('Azure skills content exceeded the size limit.')
        destination.write(chunk)


def _copy_response(response, destination, limit: int) -> None:
    length = response.headers.get('Content-Length')
    if length is not None:
        if not re.fullmatch(r'[0-9]{1,20}', length):
            raise CLIError('Azure skills response has an invalid content length.')
        length = int(length)
        if length > limit:
            raise CLIError('Azure skills content exceeded the size limit.')
    written = _copy_bounded(response, destination, limit)
    if length is not None and written != length:
        raise CLIError('Azure skills response did not match its advertised content length.')


def _numeric_header(headers, name: str) -> int | None:
    value = headers.get(name)
    # Bound conversion and display; never echo arbitrary server header text.
    if isinstance(value, str) and re.fullmatch(r'[0-9]{1,10}', value):
        return int(value)
    return None


def _http_error(error: HTTPError, operation: str, authenticated: bool) -> CLIError:
    with error:
        headers = error.headers or {}
        retry = _numeric_header(headers, 'Retry-After')
        reset = _numeric_header(headers, 'X-RateLimit-Reset')
        limited = error.code == 429 or (error.code == 403 and (
            _numeric_header(headers, 'X-RateLimit-Remaining') == 0 or retry is not None))
        if error.code == 403 and not limited:
            # A 403 alone is not evidence of rate limiting. Inspect only bounded JSON.
            body = io.BytesIO()
            try:
                _copy_bounded(error, body, METADATA_LIMIT)
                payload = json.loads(body.getvalue())
                message = payload.get('message') if isinstance(payload, dict) else None
                limited = isinstance(message, str) and 'rate limit' in message.lower()
            except (CLIError, OSError, HTTPException, ValueError, RecursionError):
                pass
        message = f'Azure skills {operation} failed (HTTP {error.code}). '
        if limited:
            message += 'GitHub rate limit reached; wait until the limit resets and retry.'
            if not authenticated and operation == 'metadata lookup':
                message += ' For anonymous metadata requests, you can also supply --gh-token.'
            if retry is not None:
                message += f' Retry after {retry} seconds.'
            if reset is not None:
                message += f' Rate limit reset: Unix time {reset}.'
        elif error.code in (401, 403):
            message += ('Check the supplied token\'s access to microsoft/azure-skills.' if authenticated else
                        'Check access to microsoft/azure-skills and any network access restrictions.')
        else:
            message += 'Check GitHub availability and repository access, then retry.'
        return CLIError(message)


def _api_json(path: str, gh_token: str | None) -> dict:
    try:
        headers = {'Accept': 'application/vnd.github+json'}
        if gh_token:
            headers['Authorization'] = 'Bearer ' + gh_token
        request = Request(API_ROOT + path, headers=headers)
        opener = build_opener(_MetadataRedirectHandler(), _DeadlineHTTPSHandler(context=ssl.create_default_context()))
        with opener.open(request, timeout=_SOCKET_TIMEOUT) as response:
            body = io.BytesIO()
            _copy_response(response, body, METADATA_LIMIT)
        try:
            payload = json.loads(body.getvalue())
        except (ValueError, RecursionError):
            raise CLIError('GitHub returned invalid Azure skills metadata JSON.') from None
        if not isinstance(payload, dict):
            raise CLIError('GitHub returned invalid Azure skills metadata fields.')
        return payload
    except HTTPError as error:
        raise _http_error(error, 'metadata lookup', bool(gh_token)) from None
    except (URLError, OSError, HTTPException, ValueError):
        # Network exceptions can contain URLs, request headers, or the token.
        raise CLIError('Azure skills metadata lookup failed. Check the network, TLS, '
                       'and proxy settings, then retry.') from None


def resolve_release(gh_token: str | None = None) -> Release:
    release = _api_json('/releases/latest', gh_token)
    tag = release.get('tag_name')
    if (not isinstance(tag, str) or not tag or len(tag) > 255 or
            any(ord(char) < 32 for char in tag) or
            release.get('draft') is not False or
            release.get('prerelease') is not False):
        raise CLIError('GitHub returned an invalid stable Azure skills release.')
    obj = _api_json('/git/ref/tags/' + quote(tag, safe=''), gh_token).get('object')
    for depth in range(6):
        if not isinstance(obj, dict):
            break
        sha = obj.get('sha')
        if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', sha):
            break
        if obj.get('type') == 'commit':
            return Release(tag, sha.lower())
        if obj.get('type') != 'tag' or depth == 5:
            break
        obj = _api_json('/git/tags/' + sha, gh_token).get('object')
    raise CLIError('Could not resolve the Azure skills release tag to a commit.')


def download_archive(release: Release, destination: Path) -> None:
    if not isinstance(release.commit, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', release.commit):
        raise CLIError('Invalid Azure skills archive commit.')
    incomplete = False
    try:
        # A separate opener and Request ensure metadata credentials cannot carry over.
        opener = build_opener(_ArchiveRedirectHandler(), _DeadlineHTTPSHandler(context=ssl.create_default_context()))
        request = Request(ARCHIVE_ROOT + release.commit)
        with opener.open(request, timeout=_SOCKET_TIMEOUT) as response:
            with destination.open('wb') as archive:
                incomplete = True
                _copy_response(response, archive, ARCHIVE_LIMIT)
        incomplete = False
    except HTTPError as error:
        raise _http_error(error, 'archive download', False) from None
    except (URLError, OSError, HTTPException, ValueError):
        raise CLIError('Azure skills archive download failed. Check the network, TLS, proxy, '
                       'and destination permissions, then retry.') from None
    finally:
        if incomplete:
            destination.unlink(missing_ok=True)


@dataclass(frozen=True)
class AgentTarget:
    identifier: str
    label: str
    destination: Path
    detected: bool


def _config_directory(variable: str, default: Path) -> Path:
    value = os.environ.get(variable)
    if value and value.strip():
        return Path(os.path.abspath(os.path.expanduser(value)))
    return default


def discover_agents() -> list[AgentTarget]:
    home = Path.home()
    claude = _config_directory('CLAUDE_CONFIG_DIR', home / '.claude')
    codex = _config_directory('CODEX_HOME', home / '.codex')
    copilot = home / '.copilot'
    pi = _config_directory('PI_CODING_AGENT_DIR', home / '.pi/agent')
    return [
        AgentTarget('claude-code', 'Claude Code', claude / 'skills', os.path.isdir(claude)),
        # Codex's config override affects detection, not its shared user skills location.
        AgentTarget('codex', 'Codex', home / '.agents/skills',
                    os.path.isdir(codex) or (os.name == 'posix' and os.path.isdir('/etc/codex'))),
        AgentTarget('github-copilot', 'GitHub Copilot', copilot / 'skills', os.path.isdir(copilot)),
        AgentTarget('pi', 'Pi', pi / 'skills', os.path.isdir(pi)),
    ]


def parse_agent_selection(value: str, defaults: list[str]) -> list[str]:
    text = value.strip()
    if not text:
        return list(defaults)
    if text.lower() == 'none':
        return []
    parts = [part.strip() for part in text.split(',')]
    if any(part not in ('1', '2', '3', '4') for part in parts):
        raise CLIError('Enter agent numbers 1-4 separated by commas, or "none".')
    selected = {int(part) - 1 for part in parts}
    return [identifier for index, identifier in enumerate(AGENT_IDS)
            if index in selected]


def _is_sudo() -> bool:
    # Treat even an empty marker conservatively; root alone does not imply sudo.
    return os.name == 'posix' and ('SUDO_UID' in os.environ or 'SUDO_USER' in os.environ)


def validate_skills_options(install_azure_skills: bool | None, skills_agents: list[str] | None) -> None:
    if skills_agents is not None and install_azure_skills is not True:
        raise ArgumentUsageError('--skills-agents requires --install-azure-skills true.')
    if install_azure_skills is not True:
        return
    if not skills_agents:
        raise RequiredArgumentMissingError('--install-azure-skills true requires a nonempty --skills-agents list.')
    unknown = [identifier for identifier in skills_agents if identifier not in AGENT_IDS]
    if unknown:
        raise InvalidArgumentValueError(
            f'Unknown --skills-agents: {", ".join(unknown)}. Choose from: {", ".join(AGENT_IDS)}.')
    if _is_sudo():
        raise CLIError(
            'Install Azure skills as an unprivileged user, not under sudo. '
            'Rerun with user-writable binary installation locations.')
