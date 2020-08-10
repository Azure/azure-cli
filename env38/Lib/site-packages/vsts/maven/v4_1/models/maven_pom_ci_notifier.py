# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomCiNotifier(Model):
    """MavenPomCiNotifier.

    :param configuration:
    :type configuration: list of str
    :param send_on_error:
    :type send_on_error: str
    :param send_on_failure:
    :type send_on_failure: str
    :param send_on_success:
    :type send_on_success: str
    :param send_on_warning:
    :type send_on_warning: str
    :param type:
    :type type: str
    """

    _attribute_map = {
        'configuration': {'key': 'configuration', 'type': '[str]'},
        'send_on_error': {'key': 'sendOnError', 'type': 'str'},
        'send_on_failure': {'key': 'sendOnFailure', 'type': 'str'},
        'send_on_success': {'key': 'sendOnSuccess', 'type': 'str'},
        'send_on_warning': {'key': 'sendOnWarning', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, configuration=None, send_on_error=None, send_on_failure=None, send_on_success=None, send_on_warning=None, type=None):
        super(MavenPomCiNotifier, self).__init__()
        self.configuration = configuration
        self.send_on_error = send_on_error
        self.send_on_failure = send_on_failure
        self.send_on_success = send_on_success
        self.send_on_warning = send_on_warning
        self.type = type
