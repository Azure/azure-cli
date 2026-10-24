# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections
import re


def _parse_semver(version_str):
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str or '')
    if match:
        return tuple(int(x) for x in match.groups())
    return (0, 0, 0)


def _major_minor(version_str):
    """Return the "Major.Minor" (X.Y) string for a version name, or '' if unparseable."""
    match = re.match(r'(\d+)\.(\d+)', version_str or '')
    if match:
        return '{}.{}'.format(*match.groups())
    return ''


def get_versions_table_format(results):
    return [_version_row(r) for r in results]


def _version_row(result):
    props = result.get('properties', {})
    return collections.OrderedDict(
        Name=result.get('name', ''),
        ChannelGroup=props.get('channelGroup', ''),
    )


def cluster_show_table_format(result):
    return [_cluster_row(result)]


def cluster_list_table_format(results):
    return [_cluster_row(r) for r in results]


def _cluster_row(result):
    props = result.get('properties', {})
    version = props.get('version', {})
    api = props.get('api', {})
    return collections.OrderedDict(
        Name=result.get('name', ''),
        Location=result.get('location', ''),
        ResourceGroup=result.get('resourceGroup', ''),
        Version=version.get('id', ''),
        ProvisioningState=props.get('provisioningState', ''),
        ApiServerUrl=api.get('url', ''),
    )


def nodepool_show_table_format(result):
    return [_nodepool_row(result)]


def nodepool_list_table_format(results):
    return [_nodepool_row(r) for r in results]


def _nodepool_row(result):
    props = result.get('properties', {})
    version = props.get('version', {})
    platform = props.get('platform', {})
    return collections.OrderedDict(
        Name=result.get('name', ''),
        Version=version.get('id', ''),
        VmSize=platform.get('vmSize', ''),
        ProvisioningState=props.get('provisioningState', ''),
    )
