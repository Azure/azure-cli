# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from collections import Counter
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.botservice.web_app_operations import WebAppOperations
from azure.cli.command_modules.botservice.kudu_client import KuduClient


class BotJsonFormatter:  # pylint:disable=too-few-public-methods

    @staticmethod
    def create_bot_json(cmd, client, resource_group_name, resource_name, logger, app_password=None,  # pylint:disable=too-many-locals
                        raw_bot_properties=None, password_only=True):
        """

        :param cmd:
        :param client:
        :param resource_group_name:
        :param resource_name:
        :param logger:
        :param app_password:
        :param raw_bot_properties:
        :return: Dictionary
        """
        if not raw_bot_properties:
            raw_bot_properties = client.bots.get(
                resource_group_name=resource_group_name,
                resource_name=resource_name
            )

        # Initialize names bot_file and secret to capture botFilePath and botFileSecret values from the application's
        # settings.
        bot_file = None
        bot_file_secret = None
        profile = Profile(cli_ctx=cmd.cli_ctx)
        if not app_password:
            site_name = WebAppOperations.get_bot_site_name(raw_bot_properties.properties.endpoint)
            app_settings = WebAppOperations.get_app_settings(
                cmd=cmd,
                resource_group_name=resource_group_name,
                name=site_name
            )

            app_password_values = [item['value'] for item in app_settings if item['name'] == 'MicrosoftAppPassword']
            app_password = app_password_values[0] if app_password_values else None
            if not app_password:
                bot_file_values = [item['value'] for item in app_settings if item['name'] == 'botFilePath']
                bot_file = bot_file_values[0] if bot_file_values else None
                bot_file_secret_values = [item['value'] for item in app_settings if item['name'] == 'botFileSecret']
                bot_file_secret = bot_file_secret_values[0] if bot_file_secret_values else None

        if not bot_file and not app_password:
            bot_site_name = WebAppOperations.get_bot_site_name(raw_bot_properties.properties.endpoint)
            scm_url = WebAppOperations.get_scm_url(cmd,
                                                   resource_group_name,
                                                   bot_site_name,
                                                   None)

            # TODO: Reevaluate "Public-or-Gov" Azure logic.
            is_public_azure = ('azurewebsites.net' in raw_bot_properties.properties.endpoint or
                               '.net' in raw_bot_properties.properties.endpoint or
                               '.com' in raw_bot_properties.properties.endpoint)
            host = 'https://portal.azure.com/' if is_public_azure else 'https://portal.azure.us/'
            subscription_id = get_subscription_id(cmd.cli_ctx)
            tenant_id = profile.get_subscription(subscription=client.config.subscription_id)['tenantId']
            settings_url = host + '#@{}/resource/subscriptions/{}/resourceGroups/{}/providers/Microsoft.BotService/botServices/{}/app_settings'.format(tenant_id, subscription_id, resource_group_name, resource_name)  # pylint: disable=line-too-long

            logger.warning('"MicrosoftAppPassword" and "botFilePath" not found in application settings')
            logger.warning('To see your bot\'s application settings, visit %s' % settings_url)
            logger.warning('To visit your deployed bot\'s code on Azure, visit Kudu for your bot at %s' % scm_url)

        elif not app_password and bot_file:
            # We have the information we need to obtain the MSA App app password via bot file data from Kudu.
            kudu_client = KuduClient(cmd, resource_group_name, resource_name, raw_bot_properties, logger)
            bot_file_data = kudu_client.get_bot_file(bot_file)
            app_password = BotJsonFormatter.__decrypt_bot_file(bot_file_data, bot_file_secret, logger, password_only)

        return {
            'type': 'abs',
            'id': raw_bot_properties.name,
            'name': raw_bot_properties.properties.display_name,
            'appId': raw_bot_properties.properties.msa_app_id,
            'appPassword': app_password,
            'endpoint': raw_bot_properties.properties.endpoint,
            'resourceGroup': str(resource_group_name),
            'tenantId': profile.get_subscription(subscription=client._config.subscription_id)['tenantId'],  # pylint:disable=protected-access
            'subscriptionId': client._config.subscription_id,  # pylint:disable=protected-access
            'serviceName': resource_name
        }

    @staticmethod
    def __decrypt_bot_file(bot_file_data, bot_file_secret, logger, password_only=True):
        """Decrypt .bot file retrieved from Kudu.

        :param bot_file_data:
        :param bot_file_secret:
        :param logger:
        :return:
        """
        services = bot_file_data['services']

        decrypt = BotJsonFormatter.__decrypt

        if password_only:
            # Get all endpoints that have potentially valid appPassword values
            endpoints = [service for service in services
                         if service.get('type') == 'endpoint' and service.get('appPassword')]
            # Reduce the retrieved endpoints to just their passwords
            app_passwords = [e['appPassword'] for e in endpoints]

            if len(app_passwords) == 1:
                return decrypt(bot_file_secret, app_passwords[0], logger)
            if len(app_passwords) > 1:
                logger.info('More than one Microsoft App Password found in bot file. Evaluating if more than one '
                            'unique App Password exists.')
                app_passwords = [decrypt(bot_file_secret, pw, logger) for pw in app_passwords]
                unique_passwords = list(Counter(app_passwords))  # pylint:disable=too-many-function-args
                if len(unique_passwords) == 1:
                    logger.info('One unique Microsoft App Password found, returning password.')
                    return unique_passwords[0]

                logger.warning('More than one unique Microsoft App Password found in the bot file, please '
                               'manually retrieve your bot file from Kudu to retrieve this information.')
                logger.warning('No Microsoft App Password returned.')
                return ''

            logger.warning('No Microsoft App Passwords found in bot file.')
            return ''

        for service in services:
            # For Azure Blob Storage
            if service.get('connectionString'):
                service['connectionString'] = decrypt(bot_file_secret, service['connectionString'], logger)
            # For LUIS and Dispatch
            if service.get('authoringKey'):
                service['authoringKey'] = decrypt(bot_file_secret, service['authoringKey'], logger)
            # For LUIS and QnA Maker
            if service.get('subscriptionKey'):
                service['subscriptionKey'] = decrypt(bot_file_secret, service['subscriptionKey'], logger)
            # For QnA Maker
            if service.get('endpointKey'):
                service['endpointKey'] = decrypt(bot_file_secret, service['endpointKey'], logger)
            # For connecting to the bot
            if service.get('appPassword'):
                service['appPassword'] = decrypt(bot_file_secret, service['appPassword'], logger)
            # For Application Insights
            if service.get('instrumentationKey'):
                service['instrumentationKey'] = decrypt(bot_file_secret, service['instrumentationKey'], logger)
            if service.get('apiKeys'):
                for apiKey in service['apiKeys']:
                    service['apiKeys'][apiKey] = decrypt(bot_file_secret, service['apiKeys'][apiKey], logger)
            # For Cosmos DB
            if service.get('key'):
                service['key'] = decrypt(bot_file_secret, service['key'], logger)
            # For generic services
            if service.get('configuration') and isinstance(service.get('configuration'), dict):
                for key in service['configuration']:
                    service['configuration'][key] = decrypt(bot_file_secret, service['configuration'][key], logger)

        return services

    @staticmethod
    def __decrypt(secret, encrypted_value, logger):
        # If the string length is 0 or no secret was passed in, return the empty string.
        if not encrypted_value or not secret:
            return encrypted_value

        parts = encrypted_value.split("!")
        if len(parts) != 2:
            logger.warn('Encrypted value "%s" not in standard encrypted format, decryption skipped.' % encrypted_value)
            return encrypted_value

        iv_text = parts[0]
        encrypted_text = parts[1]
        iv_bytes = base64.standard_b64decode(str.encode(iv_text))
        secret_bytes = base64.standard_b64decode(str.encode(secret))

        if len(iv_bytes) != 16:
            logger.warn('Initialization Vector for "%s" not valid, decryption skipped.' % encrypted_value)
            return encrypted_value
        if len(secret_bytes) != 32:
            logger.warn('Passed in secret length is invalid, decryption skipped.')
            return encrypted_value

        cipher = Cipher(algorithms.AES(secret_bytes), modes.CBC(iv_bytes), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_bytes = decryptor.update(base64.standard_b64decode(str.encode(encrypted_text))) + decryptor.finalize()

        decrypted_string = decrypted_bytes.decode('utf-8')
        return ''.join([char for char in decrypted_string if ord(char) > 31])
