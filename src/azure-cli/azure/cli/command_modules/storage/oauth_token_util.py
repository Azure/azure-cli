# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from knack.log import get_logger

logger = get_logger(__name__)


class TokenUpdater:
    """
    This class updates a given token_credential periodically using the provided callback function.
    It shows one way of making sure the credential does not become expired.
    """
    def __init__(self, token_credential, cli_ctx):
        self.token_credential = token_credential
        self.cli_ctx = cli_ctx

        # the timer needs to be protected, as later on it is possible that one thread is setting a new timer and
        # another thread is trying to cancel the timer
        self.lock = threading.Lock()
        self.timer_callback()

    def timer_callback(self):
        # call to get a new token and set a timer
        from azure.cli.core._profile import Profile
        from datetime import datetime
        # should give back token that is valid for at least 5 mins
        token = Profile(cli_ctx=self.cli_ctx).get_raw_token(
            resource="https://storage.azure.com", subscription=self.cli_ctx.data['subscription_id'])[0][2]
        try:
            self.token_credential.token = token['accessToken']
            expire = token['expiresOn']
            seconds_left = (datetime.strptime(expire, "%Y-%m-%d %H:%M:%S.%f") - datetime.now()).total_seconds()
        except KeyError:  # needed to deal with differing unserialized MSI token payload
            self.token_credential.token = token['access_token']
            expire = datetime.fromtimestamp(int(token['expires_on']))
            seconds_left = (expire - datetime.now()).total_seconds()

        if seconds_left < 180:
            logger.warning("Acquired token will expire on %s. Current time is %s.", expire, datetime.now())

        with self.lock:
            self.timer = threading.Timer(seconds_left - 180, self.timer_callback)
            self.timer.daemon = True
            self.timer.start()

    def cancel(self):
        # the timer needs to be canceled once the command has finished executing
        # if not the timer will keep going
        with self.lock:
            self.timer.cancel()
