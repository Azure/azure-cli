# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core.exceptions import HttpResponseError
from ._constants import StatusCodes


class BadSnapshotRequestException(HttpResponseError):
    def __init__(self, *args, **kwargs):
        super(BadSnapshotRequestException, self).__init__(*args, **kwargs)

    def __str__(self):
        try:
            if self.status_code == StatusCodes.BAD_REQUEST:
                json_response = self.response.json()
                error_msg = ""
                title = json_response.get("title", None)
                error_msg += "{}.".format(title) if title else ""
                error_msg += json_response.get("detail", "")

                if error_msg:
                    return error_msg

            return super().__str__()
        except Exception:  # pylint: disable=broad-except
            return super().__str__()
