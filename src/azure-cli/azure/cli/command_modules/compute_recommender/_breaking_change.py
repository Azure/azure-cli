# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_deprecate

register_command_deprecate('compute-recommender spot-placement-recommender', redirect='az compute-recommender spot-placement-score', hide=True)
# Warning Message: This command has been deprecated and will be removed in next breaking change release(2.67.0). Use `baz foo` instead.
