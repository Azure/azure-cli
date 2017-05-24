# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.cognitiveservices.models import CognitiveServicesAccountCreateParameters, Sku
from azure.cli.core.prompting import prompt_y_n
from azure.cli.core.util import CLIError

import azure.cli.core.azlogging as azlogging
logger = azlogging.get_az_logger(__name__)


def listresources(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def create(
        client, resource_group_name, account_name, sku_name, kind, location, tags=None, yes=None):

    terms = 'Notice\nMicrosoft will use data you send to the Cognitive'\
        'Services to improve Microsoft products and services.'\
        'Where you send personal data to the Cognitive Services, you are responsible '\
        'for obtaining sufficient consent from the data subjects.'\
        'The General Privacy and Security Terms in the Online Services Terms '\
        'do not apply to the Cognitive Services.'\
        'Please refer to the Microsoft Cognitive Services section in the Online '\
        'Services Terms'\
        ' (https://www.microsoft.com/en-us/Licensing/product-licensing/products.aspx)'\
        ' for details.'\
        'Microsoft offers policy controls that may be used to disable new Cognitive'\
        ' Services deployments (https://docs.microsoft.com/en-us/azure/cognitive-servic'\
        'es/cognitive-services-apis-create-account).'
    hint = '\nPlease select'
    if yes:
        logger.warning(terms)
    else:
        logger.warning(terms)
        option = prompt_y_n(hint)
        if not option:
            raise CLIError('Operation cancelled.')
    sku = Sku(sku_name)
    properties = {}
    params = CognitiveServicesAccountCreateParameters(sku, kind, location, properties, tags)
    return client.create(resource_group_name, account_name, params)


def update(client, resource_group_name, account_name, sku_name=None, tags=None):
    sku = Sku(sku_name)
    return client.update(resource_group_name, account_name, sku, tags)
