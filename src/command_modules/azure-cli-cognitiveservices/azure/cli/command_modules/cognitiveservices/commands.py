# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command

from azure.cli.command_modules.cognitiveservices._client_factory import cognitiveservices_client_factory, cognitiveservices_account_client_factory

mgmt_path = 'azure.mgmt.cognitiveservices.operations.cognitive_services_accounts_operations#CognitiveServicesAccountsOperations.'
custom_path = 'azure.cli.command_modules.cognitiveservices.custom#'

terms = 'Microsoft may use data you send to the Cognitive Services to improve Microsoft products and services. For example we may use content that you provide to the Cognitive Services to improve our underlying algorithms and models over time. Where you send personal data to the Cognitive Services, you are responsible for obtaining sufficient consent from the data subjects. The General Privacy and Security Terms in the Online Services Terms (https://www.microsoft.com/en-us/Licensing/product-licensing/products.aspx) do not apply to the Cognitive Services. You must comply with use and display requirements for the Bing Search APIs. \nPlease refer to the Microsoft Cognitive Services section in the Online Services Terms for details.'

cli_command(__name__, 'cognitiveservices account create', custom_path + 'create', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account delete', mgmt_path + 'delete', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account show',  mgmt_path + 'get_properties', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices list',  custom_path + 'list', cognitiveservices_account_client_factory)
cli_command(__name__, 'cognitiveservices account update', custom_path + 'update', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account keys regenerate', mgmt_path + 'regenerate_key', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account keys list', mgmt_path + 'list_keys', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account list-skus', mgmt_path + 'list_skus', cognitiveservices_client_factory)
#cli_command(__name__, 'cognitiveservices checkskuavailability', custom_path + 'checkskuavailability')


