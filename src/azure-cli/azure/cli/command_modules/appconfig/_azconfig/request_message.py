# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods


class RequestMessage(object):

    def __init__(self, method, headers, url, body):
        self.method = method
        self.headers = headers
        self.url = url
        self.body = body
