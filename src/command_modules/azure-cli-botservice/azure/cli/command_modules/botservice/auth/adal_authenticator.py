# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import adal
from knack.log import get_logger

logger = get_logger(__name__)


class AdalAuthenticator:  # pylint:disable=too-few-public-methods

    bot_first_party_app_id = 'f3723d34-6ff5-4ceb-a148-d99dcd2511fc'
    aad_client_id = '1950a258-227b-4e31-a9cf-717495945fc2'
    login_url = 'https://login.windows.net/common'

    @staticmethod
    def acquire_token():

        # Create ADAL Authentication Context to acquire tokens
        context = adal.AuthenticationContext(
            authority=AdalAuthenticator.login_url,
            validate_authority=True,
            api_version=None
        )

        # Acquire a device code
        code = context.acquire_user_code(
            resource=AdalAuthenticator.bot_first_party_app_id,
            client_id=AdalAuthenticator.aad_client_id,
        )

        # Request the user to perform device login
        logger.warning(code['message'])

        # Use the device code to retrieve a token
        token = context.acquire_token_with_device_code(
            resource=AdalAuthenticator.bot_first_party_app_id,
            user_code_info=code,
            client_id=AdalAuthenticator.aad_client_id
        )

        # Return the entire token object including the access token plus expiration date and other info
        return token
