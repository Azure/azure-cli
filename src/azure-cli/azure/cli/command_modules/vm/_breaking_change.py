# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_argument_deprecate

# These parameters will be replaced by new parameters after migrated to aaz based code
register_argument_deprecate(command='sig image-definition list-shared', argument='--marker')
register_argument_deprecate(command='sig image-definition list-shared', argument='--show-next-marker')
register_argument_deprecate(command='sig image-version list-shared', argument='--marker')
register_argument_deprecate(command='sig image-version list-shared', argument='--show-next-marker')
register_argument_deprecate(command='sig image-definition list-community', argument='--marker')
register_argument_deprecate(command='sig image-definition list-community', argument='--show-next-marker')
register_argument_deprecate(command='sig image-version list-community', argument='--marker')
register_argument_deprecate(command='sig image-version list-community', argument='--show-next-marker')
