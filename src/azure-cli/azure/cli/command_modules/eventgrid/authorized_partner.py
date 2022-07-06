# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from knack.util import CLIError
from dateutil.parser import parse   # pylint: disable=import-error,relative-import
from azure.mgmt.eventgrid.models import (
    Partner
)

PARTNER_NAME = "partner-name"
PARTNER_ID = "partner-registration-immutable-id"
EXPIRATION_TIME = "expiration-time"

# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddAuthorizedPartner(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        valuesLen = len(values)
        usage_error_msg = "usage error: --authorized-partner [partner-name=<name>] [partner-registration-immutable-id=<id>] [expiration-time=<timestamp>]"
        if valuesLen < 1 or valuesLen > 3:
            raise CLIError(usage_error_msg)

        partner_name = None
        partner_id = None
        expiration_time = None
        for item in values:
            try:
                key, value = item.split('=', 1)
                if key.lower() == PARTNER_NAME:
                    partner_name = value
                elif key.lower() == PARTNER_ID:
                    partner_id = value
                elif key.lower() == EXPIRATION_TIME:
                    expiration_time = value
                else:
                    raise ValueError()
            except ValueError:
                raise CLIError(usage_error_msg)

        if expiration_time is not None:
            expiration_time = parse(expiration_time)

        partner_info = Partner(
            partner_registration_immutable_id=partner_id,
            partner_name=partner_name,
            authorization_expiration_time_in_utc=expiration_time)

        if namespace.authorized_partner is None:
            namespace.authorized_partner = []
        namespace.authorized_partner.append(partner_info)
