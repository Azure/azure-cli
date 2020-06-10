# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=all
from antlr4 import *

# This class defines a complete listener for a parse tree produced by MetricAlertConditionParser.
class MetricAlertConditionListener(ParseTreeListener):

    # Enter a parse tree produced by MetricAlertConditionParser#expression.
    def enterExpression(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#expression.
    def exitExpression(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#aggregation.
    def enterAggregation(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#aggregation.
    def exitAggregation(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#namespace.
    def enterNamespace(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#namespace.
    def exitNamespace(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#metric.
    def enterMetric(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#metric.
    def exitMetric(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#operator.
    def enterOperator(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#operator.
    def exitOperator(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#threshold.
    def enterThreshold(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#threshold.
    def exitThreshold(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#where.
    def enterWhere(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#where.
    def exitWhere(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dimensions.
    def enterDimensions(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dimensions.
    def exitDimensions(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dimension.
    def enterDimension(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dimension.
    def exitDimension(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_separator.
    def enterDim_separator(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_separator.
    def exitDim_separator(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_operator.
    def enterDim_operator(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_operator.
    def exitDim_operator(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_val_separator.
    def enterDim_val_separator(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_val_separator.
    def exitDim_val_separator(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_name.
    def enterDim_name(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_name.
    def exitDim_name(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_values.
    def enterDim_values(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_values.
    def exitDim_values(self, ctx):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_value.
    def enterDim_value(self, ctx):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_value.
    def exitDim_value(self, ctx):
        pass


