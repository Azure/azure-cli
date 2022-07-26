# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from AutoscaleCondition.g4 by ANTLR 4.9.3
# encoding: utf-8
# pylint: disable=all
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .MetricAlertConditionParser import MetricAlertConditionParser
else:
    from MetricAlertConditionParser import MetricAlertConditionParser

# This class defines a complete listener for a parse tree produced by MetricAlertConditionParser.
class MetricAlertConditionListener(ParseTreeListener):

    # Enter a parse tree produced by MetricAlertConditionParser#expression.
    def enterExpression(self, ctx:MetricAlertConditionParser.ExpressionContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#expression.
    def exitExpression(self, ctx:MetricAlertConditionParser.ExpressionContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#aggregation.
    def enterAggregation(self, ctx:MetricAlertConditionParser.AggregationContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#aggregation.
    def exitAggregation(self, ctx:MetricAlertConditionParser.AggregationContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#namespace.
    def enterNamespace(self, ctx:MetricAlertConditionParser.NamespaceContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#namespace.
    def exitNamespace(self, ctx:MetricAlertConditionParser.NamespaceContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#metric.
    def enterMetric(self, ctx:MetricAlertConditionParser.MetricContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#metric.
    def exitMetric(self, ctx:MetricAlertConditionParser.MetricContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#operator.
    def enterOperator(self, ctx:MetricAlertConditionParser.OperatorContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#operator.
    def exitOperator(self, ctx:MetricAlertConditionParser.OperatorContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#threshold.
    def enterThreshold(self, ctx:MetricAlertConditionParser.ThresholdContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#threshold.
    def exitThreshold(self, ctx:MetricAlertConditionParser.ThresholdContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dynamic.
    def enterDynamic(self, ctx:MetricAlertConditionParser.DynamicContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dynamic.
    def exitDynamic(self, ctx:MetricAlertConditionParser.DynamicContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dynamics.
    def enterDynamics(self, ctx:MetricAlertConditionParser.DynamicsContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dynamics.
    def exitDynamics(self, ctx:MetricAlertConditionParser.DynamicsContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dyn_sensitivity.
    def enterDyn_sensitivity(self, ctx:MetricAlertConditionParser.Dyn_sensitivityContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dyn_sensitivity.
    def exitDyn_sensitivity(self, ctx:MetricAlertConditionParser.Dyn_sensitivityContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dyn_violations.
    def enterDyn_violations(self, ctx:MetricAlertConditionParser.Dyn_violationsContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dyn_violations.
    def exitDyn_violations(self, ctx:MetricAlertConditionParser.Dyn_violationsContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dyn_of_separator.
    def enterDyn_of_separator(self, ctx:MetricAlertConditionParser.Dyn_of_separatorContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dyn_of_separator.
    def exitDyn_of_separator(self, ctx:MetricAlertConditionParser.Dyn_of_separatorContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dyn_windows.
    def enterDyn_windows(self, ctx:MetricAlertConditionParser.Dyn_windowsContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dyn_windows.
    def exitDyn_windows(self, ctx:MetricAlertConditionParser.Dyn_windowsContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dyn_since_seperator.
    def enterDyn_since_seperator(self, ctx:MetricAlertConditionParser.Dyn_since_seperatorContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dyn_since_seperator.
    def exitDyn_since_seperator(self, ctx:MetricAlertConditionParser.Dyn_since_seperatorContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dyn_datetime.
    def enterDyn_datetime(self, ctx:MetricAlertConditionParser.Dyn_datetimeContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dyn_datetime.
    def exitDyn_datetime(self, ctx:MetricAlertConditionParser.Dyn_datetimeContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#where.
    def enterWhere(self, ctx:MetricAlertConditionParser.WhereContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#where.
    def exitWhere(self, ctx:MetricAlertConditionParser.WhereContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dimensions.
    def enterDimensions(self, ctx:MetricAlertConditionParser.DimensionsContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dimensions.
    def exitDimensions(self, ctx:MetricAlertConditionParser.DimensionsContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dimension.
    def enterDimension(self, ctx:MetricAlertConditionParser.DimensionContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dimension.
    def exitDimension(self, ctx:MetricAlertConditionParser.DimensionContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_separator.
    def enterDim_separator(self, ctx:MetricAlertConditionParser.Dim_separatorContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_separator.
    def exitDim_separator(self, ctx:MetricAlertConditionParser.Dim_separatorContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_operator.
    def enterDim_operator(self, ctx:MetricAlertConditionParser.Dim_operatorContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_operator.
    def exitDim_operator(self, ctx:MetricAlertConditionParser.Dim_operatorContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_val_separator.
    def enterDim_val_separator(self, ctx:MetricAlertConditionParser.Dim_val_separatorContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_val_separator.
    def exitDim_val_separator(self, ctx:MetricAlertConditionParser.Dim_val_separatorContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_name.
    def enterDim_name(self, ctx:MetricAlertConditionParser.Dim_nameContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_name.
    def exitDim_name(self, ctx:MetricAlertConditionParser.Dim_nameContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_values.
    def enterDim_values(self, ctx:MetricAlertConditionParser.Dim_valuesContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_values.
    def exitDim_values(self, ctx:MetricAlertConditionParser.Dim_valuesContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#dim_value.
    def enterDim_value(self, ctx:MetricAlertConditionParser.Dim_valueContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#dim_value.
    def exitDim_value(self, ctx:MetricAlertConditionParser.Dim_valueContext):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#options_.
    def enterOptions_(self, ctx:MetricAlertConditionParser.Options_Context):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#options_.
    def exitOptions_(self, ctx:MetricAlertConditionParser.Options_Context):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#with_.
    def enterWith_(self, ctx:MetricAlertConditionParser.With_Context):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#with_.
    def exitWith_(self, ctx:MetricAlertConditionParser.With_Context):
        pass


    # Enter a parse tree produced by MetricAlertConditionParser#option.
    def enterOption(self, ctx:MetricAlertConditionParser.OptionContext):
        pass

    # Exit a parse tree produced by MetricAlertConditionParser#option.
    def exitOption(self, ctx:MetricAlertConditionParser.OptionContext):
        pass



del MetricAlertConditionParser