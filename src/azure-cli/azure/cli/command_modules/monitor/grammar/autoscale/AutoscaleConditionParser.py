# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from AutoscaleCondition.g4 by ANTLR 4.9.3
# encoding: utf-8
# pylint: disable=all
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\34")
        buf.write("\u0081\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\4\20\t\20\4\21\t\21\3\2\3\2\3\2\3\2\3")
        buf.write("\2\7\2(\n\2\f\2\16\2+\13\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2")
        buf.write("\3\2\3\2\7\2\66\n\2\f\2\16\29\13\2\3\2\7\2<\n\2\f\2\16")
        buf.write("\2?\13\2\3\3\3\3\3\3\3\4\6\4E\n\4\r\4\16\4F\3\5\6\5J\n")
        buf.write("\5\r\5\16\5K\3\6\3\6\3\6\3\7\3\7\3\7\3\b\3\b\3\t\3\t\3")
        buf.write("\t\3\n\3\n\3\n\3\n\3\n\7\n^\n\n\f\n\16\na\13\n\3\13\3")
        buf.write("\13\3\13\3\13\3\f\3\f\3\f\3\r\3\r\3\r\3\16\3\16\3\16\3")
        buf.write("\17\3\17\3\17\3\20\3\20\3\20\3\20\7\20w\n\20\f\20\16\20")
        buf.write("z\13\20\3\21\6\21}\n\21\r\21\16\21~\3\21\2\2\22\2\4\6")
        buf.write("\b\n\f\16\20\22\24\26\30\32\34\36 \2\b\5\2\3\13\32\32")
        buf.write("\34\34\7\2\3\4\6\t\f\16\32\32\34\34\4\2\r\r\23\23\3\2")
        buf.write("\17\20\4\2\r\r\26\26\b\2\4\6\b\b\21\21\30\30\32\32\34")
        buf.write("\34\2x\2)\3\2\2\2\4@\3\2\2\2\6D\3\2\2\2\bI\3\2\2\2\nM")
        buf.write("\3\2\2\2\fP\3\2\2\2\16S\3\2\2\2\20U\3\2\2\2\22X\3\2\2")
        buf.write("\2\24b\3\2\2\2\26f\3\2\2\2\30i\3\2\2\2\32l\3\2\2\2\34")
        buf.write("o\3\2\2\2\36r\3\2\2\2 |\3\2\2\2\"#\7\31\2\2#$\5\6\4\2")
        buf.write("$%\7\31\2\2%&\7\32\2\2&(\3\2\2\2\'\"\3\2\2\2(+\3\2\2\2")
        buf.write(")\'\3\2\2\2)*\3\2\2\2*,\3\2\2\2+)\3\2\2\2,-\5\b\5\2-.")
        buf.write("\7\32\2\2./\3\2\2\2/\60\5\n\6\2\60\61\5\f\7\2\61\62\5")
        buf.write("\4\3\2\62\67\5\16\b\2\63\64\7\32\2\2\64\66\5\22\n\2\65")
        buf.write("\63\3\2\2\2\669\3\2\2\2\67\65\3\2\2\2\678\3\2\2\28=\3")
        buf.write("\2\2\29\67\3\2\2\2:<\7\33\2\2;:\3\2\2\2<?\3\2\2\2=;\3")
        buf.write("\2\2\2=>\3\2\2\2>\3\3\2\2\2?=\3\2\2\2@A\7\34\2\2AB\7\32")
        buf.write("\2\2B\5\3\2\2\2CE\t\2\2\2DC\3\2\2\2EF\3\2\2\2FD\3\2\2")
        buf.write("\2FG\3\2\2\2G\7\3\2\2\2HJ\t\3\2\2IH\3\2\2\2JK\3\2\2\2")
        buf.write("KI\3\2\2\2KL\3\2\2\2L\t\3\2\2\2MN\7\27\2\2NO\7\32\2\2")
        buf.write("O\13\3\2\2\2PQ\7\30\2\2QR\7\32\2\2R\r\3\2\2\2ST\7\34\2")
        buf.write("\2T\17\3\2\2\2UV\7\22\2\2VW\7\32\2\2W\21\3\2\2\2XY\5\20")
        buf.write("\t\2Y_\5\24\13\2Z[\5\26\f\2[\\\5\24\13\2\\^\3\2\2\2]Z")
        buf.write("\3\2\2\2^a\3\2\2\2_]\3\2\2\2_`\3\2\2\2`\23\3\2\2\2a_\3")
        buf.write("\2\2\2bc\5\34\17\2cd\5\30\r\2de\5\36\20\2e\25\3\2\2\2")
        buf.write("fg\t\4\2\2gh\7\32\2\2h\27\3\2\2\2ij\t\5\2\2jk\7\32\2\2")
        buf.write("k\31\3\2\2\2lm\t\6\2\2mn\7\32\2\2n\33\3\2\2\2op\7\34\2")
        buf.write("\2pq\7\32\2\2q\35\3\2\2\2rx\5 \21\2st\5\32\16\2tu\5 \21")
        buf.write("\2uw\3\2\2\2vs\3\2\2\2wz\3\2\2\2xv\3\2\2\2xy\3\2\2\2y")
        buf.write("\37\3\2\2\2zx\3\2\2\2{}\t\7\2\2|{\3\2\2\2}~\3\2\2\2~|")
        buf.write("\3\2\2\2~\177\3\2\2\2\177!\3\2\2\2\n)\67=FK_x~")
        return buf.getvalue()


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
        self.checkVersion("4.9.3")
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
            while _la==AutoscaleConditionParser.QUOTE:
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
            while _la==AutoscaleConditionParser.WHITESPACE:
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
            while _la==AutoscaleConditionParser.NEWLINE:
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
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << AutoscaleConditionParser.T__0) | (1 << AutoscaleConditionParser.T__1) | (1 << AutoscaleConditionParser.T__2) | (1 << AutoscaleConditionParser.T__3) | (1 << AutoscaleConditionParser.T__4) | (1 << AutoscaleConditionParser.T__5) | (1 << AutoscaleConditionParser.T__6) | (1 << AutoscaleConditionParser.T__7) | (1 << AutoscaleConditionParser.T__8) | (1 << AutoscaleConditionParser.WHITESPACE) | (1 << AutoscaleConditionParser.WORD))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 68 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << AutoscaleConditionParser.T__0) | (1 << AutoscaleConditionParser.T__1) | (1 << AutoscaleConditionParser.T__2) | (1 << AutoscaleConditionParser.T__3) | (1 << AutoscaleConditionParser.T__4) | (1 << AutoscaleConditionParser.T__5) | (1 << AutoscaleConditionParser.T__6) | (1 << AutoscaleConditionParser.T__7) | (1 << AutoscaleConditionParser.T__8) | (1 << AutoscaleConditionParser.WHITESPACE) | (1 << AutoscaleConditionParser.WORD))) != 0)):
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
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << AutoscaleConditionParser.T__0) | (1 << AutoscaleConditionParser.T__1) | (1 << AutoscaleConditionParser.T__3) | (1 << AutoscaleConditionParser.T__4) | (1 << AutoscaleConditionParser.T__5) | (1 << AutoscaleConditionParser.T__6) | (1 << AutoscaleConditionParser.T__9) | (1 << AutoscaleConditionParser.T__10) | (1 << AutoscaleConditionParser.T__11) | (1 << AutoscaleConditionParser.WHITESPACE) | (1 << AutoscaleConditionParser.WORD))) != 0)):
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
            while _la==AutoscaleConditionParser.T__10 or _la==AutoscaleConditionParser.AND:
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
            if not(_la==AutoscaleConditionParser.T__10 or _la==AutoscaleConditionParser.AND):
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
            if not(_la==AutoscaleConditionParser.T__12 or _la==AutoscaleConditionParser.T__13):
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
            if not(_la==AutoscaleConditionParser.T__10 or _la==AutoscaleConditionParser.OR):
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
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << AutoscaleConditionParser.T__1) | (1 << AutoscaleConditionParser.T__2) | (1 << AutoscaleConditionParser.T__3) | (1 << AutoscaleConditionParser.T__5) | (1 << AutoscaleConditionParser.T__14) | (1 << AutoscaleConditionParser.NUMBER) | (1 << AutoscaleConditionParser.WHITESPACE) | (1 << AutoscaleConditionParser.WORD))) != 0)):
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





