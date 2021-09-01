# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.botservice.models import CheckNameAvailabilityRequestBody

class NameAvailability:
    @staticmethod
    def check_name_availability(client, resource_name, bot_type):
        _request_body = CheckNameAvailabilityRequestBody(
            name = resource_name,
            type = bot_type);
        return client.bots.get_check_name_availability(_request_body)

    @staticmethod
    def check_enterprise_channel_name_availability(client, channel_name):
        return client.enterprise_channels.check_name_availability(channel_name)
