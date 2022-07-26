# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from packaging.version import parse
from typing import Callable, List, NamedTuple, Union

from azure.cli.core.extension import ext_compat_with_cli, WHEEL_INFO_RE
from azure.cli.core.extension._index import get_index_extensions

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


class NoExtensionCandidatesError(Exception):
    pass


class _ExtensionFilter(NamedTuple):
    # A function that filters a list of extensions
    filter: Callable[[List[dict]], List[dict]]
    # Message of exception raised if a filter leaves no candidates
    on_empty_results_message: Union[str, Callable[[List[dict]], str]]


def _is_not_platform_specific(item):
    parsed_filename = WHEEL_INFO_RE(item['filename'])
    p = parsed_filename.groupdict()
    if p.get('abi') == 'none' and p.get('plat') == 'any':
        return True
    logger.debug("Skipping '%s' as not universal wheel."
                 "We do not currently support platform specific extension detection. "
                 "They can be installed with the full URL %s", item['filename'], item.get('downloadUrl'))
    return False


def _is_compatible_with_cli_version(item):
    is_compatible, cli_core_version, min_required, max_required, min_ext_required = ext_compat_with_cli(
        item['metadata'])
    if is_compatible:
        return True
    logger.debug("Skipping '%s' as not compatible with this version of the CLI. "
                 "Extension compatibility result: is_compatible=%s cli_core_version=%s ext_version=%s "
                 "min_core_required=%s max_core_required=%s min_ext_required=%s", item['filename'], is_compatible,
                 cli_core_version, item['metadata'].get('version'), min_required, max_required, min_ext_required)
    return False


def _is_greater_than_cur_version(cur_version):
    if not cur_version:
        return None
    cur_version_parsed = parse(cur_version)

    def filter_func(item):
        item_version = parse(item['metadata']['version'])
        if item_version > cur_version_parsed:
            return True
        logger.debug("Skipping '%s' as %s not greater than current version %s", item['filename'],
                     item_version, cur_version_parsed)
        return False
    return filter_func


def _get_latest_version(candidates: List[dict]) -> List[dict]:
    return [max(candidates, key=lambda c: parse(c['metadata']['version']))]


def _get_version_compatibility_feedback(candidates: List[dict]) -> str:
    from .operations import check_version_compatibility

    try:
        check_version_compatibility(_get_latest_version(candidates)[0].get("metadata"))
        return ""
    except CLIError as e:
        return e.args[0]


def resolve_from_index(extension_name, cur_version=None, index_url=None, target_version=None, cli_ctx=None):
    """Gets the download Url and digest for the matching extension

    Args:
        extension_name (str): Name of
        cur_version (str, optional): Threshold version to filter out extensions. Defaults to None.
        index_url (str, optional):  Defaults to None.
        target_version (str, optional): Version of extension to install. Defaults to latest version.
        cli_ctx (, optional): CLI Context. Defaults to None.

    Raises:
        NoExtensionCandidatesError when an extension:
            * Doesn't exist
            * Has no versions compatible with the current platform
            * Has no versions more recent than currently installed version
            * Has no versions that are compatible with the version of azure cli

    Returns:
        tuple: (Download Url, SHA digest)
    """
    candidates = get_index_extensions(index_url=index_url, cli_ctx=cli_ctx).get(extension_name, [])

    if not candidates:
        raise NoExtensionCandidatesError(f"No extension found with name '{extension_name}'")

    # Helper to curry predicate functions
    def list_filter(f):
        return lambda cs: list(filter(f, cs))

    candidate_filters = [
        _ExtensionFilter(
            filter=list_filter(_is_not_platform_specific),
            on_empty_results_message=f"No suitable extensions found for '{extension_name}'."
        )
    ]

    if target_version:
        candidate_filters += [
            _ExtensionFilter(
                filter=list_filter(lambda c: c['metadata']['version'] == target_version),
                on_empty_results_message=f"Version '{target_version}' not found for extension '{extension_name}'"
            )
        ]
    else:
        candidate_filters += [
            _ExtensionFilter(
                filter=list_filter(_is_greater_than_cur_version(cur_version)),
                on_empty_results_message=f"Latest version of '{extension_name}' is already installed."
            )
        ]

    candidate_filters += [
        _ExtensionFilter(
            filter=list_filter(_is_compatible_with_cli_version),
            on_empty_results_message=_get_version_compatibility_feedback
        ),
        _ExtensionFilter(
            filter=_get_latest_version,
            on_empty_results_message=f"No suitable extensions found for '{extension_name}'."
        )
    ]

    for candidate_filter, on_empty_results_message in candidate_filters:
        logger.debug("Candidates %s", [c['filename'] for c in candidates])
        filtered_candidates = candidate_filter(candidates)

        if not filtered_candidates and (on_empty_results_message is not None):
            if not isinstance(on_empty_results_message, str):
                on_empty_results_message = on_empty_results_message(candidates)
            raise NoExtensionCandidatesError(on_empty_results_message)

        candidates = filtered_candidates

    chosen = candidates[0]

    logger.debug("Chosen %s", chosen)
    download_url, digest = chosen.get('downloadUrl'), chosen.get('sha256Digest')
    if not download_url:
        raise NoExtensionCandidatesError("No download url found.")
    azmirror_endpoint = cli_ctx.cloud.endpoints.azmirror_storage_account_resource_id if cli_ctx and \
        cli_ctx.cloud.endpoints.has_endpoint_set('azmirror_storage_account_resource_id') else None
    config_index_url = cli_ctx.config.get('extension', 'index_url', None) if cli_ctx else None
    if azmirror_endpoint and not config_index_url:
        # when extension index and wheels are mirrored in airgapped clouds from public cloud
        # the content of the index.json is not updated, so we need to modify the wheel url got
        # from the index.json here.
        import posixpath
        whl_name = download_url.split('/')[-1]
        download_url = posixpath.join(azmirror_endpoint, 'extensions', whl_name)
    return download_url, digest


def resolve_project_url_from_index(extension_name):
    """
    Gets the project url of the matching extension from the index
    """
    candidates = get_index_extensions().get(extension_name, [])
    if not candidates:
        raise NoExtensionCandidatesError("No extension found with name '{}'".format(extension_name))
    try:
        return candidates[0]['metadata']['extensions']['python.details']['project_urls']['Home']
    except KeyError as ex:
        logger.debug(ex)
        raise CLIError('Could not find project information for extension {}.'.format(extension_name))
