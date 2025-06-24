# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from AutoscaleCondition.g4 by ANTLR 4.13.1
# encoding: utf-8
# pylint: disable=all
from antlr4 import *
from io import StringIO
import sys
from typing import TextIO

def serializedATN():
    return [
        4,1,26,127,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,1,0,1,0,1,0,1,0,1,0,5,0,38,8,0,10,0,12,0,41,
        9,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,5,0,52,8,0,10,0,12,0,55,
        9,0,1,0,5,0,58,8,0,10,0,12,0,61,9,0,1,1,1,1,1,1,1,2,4,2,67,8,2,11,
        2,12,2,68,1,3,4,3,72,8,3,11,3,12,3,73,1,4,1,4,1,4,1,5,1,5,1,5,1,
        6,1,6,1,7,1,7,1,7,1,8,1,8,1,8,1,8,1,8,5,8,92,8,8,10,8,12,8,95,9,
        8,1,9,1,9,1,9,1,9,1,10,1,10,1,10,1,11,1,11,1,11,1,12,1,12,1,12,1,
        13,1,13,1,13,1,14,1,14,1,14,1,14,5,14,117,8,14,10,14,12,14,120,9,
        14,1,15,4,15,123,8,15,11,15,12,15,124,1,15,0,0,16,0,2,4,6,8,10,12,
        14,16,18,20,22,24,26,28,30,0,6,3,0,1,9,24,24,26,26,5,0,1,2,4,7,10,
        12,24,24,26,26,2,0,11,11,17,17,1,0,13,14,2,0,11,11,20,20,6,0,2,4,
        6,6,15,15,22,22,24,24,26,26,118,0,39,1,0,0,0,2,62,1,0,0,0,4,66,1,
        0,0,0,6,71,1,0,0,0,8,75,1,0,0,0,10,78,1,0,0,0,12,81,1,0,0,0,14,83,
        1,0,0,0,16,86,1,0,0,0,18,96,1,0,0,0,20,100,1,0,0,0,22,103,1,0,0,
        0,24,106,1,0,0,0,26,109,1,0,0,0,28,112,1,0,0,0,30,122,1,0,0,0,32,
        33,5,23,0,0,33,34,3,4,2,0,34,35,5,23,0,0,35,36,5,24,0,0,36,38,1,
        0,0,0,37,32,1,0,0,0,38,41,1,0,0,0,39,37,1,0,0,0,39,40,1,0,0,0,40,
        42,1,0,0,0,41,39,1,0,0,0,42,43,3,6,3,0,43,44,5,24,0,0,44,45,1,0,
        0,0,45,46,3,8,4,0,46,47,3,10,5,0,47,48,3,2,1,0,48,53,3,12,6,0,49,
        50,5,24,0,0,50,52,3,16,8,0,51,49,1,0,0,0,52,55,1,0,0,0,53,51,1,0,
        0,0,53,54,1,0,0,0,54,59,1,0,0,0,55,53,1,0,0,0,56,58,5,25,0,0,57,
        56,1,0,0,0,58,61,1,0,0,0,59,57,1,0,0,0,59,60,1,0,0,0,60,1,1,0,0,
        0,61,59,1,0,0,0,62,63,5,26,0,0,63,64,5,24,0,0,64,3,1,0,0,0,65,67,
        7,0,0,0,66,65,1,0,0,0,67,68,1,0,0,0,68,66,1,0,0,0,68,69,1,0,0,0,
        69,5,1,0,0,0,70,72,7,1,0,0,71,70,1,0,0,0,72,73,1,0,0,0,73,71,1,0,
        0,0,73,74,1,0,0,0,74,7,1,0,0,0,75,76,5,21,0,0,76,77,5,24,0,0,77,
        9,1,0,0,0,78,79,5,22,0,0,79,80,5,24,0,0,80,11,1,0,0,0,81,82,5,26,
        0,0,82,13,1,0,0,0,83,84,5,16,0,0,84,85,5,24,0,0,85,15,1,0,0,0,86,
        87,3,14,7,0,87,93,3,18,9,0,88,89,3,20,10,0,89,90,3,18,9,0,90,92,
        1,0,0,0,91,88,1,0,0,0,92,95,1,0,0,0,93,91,1,0,0,0,93,94,1,0,0,0,
        94,17,1,0,0,0,95,93,1,0,0,0,96,97,3,26,13,0,97,98,3,22,11,0,98,99,
        3,28,14,0,99,19,1,0,0,0,100,101,7,2,0,0,101,102,5,24,0,0,102,21,
        1,0,0,0,103,104,7,3,0,0,104,105,5,24,0,0,105,23,1,0,0,0,106,107,
        7,4,0,0,107,108,5,24,0,0,108,25,1,0,0,0,109,110,5,26,0,0,110,111,
        5,24,0,0,111,27,1,0,0,0,112,118,3,30,15,0,113,114,3,24,12,0,114,
        115,3,30,15,0,115,117,1,0,0,0,116,113,1,0,0,0,117,120,1,0,0,0,118,
        116,1,0,0,0,118,119,1,0,0,0,119,29,1,0,0,0,120,118,1,0,0,0,121,123,
        7,5,0,0,122,121,1,0,0,0,123,124,1,0,0,0,124,122,1,0,0,0,124,125,
        1,0,0,0,125,31,1,0,0,0,8,39,53,59,68,73,93,118,124
    ]

class AutoscaleConditionParser ( Parser ):

    grammarFileName = "AutoscaleCondition.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'/'", "'.'", "'*'", "'-'", "'_'", "':'", 
                     "'%'", "'#'", "'@'", "'\\'", "','", "'|'", "'=='", 
                     "'!='", "'~'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "WHERE", "AND", "INCLUDES", "EXCLUDES", "OR", "OPERATOR", 
                      "NUMBER", "QUOTE", "WHITESPACE", "NEWLINE", "WORD" ]

    RULE_expression = 0
    RULE_aggregation = 1
    RULE_namespace = 2
    RULE_metric = 3
    RULE_operator = 4
    RULE_threshold = 5
    RULE_period = 6
    RULE_where = 7
    RULE_dimensions = 8
    RULE_dimension = 9
    RULE_dim_separator = 10
    RULE_dim_operator = 11
    RULE_dim_val_separator = 12
    RULE_dim_name = 13
    RULE_dim_values = 14
    RULE_dim_value = 15

    ruleNames =  [ "expression", "aggregation", "namespace", "metric", "operator", 
                   "threshold", "period", "where", "dimensions", "dimension", 
                   "dim_separator", "dim_operator", "dim_val_separator", 
                   "dim_name", "dim_values", "dim_value" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    T__9=10
    T__10=11
    T__11=12
    T__12=13
    T__13=14
    T__14=15
    WHERE=16
    AND=17
    INCLUDES=18
    EXCLUDES=19
    OR=20
    OPERATOR=21
    NUMBER=22
    QUOTE=23
    WHITESPACE=24
    NEWLINE=25
    WORD=26

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def operator(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.OperatorContext,0)


        def threshold(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.ThresholdContext,0)


        def aggregation(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.AggregationContext,0)


        def period(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.PeriodContext,0)


        def metric(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.MetricContext,0)


        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WHITESPACE)
            else:
                return self.getToken(AutoscaleConditionParser.WHITESPACE, i)

        def QUOTE(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.QUOTE)
            else:
                return self.getToken(AutoscaleConditionParser.QUOTE, i)

        def namespace(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(AutoscaleConditionParser.NamespaceContext)
            else:
                return self.getTypedRuleContext(AutoscaleConditionParser.NamespaceContext,i)


        def dimensions(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(AutoscaleConditionParser.DimensionsContext)
            else:
                return self.getTypedRuleContext(AutoscaleConditionParser.DimensionsContext,i)


        def NEWLINE(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.NEWLINE)
            else:
                return self.getToken(AutoscaleConditionParser.NEWLINE, i)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_expression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression" ):
                listener.enterExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression" ):
                listener.exitExpression(self)




    def expression(self):

        localctx = AutoscaleConditionParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_expression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 39
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==23:
                self.state = 32
                self.match(AutoscaleConditionParser.QUOTE)
                self.state = 33
                self.namespace()
                self.state = 34
                self.match(AutoscaleConditionParser.QUOTE)
                self.state = 35
                self.match(AutoscaleConditionParser.WHITESPACE)
                self.state = 41
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 42
            self.metric()
            self.state = 43
            self.match(AutoscaleConditionParser.WHITESPACE)
            self.state = 45
            self.operator()
            self.state = 46
            self.threshold()
            self.state = 47
            self.aggregation()
            self.state = 48
            self.period()
            self.state = 53
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==24:
                self.state = 49
                self.match(AutoscaleConditionParser.WHITESPACE)
                self.state = 50
                self.dimensions()
                self.state = 55
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 59
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==25:
                self.state = 56
                self.match(AutoscaleConditionParser.NEWLINE)
                self.state = 61
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AggregationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORD(self):
            return self.getToken(AutoscaleConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_aggregation

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAggregation" ):
                listener.enterAggregation(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAggregation" ):
                listener.exitAggregation(self)




    def aggregation(self):

        localctx = AutoscaleConditionParser.AggregationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_aggregation)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 62
            self.match(AutoscaleConditionParser.WORD)
            self.state = 63
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NamespaceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WORD)
            else:
                return self.getToken(AutoscaleConditionParser.WORD, i)

        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WHITESPACE)
            else:
                return self.getToken(AutoscaleConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_namespace

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNamespace" ):
                listener.enterNamespace(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNamespace" ):
                listener.exitNamespace(self)




    def namespace(self):

        localctx = AutoscaleConditionParser.NamespaceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_namespace)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 66 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 65
                _la = self._input.LA(1)
                if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 83887102) != 0):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 68 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((_la) & ~0x3f) == 0 and ((1 << _la) & 83887102) != 0):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MetricContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WORD)
            else:
                return self.getToken(AutoscaleConditionParser.WORD, i)

        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WHITESPACE)
            else:
                return self.getToken(AutoscaleConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_metric

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMetric" ):
                listener.enterMetric(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMetric" ):
                listener.exitMetric(self)




    def metric(self):

        localctx = AutoscaleConditionParser.MetricContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_metric)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 71 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 70
                    _la = self._input.LA(1)
                    if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 83893494) != 0):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 73 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,4,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OperatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OPERATOR(self):
            return self.getToken(AutoscaleConditionParser.OPERATOR, 0)

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_operator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOperator" ):
                listener.enterOperator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOperator" ):
                listener.exitOperator(self)




    def operator(self):

        localctx = AutoscaleConditionParser.OperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_operator)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 75
            self.match(AutoscaleConditionParser.OPERATOR)
            self.state = 76
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ThresholdContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(AutoscaleConditionParser.NUMBER, 0)

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_threshold

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterThreshold" ):
                listener.enterThreshold(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitThreshold" ):
                listener.exitThreshold(self)




    def threshold(self):

        localctx = AutoscaleConditionParser.ThresholdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_threshold)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 78
            self.match(AutoscaleConditionParser.NUMBER)
            self.state = 79
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PeriodContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORD(self):
            return self.getToken(AutoscaleConditionParser.WORD, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_period

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPeriod" ):
                listener.enterPeriod(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPeriod" ):
                listener.exitPeriod(self)




    def period(self):

        localctx = AutoscaleConditionParser.PeriodContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_period)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 81
            self.match(AutoscaleConditionParser.WORD)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WhereContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHERE(self):
            return self.getToken(AutoscaleConditionParser.WHERE, 0)

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_where

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWhere" ):
                listener.enterWhere(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWhere" ):
                listener.exitWhere(self)




    def where(self):

        localctx = AutoscaleConditionParser.WhereContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_where)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 83
            self.match(AutoscaleConditionParser.WHERE)
            self.state = 84
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DimensionsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def where(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.WhereContext,0)


        def dimension(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(AutoscaleConditionParser.DimensionContext)
            else:
                return self.getTypedRuleContext(AutoscaleConditionParser.DimensionContext,i)


        def dim_separator(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(AutoscaleConditionParser.Dim_separatorContext)
            else:
                return self.getTypedRuleContext(AutoscaleConditionParser.Dim_separatorContext,i)


        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dimensions

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDimensions" ):
                listener.enterDimensions(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDimensions" ):
                listener.exitDimensions(self)




    def dimensions(self):

        localctx = AutoscaleConditionParser.DimensionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_dimensions)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 86
            self.where()
            self.state = 87
            self.dimension()
            self.state = 93
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==11 or _la==17:
                self.state = 88
                self.dim_separator()
                self.state = 89
                self.dimension()
                self.state = 95
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DimensionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def dim_name(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.Dim_nameContext,0)


        def dim_operator(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.Dim_operatorContext,0)


        def dim_values(self):
            return self.getTypedRuleContext(AutoscaleConditionParser.Dim_valuesContext,0)


        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dimension

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDimension" ):
                listener.enterDimension(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDimension" ):
                listener.exitDimension(self)




    def dimension(self):

        localctx = AutoscaleConditionParser.DimensionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_dimension)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 96
            self.dim_name()
            self.state = 97
            self.dim_operator()
            self.state = 98
            self.dim_values()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_separatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def AND(self):
            return self.getToken(AutoscaleConditionParser.AND, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dim_separator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_separator" ):
                listener.enterDim_separator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_separator" ):
                listener.exitDim_separator(self)




    def dim_separator(self):

        localctx = AutoscaleConditionParser.Dim_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_dim_separator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 100
            _la = self._input.LA(1)
            if not(_la==11 or _la==17):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 101
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_operatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dim_operator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_operator" ):
                listener.enterDim_operator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_operator" ):
                listener.exitDim_operator(self)




    def dim_operator(self):

        localctx = AutoscaleConditionParser.Dim_operatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_dim_operator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 103
            _la = self._input.LA(1)
            if not(_la==13 or _la==14):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 104
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_val_separatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def OR(self):
            return self.getToken(AutoscaleConditionParser.OR, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dim_val_separator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_val_separator" ):
                listener.enterDim_val_separator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_val_separator" ):
                listener.exitDim_val_separator(self)




    def dim_val_separator(self):

        localctx = AutoscaleConditionParser.Dim_val_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_dim_val_separator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 106
            _la = self._input.LA(1)
            if not(_la==11 or _la==20):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 107
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORD(self):
            return self.getToken(AutoscaleConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(AutoscaleConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dim_name

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_name" ):
                listener.enterDim_name(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_name" ):
                listener.exitDim_name(self)




    def dim_name(self):

        localctx = AutoscaleConditionParser.Dim_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_dim_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 109
            self.match(AutoscaleConditionParser.WORD)
            self.state = 110
            self.match(AutoscaleConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_valuesContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def dim_value(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(AutoscaleConditionParser.Dim_valueContext)
            else:
                return self.getTypedRuleContext(AutoscaleConditionParser.Dim_valueContext,i)


        def dim_val_separator(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(AutoscaleConditionParser.Dim_val_separatorContext)
            else:
                return self.getTypedRuleContext(AutoscaleConditionParser.Dim_val_separatorContext,i)


        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dim_values

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_values" ):
                listener.enterDim_values(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_values" ):
                listener.exitDim_values(self)




    def dim_values(self):

        localctx = AutoscaleConditionParser.Dim_valuesContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_dim_values)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 112
            self.dim_value()
            self.state = 118
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,6,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 113
                    self.dim_val_separator()
                    self.state = 114
                    self.dim_value() 
                self.state = 120
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,6,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_valueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.NUMBER)
            else:
                return self.getToken(AutoscaleConditionParser.NUMBER, i)

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WORD)
            else:
                return self.getToken(AutoscaleConditionParser.WORD, i)

        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(AutoscaleConditionParser.WHITESPACE)
            else:
                return self.getToken(AutoscaleConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return AutoscaleConditionParser.RULE_dim_value

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_value" ):
                listener.enterDim_value(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_value" ):
                listener.exitDim_value(self)




    def dim_value(self):

        localctx = AutoscaleConditionParser.Dim_valueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_dim_value)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 122 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 121
                    _la = self._input.LA(1)
                    if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 88113244) != 0):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 124 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,7,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx
