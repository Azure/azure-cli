# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements


def load_arguments(self, _):

    with self.argument_context("billing invoice") as c:
        c.argument(
            "account_name", help="The ID that uniquely identifies a billing account"
        )
        c.argument("invoice_name", help="The ID that uniquely identifies an invoice")
        c.argument(
            "download_token",
            help="The download token with document source and document ID",
        )
        c.argument("download_urls", help="Space-separated list of download urls for individual")
