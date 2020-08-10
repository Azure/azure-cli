# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataProviderResult(Model):
    """DataProviderResult.

    :param client_providers: This is the set of data providers that were requested, but either they were defined as client providers, or as remote providers that failed and may be retried by the client.
    :type client_providers: dict
    :param data: Property bag of data keyed off of the data provider contribution id
    :type data: dict
    :param exceptions: Set of exceptions that occurred resolving the data providers.
    :type exceptions: dict
    :param resolved_providers: List of data providers resolved in the data-provider query
    :type resolved_providers: list of :class:`ResolvedDataProvider <contributions.v4_1.models.ResolvedDataProvider>`
    :param scope_name: Scope name applied to this data provider result.
    :type scope_name: str
    :param scope_value: Scope value applied to this data provider result.
    :type scope_value: str
    :param shared_data: Property bag of shared data that was contributed to by any of the individual data providers
    :type shared_data: dict
    """

    _attribute_map = {
        'client_providers': {'key': 'clientProviders', 'type': '{ClientDataProviderQuery}'},
        'data': {'key': 'data', 'type': '{object}'},
        'exceptions': {'key': 'exceptions', 'type': '{DataProviderExceptionDetails}'},
        'resolved_providers': {'key': 'resolvedProviders', 'type': '[ResolvedDataProvider]'},
        'scope_name': {'key': 'scopeName', 'type': 'str'},
        'scope_value': {'key': 'scopeValue', 'type': 'str'},
        'shared_data': {'key': 'sharedData', 'type': '{object}'}
    }

    def __init__(self, client_providers=None, data=None, exceptions=None, resolved_providers=None, scope_name=None, scope_value=None, shared_data=None):
        super(DataProviderResult, self).__init__()
        self.client_providers = client_providers
        self.data = data
        self.exceptions = exceptions
        self.resolved_providers = resolved_providers
        self.scope_name = scope_name
        self.scope_value = scope_value
        self.shared_data = shared_data
