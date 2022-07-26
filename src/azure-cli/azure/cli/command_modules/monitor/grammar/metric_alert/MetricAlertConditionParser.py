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
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\36")
        buf.write("\u00c7\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23\t\23")
        buf.write("\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30\4\31")
        buf.write("\t\31\4\32\t\32\4\33\t\33\3\2\3\2\3\2\3\2\7\2;\n\2\f\2")
        buf.write("\16\2>\13\2\3\2\3\2\3\2\3\2\3\2\3\2\5\2F\n\2\3\2\3\2\3")
        buf.write("\2\5\2K\n\2\3\2\3\2\7\2O\n\2\f\2\16\2R\13\2\3\2\3\2\5")
        buf.write("\2V\n\2\3\2\7\2Y\n\2\f\2\16\2\\\13\2\3\3\3\3\3\3\3\4\6")
        buf.write("\4b\n\4\r\4\16\4c\3\5\6\5g\n\5\r\5\16\5h\3\6\3\6\3\6\3")
        buf.write("\7\3\7\3\b\3\b\3\b\3\t\3\t\3\t\3\t\3\t\3\t\3\t\3\t\3\t")
        buf.write("\7\t|\n\t\f\t\16\t\177\13\t\3\n\3\n\3\n\3\13\3\13\3\13")
        buf.write("\3\f\3\f\3\f\3\r\3\r\3\16\3\16\3\16\3\17\6\17\u0090\n")
        buf.write("\17\r\17\16\17\u0091\3\20\3\20\3\20\3\21\3\21\3\21\3\21")
        buf.write("\3\21\7\21\u009c\n\21\f\21\16\21\u009f\13\21\3\22\3\22")
        buf.write("\3\22\3\22\3\23\3\23\3\23\3\24\3\24\3\24\3\25\3\25\3\25")
        buf.write("\3\26\3\26\3\26\3\27\3\27\3\27\3\27\7\27\u00b5\n\27\f")
        buf.write("\27\16\27\u00b8\13\27\3\30\6\30\u00bb\n\30\r\30\16\30")
        buf.write("\u00bc\3\31\3\31\3\31\3\32\3\32\3\32\3\33\3\33\3\33\2")
        buf.write("\2\34\2\4\6\b\n\f\16\20\22\24\26\30\32\34\36 \"$&(*,.")
        buf.write("\60\62\64\2\t\5\2\3\4\32\32\36\36\6\2\3\13\32\32\34\34")
        buf.write("\36\36\b\2\3\3\7\7\t\t\f\f\32\32\36\36\4\2\n\n\20\20\3")
        buf.write("\2\21\22\4\2\n\n\23\23\t\2\3\3\5\5\7\13\r\16\32\32\34")
        buf.write("\34\36\36\2\u00b9\2\66\3\2\2\2\4]\3\2\2\2\6a\3\2\2\2\b")
        buf.write("f\3\2\2\2\nj\3\2\2\2\fm\3\2\2\2\16o\3\2\2\2\20r\3\2\2")
        buf.write("\2\22\u0080\3\2\2\2\24\u0083\3\2\2\2\26\u0086\3\2\2\2")
        buf.write("\30\u0089\3\2\2\2\32\u008b\3\2\2\2\34\u008f\3\2\2\2\36")
        buf.write("\u0093\3\2\2\2 \u0096\3\2\2\2\"\u00a0\3\2\2\2$\u00a4\3")
        buf.write("\2\2\2&\u00a7\3\2\2\2(\u00aa\3\2\2\2*\u00ad\3\2\2\2,\u00b0")
        buf.write("\3\2\2\2.\u00ba\3\2\2\2\60\u00be\3\2\2\2\62\u00c1\3\2")
        buf.write("\2\2\64\u00c4\3\2\2\2\66<\5\4\3\2\678\5\6\4\289\7\3\2")
        buf.write("\29;\3\2\2\2:\67\3\2\2\2;>\3\2\2\2<:\3\2\2\2<=\3\2\2\2")
        buf.write("=E\3\2\2\2><\3\2\2\2?@\7\33\2\2@A\5\b\5\2AB\7\33\2\2B")
        buf.write("C\7\34\2\2CF\3\2\2\2DF\5\b\5\2E?\3\2\2\2ED\3\2\2\2FG\3")
        buf.write("\2\2\2GJ\5\n\6\2HK\5\f\7\2IK\5\20\t\2JH\3\2\2\2JI\3\2")
        buf.write("\2\2KP\3\2\2\2LM\7\34\2\2MO\5 \21\2NL\3\2\2\2OR\3\2\2")
        buf.write("\2PN\3\2\2\2PQ\3\2\2\2QU\3\2\2\2RP\3\2\2\2ST\7\34\2\2")
        buf.write("TV\5\60\31\2US\3\2\2\2UV\3\2\2\2VZ\3\2\2\2WY\7\35\2\2")
        buf.write("XW\3\2\2\2Y\\\3\2\2\2ZX\3\2\2\2Z[\3\2\2\2[\3\3\2\2\2\\")
        buf.write("Z\3\2\2\2]^\7\36\2\2^_\7\34\2\2_\5\3\2\2\2`b\t\2\2\2a")
        buf.write("`\3\2\2\2bc\3\2\2\2ca\3\2\2\2cd\3\2\2\2d\7\3\2\2\2eg\t")
        buf.write("\3\2\2fe\3\2\2\2gh\3\2\2\2hf\3\2\2\2hi\3\2\2\2i\t\3\2")
        buf.write("\2\2jk\7\31\2\2kl\7\34\2\2l\13\3\2\2\2mn\7\32\2\2n\r\3")
        buf.write("\2\2\2op\7\24\2\2pq\7\34\2\2q\17\3\2\2\2rs\5\16\b\2st")
        buf.write("\5\22\n\2tu\5\24\13\2uv\5\26\f\2v}\5\30\r\2wx\7\34\2\2")
        buf.write("xy\5\32\16\2yz\5\34\17\2z|\3\2\2\2{w\3\2\2\2|\177\3\2")
        buf.write("\2\2}{\3\2\2\2}~\3\2\2\2~\21\3\2\2\2\177}\3\2\2\2\u0080")
        buf.write("\u0081\7\36\2\2\u0081\u0082\7\34\2\2\u0082\23\3\2\2\2")
        buf.write("\u0083\u0084\7\32\2\2\u0084\u0085\7\34\2\2\u0085\25\3")
        buf.write("\2\2\2\u0086\u0087\7\25\2\2\u0087\u0088\7\34\2\2\u0088")
        buf.write("\27\3\2\2\2\u0089\u008a\7\32\2\2\u008a\31\3\2\2\2\u008b")
        buf.write("\u008c\7\26\2\2\u008c\u008d\7\34\2\2\u008d\33\3\2\2\2")
        buf.write("\u008e\u0090\t\4\2\2\u008f\u008e\3\2\2\2\u0090\u0091\3")
        buf.write("\2\2\2\u0091\u008f\3\2\2\2\u0091\u0092\3\2\2\2\u0092\35")
        buf.write("\3\2\2\2\u0093\u0094\7\17\2\2\u0094\u0095\7\34\2\2\u0095")
        buf.write("\37\3\2\2\2\u0096\u0097\5\36\20\2\u0097\u009d\5\"\22\2")
        buf.write("\u0098\u0099\5$\23\2\u0099\u009a\5\"\22\2\u009a\u009c")
        buf.write("\3\2\2\2\u009b\u0098\3\2\2\2\u009c\u009f\3\2\2\2\u009d")
        buf.write("\u009b\3\2\2\2\u009d\u009e\3\2\2\2\u009e!\3\2\2\2\u009f")
        buf.write("\u009d\3\2\2\2\u00a0\u00a1\5*\26\2\u00a1\u00a2\5&\24\2")
        buf.write("\u00a2\u00a3\5,\27\2\u00a3#\3\2\2\2\u00a4\u00a5\t\5\2")
        buf.write("\2\u00a5\u00a6\7\34\2\2\u00a6%\3\2\2\2\u00a7\u00a8\t\6")
        buf.write("\2\2\u00a8\u00a9\7\34\2\2\u00a9\'\3\2\2\2\u00aa\u00ab")
        buf.write("\t\7\2\2\u00ab\u00ac\7\34\2\2\u00ac)\3\2\2\2\u00ad\u00ae")
        buf.write("\7\36\2\2\u00ae\u00af\7\34\2\2\u00af+\3\2\2\2\u00b0\u00b6")
        buf.write("\5.\30\2\u00b1\u00b2\5(\25\2\u00b2\u00b3\5.\30\2\u00b3")
        buf.write("\u00b5\3\2\2\2\u00b4\u00b1\3\2\2\2\u00b5\u00b8\3\2\2\2")
        buf.write("\u00b6\u00b4\3\2\2\2\u00b6\u00b7\3\2\2\2\u00b7-\3\2\2")
        buf.write("\2\u00b8\u00b6\3\2\2\2\u00b9\u00bb\t\b\2\2\u00ba\u00b9")
        buf.write("\3\2\2\2\u00bb\u00bc\3\2\2\2\u00bc\u00ba\3\2\2\2\u00bc")
        buf.write("\u00bd\3\2\2\2\u00bd/\3\2\2\2\u00be\u00bf\5\62\32\2\u00bf")
        buf.write("\u00c0\5\64\33\2\u00c0\61\3\2\2\2\u00c1\u00c2\7\27\2\2")
        buf.write("\u00c2\u00c3\7\34\2\2\u00c3\63\3\2\2\2\u00c4\u00c5\7\30")
        buf.write("\2\2\u00c5\65\3\2\2\2\17<EJPUZch}\u0091\u009d\u00b6\u00bc")
        return buf.getvalue()


class MetricAlertConditionParser ( Parser ):

    grammarFileName = "MetricAlertCondition.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'.'", "'/'", "'_'", "'\\'", "':'", "'%'", 
                     "'-'", "','", "'|'", "'+'", "'*'", "'~'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "WHERE", "AND", "INCLUDES", "EXCLUDES", 
                      "OR", "DYNAMIC", "OF", "SINCE", "WITH", "SKIPMETRICVALIDATION", 
                      "OPERATOR", "NUMBER", "QUOTE", "WHITESPACE", "NEWLINE", 
                      "WORD" ]

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
    WHERE=13
    AND=14
    INCLUDES=15
    EXCLUDES=16
    OR=17
    DYNAMIC=18
    OF=19
    SINCE=20
    WITH=21
    SKIPMETRICVALIDATION=22
    OPERATOR=23
    NUMBER=24
    QUOTE=25
    WHITESPACE=26
    NEWLINE=27
    WORD=28

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
            if token in [MetricAlertConditionParser.QUOTE]:
                self.state = 61
                self.match(MetricAlertConditionParser.QUOTE)
                self.state = 62
                self.metric()
                self.state = 63
                self.match(MetricAlertConditionParser.QUOTE)
                self.state = 64
                self.match(MetricAlertConditionParser.WHITESPACE)
                pass
            elif token in [MetricAlertConditionParser.T__0, MetricAlertConditionParser.T__1, MetricAlertConditionParser.T__2, MetricAlertConditionParser.T__3, MetricAlertConditionParser.T__4, MetricAlertConditionParser.T__5, MetricAlertConditionParser.T__6, MetricAlertConditionParser.T__7, MetricAlertConditionParser.T__8, MetricAlertConditionParser.NUMBER, MetricAlertConditionParser.WHITESPACE, MetricAlertConditionParser.WORD]:
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
            if token in [MetricAlertConditionParser.NUMBER]:
                self.state = 70
                self.threshold()
                pass
            elif token in [MetricAlertConditionParser.DYNAMIC]:
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
            if _la==MetricAlertConditionParser.WHITESPACE:
                self.state = 81
                self.match(MetricAlertConditionParser.WHITESPACE)
                self.state = 82
                self.options_()


            self.state = 88
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==MetricAlertConditionParser.NEWLINE:
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
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__1) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WORD))) != 0)):
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
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__1) | (1 << MetricAlertConditionParser.T__2) | (1 << MetricAlertConditionParser.T__3) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__5) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.T__7) | (1 << MetricAlertConditionParser.T__8) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 102 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__1) | (1 << MetricAlertConditionParser.T__2) | (1 << MetricAlertConditionParser.T__3) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__5) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.T__7) | (1 << MetricAlertConditionParser.T__8) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
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
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.T__9) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WORD))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 143 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.T__9) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WORD))) != 0)):
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
            while _la==MetricAlertConditionParser.T__7 or _la==MetricAlertConditionParser.AND:
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
            if not(_la==MetricAlertConditionParser.T__7 or _la==MetricAlertConditionParser.AND):
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
            if not(_la==MetricAlertConditionParser.INCLUDES or _la==MetricAlertConditionParser.EXCLUDES):
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
            if not(_la==MetricAlertConditionParser.T__7 or _la==MetricAlertConditionParser.OR):
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
                    if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MetricAlertConditionParser.T__0) | (1 << MetricAlertConditionParser.T__2) | (1 << MetricAlertConditionParser.T__4) | (1 << MetricAlertConditionParser.T__5) | (1 << MetricAlertConditionParser.T__6) | (1 << MetricAlertConditionParser.T__7) | (1 << MetricAlertConditionParser.T__8) | (1 << MetricAlertConditionParser.T__10) | (1 << MetricAlertConditionParser.T__11) | (1 << MetricAlertConditionParser.NUMBER) | (1 << MetricAlertConditionParser.WHITESPACE) | (1 << MetricAlertConditionParser.WORD))) != 0)):
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





