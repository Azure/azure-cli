# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=all

# Generated from MetricAlertCondition.g4 by ANTLR 4.7.1
# encoding: utf-8
from __future__ import print_function
from antlr4 import *
from io import StringIO
import sys

def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3")
        buf.write(u"\17{\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write(u"\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4")
        buf.write(u"\16\t\16\4\17\t\17\4\20\t\20\3\2\3\2\3\2\3\2\7\2%\n\2")
        buf.write(u"\f\2\16\2(\13\2\3\2\3\2\3\2\3\2\3\2\3\2\5\2\60\n\2\3")
        buf.write(u"\2\3\2\3\2\3\2\7\2\66\n\2\f\2\16\29\13\2\3\2\7\2<\n\2")
        buf.write(u"\f\2\16\2?\13\2\3\3\3\3\3\3\3\4\3\4\3\5\6\5G\n\5\r\5")
        buf.write(u"\16\5H\3\6\3\6\3\6\3\7\3\7\3\b\3\b\3\b\3\t\3\t\3\t\3")
        buf.write(u"\t\3\t\7\tX\n\t\f\t\16\t[\13\t\3\n\3\n\3\n\3\n\3\13\3")
        buf.write(u"\13\3\13\3\f\3\f\3\f\3\r\3\r\3\r\3\16\3\16\3\16\3\17")
        buf.write(u"\3\17\3\17\3\17\7\17q\n\17\f\17\16\17t\13\17\3\20\6\20")
        buf.write(u"w\n\20\r\20\16\20x\3\20\2\2\21\2\4\6\b\n\f\16\20\22\24")
        buf.write(u"\26\30\32\34\36\2\7\4\2\r\r\17\17\4\2\4\4\6\6\3\2\7\b")
        buf.write(u"\4\2\4\4\t\t\5\2\13\13\r\r\17\17\2s\2 \3\2\2\2\4@\3\2")
        buf.write(u"\2\2\6C\3\2\2\2\bF\3\2\2\2\nJ\3\2\2\2\fM\3\2\2\2\16O")
        buf.write(u"\3\2\2\2\20R\3\2\2\2\22\\\3\2\2\2\24`\3\2\2\2\26c\3\2")
        buf.write(u"\2\2\30f\3\2\2\2\32i\3\2\2\2\34l\3\2\2\2\36v\3\2\2\2")
        buf.write(u" &\5\4\3\2!\"\5\6\4\2\"#\7\3\2\2#%\3\2\2\2$!\3\2\2\2")
        buf.write(u"%(\3\2\2\2&$\3\2\2\2&\'\3\2\2\2\'/\3\2\2\2(&\3\2\2\2")
        buf.write(u")*\7\f\2\2*+\5\b\5\2+,\7\f\2\2,-\7\r\2\2-\60\3\2\2\2")
        buf.write(u".\60\5\b\5\2/)\3\2\2\2/.\3\2\2\2\60\61\3\2\2\2\61\62")
        buf.write(u"\5\n\6\2\62\67\5\f\7\2\63\64\7\r\2\2\64\66\5\20\t\2\65")
        buf.write(u"\63\3\2\2\2\669\3\2\2\2\67\65\3\2\2\2\678\3\2\2\28=\3")
        buf.write(u"\2\2\29\67\3\2\2\2:<\7\16\2\2;:\3\2\2\2<?\3\2\2\2=;\3")
        buf.write(u"\2\2\2=>\3\2\2\2>\3\3\2\2\2?=\3\2\2\2@A\7\17\2\2AB\7")
        buf.write(u"\r\2\2B\5\3\2\2\2CD\7\17\2\2D\7\3\2\2\2EG\t\2\2\2FE\3")
        buf.write(u"\2\2\2GH\3\2\2\2HF\3\2\2\2HI\3\2\2\2I\t\3\2\2\2JK\7\n")
        buf.write(u"\2\2KL\7\r\2\2L\13\3\2\2\2MN\7\13\2\2N\r\3\2\2\2OP\7")
        buf.write(u"\5\2\2PQ\7\r\2\2Q\17\3\2\2\2RS\5\16\b\2SY\5\22\n\2TU")
        buf.write(u"\5\24\13\2UV\5\22\n\2VX\3\2\2\2WT\3\2\2\2X[\3\2\2\2Y")
        buf.write(u"W\3\2\2\2YZ\3\2\2\2Z\21\3\2\2\2[Y\3\2\2\2\\]\5\32\16")
        buf.write(u"\2]^\5\26\f\2^_\5\34\17\2_\23\3\2\2\2`a\t\3\2\2ab\7\r")
        buf.write(u"\2\2b\25\3\2\2\2cd\t\4\2\2de\7\r\2\2e\27\3\2\2\2fg\t")
        buf.write(u"\5\2\2gh\7\r\2\2h\31\3\2\2\2ij\7\17\2\2jk\7\r\2\2k\33")
        buf.write(u"\3\2\2\2lr\5\36\20\2mn\5\30\r\2no\5\36\20\2oq\3\2\2\2")
        buf.write(u"pm\3\2\2\2qt\3\2\2\2rp\3\2\2\2rs\3\2\2\2s\35\3\2\2\2")
        buf.write(u"tr\3\2\2\2uw\t\6\2\2vu\3\2\2\2wx\3\2\2\2xv\3\2\2\2xy")
        buf.write(u"\3\2\2\2y\37\3\2\2\2\n&/\67=HYrx")
        return buf.getvalue()


class MetricAlertConditionParser ( Parser ):

    grammarFileName = "MetricAlertCondition.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ u"<INVALID>", u"'.'", u"','" ]

    symbolicNames = [ u"<INVALID>", u"<INVALID>", u"<INVALID>", u"WHERE", 
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
    WHERE=3
    AND=4
    INCLUDES=5
    EXCLUDES=6
    OR=7
    OPERATOR=8
    NUMBER=9
    QUOTE=10
    WHITESPACE=11
    NEWLINE=12
    WORD=13

    def __init__(self, input, output=sys.stdout):
        super(MetricAlertConditionParser, self).__init__(input, output=output)
        self.checkVersion("4.7.1")
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
            elif token in [MetricAlertConditionParser.WHITESPACE, MetricAlertConditionParser.WORD]:
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

        def WORD(self):
            return self.getToken(MetricAlertConditionParser.WORD, 0)

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
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 65
            self.match(MetricAlertConditionParser.WORD)
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
            self.state = 68 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 67
                _la = self._input.LA(1)
                if not(_la==MetricAlertConditionParser.WHITESPACE or _la==MetricAlertConditionParser.WORD):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 70 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==MetricAlertConditionParser.WHITESPACE or _la==MetricAlertConditionParser.WORD):
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
            self.state = 72
            self.match(MetricAlertConditionParser.OPERATOR)
            self.state = 73
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
            self.state = 75
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
            self.state = 77
            self.match(MetricAlertConditionParser.WHERE)
            self.state = 78
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
            self.state = 80
            self.where()
            self.state = 81
            self.dimension()
            self.state = 87
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==MetricAlertConditionParser.T__1 or _la==MetricAlertConditionParser.AND:
                self.state = 82
                self.dim_separator()
                self.state = 83
                self.dimension()
                self.state = 89
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
            self.state = 90
            self.dim_name()
            self.state = 91
            self.dim_operator()
            self.state = 92
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
            self.state = 94
            _la = self._input.LA(1)
            if not(_la==MetricAlertConditionParser.T__1 or _la==MetricAlertConditionParser.AND):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 95
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
            self.state = 97
            _la = self._input.LA(1)
            if not(_la==MetricAlertConditionParser.INCLUDES or _la==MetricAlertConditionParser.EXCLUDES):
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
            self.state = 100
            _la = self._input.LA(1)
            if not(_la==MetricAlertConditionParser.T__1 or _la==MetricAlertConditionParser.OR):
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
            self.state = 103
            self.match(MetricAlertConditionParser.WORD)
            self.state = 104
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
            self.state = 106
            self.dim_value()
            self.state = 112
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,6,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 107
                    self.dim_val_separator()
                    self.state = 108
                    self.dim_value() 
                self.state = 114
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
            self.state = 116 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 115
                    _la = self._input.LA(1)
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 118 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,7,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





