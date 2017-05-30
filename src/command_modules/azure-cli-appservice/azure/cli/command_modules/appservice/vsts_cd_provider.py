# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from sys import stderr
from vsts_cd_manager.continuous_delivery_manager import ContinuousDeliveryManager
from azure.cli.core._profile import Profile


class VstsContinuousDeliveryProvider(object):
    def __init__(self):
        self._progress_last_message = ''

    def setup_continuous_delivery(self,
                                  resource_group_name, name, repo_url, branch, git_token,
                                  slot, cd_app_type, cd_account, cd_create_account, location):
        """
        This method sets up CD for an Azure Web App thru Team Services
        """

        # Gather information about the Azure connection
        profile = Profile()
        subscription = profile.get_subscription()
        user = profile.get_current_account_user()
        cred, _, _ = profile.get_login_credentials(subscription_id=None)

        cd_manager = ContinuousDeliveryManager(self._update_progress)

        # Generate an Azure token with the VSTS resource app id
        auth_token = profile.get_access_token_for_resource(user, None, cd_manager.get_vsts_app_id())

        cd_manager.set_repository_info(repo_url, branch, git_token)
        cd_manager.set_azure_web_info(resource_group_name, name, cred, subscription['id'],
                                      subscription['name'], subscription['tenantId'], location)
        vsts_cd_status = cd_manager.setup_continuous_delivery(slot, cd_app_type, cd_account,
                                                              cd_create_account, auth_token)
        return vsts_cd_status

    def remove_continuous_delivery(self):  # pylint: disable=no-self-use
        """
        To be Implemented
        """
        # TODO: this would be called by appservice web source-control delete
        pass

    def _update_progress(self, current, total, status):
        if total:
            percent_done = current * 100 / total
            message = '{: >3.0f}% complete: {}'.format(percent_done, status)
            # Erase the previous message
            # (backspace to beginning, space over the text and backspace again)
            l = len(self._progress_last_message)
            print('\b' * l + ' ' * l + '\b' * l, end='', file=stderr)
            print(message, end='', file=stderr)
            self._progress_last_message = message
            stderr.flush()
            if current == total:
                print('', file=stderr)
