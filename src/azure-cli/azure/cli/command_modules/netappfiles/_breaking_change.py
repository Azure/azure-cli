# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_required_flag_breaking_change, register_default_value_breaking_change, register_other_breaking_change, register_argument_deprecate

register_argument_deprecate('netappfiles volume create', '--is-restoring', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--avs-data-store', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--creation-token', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--is-large-volume', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--is-restoring', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--ldap-enabled', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--network-features', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--security-style', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--volume-type', target_version='2.73.0')

# register_required_flag_breaking_change('bar foo', '--name')
# register_default_value_breaking_change('bar foo baz', '--foobar', 'A', 'B', target_version='May 2025')
# register_other_breaking_change('bar foo baz', 'During May 2024, another Breaking Change would happen in Build Event.')