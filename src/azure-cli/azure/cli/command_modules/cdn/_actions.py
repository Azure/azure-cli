# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse


# pylint:disable=protected-access
# pylint:disable=too-few-public-methods
class OriginType(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        deep_created_origin = self.get_origin(values, option_string)
        super().__call__(parser, namespace, deep_created_origin, option_string)

    def get_origin(self, values, option_string):
        from azure.mgmt.cdn.models import DeepCreatedOrigin

        if not 1 <= len(values) <= 3 and not 5 <= len(values) <= 6:
            msg = '%s takes 1, 2, 3, 5, or 6 values, %d given'
            raise argparse.ArgumentError(
                self, msg % (option_string, len(values)))

        deep_created_origin = DeepCreatedOrigin(
            name='origin',
            host_name=values[0],
            http_port=80,
            https_port=443)

        if len(values) > 1:
            deep_created_origin.http_port = int(values[1])
        if len(values) > 2:
            deep_created_origin.https_port = int(values[2])
        if len(values) > 4:
            deep_created_origin.private_link_resource_id = values[3]
            deep_created_origin.private_link_location = values[4]
        if len(values) > 5:
            deep_created_origin.private_link_approval_message = values[5]
        return deep_created_origin
