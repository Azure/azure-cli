# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_argument_deprecate

register_argument_deprecate('netappfiles volume create', '--endpoint-type', target_version='2.78.0')
register_argument_deprecate('netappfiles volume update', '--endpoint-type', target_version='2.78.0')
