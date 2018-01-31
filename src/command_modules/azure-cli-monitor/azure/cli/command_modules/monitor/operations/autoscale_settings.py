# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def scaffold_autoscale_settings_parameters(client):  # pylint: disable=unused-argument
    """Scaffold fully formed autoscale-settings' parameters as json template """

    import os.path
    from knack.util import CLIError
    from azure.cli.core.util import get_file_json

    # Autoscale settings parameter scaffold file path
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    autoscale_settings_parameter_file_path = os.path.join(
        curr_dir, 'autoscale-parameters-template.json')

    if not os.path.exists(autoscale_settings_parameter_file_path):
        raise CLIError('File {} not found.'.format(autoscale_settings_parameter_file_path))

    return get_file_json(autoscale_settings_parameter_file_path)
