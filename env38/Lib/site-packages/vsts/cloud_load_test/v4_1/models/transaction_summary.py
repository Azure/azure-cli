# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TransactionSummary(Model):
    """TransactionSummary.

    :param average_response_time:
    :type average_response_time: float
    :param average_transaction_time:
    :type average_transaction_time: float
    :param percentile_data:
    :type percentile_data: list of :class:`SummaryPercentileData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.SummaryPercentileData>`
    :param scenario_name:
    :type scenario_name: str
    :param test_name:
    :type test_name: str
    :param total_transactions:
    :type total_transactions: int
    :param transaction_name:
    :type transaction_name: str
    """

    _attribute_map = {
        'average_response_time': {'key': 'averageResponseTime', 'type': 'float'},
        'average_transaction_time': {'key': 'averageTransactionTime', 'type': 'float'},
        'percentile_data': {'key': 'percentileData', 'type': '[SummaryPercentileData]'},
        'scenario_name': {'key': 'scenarioName', 'type': 'str'},
        'test_name': {'key': 'testName', 'type': 'str'},
        'total_transactions': {'key': 'totalTransactions', 'type': 'int'},
        'transaction_name': {'key': 'transactionName', 'type': 'str'}
    }

    def __init__(self, average_response_time=None, average_transaction_time=None, percentile_data=None, scenario_name=None, test_name=None, total_transactions=None, transaction_name=None):
        super(TransactionSummary, self).__init__()
        self.average_response_time = average_response_time
        self.average_transaction_time = average_transaction_time
        self.percentile_data = percentile_data
        self.scenario_name = scenario_name
        self.test_name = test_name
        self.total_transactions = total_transactions
        self.transaction_name = transaction_name
