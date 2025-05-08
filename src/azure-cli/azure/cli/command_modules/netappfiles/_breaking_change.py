# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_argument_deprecate

register_argument_deprecate('netappfiles volume create', '--is-restoring', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--avs-data-store', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--creation-token', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--is-large-volume', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--is-restoring', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--ldap-enabled', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--network-features', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--security-style', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--volume-type', target_version='2.73.0')
register_argument_deprecate('netappfiles volume update', '--endpoint-type', target_version='2.73.0')
