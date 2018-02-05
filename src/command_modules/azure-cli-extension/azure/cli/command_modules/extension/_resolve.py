# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from wheel.install import WHEEL_INFO_RE
from pkg_resources import parse_version

from knack.log import get_logger

from azure.cli.core.extension import ext_compat_with_cli

from azure.cli.command_modules.extension._index import get_index_extensions


logger = get_logger(__name__)


class NoExtensionCandidatesError(Exception):
    pass


def _is_not_platform_specific(item):
    parsed_filename = WHEEL_INFO_RE(item['filename'])
    p = parsed_filename.groupdict()
    if p.get('pyver') == 'py2.py3' and p.get('abi') == 'none' and p.get('plat') == 'any':
        return True
    logger.debug("Skipping '%s' as not universal wheel."
                 "We do not currently support platform specific extension detection. "
                 "They can be installed with the full URL %s", item['filename'], item.get('downloadUrl'))
    return False


def _is_compatible_with_cli_version(item):
    is_compatible, cli_core_version, min_required, max_required = ext_compat_with_cli(item['metadata'])
    if is_compatible:
        return True
    logger.debug("Skipping '%s' as not compatible with this version of the CLI. "
                 "Extension compatibility result: is_compatible=%s cli_core_version=%s min_required=%s "
                 "max_required=%s", item['filename'], is_compatible, cli_core_version, min_required, max_required)
    return False


def _is_greater_than_cur_version(cur_version):
    if not cur_version:
        return None
    cur_version_parsed = parse_version(cur_version)

    def filter_func(item):
        item_version = parse_version(item['metadata']['version'])
        if item_version > cur_version_parsed:
            return True
        logger.debug("Skipping '%s' as %s not greater than current version %s", item['filename'],
                     item_version, cur_version_parsed)
        return False
    return filter_func


def resolve_from_index(extension_name, cur_version=None, index_url=None):
    candidates = get_index_extensions(index_url=index_url).get(extension_name, [])
    if not candidates:
        raise NoExtensionCandidatesError("No extension found with name '{}'".format(extension_name))

    filters = [_is_not_platform_specific, _is_compatible_with_cli_version, _is_greater_than_cur_version(cur_version)]
    for f in filters:
        logger.debug("Candidates %s", [c['filename'] for c in candidates])
        candidates = list(filter(f, candidates))
    if not candidates:
        raise NoExtensionCandidatesError("No suitable extensions found.")

    candidates_sorted = sorted(candidates, key=lambda c: parse_version(c['metadata']['version']), reverse=True)
    logger.debug("Candidates %s", [c['filename'] for c in candidates_sorted])
    logger.debug("Choosing the latest of the remaining candidates.")
    chosen = candidates_sorted[0]
    logger.debug("Chosen %s", chosen)
    download_url, digest = chosen.get('downloadUrl'), chosen.get('sha256Digest')
    if not download_url:
        raise NoExtensionCandidatesError("No download url found.")
    return download_url, digest
