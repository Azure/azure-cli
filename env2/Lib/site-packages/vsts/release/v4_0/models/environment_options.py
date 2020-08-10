# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EnvironmentOptions(Model):
    """EnvironmentOptions.

    :param email_notification_type:
    :type email_notification_type: str
    :param email_recipients:
    :type email_recipients: str
    :param enable_access_token:
    :type enable_access_token: bool
    :param publish_deployment_status:
    :type publish_deployment_status: bool
    :param skip_artifacts_download:
    :type skip_artifacts_download: bool
    :param timeout_in_minutes:
    :type timeout_in_minutes: int
    """

    _attribute_map = {
        'email_notification_type': {'key': 'emailNotificationType', 'type': 'str'},
        'email_recipients': {'key': 'emailRecipients', 'type': 'str'},
        'enable_access_token': {'key': 'enableAccessToken', 'type': 'bool'},
        'publish_deployment_status': {'key': 'publishDeploymentStatus', 'type': 'bool'},
        'skip_artifacts_download': {'key': 'skipArtifactsDownload', 'type': 'bool'},
        'timeout_in_minutes': {'key': 'timeoutInMinutes', 'type': 'int'}
    }

    def __init__(self, email_notification_type=None, email_recipients=None, enable_access_token=None, publish_deployment_status=None, skip_artifacts_download=None, timeout_in_minutes=None):
        super(EnvironmentOptions, self).__init__()
        self.email_notification_type = email_notification_type
        self.email_recipients = email_recipients
        self.enable_access_token = enable_access_token
        self.publish_deployment_status = publish_deployment_status
        self.skip_artifacts_download = skip_artifacts_download
        self.timeout_in_minutes = timeout_in_minutes
