# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


class HttpResponseValidator:  # pylint:disable=too-few-public-methods

    @staticmethod
    def check_response_status(response, expected_code=None):
        expected_code = expected_code or 200
        if response.status_code != expected_code:
            raise CLIError('Failed with status code {} and reason {}'.format(
                response.status_code, response.text))
