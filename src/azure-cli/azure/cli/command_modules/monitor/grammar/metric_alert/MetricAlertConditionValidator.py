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
    '<=': 'LessThanOrEqual',
    '><': 'GreaterOrLessThan'
}

agg_conversion = {
    'avg': 'Average',
    'min': 'Minimum',
    'max': 'Maximum',
    'total': 'Total',
    'count': 'Count'
}

sens_conversion = {
    'low': 'Low',
    'medium': 'Medium',
    'high': 'High',
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
        self.parameters['operator'] = op_conversion[ctx.getText().strip()]

    # Exit a parse tree produced by MetricAlertConditionParser#threshold.
    def exitThreshold(self, ctx):
        self.parameters['threshold'] = ctx.getText().strip()

    def exitDynamic(self, ctx):
        self.parameters['failing_periods'] = {}

    def exitDyn_sensitivity(self, ctx):
        sensitivity = sens_conversion[ctx.getText().strip().lower()]
        self.parameters['alert_sensitivity'] = sensitivity

    def exitDyn_violations(self, ctx):
        min_failing_periods_to_alert = float(ctx.getText().strip())
        if min_failing_periods_to_alert < 1 or min_failing_periods_to_alert > 6:
            message = "Violations {} should be 1-6."
            raise ValueError(message.format(min_failing_periods_to_alert))
        self.parameters['failing_periods']['min_failing_periods_to_alert'] = min_failing_periods_to_alert

    def exitDyn_windows(self, ctx):
        number_of_evaluation_periods = float(ctx.getText().strip())
        min_failing_periods_to_alert = self.parameters['failing_periods']['min_failing_periods_to_alert']
        if number_of_evaluation_periods < 1 or number_of_evaluation_periods > 6:
            message = "Windows {} should be 1-6."
            raise ValueError(message.format(number_of_evaluation_periods))
        if min_failing_periods_to_alert > number_of_evaluation_periods:
            message = "Violations {} should be smaller or equal to windows {}."
            raise ValueError(message.format(min_failing_periods_to_alert, number_of_evaluation_periods))
        self.parameters['failing_periods']['number_of_evaluation_periods'] = number_of_evaluation_periods

    def exitDyn_datetime(self, ctx):
        from msrest.serialization import Deserializer
        from msrest.exceptions import DeserializationError
        datetime_str = ctx.getText().strip()
        try:
            self.parameters['ignore_data_before'] = Deserializer.deserialize_iso(datetime_str)
        except DeserializationError:
            message = "Datetime {} is not a valid ISO-8601 format"
            raise ValueError(message.format(datetime_str))

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

    # Exit a parse tree produced by MetricAlertConditionParser#option.
    def exitOption(self, ctx):
        if ctx.getText().strip().lower() == 'skipmetricvalidation':
            self.parameters['skip_metric_validation'] = True

    def result(self):
        from azure.mgmt.monitor.models import MetricCriteria, MetricDimension, DynamicMetricCriteria, \
            DynamicThresholdFailingPeriods
        dim_params = self.parameters.get('dimensions', [])
        dimensions = []
        for dim in dim_params:
            dimensions.append(MetricDimension(**dim))
        self.parameters['dimensions'] = dimensions
        self.parameters['name'] = ''  # will be auto-populated later

        if 'failing_periods' in self.parameters:
            # dynamic metric criteria
            failing_periods = DynamicThresholdFailingPeriods(**self.parameters['failing_periods'])
            self.parameters['failing_periods'] = failing_periods
            return DynamicMetricCriteria(**self.parameters)

        # static metric criteria
        return MetricCriteria(**self.parameters)
