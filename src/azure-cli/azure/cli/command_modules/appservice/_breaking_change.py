# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (register_output_breaking_change,
                                            register_argument_deprecate)

# az webapp list-runtimes output format change
register_output_breaking_change(
    'webapp list-runtimes',
    description='The output will change from a flat list of strings to a structured list of objects '
                'with keys: os, runtime, version, config, support, end_of_life.',
    guide='Update scripts that parse the current string-list output. The new output is a list of '
          'dicts with keys: os, runtime, version, config, support, end_of_life. '
          'New --runtime and --support filter parameters will be added. '
          'Use -o table for a human-readable view, or -o json and parse the new structured format.')

# az webapp list-runtimes --linux removal
register_argument_deprecate('webapp list-runtimes', '--linux', redirect='--os-type')

# az webapp list-runtimes --show-runtime-details removal
register_argument_deprecate('webapp list-runtimes', '--show-runtime-details')
