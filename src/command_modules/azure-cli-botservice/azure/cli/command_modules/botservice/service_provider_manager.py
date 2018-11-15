# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


class ServiceProviderManager:
    @staticmethod
    def get_service_providers(client, name=None):
        service_provider_response = client.bot_connection.list_service_providers()
        name = name and name.lower()
        if name:
            try:
                return next((item for item in service_provider_response.value if
                             item.properties.service_provider_name.lower() == name.lower()))
            except StopIteration:
                raise CLIError('A service provider with the name {0} was not found'.format(name))
        return service_provider_response

