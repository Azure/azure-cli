# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.operations.latest.network.dns.record_set._base import RecordSetCreate


class RecordSetSOACreate(RecordSetCreate):
    """Internal command for updating SOA record sets via PUT.

    SOA record sets are created automatically with the DNS zone and cannot be
    created independently.  This class is used only by _add_save_record in
    custom.py to persist SOA record changes through the create-or-update
    (PUT) API.
    """

    def pre_operations(self):
        args = self.ctx.args
        args.record_type = "SOA"
        args.name = "@"
