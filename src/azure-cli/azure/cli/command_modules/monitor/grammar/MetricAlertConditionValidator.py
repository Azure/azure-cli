# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .MetricAlertConditionListener import MetricAlertConditionListener


op_conversion = {
    '=': 'Equals',
    '!=': 'NotEquals',
    '>': 'GreaterThan',
    '>=': 'GreaterThanOrEqual',
    '<': 'LessThan',
    '<=': 'LessThanOrEqual'
}

agg_conversion = {
    'avg': 'Average',
    'min': 'Minimum',
    'max': 'Maximum',
    'total': 'Total',
    'count': 'Count'
}

dim_op_conversion = {
    'includes': 'Include',
    'excludes': 'Exclude'
}

# This class defines a complete listener for a parse tree produced by MetricAlertConditionParser.
class MetricAlertConditionValidator(MetricAlertConditionListener):

    def __init__(self):
        super(MetricAlertConditionValidator, self).__init__()
        self.parameters = {}
        self._dimension_index = 0

    # Exit a parse tree produced by MetricAlertConditionParser#aggregation.
    def exitAggregation(self, ctx):
        aggregation = agg_conversion[ctx.getText().strip()]
        self.parameters['time_aggregation'] = aggregation

    # Exit a parse tree produced by MetricAlertConditionParser#namespace.
    def exitNamespace(self, ctx):
        self.parameters['metric_namespace'] = ctx.getText().strip()

    # Exit a parse tree produced by MetricAlertConditionParser#metric.
    def exitMetric(self, ctx):
        self.parameters['metric_name'] = ctx.getText().strip()

    # Exit a parse tree produced by MetricAlertConditionParser#operator.
    def exitOperator(self, ctx):
        operator = op_conversion[ctx.getText().strip()]
        self.parameters['operator'] = operator

    # Exit a parse tree produced by MetricAlertConditionParser#threshold.
    def exitThreshold(self, ctx):
        self.parameters['threshold'] = ctx.getText().strip()

    # Enter a parse tree produced by MetricAlertConditionParser#dimensions.
    def enterDimensions(self, ctx):
        self.parameters['dimensions'] = []

    # Enter a parse tree produced by MetricAlertConditionParser#dimension.
    def enterDimension(self, ctx):
        self.parameters['dimensions'].append({})

    # Exit a parse tree produced by MetricAlertConditionParser#dimension.
    def exitDimension(self, ctx):
        self._dimension_index = self._dimension_index + 1

    # Exit a parse tree produced by MetricAlertConditionParser#dname.
    def exitDim_name(self, ctx):
        self.parameters['dimensions'][self._dimension_index]['name'] = ctx.getText().strip()

    # Exit a parse tree produced by MetricAlertConditionParser#dop.
    def exitDim_operator(self, ctx):
        op_text = ctx.getText().strip()
        self.parameters['dimensions'][self._dimension_index]['operator'] = dim_op_conversion[op_text.lower()]

    # Exit a parse tree produced by MetricAlertConditionParser#dvalues.
    def exitDim_values(self, ctx):
        dvalues = ctx.getText().strip().split(' ')
        self.parameters['dimensions'][self._dimension_index]['values'] = [x for x in dvalues if x not in ['', 'or']]

    def result(self):
        from azure.mgmt.monitor.models import MetricCriteria, MetricDimension
        dim_params = self.parameters.get('dimensions', [])
        dimensions = []
        for dim in dim_params:
            dimensions.append(MetricDimension(**dim))
        self.parameters['dimensions'] = dimensions
        self.parameters['name'] = ''  # will be auto-populated later
        return MetricCriteria(**self.parameters)
