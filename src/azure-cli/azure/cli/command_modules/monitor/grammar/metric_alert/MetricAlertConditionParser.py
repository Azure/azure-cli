# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from MetricAlertCondition.g4 by ANTLR 4.13.1
# encoding: utf-8
# pylint: disable=all
from antlr4 import *
import sys
from typing import TextIO

def serializedATN():
    return [
        4,1,30,197,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,1,0,1,0,1,
        0,1,0,5,0,57,8,0,10,0,12,0,60,9,0,1,0,1,0,1,0,1,0,1,0,1,0,3,0,68,
        8,0,1,0,1,0,1,0,3,0,73,8,0,1,0,1,0,5,0,77,8,0,10,0,12,0,80,9,0,1,
        0,1,0,3,0,84,8,0,1,0,5,0,87,8,0,10,0,12,0,90,9,0,1,1,1,1,1,1,1,2,
        4,2,96,8,2,11,2,12,2,97,1,3,4,3,101,8,3,11,3,12,3,102,1,4,1,4,1,
        4,1,5,1,5,1,6,1,6,1,6,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,5,7,122,
        8,7,10,7,12,7,125,9,7,1,8,1,8,1,8,1,9,1,9,1,9,1,10,1,10,1,10,1,11,
        1,11,1,12,1,12,1,12,1,13,4,13,142,8,13,11,13,12,13,143,1,14,1,14,
        1,14,1,15,1,15,1,15,1,15,1,15,5,15,154,8,15,10,15,12,15,157,9,15,
        1,16,1,16,1,16,1,16,1,17,1,17,1,17,1,18,1,18,1,18,1,19,1,19,1,19,
        1,20,1,20,1,20,1,21,1,21,1,21,1,21,5,21,179,8,21,10,21,12,21,182,
        9,21,1,22,4,22,185,8,22,11,22,12,22,186,1,23,1,23,1,23,1,24,1,24,
        1,24,1,25,1,25,1,25,0,0,26,0,2,4,6,8,10,12,14,16,18,20,22,24,26,
        28,30,32,34,36,38,40,42,44,46,48,50,0,7,3,0,1,3,26,26,30,30,4,0,
        1,11,26,26,28,28,30,30,6,0,1,1,3,3,6,6,12,12,26,26,30,30,2,0,8,8,
        16,16,1,0,17,18,2,0,8,8,19,19,7,0,1,1,3,4,6,9,13,14,26,26,28,28,
        30,30,183,0,52,1,0,0,0,2,91,1,0,0,0,4,95,1,0,0,0,6,100,1,0,0,0,8,
        104,1,0,0,0,10,107,1,0,0,0,12,109,1,0,0,0,14,112,1,0,0,0,16,126,
        1,0,0,0,18,129,1,0,0,0,20,132,1,0,0,0,22,135,1,0,0,0,24,137,1,0,
        0,0,26,141,1,0,0,0,28,145,1,0,0,0,30,148,1,0,0,0,32,158,1,0,0,0,
        34,162,1,0,0,0,36,165,1,0,0,0,38,168,1,0,0,0,40,171,1,0,0,0,42,174,
        1,0,0,0,44,184,1,0,0,0,46,188,1,0,0,0,48,191,1,0,0,0,50,194,1,0,
        0,0,52,58,3,2,1,0,53,54,3,4,2,0,54,55,5,1,0,0,55,57,1,0,0,0,56,53,
        1,0,0,0,57,60,1,0,0,0,58,56,1,0,0,0,58,59,1,0,0,0,59,67,1,0,0,0,
        60,58,1,0,0,0,61,62,5,27,0,0,62,63,3,6,3,0,63,64,5,27,0,0,64,65,
        5,28,0,0,65,68,1,0,0,0,66,68,3,6,3,0,67,61,1,0,0,0,67,66,1,0,0,0,
        68,69,1,0,0,0,69,72,3,8,4,0,70,73,3,10,5,0,71,73,3,14,7,0,72,70,
        1,0,0,0,72,71,1,0,0,0,73,78,1,0,0,0,74,75,5,28,0,0,75,77,3,30,15,
        0,76,74,1,0,0,0,77,80,1,0,0,0,78,76,1,0,0,0,78,79,1,0,0,0,79,83,
        1,0,0,0,80,78,1,0,0,0,81,82,5,28,0,0,82,84,3,46,23,0,83,81,1,0,0,
        0,83,84,1,0,0,0,84,88,1,0,0,0,85,87,5,29,0,0,86,85,1,0,0,0,87,90,
        1,0,0,0,88,86,1,0,0,0,88,89,1,0,0,0,89,1,1,0,0,0,90,88,1,0,0,0,91,
        92,5,30,0,0,92,93,5,28,0,0,93,3,1,0,0,0,94,96,7,0,0,0,95,94,1,0,
        0,0,96,97,1,0,0,0,97,95,1,0,0,0,97,98,1,0,0,0,98,5,1,0,0,0,99,101,
        7,1,0,0,100,99,1,0,0,0,101,102,1,0,0,0,102,100,1,0,0,0,102,103,1,
        0,0,0,103,7,1,0,0,0,104,105,5,25,0,0,105,106,5,28,0,0,106,9,1,0,
        0,0,107,108,5,26,0,0,108,11,1,0,0,0,109,110,5,20,0,0,110,111,5,28,
        0,0,111,13,1,0,0,0,112,113,3,12,6,0,113,114,3,16,8,0,114,115,3,18,
        9,0,115,116,3,20,10,0,116,123,3,22,11,0,117,118,5,28,0,0,118,119,
        3,24,12,0,119,120,3,26,13,0,120,122,1,0,0,0,121,117,1,0,0,0,122,
        125,1,0,0,0,123,121,1,0,0,0,123,124,1,0,0,0,124,15,1,0,0,0,125,123,
        1,0,0,0,126,127,5,30,0,0,127,128,5,28,0,0,128,17,1,0,0,0,129,130,
        5,26,0,0,130,131,5,28,0,0,131,19,1,0,0,0,132,133,5,21,0,0,133,134,
        5,28,0,0,134,21,1,0,0,0,135,136,5,26,0,0,136,23,1,0,0,0,137,138,
        5,22,0,0,138,139,5,28,0,0,139,25,1,0,0,0,140,142,7,2,0,0,141,140,
        1,0,0,0,142,143,1,0,0,0,143,141,1,0,0,0,143,144,1,0,0,0,144,27,1,
        0,0,0,145,146,5,15,0,0,146,147,5,28,0,0,147,29,1,0,0,0,148,149,3,
        28,14,0,149,155,3,32,16,0,150,151,3,34,17,0,151,152,3,32,16,0,152,
        154,1,0,0,0,153,150,1,0,0,0,154,157,1,0,0,0,155,153,1,0,0,0,155,
        156,1,0,0,0,156,31,1,0,0,0,157,155,1,0,0,0,158,159,3,40,20,0,159,
        160,3,36,18,0,160,161,3,42,21,0,161,33,1,0,0,0,162,163,7,3,0,0,163,
        164,5,28,0,0,164,35,1,0,0,0,165,166,7,4,0,0,166,167,5,28,0,0,167,
        37,1,0,0,0,168,169,7,5,0,0,169,170,5,28,0,0,170,39,1,0,0,0,171,172,
        5,30,0,0,172,173,5,28,0,0,173,41,1,0,0,0,174,180,3,44,22,0,175,176,
        3,38,19,0,176,177,3,44,22,0,177,179,1,0,0,0,178,175,1,0,0,0,179,
        182,1,0,0,0,180,178,1,0,0,0,180,181,1,0,0,0,181,43,1,0,0,0,182,180,
        1,0,0,0,183,185,7,6,0,0,184,183,1,0,0,0,185,186,1,0,0,0,186,184,
        1,0,0,0,186,187,1,0,0,0,187,45,1,0,0,0,188,189,3,48,24,0,189,190,
        3,50,25,0,190,47,1,0,0,0,191,192,5,23,0,0,192,193,5,28,0,0,193,49,
        1,0,0,0,194,195,5,24,0,0,195,51,1,0,0,0,13,58,67,72,78,83,88,97,
        102,123,143,155,180,186
    ]

class MetricAlertConditionParser ( Parser ):

    grammarFileName = "MetricAlertCondition.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'.'", "'/'", "'-'", "'_'", "'\\'", "':'", 
                     "'%'", "','", "'|'", "'('", "')'", "'+'", "'*'", "'~'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "WHERE", "AND", 
                      "INCLUDES", "EXCLUDES", "OR", "DYNAMIC", "OF", "SINCE", 
                      "WITH", "SKIPMETRICVALIDATION", "OPERATOR", "NUMBER", 
                      "QUOTE", "WHITESPACE", "NEWLINE", "WORD" ]

    RULE_expression = 0
    RULE_aggregation = 1
    RULE_namespace = 2
    RULE_metric = 3
    RULE_operator = 4
    RULE_threshold = 5
    RULE_dynamic = 6
    RULE_dynamics = 7
    RULE_dyn_sensitivity = 8
    RULE_dyn_violations = 9
    RULE_dyn_of_separator = 10
    RULE_dyn_windows = 11
    RULE_dyn_since_seperator = 12
    RULE_dyn_datetime = 13
    RULE_where = 14
    RULE_dimensions = 15
    RULE_dimension = 16
    RULE_dim_separator = 17
    RULE_dim_operator = 18
    RULE_dim_val_separator = 19
    RULE_dim_name = 20
    RULE_dim_values = 21
    RULE_dim_value = 22
    RULE_options_ = 23
    RULE_with_ = 24
    RULE_option = 25

    ruleNames =  [ "expression", "aggregation", "namespace", "metric", "operator", 
                   "threshold", "dynamic", "dynamics", "dyn_sensitivity", 
                   "dyn_violations", "dyn_of_separator", "dyn_windows", 
                   "dyn_since_seperator", "dyn_datetime", "where", "dimensions", 
                   "dimension", "dim_separator", "dim_operator", "dim_val_separator", 
                   "dim_name", "dim_values", "dim_value", "options_", "with_", 
                   "option" ]

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
    WHERE=15
    AND=16
    INCLUDES=17
    EXCLUDES=18
    OR=19
    DYNAMIC=20
    OF=21
    SINCE=22
    WITH=23
    SKIPMETRICVALIDATION=24
    OPERATOR=25
    NUMBER=26
    QUOTE=27
    WHITESPACE=28
    NEWLINE=29
    WORD=30

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

        def aggregation(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.AggregationContext,0)


        def operator(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.OperatorContext,0)


        def QUOTE(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.QUOTE)
            else:
                return self.getToken(MetricAlertConditionParser.QUOTE, i)

        def metric(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.MetricContext,0)


        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def threshold(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.ThresholdContext,0)


        def dynamics(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.DynamicsContext,0)


        def namespace(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.NamespaceContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.NamespaceContext,i)


        def dimensions(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.DimensionsContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.DimensionsContext,i)


        def options_(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Options_Context,0)


        def NEWLINE(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.NEWLINE)
            else:
                return self.getToken(MetricAlertConditionParser.NEWLINE, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_expression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression" ):
                listener.enterExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression" ):
                listener.exitExpression(self)




    def expression(self):

        localctx = MetricAlertConditionParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_expression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 52
            self.aggregation()
            self.state = 58
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,0,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 53
                    self.namespace()
                    self.state = 54
                    self.match(MetricAlertConditionParser.T__0) 
                self.state = 60
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,0,self._ctx)

            self.state = 67
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [27]:
                self.state = 61
                self.match(MetricAlertConditionParser.QUOTE)
                self.state = 62
                self.metric()
                self.state = 63
                self.match(MetricAlertConditionParser.QUOTE)
                self.state = 64
                self.match(MetricAlertConditionParser.WHITESPACE)
                pass
            elif token in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 26, 28, 30]:
                self.state = 66
                self.metric()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 69
            self.operator()
            self.state = 72
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [26]:
                self.state = 70
                self.threshold()
                pass
            elif token in [20]:
                self.state = 71
                self.dynamics()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 78
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,3,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 74
                    self.match(MetricAlertConditionParser.WHITESPACE)
                    self.state = 75
                    self.dimensions() 
                self.state = 80
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,3,self._ctx)

            self.state = 83
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==28:
                self.state = 81
                self.match(MetricAlertConditionParser.WHITESPACE)
                self.state = 82
                self.options_()


            self.state = 88
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==29:
                self.state = 85
                self.match(MetricAlertConditionParser.NEWLINE)
                self.state = 90
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
            return self.getToken(MetricAlertConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_aggregation

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAggregation" ):
                listener.enterAggregation(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAggregation" ):
                listener.exitAggregation(self)




    def aggregation(self):

        localctx = MetricAlertConditionParser.AggregationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_aggregation)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 91
            self.match(MetricAlertConditionParser.WORD)
            self.state = 92
            self.match(MetricAlertConditionParser.WHITESPACE)
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

        def NUMBER(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.NUMBER)
            else:
                return self.getToken(MetricAlertConditionParser.NUMBER, i)

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_namespace

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNamespace" ):
                listener.enterNamespace(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNamespace" ):
                listener.exitNamespace(self)




    def namespace(self):

        localctx = MetricAlertConditionParser.NamespaceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_namespace)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 95 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 94
                    _la = self._input.LA(1)
                    if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 1140850702) != 0):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 97 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,6,self._ctx)

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

        def NUMBER(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.NUMBER)
            else:
                return self.getToken(MetricAlertConditionParser.NUMBER, i)

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_metric

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMetric" ):
                listener.enterMetric(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMetric" ):
                listener.exitMetric(self)




    def metric(self):

        localctx = MetricAlertConditionParser.MetricContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_metric)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 100 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 99
                _la = self._input.LA(1)
                if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 1409290238) != 0):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 102 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((_la) & ~0x3f) == 0 and ((1 << _la) & 1409290238) != 0):
                    break

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
            return self.getToken(MetricAlertConditionParser.OPERATOR, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_operator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOperator" ):
                listener.enterOperator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOperator" ):
                listener.exitOperator(self)




    def operator(self):

        localctx = MetricAlertConditionParser.OperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_operator)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 104
            self.match(MetricAlertConditionParser.OPERATOR)
            self.state = 105
            self.match(MetricAlertConditionParser.WHITESPACE)
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
            return self.getToken(MetricAlertConditionParser.NUMBER, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_threshold

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterThreshold" ):
                listener.enterThreshold(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitThreshold" ):
                listener.exitThreshold(self)




    def threshold(self):

        localctx = MetricAlertConditionParser.ThresholdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_threshold)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 107
            self.match(MetricAlertConditionParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DynamicContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DYNAMIC(self):
            return self.getToken(MetricAlertConditionParser.DYNAMIC, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dynamic

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDynamic" ):
                listener.enterDynamic(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDynamic" ):
                listener.exitDynamic(self)




    def dynamic(self):

        localctx = MetricAlertConditionParser.DynamicContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_dynamic)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 109
            self.match(MetricAlertConditionParser.DYNAMIC)
            self.state = 110
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DynamicsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def dynamic(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.DynamicContext,0)


        def dyn_sensitivity(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dyn_sensitivityContext,0)


        def dyn_violations(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dyn_violationsContext,0)


        def dyn_of_separator(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dyn_of_separatorContext,0)


        def dyn_windows(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dyn_windowsContext,0)


        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def dyn_since_seperator(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dyn_since_seperatorContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dyn_since_seperatorContext,i)


        def dyn_datetime(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dyn_datetimeContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dyn_datetimeContext,i)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dynamics

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDynamics" ):
                listener.enterDynamics(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDynamics" ):
                listener.exitDynamics(self)




    def dynamics(self):

        localctx = MetricAlertConditionParser.DynamicsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_dynamics)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 112
            self.dynamic()
            self.state = 113
            self.dyn_sensitivity()
            self.state = 114
            self.dyn_violations()
            self.state = 115
            self.dyn_of_separator()
            self.state = 116
            self.dyn_windows()
            self.state = 123
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 117
                    self.match(MetricAlertConditionParser.WHITESPACE)
                    self.state = 118
                    self.dyn_since_seperator()
                    self.state = 119
                    self.dyn_datetime() 
                self.state = 125
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dyn_sensitivityContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WORD(self):
            return self.getToken(MetricAlertConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dyn_sensitivity

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDyn_sensitivity" ):
                listener.enterDyn_sensitivity(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDyn_sensitivity" ):
                listener.exitDyn_sensitivity(self)




    def dyn_sensitivity(self):

        localctx = MetricAlertConditionParser.Dyn_sensitivityContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_dyn_sensitivity)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 126
            self.match(MetricAlertConditionParser.WORD)
            self.state = 127
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dyn_violationsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(MetricAlertConditionParser.NUMBER, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dyn_violations

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDyn_violations" ):
                listener.enterDyn_violations(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDyn_violations" ):
                listener.exitDyn_violations(self)




    def dyn_violations(self):

        localctx = MetricAlertConditionParser.Dyn_violationsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_dyn_violations)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 129
            self.match(MetricAlertConditionParser.NUMBER)
            self.state = 130
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dyn_of_separatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OF(self):
            return self.getToken(MetricAlertConditionParser.OF, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dyn_of_separator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDyn_of_separator" ):
                listener.enterDyn_of_separator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDyn_of_separator" ):
                listener.exitDyn_of_separator(self)




    def dyn_of_separator(self):

        localctx = MetricAlertConditionParser.Dyn_of_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_dyn_of_separator)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 132
            self.match(MetricAlertConditionParser.OF)
            self.state = 133
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dyn_windowsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(MetricAlertConditionParser.NUMBER, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dyn_windows

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDyn_windows" ):
                listener.enterDyn_windows(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDyn_windows" ):
                listener.exitDyn_windows(self)




    def dyn_windows(self):

        localctx = MetricAlertConditionParser.Dyn_windowsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_dyn_windows)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 135
            self.match(MetricAlertConditionParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dyn_since_seperatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SINCE(self):
            return self.getToken(MetricAlertConditionParser.SINCE, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dyn_since_seperator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDyn_since_seperator" ):
                listener.enterDyn_since_seperator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDyn_since_seperator" ):
                listener.exitDyn_since_seperator(self)




    def dyn_since_seperator(self):

        localctx = MetricAlertConditionParser.Dyn_since_seperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_dyn_since_seperator)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 137
            self.match(MetricAlertConditionParser.SINCE)
            self.state = 138
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dyn_datetimeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.NUMBER)
            else:
                return self.getToken(MetricAlertConditionParser.NUMBER, i)

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dyn_datetime

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDyn_datetime" ):
                listener.enterDyn_datetime(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDyn_datetime" ):
                listener.exitDyn_datetime(self)




    def dyn_datetime(self):

        localctx = MetricAlertConditionParser.Dyn_datetimeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_dyn_datetime)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 141 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 140
                _la = self._input.LA(1)
                if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 1140854858) != 0):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 143 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((_la) & ~0x3f) == 0 and ((1 << _la) & 1140854858) != 0):
                    break

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
            return self.getToken(MetricAlertConditionParser.WHERE, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_where

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWhere" ):
                listener.enterWhere(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWhere" ):
                listener.exitWhere(self)




    def where(self):

        localctx = MetricAlertConditionParser.WhereContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_where)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 145
            self.match(MetricAlertConditionParser.WHERE)
            self.state = 146
            self.match(MetricAlertConditionParser.WHITESPACE)
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
            return self.getTypedRuleContext(MetricAlertConditionParser.WhereContext,0)


        def dimension(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.DimensionContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.DimensionContext,i)


        def dim_separator(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dim_separatorContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dim_separatorContext,i)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dimensions

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDimensions" ):
                listener.enterDimensions(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDimensions" ):
                listener.exitDimensions(self)




    def dimensions(self):

        localctx = MetricAlertConditionParser.DimensionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_dimensions)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 148
            self.where()
            self.state = 149
            self.dimension()
            self.state = 155
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==8 or _la==16:
                self.state = 150
                self.dim_separator()
                self.state = 151
                self.dimension()
                self.state = 157
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
            return self.getTypedRuleContext(MetricAlertConditionParser.Dim_nameContext,0)


        def dim_operator(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dim_operatorContext,0)


        def dim_values(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dim_valuesContext,0)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dimension

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDimension" ):
                listener.enterDimension(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDimension" ):
                listener.exitDimension(self)




    def dimension(self):

        localctx = MetricAlertConditionParser.DimensionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_dimension)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 158
            self.dim_name()
            self.state = 159
            self.dim_operator()
            self.state = 160
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
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def AND(self):
            return self.getToken(MetricAlertConditionParser.AND, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_separator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_separator" ):
                listener.enterDim_separator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_separator" ):
                listener.exitDim_separator(self)




    def dim_separator(self):

        localctx = MetricAlertConditionParser.Dim_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_dim_separator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 162
            _la = self._input.LA(1)
            if not(_la==8 or _la==16):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 163
            self.match(MetricAlertConditionParser.WHITESPACE)
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
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def INCLUDES(self):
            return self.getToken(MetricAlertConditionParser.INCLUDES, 0)

        def EXCLUDES(self):
            return self.getToken(MetricAlertConditionParser.EXCLUDES, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_operator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_operator" ):
                listener.enterDim_operator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_operator" ):
                listener.exitDim_operator(self)




    def dim_operator(self):

        localctx = MetricAlertConditionParser.Dim_operatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_dim_operator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 165
            _la = self._input.LA(1)
            if not(_la==17 or _la==18):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 166
            self.match(MetricAlertConditionParser.WHITESPACE)
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
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def OR(self):
            return self.getToken(MetricAlertConditionParser.OR, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_val_separator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_val_separator" ):
                listener.enterDim_val_separator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_val_separator" ):
                listener.exitDim_val_separator(self)




    def dim_val_separator(self):

        localctx = MetricAlertConditionParser.Dim_val_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_dim_val_separator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 168
            _la = self._input.LA(1)
            if not(_la==8 or _la==19):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 169
            self.match(MetricAlertConditionParser.WHITESPACE)
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
            return self.getToken(MetricAlertConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_name

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_name" ):
                listener.enterDim_name(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_name" ):
                listener.exitDim_name(self)




    def dim_name(self):

        localctx = MetricAlertConditionParser.Dim_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_dim_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 171
            self.match(MetricAlertConditionParser.WORD)
            self.state = 172
            self.match(MetricAlertConditionParser.WHITESPACE)
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
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dim_valueContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dim_valueContext,i)


        def dim_val_separator(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dim_val_separatorContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dim_val_separatorContext,i)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_values

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_values" ):
                listener.enterDim_values(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_values" ):
                listener.exitDim_values(self)




    def dim_values(self):

        localctx = MetricAlertConditionParser.Dim_valuesContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_dim_values)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 174
            self.dim_value()
            self.state = 180
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,11,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 175
                    self.dim_val_separator()
                    self.state = 176
                    self.dim_value() 
                self.state = 182
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,11,self._ctx)

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
                return self.getTokens(MetricAlertConditionParser.NUMBER)
            else:
                return self.getToken(MetricAlertConditionParser.NUMBER, i)

        def WORD(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def WHITESPACE(self, i:int=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_value

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDim_value" ):
                listener.enterDim_value(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDim_value" ):
                listener.exitDim_value(self)




    def dim_value(self):

        localctx = MetricAlertConditionParser.Dim_valueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_dim_value)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 184 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 183
                    _la = self._input.LA(1)
                    if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 1409311706) != 0):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 186 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,12,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Options_Context(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def with_(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.With_Context,0)


        def option(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.OptionContext,0)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_options_

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOptions_" ):
                listener.enterOptions_(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOptions_" ):
                listener.exitOptions_(self)




    def options_(self):

        localctx = MetricAlertConditionParser.Options_Context(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_options_)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 188
            self.with_()
            self.state = 189
            self.option()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class With_Context(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WITH(self):
            return self.getToken(MetricAlertConditionParser.WITH, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_with_

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWith_" ):
                listener.enterWith_(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWith_" ):
                listener.exitWith_(self)




    def with_(self):

        localctx = MetricAlertConditionParser.With_Context(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_with_)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 191
            self.match(MetricAlertConditionParser.WITH)
            self.state = 192
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OptionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SKIPMETRICVALIDATION(self):
            return self.getToken(MetricAlertConditionParser.SKIPMETRICVALIDATION, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_option

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOption" ):
                listener.enterOption(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOption" ):
                listener.exitOption(self)




    def option(self):

        localctx = MetricAlertConditionParser.OptionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_option)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 194
            self.match(MetricAlertConditionParser.SKIPMETRICVALIDATION)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





