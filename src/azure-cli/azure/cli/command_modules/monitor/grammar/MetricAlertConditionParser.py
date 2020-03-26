# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# encoding: utf-8
# pylint: disable=all
# Generated from MetricAlertCondition.g4 by ANTLR 4.7.2

from __future__ import print_function
from antlr4 import *
from io import StringIO
import sys


def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3")
        buf.write(u"\27~\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write(u"\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4")
        buf.write(u"\16\t\16\4\17\t\17\4\20\t\20\3\2\3\2\3\2\3\2\7\2%\n\2")
        buf.write(u"\f\2\16\2(\13\2\3\2\3\2\3\2\3\2\3\2\3\2\5\2\60\n\2\3")
        buf.write(u"\2\3\2\3\2\3\2\7\2\66\n\2\f\2\16\29\13\2\3\2\7\2<\n\2")
        buf.write(u"\f\2\16\2?\13\2\3\3\3\3\3\3\3\4\6\4E\n\4\r\4\16\4F\3")
        buf.write(u"\5\6\5J\n\5\r\5\16\5K\3\6\3\6\3\6\3\7\3\7\3\b\3\b\3\b")
        buf.write(u"\3\t\3\t\3\t\3\t\3\t\7\t[\n\t\f\t\16\t^\13\t\3\n\3\n")
        buf.write(u"\3\n\3\n\3\13\3\13\3\13\3\f\3\f\3\f\3\r\3\r\3\r\3\16")
        buf.write(u"\3\16\3\16\3\17\3\17\3\17\3\17\7\17t\n\17\f\17\16\17")
        buf.write(u"w\13\17\3\20\6\20z\n\20\r\20\16\20{\3\20\2\2\21\2\4\6")
        buf.write(u"\b\n\f\16\20\22\24\26\30\32\34\36\2\b\4\2\3\4\27\27\5")
        buf.write(u"\2\3\t\25\25\27\27\4\2\n\n\16\16\3\2\17\20\4\2\n\n\21")
        buf.write(u"\21\t\2\3\3\7\7\t\t\13\f\23\23\25\25\27\27\2w\2 \3\2")
        buf.write(u"\2\2\4@\3\2\2\2\6D\3\2\2\2\bI\3\2\2\2\nM\3\2\2\2\fP\3")
        buf.write(u"\2\2\2\16R\3\2\2\2\20U\3\2\2\2\22_\3\2\2\2\24c\3\2\2")
        buf.write(u"\2\26f\3\2\2\2\30i\3\2\2\2\32l\3\2\2\2\34o\3\2\2\2\36")
        buf.write(u"y\3\2\2\2 &\5\4\3\2!\"\5\6\4\2\"#\7\3\2\2#%\3\2\2\2$")
        buf.write(u"!\3\2\2\2%(\3\2\2\2&$\3\2\2\2&\'\3\2\2\2\'/\3\2\2\2(")
        buf.write(u"&\3\2\2\2)*\7\24\2\2*+\5\b\5\2+,\7\24\2\2,-\7\25\2\2")
        buf.write(u"-\60\3\2\2\2.\60\5\b\5\2/)\3\2\2\2/.\3\2\2\2\60\61\3")
        buf.write(u"\2\2\2\61\62\5\n\6\2\62\67\5\f\7\2\63\64\7\25\2\2\64")
        buf.write(u"\66\5\20\t\2\65\63\3\2\2\2\669\3\2\2\2\67\65\3\2\2\2")
        buf.write(u"\678\3\2\2\28=\3\2\2\29\67\3\2\2\2:<\7\26\2\2;:\3\2\2")
        buf.write(u"\2<?\3\2\2\2=;\3\2\2\2=>\3\2\2\2>\3\3\2\2\2?=\3\2\2\2")
        buf.write(u"@A\7\27\2\2AB\7\25\2\2B\5\3\2\2\2CE\t\2\2\2DC\3\2\2\2")
        buf.write(u"EF\3\2\2\2FD\3\2\2\2FG\3\2\2\2G\7\3\2\2\2HJ\t\3\2\2I")
        buf.write(u"H\3\2\2\2JK\3\2\2\2KI\3\2\2\2KL\3\2\2\2L\t\3\2\2\2MN")
        buf.write(u"\7\22\2\2NO\7\25\2\2O\13\3\2\2\2PQ\7\23\2\2Q\r\3\2\2")
        buf.write(u"\2RS\7\r\2\2ST\7\25\2\2T\17\3\2\2\2UV\5\16\b\2V\\\5\22")
        buf.write(u"\n\2WX\5\24\13\2XY\5\22\n\2Y[\3\2\2\2ZW\3\2\2\2[^\3\2")
        buf.write(u"\2\2\\Z\3\2\2\2\\]\3\2\2\2]\21\3\2\2\2^\\\3\2\2\2_`\5")
        buf.write(u"\32\16\2`a\5\26\f\2ab\5\34\17\2b\23\3\2\2\2cd\t\4\2\2")
        buf.write(u"de\7\25\2\2e\25\3\2\2\2fg\t\5\2\2gh\7\25\2\2h\27\3\2")
        buf.write(u"\2\2ij\t\6\2\2jk\7\25\2\2k\31\3\2\2\2lm\7\27\2\2mn\7")
        buf.write(u"\25\2\2n\33\3\2\2\2ou\5\36\20\2pq\5\30\r\2qr\5\36\20")
        buf.write(u"\2rt\3\2\2\2sp\3\2\2\2tw\3\2\2\2us\3\2\2\2uv\3\2\2\2")
        buf.write(u"v\35\3\2\2\2wu\3\2\2\2xz\t\7\2\2yx\3\2\2\2z{\3\2\2\2")
        buf.write(u"{y\3\2\2\2{|\3\2\2\2|\37\3\2\2\2\13&/\67=FK\\u{")
        return buf.getvalue()


class MetricAlertConditionParser ( Parser ):

    grammarFileName = "MetricAlertCondition.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ u"<INVALID>", u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", 
                     u"'%'", u"'-'", u"','", u"'*'", u"'~'" ]

    symbolicNames = [ u"<INVALID>", u"<INVALID>", u"<INVALID>", u"<INVALID>", 
                      u"<INVALID>", u"<INVALID>", u"<INVALID>", u"<INVALID>", 
                      u"<INVALID>", u"<INVALID>", u"<INVALID>", u"WHERE", 
                      u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
                      u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    RULE_expression = 0
    RULE_aggregation = 1
    RULE_namespace = 2
    RULE_metric = 3
    RULE_operator = 4
    RULE_threshold = 5
    RULE_where = 6
    RULE_dimensions = 7
    RULE_dimension = 8
    RULE_dim_separator = 9
    RULE_dim_operator = 10
    RULE_dim_val_separator = 11
    RULE_dim_name = 12
    RULE_dim_values = 13
    RULE_dim_value = 14

    ruleNames =  [ u"expression", u"aggregation", u"namespace", u"metric", 
                   u"operator", u"threshold", u"where", u"dimensions", u"dimension", 
                   u"dim_separator", u"dim_operator", u"dim_val_separator", 
                   u"dim_name", u"dim_values", u"dim_value" ]

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
    WHERE=11
    AND=12
    INCLUDES=13
    EXCLUDES=14
    OR=15
    OPERATOR=16
    NUMBER=17
    QUOTE=18
    WHITESPACE=19
    NEWLINE=20
    WORD=21

    def __init__(self, input, output=sys.stdout):
        super(MetricAlertConditionParser, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ExpressionContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.ExpressionContext, self).__init__(parent, invokingState)
            self.parser = parser

        def aggregation(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.AggregationContext,0)


        def operator(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.OperatorContext,0)


        def threshold(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.ThresholdContext,0)


        def QUOTE(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.QUOTE)
            else:
                return self.getToken(MetricAlertConditionParser.QUOTE, i)

        def metric(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.MetricContext,0)


        def WHITESPACE(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def namespace(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.NamespaceContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.NamespaceContext,i)


        def dimensions(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.DimensionsContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.DimensionsContext,i)


        def NEWLINE(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.NEWLINE)
            else:
                return self.getToken(MetricAlertConditionParser.NEWLINE, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_expression

        def enterRule(self, listener):
            if hasattr(listener, "enterExpression"):
                listener.enterExpression(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitExpression"):
                listener.exitExpression(self)




    def expression(self):

        localctx = MetricAlertConditionParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_expression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 30
            self.aggregation()
            self.state = 36
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,0,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 31
                    self.namespace()
                    self.state = 32
                    self.match(MetricAlertConditionParser.T__0) 
                self.state = 38
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,0,self._ctx)

            self.state = 45
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [MetricAlertConditionParser.QUOTE]:
                self.state = 39
                self.match(MetricAlertConditionParser.QUOTE)
                self.state = 40
                self.metric()
                self.state = 41
                self.match(MetricAlertConditionParser.QUOTE)
                self.state = 42
                self.match(MetricAlertConditionParser.WHITESPACE)
                pass
            elif token in [MetricAlertConditionParser.T__0, MetricAlertConditionParser.T__1, MetricAlertConditionParser.T__2, MetricAlertConditionParser.T__3, MetricAlertConditionParser.T__4, MetricAlertConditionParser.T__5, MetricAlertConditionParser.T__6, MetricAlertConditionParser.WHITESPACE, MetricAlertConditionParser.WORD]:
                self.state = 44
                self.metric()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 47
            self.operator()
            self.state = 48
            self.threshold()
            self.state = 53
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==MetricAlertConditionParser.WHITESPACE:
                self.state = 49
                self.match(MetricAlertConditionParser.WHITESPACE)
                self.state = 50
                self.dimensions()
                self.state = 55
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 59
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==MetricAlertConditionParser.NEWLINE:
                self.state = 56
                self.match(MetricAlertConditionParser.NEWLINE)
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

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.AggregationContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WORD(self):
            return self.getToken(MetricAlertConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_aggregation

        def enterRule(self, listener):
            if hasattr(listener, "enterAggregation"):
                listener.enterAggregation(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitAggregation"):
                listener.exitAggregation(self)




    def aggregation(self):

        localctx = MetricAlertConditionParser.AggregationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_aggregation)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 62
            self.match(MetricAlertConditionParser.WORD)
            self.state = 63
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NamespaceContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.NamespaceContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WORD(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_namespace

        def enterRule(self, listener):
            if hasattr(listener, "enterNamespace"):
                listener.enterNamespace(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitNamespace"):
                listener.exitNamespace(self)




    def namespace(self):

        localctx = MetricAlertConditionParser.NamespaceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_namespace)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 66 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 65
                    _la = self._input.LA(1)
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__1) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 68 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,4,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MetricContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.MetricContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WORD(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def WHITESPACE(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_metric

        def enterRule(self, listener):
            if hasattr(listener, "enterMetric"):
                listener.enterMetric(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitMetric"):
                listener.exitMetric(self)




    def metric(self):

        localctx = MetricAlertConditionParser.MetricContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_metric)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 71 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 70
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__1) | (1 << MetricAlertConditionParser.T__2) | (1 << MetricAlertConditionParser.T__3) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__5) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 73 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__1) | (1 << MetricAlertConditionParser.T__2) | (1 << MetricAlertConditionParser.T__3) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__5) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OperatorContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.OperatorContext, self).__init__(parent, invokingState)
            self.parser = parser

        def OPERATOR(self):
            return self.getToken(MetricAlertConditionParser.OPERATOR, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_operator

        def enterRule(self, listener):
            if hasattr(listener, "enterOperator"):
                listener.enterOperator(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitOperator"):
                listener.exitOperator(self)




    def operator(self):

        localctx = MetricAlertConditionParser.OperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_operator)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 75
            self.match(MetricAlertConditionParser.OPERATOR)
            self.state = 76
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ThresholdContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.ThresholdContext, self).__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(MetricAlertConditionParser.NUMBER, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_threshold

        def enterRule(self, listener):
            if hasattr(listener, "enterThreshold"):
                listener.enterThreshold(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitThreshold"):
                listener.exitThreshold(self)




    def threshold(self):

        localctx = MetricAlertConditionParser.ThresholdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_threshold)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 78
            self.match(MetricAlertConditionParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WhereContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.WhereContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WHERE(self):
            return self.getToken(MetricAlertConditionParser.WHERE, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_where

        def enterRule(self, listener):
            if hasattr(listener, "enterWhere"):
                listener.enterWhere(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitWhere"):
                listener.exitWhere(self)




    def where(self):

        localctx = MetricAlertConditionParser.WhereContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_where)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 80
            self.match(MetricAlertConditionParser.WHERE)
            self.state = 81
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DimensionsContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.DimensionsContext, self).__init__(parent, invokingState)
            self.parser = parser

        def where(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.WhereContext,0)


        def dimension(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.DimensionContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.DimensionContext,i)


        def dim_separator(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dim_separatorContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dim_separatorContext,i)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dimensions

        def enterRule(self, listener):
            if hasattr(listener, "enterDimensions"):
                listener.enterDimensions(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDimensions"):
                listener.exitDimensions(self)




    def dimensions(self):

        localctx = MetricAlertConditionParser.DimensionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_dimensions)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 83
            self.where()
            self.state = 84
            self.dimension()
            self.state = 90
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==MetricAlertConditionParser.T__7 or _la==MetricAlertConditionParser.AND:
                self.state = 85
                self.dim_separator()
                self.state = 86
                self.dimension()
                self.state = 92
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

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.DimensionContext, self).__init__(parent, invokingState)
            self.parser = parser

        def dim_name(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dim_nameContext,0)


        def dim_operator(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dim_operatorContext,0)


        def dim_values(self):
            return self.getTypedRuleContext(MetricAlertConditionParser.Dim_valuesContext,0)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dimension

        def enterRule(self, listener):
            if hasattr(listener, "enterDimension"):
                listener.enterDimension(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDimension"):
                listener.exitDimension(self)




    def dimension(self):

        localctx = MetricAlertConditionParser.DimensionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_dimension)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 93
            self.dim_name()
            self.state = 94
            self.dim_operator()
            self.state = 95
            self.dim_values()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_separatorContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.Dim_separatorContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def AND(self):
            return self.getToken(MetricAlertConditionParser.AND, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_separator

        def enterRule(self, listener):
            if hasattr(listener, "enterDim_separator"):
                listener.enterDim_separator(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDim_separator"):
                listener.exitDim_separator(self)




    def dim_separator(self):

        localctx = MetricAlertConditionParser.Dim_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_dim_separator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 97
            _la = self._input.LA(1)
            if not(_la==MetricAlertConditionParser.T__7 or _la==MetricAlertConditionParser.AND):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 98
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_operatorContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.Dim_operatorContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def INCLUDES(self):
            return self.getToken(MetricAlertConditionParser.INCLUDES, 0)

        def EXCLUDES(self):
            return self.getToken(MetricAlertConditionParser.EXCLUDES, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_operator

        def enterRule(self, listener):
            if hasattr(listener, "enterDim_operator"):
                listener.enterDim_operator(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDim_operator"):
                listener.exitDim_operator(self)




    def dim_operator(self):

        localctx = MetricAlertConditionParser.Dim_operatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_dim_operator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 100
            _la = self._input.LA(1)
            if not(_la==MetricAlertConditionParser.INCLUDES or _la==MetricAlertConditionParser.EXCLUDES):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 101
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_val_separatorContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.Dim_val_separatorContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def OR(self):
            return self.getToken(MetricAlertConditionParser.OR, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_val_separator

        def enterRule(self, listener):
            if hasattr(listener, "enterDim_val_separator"):
                listener.enterDim_val_separator(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDim_val_separator"):
                listener.exitDim_val_separator(self)




    def dim_val_separator(self):

        localctx = MetricAlertConditionParser.Dim_val_separatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_dim_val_separator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 103
            _la = self._input.LA(1)
            if not(_la==MetricAlertConditionParser.T__7 or _la==MetricAlertConditionParser.OR):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 104
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_nameContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.Dim_nameContext, self).__init__(parent, invokingState)
            self.parser = parser

        def WORD(self):
            return self.getToken(MetricAlertConditionParser.WORD, 0)

        def WHITESPACE(self):
            return self.getToken(MetricAlertConditionParser.WHITESPACE, 0)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_name

        def enterRule(self, listener):
            if hasattr(listener, "enterDim_name"):
                listener.enterDim_name(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDim_name"):
                listener.exitDim_name(self)




    def dim_name(self):

        localctx = MetricAlertConditionParser.Dim_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_dim_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 106
            self.match(MetricAlertConditionParser.WORD)
            self.state = 107
            self.match(MetricAlertConditionParser.WHITESPACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_valuesContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.Dim_valuesContext, self).__init__(parent, invokingState)
            self.parser = parser

        def dim_value(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dim_valueContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dim_valueContext,i)


        def dim_val_separator(self, i=None):
            if i is None:
                return self.getTypedRuleContexts(MetricAlertConditionParser.Dim_val_separatorContext)
            else:
                return self.getTypedRuleContext(MetricAlertConditionParser.Dim_val_separatorContext,i)


        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_values

        def enterRule(self, listener):
            if hasattr(listener, "enterDim_values"):
                listener.enterDim_values(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDim_values"):
                listener.exitDim_values(self)




    def dim_values(self):

        localctx = MetricAlertConditionParser.Dim_valuesContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_dim_values)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 109
            self.dim_value()
            self.state = 115
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,7,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 110
                    self.dim_val_separator()
                    self.state = 111
                    self.dim_value() 
                self.state = 117
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,7,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Dim_valueContext(ParserRuleContext):

        def __init__(self, parser, parent=None, invokingState=-1):
            super(MetricAlertConditionParser.Dim_valueContext, self).__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.NUMBER)
            else:
                return self.getToken(MetricAlertConditionParser.NUMBER, i)

        def WORD(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WORD)
            else:
                return self.getToken(MetricAlertConditionParser.WORD, i)

        def WHITESPACE(self, i=None):
            if i is None:
                return self.getTokens(MetricAlertConditionParser.WHITESPACE)
            else:
                return self.getToken(MetricAlertConditionParser.WHITESPACE, i)

        def getRuleIndex(self):
            return MetricAlertConditionParser.RULE_dim_value

        def enterRule(self, listener):
            if hasattr(listener, "enterDim_value"):
                listener.enterDim_value(self)

        def exitRule(self, listener):
            if hasattr(listener, "exitDim_value"):
                listener.exitDim_value(self)




    def dim_value(self):

        localctx = MetricAlertConditionParser.Dim_valueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_dim_value)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 119 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 118
                    _la = self._input.LA(1)
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.T__8) | (1 << MetricAlertConditionParser.T__9) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 121 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





