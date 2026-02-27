# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from azure.cli.core.azclierror import CLIError


# pylint:disable=protected-access
# pylint:disable=too-few-public-methods
class AROPlatformWorkloadIdentityAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.redhatopenshift.models import PlatformWorkloadIdentity
        try:
            if len(values) != 2:
                msg = f"{option_string} requires 2 values in format: `OPERATOR_NAME RESOURCE_ID`"
                raise argparse.ArgumentError(self, msg)

            operator_name, resource_id = values
            parsed = (operator_name, PlatformWorkloadIdentity(resource_id=resource_id))

            super().__call__(parser, namespace, parsed, option_string)

        except ValueError as e:
            raise CLIError(f"usage error: {option_string} NAME ID") from e
