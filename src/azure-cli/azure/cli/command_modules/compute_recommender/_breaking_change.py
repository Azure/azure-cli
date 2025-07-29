# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_deprecate

register_command_deprecate(
    'compute-recommender spot-placement-recommender',
    redirect='az compute-recommender spot-placement-score',
    hide=True)
