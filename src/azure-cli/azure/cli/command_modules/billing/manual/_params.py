# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from ..action import AddSoldTo


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
        c.argument(
            "download_urls", help="Space-separated list of download urls for individual"
        )

    with self.argument_context("billing invoice show") as c:
        c.argument(
            "account_name",
            type=str,
            help="The ID that uniquely identifies a billing account.",
        )
        c.argument(
            "invoice_name",
            options_list=["--name", "-n", "--invoice-name"],
            type=str,
            help="The ID that " "uniquely identifies an invoice.",
        )
        c.argument(
            "by_subscription",
            action="store_true",
            help="When provided, it must work with --invoice-name to get an invoice by subscription ID and invoice ID",
        )

    with self.argument_context("billing policy") as c:
        c.argument(
            "account_name", help="The ID that uniquely identifies a billing account"
        )
        c.argument(
            "profile_name",
            type=str,
            help="The ID that uniquely identifies a billing profile.",
        )
        c.argument("customer_name", help="The ID that uniquely identifies a customer")

    with self.argument_context('billing profile create') as c:
        c.argument('bill_to', action=AddSoldTo, nargs='*', help='Billing address.')

    with self.argument_context('billing profile update') as c:
        c.argument('bill_to', action=AddSoldTo, nargs='*', help='Billing address.')

    with self.argument_context('billing role-assignment') as c:
        c.argument('account_name', type=str, help='The ID that uniquely identifies a billing account.')
        c.argument('name', options_list=['--name', '-n'], type=str, help='The ID that uniquely identifies a role '
                   'assignment.')
        c.argument('profile_name', type=str, help='The ID that uniquely identifies a billing profile.')
        c.argument('invoice_section_name', type=str, help='The ID that uniquely identifies an invoice section.')
