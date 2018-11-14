# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.mgmt.botservice.models import (
    ConnectionSetting,
    ConnectionSettingProperties,
    ConnectionSettingParameter)

# TODO: Not yet wired up to commands.py
class BotConnectionsManager:
    @staticmethod
    def create_connection(client, resource_group_name, resource_name, connection_name, client_id,
                          client_secret, scopes, service_provider_name, parameters=None):
        service_provider = BotConnectionsManager.get_service_providers(client, name=service_provider_name)
        if not service_provider:
            raise CLIError(
                'Invalid Service Provider Name passed. Use listprovider command to see all available providers')
        connection_parameters = []
        if parameters:
            for parameter in parameters:
                pair = parameter.split('=', 1)
                if len(pair) == 1:
                    raise CLIError('usage error: --parameters STRING=STRING STRING=STRING')
                connection_parameters.append(ConnectionSettingParameter(key=pair[0], value=pair[1]))
        setting = ConnectionSetting(
            location='global',
            properties=ConnectionSettingProperties(
                client_id=client_id,
                client_secret=client_secret,
                scopes=scopes,
                service_provider_id=service_provider.properties.id,
                parameters=connection_parameters
            )
        )
        return client.bot_connection.create(resource_group_name, resource_name, connection_name, setting)

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

