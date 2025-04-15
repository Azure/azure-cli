# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from AutoscaleCondition.g4 by ANTLR 4.13.1
# pylint: disable=all
from antlr4 import *
if "." in __name__:
    from .AutoscaleConditionParser import AutoscaleConditionParser
else:
    from AutoscaleConditionParser import AutoscaleConditionParser

# This class defines a complete listener for a parse tree produced by AutoscaleConditionParser.
class AutoscaleConditionListener(ParseTreeListener):

    # Enter a parse tree produced by AutoscaleConditionParser#expression.
    def enterExpression(self, ctx:AutoscaleConditionParser.ExpressionContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#expression.
    def exitExpression(self, ctx:AutoscaleConditionParser.ExpressionContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#aggregation.
    def enterAggregation(self, ctx:AutoscaleConditionParser.AggregationContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#aggregation.
    def exitAggregation(self, ctx:AutoscaleConditionParser.AggregationContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#namespace.
    def enterNamespace(self, ctx:AutoscaleConditionParser.NamespaceContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#namespace.
    def exitNamespace(self, ctx:AutoscaleConditionParser.NamespaceContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#metric.
    def enterMetric(self, ctx:AutoscaleConditionParser.MetricContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#metric.
    def exitMetric(self, ctx:AutoscaleConditionParser.MetricContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#operator.
    def enterOperator(self, ctx:AutoscaleConditionParser.OperatorContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#operator.
    def exitOperator(self, ctx:AutoscaleConditionParser.OperatorContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#threshold.
    def enterThreshold(self, ctx:AutoscaleConditionParser.ThresholdContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#threshold.
    def exitThreshold(self, ctx:AutoscaleConditionParser.ThresholdContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#period.
    def enterPeriod(self, ctx:AutoscaleConditionParser.PeriodContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#period.
    def exitPeriod(self, ctx:AutoscaleConditionParser.PeriodContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#where.
    def enterWhere(self, ctx:AutoscaleConditionParser.WhereContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#where.
    def exitWhere(self, ctx:AutoscaleConditionParser.WhereContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dimensions.
    def enterDimensions(self, ctx:AutoscaleConditionParser.DimensionsContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dimensions.
    def exitDimensions(self, ctx:AutoscaleConditionParser.DimensionsContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dimension.
    def enterDimension(self, ctx:AutoscaleConditionParser.DimensionContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dimension.
    def exitDimension(self, ctx:AutoscaleConditionParser.DimensionContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dim_separator.
    def enterDim_separator(self, ctx:AutoscaleConditionParser.Dim_separatorContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dim_separator.
    def exitDim_separator(self, ctx:AutoscaleConditionParser.Dim_separatorContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dim_operator.
    def enterDim_operator(self, ctx:AutoscaleConditionParser.Dim_operatorContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dim_operator.
    def exitDim_operator(self, ctx:AutoscaleConditionParser.Dim_operatorContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dim_val_separator.
    def enterDim_val_separator(self, ctx:AutoscaleConditionParser.Dim_val_separatorContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dim_val_separator.
    def exitDim_val_separator(self, ctx:AutoscaleConditionParser.Dim_val_separatorContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dim_name.
    def enterDim_name(self, ctx:AutoscaleConditionParser.Dim_nameContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dim_name.
    def exitDim_name(self, ctx:AutoscaleConditionParser.Dim_nameContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dim_values.
    def enterDim_values(self, ctx:AutoscaleConditionParser.Dim_valuesContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dim_values.
    def exitDim_values(self, ctx:AutoscaleConditionParser.Dim_valuesContext):
        pass


    # Enter a parse tree produced by AutoscaleConditionParser#dim_value.
    def enterDim_value(self, ctx:AutoscaleConditionParser.Dim_valueContext):
        pass

    # Exit a parse tree produced by AutoscaleConditionParser#dim_value.
    def exitDim_value(self, ctx:AutoscaleConditionParser.Dim_valueContext):
        pass



del AutoscaleConditionParser