# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Agent selection, bounded retrieval, staging, and publication for optional Azure skills installation."""

import io
import json
import os
import re
import shutil
import ssl
import stat
import sys
import tempfile
import time
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass, field
from http.client import HTTPException, HTTPResponse, HTTPSConnection
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import yaml
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt, prompt_y_n
from knack.util import CLIError
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)


logger = get_logger(__name__)

AGENT_IDS = ('claude-code', 'codex', 'github-copilot', 'pi')
API_ROOT = 'https://api.github.com/repos/microsoft/azure-skills'
ARCHIVE_ROOT = 'https://codeload.github.com/microsoft/azure-skills/zip/'
METADATA_LIMIT = 1024 * 1024
ARCHIVE_LIMIT = 64 * 1024 * 1024
EXPANDED_LIMIT = 256 * 1024 * 1024
FILE_LIMIT = 16 * 1024 * 1024
ENTRY_LIMIT = 10000
PATH_DEPTH_LIMIT = 32
_SKILLS_PATH = ('.github', 'plugins', 'azure-skills', 'skills')
_LICENSE_NOTICE = 'LICENSE.azure-skills'
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


def _path_key(parts):
    # Normalize before folding too: folding can turn combining marks into letters.
    return tuple(unicodedata.normalize('NFD', unicodedata.normalize('NFD', part).casefold()) for part in parts)


def _validated_members(bundle):
    members = bundle.infolist()
    if not members or len(members) > ENTRY_LIMIT:
        raise CLIError('Azure skills archive is empty or exceeded the entry limit.')
    paths = {}
    explicit = set()
    roots = set()
    total = 0
    validated = []
    for member in members:
        # orig_filename retains NULs that ZipInfo.filename silently truncates.
        raw = member.orig_filename
        is_directory = member.is_dir()
        parts = tuple(raw.removesuffix('/').split('/'))
        if len(parts) > PATH_DEPTH_LIMIT:
            raise CLIError('Azure skills archive exceeded the path depth limit.')
        for part in parts:
            basename = part.split('.')[0].rstrip(' ').upper()
            if (not part or part in ('.', '..') or part.endswith((' ', '.')) or
                    any(ord(char) < 32 or char in '\\:<>"|?*' for char in part) or
                    basename in ('CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$') or
                    re.fullmatch(r'(COM|LPT)[1-9¹²³]', basename)):
                raise CLIError('Azure skills archive contains an unsafe path.')
        mode = stat.S_IFMT(member.external_attr >> 16)
        allowed_modes = (0, stat.S_IFDIR) if is_directory else (0, stat.S_IFREG)
        if mode not in allowed_modes or (is_directory and member.file_size):
            raise CLIError('Azure skills archive contains a link, special file, or invalid directory.')
        if member.flag_bits & (1 | 64):
            raise CLIError('Azure skills archive contains an encrypted entry.')
        if member.file_size < 0 or member.compress_size < 0:
            raise CLIError('Azure skills archive contains invalid size metadata.')
        total += member.file_size
        if total > EXPANDED_LIMIT:
            raise CLIError('Azure skills archive exceeded the expanded size limit.')
        key = _path_key(parts)
        if key in explicit:
            raise CLIError('Azure skills archive contains duplicate or platform-colliding paths.')
        explicit.add(key)
        # Record implicit ancestors too: ZIPs need not contain directory entries.
        for depth in range(1, len(parts) + 1):
            prefix = key[:depth]
            value = (parts[:depth], is_directory or depth < len(parts))
            if prefix in paths and paths[prefix] != value:
                raise CLIError('Azure skills archive contains file/directory or platform-colliding paths.')
            paths[prefix] = value
        roots.add(parts[0])
        if len(roots) > 1 or (len(parts) == 1 and not is_directory):
            raise CLIError('Azure skills archive must contain one repository root directory.')
        validated.append((member, parts))
    return validated


def _validate_skill_frontmatter(path):
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        if not lines or lines[0].rstrip() != '---':
            raise ValueError('Missing frontmatter')
        end = next(index for index in range(1, len(lines)) if lines[index].rstrip() == '---')
        metadata = yaml.safe_load('\n'.join(lines[1:end]))
        if not isinstance(metadata, dict) or any(
                not isinstance(metadata.get(field), str) or not metadata[field].strip()
                for field in ('name', 'description')):
            raise ValueError('Missing name or description')
    except (UnicodeError, ValueError, StopIteration, RecursionError, yaml.YAMLError):
        raise CLIError(f'Invalid SKILL.md frontmatter in {path}. Expected nonempty name and description strings.') from None


def stage_bundle(archive: Path, staging: Path) -> list[Path]:
    """Validate a repository ZIP and stage complete skill trees in a new private directory."""
    owned = False
    complete = False
    try:
        if archive.stat().st_size > ARCHIVE_LIMIT:
            raise CLIError('Azure skills archive exceeded the size limit.')
        with zipfile.ZipFile(archive) as bundle:
            members = _validated_members(bundle)
            root = members[0][1][0]
            prefix = (root,) + _SKILLS_PATH
            payload = [(member, parts[len(prefix):]) for member, parts in members
                       if parts[:len(prefix)] == prefix and len(parts) > len(prefix)]
            license_member = next((member for member, parts in members
                                   if parts == (root, 'LICENSE') and not member.is_dir()), None)
            if license_member is None or not license_member.file_size:
                raise CLIError('Azure skills archive is missing its repository LICENSE notice.')
            names = sorted({parts[0] for _, parts in payload})
            files = {parts for member, parts in payload if not member.is_dir()}
            if (not names or any(len(parts) < 2 for parts in files) or
                    any((name, 'SKILL.md') not in files for name in names)):
                raise CLIError('Azure skills payload requires an immediate SKILL.md in every top-level skill directory.')
            if any(member.file_size > FILE_LIMIT for member, _ in payload) or license_member.file_size > FILE_LIMIT:
                raise CLIError('Azure skills archive exceeded the per-file size limit.')
            for member, parts in payload:
                if len(parts) >= 2 and _path_key((parts[1],)) == _path_key((_LICENSE_NOTICE,)):
                    if parts[1] != _LICENSE_NOTICE or len(parts) != 2 or member.is_dir():
                        raise CLIError('Azure skills payload collides with the LICENSE.azure-skills notice.')

            # mkdir must fail for existing directories, files, and symlinks; never clean those up.
            staging.mkdir(mode=0o700)
            owned = True
            license_buffer = io.BytesIO()
            with bundle.open(license_member) as source:
                written = _copy_bounded(source, license_buffer, min(FILE_LIMIT, EXPANDED_LIMIT))
            if written != license_member.file_size:
                raise CLIError('Azure skills archive LICENSE did not match its advertised size.')
            license_content = license_buffer.getvalue()
            total = 0
            for member, parts in payload:
                destination = staging.joinpath(*parts)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, destination.open('xb') as output:
                    written = _copy_bounded(source, output, min(FILE_LIMIT, EXPANDED_LIMIT - total))
                if written != member.file_size:
                    raise CLIError(f'Azure skills archive member {member.filename} did not match its advertised size.')
                total += written
                # Nested SKILL.md files can be supporting guides, not standalone entry points.
                if len(parts) == 2 and parts[1] == 'SKILL.md':
                    _validate_skill_frontmatter(destination)
                if os.name == 'posix':
                    # Retain executable resources, not setuid/setgid/sticky or archive write permissions.
                    destination.chmod((destination.stat().st_mode & 0o666) | ((member.external_attr >> 16) & 0o111))

            trees = [staging / name for name in names]
            for tree in trees:
                notice = tree / _LICENSE_NOTICE
                if notice.exists():
                    if notice.read_bytes() != license_content:
                        raise CLIError('Azure skills payload has differing LICENSE.azure-skills content.')
                else:
                    # Count every added notice: a large license must not multiply without a bound.
                    with notice.open('xb') as output:
                        total += _copy_bounded(io.BytesIO(license_content), output,
                                               min(FILE_LIMIT, EXPANDED_LIMIT - total))
        complete = True
        return trees
    except (OSError, ValueError, EOFError, RuntimeError, zipfile.BadZipFile, zlib.error) as error:
        raise CLIError(f'Could not stage the Azure skills archive: {error}') from None
    finally:
        if owned and not complete:
            shutil.rmtree(staging)


@dataclass(frozen=True)
class AgentTarget:
    identifier: str
    label: str
    destination: Path
    detected: bool


@dataclass
class InstallReport:
    installed: list[Path] = field(default_factory=list)
    already_present: list[Path] = field(default_factory=list)
    conflicts: list[Path] = field(default_factory=list)
    failures: list[tuple[Path, str]] = field(default_factory=list)


def _is_indirection(info) -> bool:
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))


def _check_directory_path(path: Path) -> None:
    # Walk lexically, before normalization: resolving a link would hide the unsafe ancestor.
    for directory in (*reversed(path.parents), path):
        try:
            info = directory.lstat()
        except FileNotFoundError:
            continue
        if _is_indirection(info):
            raise CLIError(f'Azure skills destination uses a symlink or reparse point: {directory}. '
                           'Choose a destination without filesystem indirection.')
        if not stat.S_ISDIR(info.st_mode):
            raise CLIError(f'Azure skills destination ancestor is not a directory: {directory}.')


def _same_tree(source: Path, destination: Path) -> bool:
    """Compare exact names, bytes, and Unix file executable bits without following tree links."""
    try:
        source_info, destination_info = source.lstat(), destination.lstat()
    except FileNotFoundError:
        return False
    if _is_indirection(source_info) or _is_indirection(destination_info):
        return False
    if stat.S_ISDIR(source_info.st_mode) and stat.S_ISDIR(destination_info.st_mode):
        names = sorted(path.name for path in source.iterdir())
        if names != sorted(path.name for path in destination.iterdir()):
            return False
        return all(_same_tree(source / name, destination / name) for name in names)
    if not (stat.S_ISREG(source_info.st_mode) and stat.S_ISREG(destination_info.st_mode)):
        return False
    if source_info.st_size != destination_info.st_size:
        return False
    if os.name == 'posix' and (source_info.st_mode & 0o111) != (destination_info.st_mode & 0o111):
        return False
    with source.open('rb') as left, destination.open('rb') as right:
        while True:
            chunk = left.read(65536)
            if chunk != right.read(65536):
                return False
            if not chunk:
                return True


def _publish_one(source: Path, destination: Path) -> str:
    """Publish a validated tree under a cooperative lock, never merge an existing entry.

    Checks reject existing indirection, not hostile local writers racing filesystem operations.
    The caller owns and retains the validated source returned by stage_bundle.
    """
    destination = Path.cwd() / destination
    destination_root = destination.parent
    _check_directory_path(destination_root)
    destination_root.parent.mkdir(parents=True, exist_ok=True)
    _check_directory_path(destination_root)
    lock_path = destination_root.parent / '.az-azure-skills.lock'
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise CLIError(f'Azure skills installation lock already exists: {lock_path}. '
                       'Verify no installation is running before manually addressing this lock; '
                       'it will not be removed automatically.') from None
    temporary = None
    cancelled = False
    try:
        os.close(descriptor)
        _check_directory_path(destination_root)
        destination_root.mkdir(exist_ok=True)
        try:
            destination.lstat()
        except FileNotFoundError:
            pass
        else:
            return 'already_present' if _same_tree(source, destination) else 'conflict'

        # A private sibling keeps incomplete content outside this skills root.
        temporary = Path(tempfile.mkdtemp(prefix='.az-azure-skills-', dir=destination_root.parent))
        prepared = temporary / source.name
        shutil.copytree(source, prepared)
        _check_directory_path(destination_root)
        try:
            destination.lstat()
        except FileNotFoundError:
            prepared.rename(destination)
            return 'installed'
        return 'conflict'
    except KeyboardInterrupt:
        cancelled = True
        raise
    finally:
        try:
            try:
                if temporary is not None:
                    shutil.rmtree(temporary)
            finally:
                # Only reached after this invocation acquired the exclusive lock.
                lock_path.unlink()
        except OSError as error:
            if cancelled:
                # Cleanup failure must not turn cancellation into a recoverable per-path error.
                raise KeyboardInterrupt(f'Cleanup failed: {error}') from error
            raise


def publish_skills(skill_dirs: list[Path], targets: list[AgentTarget]) -> InstallReport:
    """Record per-path first-install outcomes, not a coherent-bundle or update guarantee."""
    report = InstallReport()
    seen = set()
    for target in targets:
        for source in skill_dirs:
            destination = Path.cwd() / target.destination / source.name
            try:
                _check_directory_path(destination.parent)
                destination = Path(os.path.abspath(destination))
                key = os.path.normcase(str(destination))
                if key in seen:
                    continue
                seen.add(key)
                # Keep the selected AgentTargets intact, including all labels for shared destinations.
                result = _publish_one(source, destination)
                if result == 'installed':
                    report.installed.append(destination)
                elif result == 'already_present':
                    report.already_present.append(destination)
                else:
                    report.conflicts.append(destination)
            except KeyboardInterrupt as error:
                message = 'Azure skills publication cancelled; earlier installations remain.'
                if str(error):
                    message += f' {error}'
                report.failures.append((destination, message))
                return report
            except (OSError, CLIError) as error:
                report.failures.append((destination, str(error)))
    return report


def _config_directory(variable: str, default: Path) -> Path:
    value = os.environ.get(variable)
    if value and value.strip():
        # Preserve '..' until publication can inspect every lexical ancestor for indirection.
        return Path(os.path.expanduser(value)).absolute()
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


def _confirm_skills(message: str) -> bool:
    try:
        return prompt_y_n(message, default='n')
    except (NoTTYException, EOFError, KeyboardInterrupt):
        logger.warning('Azure skills offer cancelled; kubectl and kubelogin remain installed.')
        return False


def _choose_skill_targets() -> list[AgentTarget]:
    if not _confirm_skills('Install Microsoft Azure skills for your coding agents?'):
        return []
    targets = discover_agents()
    defaults = [target.identifier for target in targets if target.detected]
    numbers = ','.join(str(index + 1) for index, target in enumerate(targets) if target.detected)
    print('Select agents:')
    for index, target in enumerate(targets, 1):
        status = 'detected, selected' if target.detected else 'not detected'
        print(f'  {index}. {target.label}: {status}')
    while True:
        try:
            value = prompt(f'Enter agent numbers, comma-separated. Enter keeps [{numbers}]; "none" skips: ')
        except (NoTTYException, EOFError, KeyboardInterrupt):
            logger.warning('Azure skills selection cancelled; kubectl and kubelogin remain installed.')
            return []
        try:
            selected = parse_agent_selection(value, defaults)
            return [target for target in targets if target.identifier in selected]
        except CLIError as error:
            logger.warning('%s', error)


def _show_skill_targets(targets: list[AgentTarget]) -> None:
    logger.warning('Install user-level Azure skills only; no MCP configuration, hooks, or agent applications. '
                   'Some workflows require tools configured separately.')
    for target in targets:
        logger.warning('  %s: %s', target.label, target.destination)
    if any(target.identifier == 'codex' for target in targets):
        logger.warning('Codex uses the shared ~/.agents/skills directory. Skills can also be visible to '
                       'Pi and GitHub Copilot even when they are not selected. '
                       'Selection controls destinations, not agent enable/disable configuration.')


def _report_skills(report: InstallReport) -> None:
    for label, paths in (('Installed', report.installed), ('Already present', report.already_present),
                         ('Skipped/conflicting', report.conflicts)):
        logger.warning('%s (%d):%s', label, len(paths), ''.join(f'\n  {path}' for path in paths))
    logger.warning('Failed (%d):%s', len(report.failures),
                   ''.join(f'\n  {path}: {reason}' for path, reason in report.failures))


def _skills_recovery(targets: list[AgentTarget], manual: bool) -> str:
    guidance = ''
    if manual:
        guidance = (
            'Review the reported paths and preserve user modifications; do not assume this command owns them. '
            'If replacement is wanted, move only reviewed Azure skill directories to backups outside all agent '
            'skill discovery paths. For a coherent replacement of a partial or mixed-version bundle, review and '
            'back up its other Azure skill directories too, not just conflicts. Do not remove the entire skills '
            'root or unrelated skills; shared-directory changes affect other agents. Keep backups until the new '
            'installation has been checked. ')
    agents = ' '.join(target.identifier for target in targets) or '<selected agents>'
    return (guidance + 'Address the reported cause before a retry. A network-only failure can be retried directly. '
            f'Retry with az aks install-cli --install-azure-skills true --skills-agents {agents}. '
            'This also reruns binary installation and resolves the then-current release; the release may have changed. '
            'Retries do not guarantee a coherent bundle, and this first-install-only command '
            'does not update existing skills.')


def maybe_install_azure_skills(cmd, install_azure_skills: bool | None = None,
                              skills_agents: list[str] | None = None, gh_token: str | None = None) -> None:
    """Offer skills only after binary success; the command handler owns argument preflight."""
    if install_azure_skills is False:
        return
    explicit = install_azure_skills is True
    if not explicit:
        if not sys.stdin.isatty() or cmd.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False):
            return
        if _is_sudo():
            logger.warning('Skipping Azure skills under sudo. Install as an unprivileged user; '
                           'rerun with user-writable binary installation locations.')
            return

    targets = []
    source = 'Azure skills source was not resolved.'
    report = None
    failure = None
    publishing = False
    try:
        # Registry membership deduplicates IDs, but lexical destinations must reach publish_skills
        # unchanged so it can validate ancestors before normalizing and deduplicating paths.
        targets = ([target for target in discover_agents() if target.identifier in skills_agents]
                   if explicit else _choose_skill_targets())
        if not targets:
            return
        _show_skill_targets(targets)
        if not explicit and not _confirm_skills('Install Azure skills at these destinations?'):
            return
        try:
            with tempfile.TemporaryDirectory(prefix='az-azure-skills-') as temporary:
                root = Path(temporary)
                release = resolve_release(gh_token)
                source = (f'Azure skills source for this attempt: microsoft/azure-skills, '
                          f'{release.tag}, commit {release.commit}.')
                logger.warning('%s', source)
                archive = root / 'azure-skills.zip'
                download_archive(release, archive)
                trees = stage_bundle(archive, root / 'staged')
                publishing = True
                report = publish_skills(trees, targets)
        except KeyboardInterrupt:
            failure = ('Azure skills installation cancelled; earlier installations remain.' if publishing else
                       'Azure skills installation cancelled; no skills were published.')
    except (CLIError, OSError) as error:
        failure = f'Azure skills installation failed: {error}'

    if report is not None:
        _report_skills(report)
        if report.conflicts or report.failures:
            reasons = [f'Conflict: {path}' for path in report.conflicts]
            reasons.extend(f'{path}: {reason}' for path, reason in report.failures)
            if failure:
                reasons.append(failure)
            failure = 'Azure skills installation is incomplete. ' + '; '.join(reasons)
    if failure:
        message = (f'{failure} kubectl and kubelogin remain installed. {source} '
                   + _skills_recovery(targets, publishing))
        logger.warning('%s', message)
        if explicit:
            raise CLIError(message)
        return
    logger.warning('Azure skills installation complete. kubectl and kubelogin remain installed. %s', source)
