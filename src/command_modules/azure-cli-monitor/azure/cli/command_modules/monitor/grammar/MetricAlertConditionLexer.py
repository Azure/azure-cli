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
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2")
        buf.write(u"\17\u00b4\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\3\2\3\2\3\3\3\3\3\4\3\4")
        buf.write(u"\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n\3\13")
        buf.write(u"\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20\3\20\3")
        buf.write(u"\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3\25\3\25")
        buf.write(u"\3\25\3\25\3\25\3\26\3\26\3\26\3\26\3\27\3\27\3\27\3")
        buf.write(u"\27\3\27\3\27\3\27\3\27\3\27\3\30\3\30\3\30\3\30\3\30")
        buf.write(u"\3\30\3\30\3\30\3\30\3\31\3\31\3\31\3\32\3\32\3\32\3")
        buf.write(u"\32\3\32\3\32\3\32\3\32\3\32\5\32\u008e\n\32\3\33\6\33")
        buf.write(u"\u0091\n\33\r\33\16\33\u0092\3\33\3\33\6\33\u0097\n\33")
        buf.write(u"\r\33\16\33\u0098\5\33\u009b\n\33\3\34\3\34\3\35\6\35")
        buf.write(u"\u00a0\n\35\r\35\16\35\u00a1\3\36\5\36\u00a5\n\36\3\36")
        buf.write(u"\3\36\6\36\u00a9\n\36\r\36\16\36\u00aa\3\37\3\37\3\37")
        buf.write(u"\3\37\6\37\u00b1\n\37\r\37\16\37\u00b2\2\2 \3\3\5\4\7")
        buf.write(u"\2\t\2\13\2\r\2\17\2\21\2\23\2\25\2\27\2\31\2\33\2\35")
        buf.write(u"\2\37\2!\2#\2%\2\'\2)\5+\6-\7/\b\61\t\63\n\65\13\67\f")
        buf.write(u"9\r;\16=\17\3\2\26\4\2CCcc\4\2EEee\4\2FFff\4\2GGgg\4")
        buf.write(u"\2JJjj\4\2KKkk\4\2NNnn\4\2PPpp\4\2QQqq\4\2TTtt\4\2UU")
        buf.write(u"uu\4\2WWww\4\2YYyy\4\2ZZzz\3\2\62;\3\2c|\3\2C\\\4\2.")
        buf.write(u".\60\60\4\2$$))\4\2\13\13\"\"\2\u00b2\2\3\3\2\2\2\2\5")
        buf.write(u"\3\2\2\2\2)\3\2\2\2\2+\3\2\2\2\2-\3\2\2\2\2/\3\2\2\2")
        buf.write(u"\2\61\3\2\2\2\2\63\3\2\2\2\2\65\3\2\2\2\2\67\3\2\2\2")
        buf.write(u"\29\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2\3?\3\2\2\2\5A\3\2\2")
        buf.write(u"\2\7C\3\2\2\2\tE\3\2\2\2\13G\3\2\2\2\rI\3\2\2\2\17K\3")
        buf.write(u"\2\2\2\21M\3\2\2\2\23O\3\2\2\2\25Q\3\2\2\2\27S\3\2\2")
        buf.write(u"\2\31U\3\2\2\2\33W\3\2\2\2\35Y\3\2\2\2\37[\3\2\2\2!]")
        buf.write(u"\3\2\2\2#_\3\2\2\2%a\3\2\2\2\'c\3\2\2\2)e\3\2\2\2+k\3")
        buf.write(u"\2\2\2-o\3\2\2\2/x\3\2\2\2\61\u0081\3\2\2\2\63\u008d")
        buf.write(u"\3\2\2\2\65\u0090\3\2\2\2\67\u009c\3\2\2\29\u009f\3\2")
        buf.write(u"\2\2;\u00a8\3\2\2\2=\u00b0\3\2\2\2?@\7\60\2\2@\4\3\2")
        buf.write(u"\2\2AB\7.\2\2B\6\3\2\2\2CD\t\2\2\2D\b\3\2\2\2EF\t\3\2")
        buf.write(u"\2F\n\3\2\2\2GH\t\4\2\2H\f\3\2\2\2IJ\t\5\2\2J\16\3\2")
        buf.write(u"\2\2KL\t\6\2\2L\20\3\2\2\2MN\t\7\2\2N\22\3\2\2\2OP\t")
        buf.write(u"\b\2\2P\24\3\2\2\2QR\t\t\2\2R\26\3\2\2\2ST\t\n\2\2T\30")
        buf.write(u"\3\2\2\2UV\t\13\2\2V\32\3\2\2\2WX\t\f\2\2X\34\3\2\2\2")
        buf.write(u"YZ\t\r\2\2Z\36\3\2\2\2[\\\t\16\2\2\\ \3\2\2\2]^\t\17")
        buf.write(u"\2\2^\"\3\2\2\2_`\t\20\2\2`$\3\2\2\2ab\t\21\2\2b&\3\2")
        buf.write(u"\2\2cd\t\22\2\2d(\3\2\2\2ef\5\37\20\2fg\5\17\b\2gh\5")
        buf.write(u"\r\7\2hi\5\31\r\2ij\5\r\7\2j*\3\2\2\2kl\5\7\4\2lm\5\25")
        buf.write(u"\13\2mn\5\13\6\2n,\3\2\2\2op\5\21\t\2pq\5\25\13\2qr\5")
        buf.write(u"\t\5\2rs\5\23\n\2st\5\35\17\2tu\5\13\6\2uv\5\r\7\2vw")
        buf.write(u"\5\33\16\2w.\3\2\2\2xy\5\r\7\2yz\5!\21\2z{\5\t\5\2{|")
        buf.write(u"\5\23\n\2|}\5\35\17\2}~\5\13\6\2~\177\5\r\7\2\177\u0080")
        buf.write(u"\5\33\16\2\u0080\60\3\2\2\2\u0081\u0082\5\27\f\2\u0082")
        buf.write(u"\u0083\5\31\r\2\u0083\62\3\2\2\2\u0084\u008e\7>\2\2\u0085")
        buf.write(u"\u0086\7>\2\2\u0086\u008e\7?\2\2\u0087\u008e\7?\2\2\u0088")
        buf.write(u"\u0089\7@\2\2\u0089\u008e\7?\2\2\u008a\u008e\7@\2\2\u008b")
        buf.write(u"\u008c\7#\2\2\u008c\u008e\7?\2\2\u008d\u0084\3\2\2\2")
        buf.write(u"\u008d\u0085\3\2\2\2\u008d\u0087\3\2\2\2\u008d\u0088")
        buf.write(u"\3\2\2\2\u008d\u008a\3\2\2\2\u008d\u008b\3\2\2\2\u008e")
        buf.write(u"\64\3\2\2\2\u008f\u0091\5#\22\2\u0090\u008f\3\2\2\2\u0091")
        buf.write(u"\u0092\3\2\2\2\u0092\u0090\3\2\2\2\u0092\u0093\3\2\2")
        buf.write(u"\2\u0093\u009a\3\2\2\2\u0094\u0096\t\23\2\2\u0095\u0097")
        buf.write(u"\5#\22\2\u0096\u0095\3\2\2\2\u0097\u0098\3\2\2\2\u0098")
        buf.write(u"\u0096\3\2\2\2\u0098\u0099\3\2\2\2\u0099\u009b\3\2\2")
        buf.write(u"\2\u009a\u0094\3\2\2\2\u009a\u009b\3\2\2\2\u009b\66\3")
        buf.write(u"\2\2\2\u009c\u009d\t\24\2\2\u009d8\3\2\2\2\u009e\u00a0")
        buf.write(u"\t\25\2\2\u009f\u009e\3\2\2\2\u00a0\u00a1\3\2\2\2\u00a1")
        buf.write(u"\u009f\3\2\2\2\u00a1\u00a2\3\2\2\2\u00a2:\3\2\2\2\u00a3")
        buf.write(u"\u00a5\7\17\2\2\u00a4\u00a3\3\2\2\2\u00a4\u00a5\3\2\2")
        buf.write(u"\2\u00a5\u00a6\3\2\2\2\u00a6\u00a9\7\f\2\2\u00a7\u00a9")
        buf.write(u"\7\17\2\2\u00a8\u00a4\3\2\2\2\u00a8\u00a7\3\2\2\2\u00a9")
        buf.write(u"\u00aa\3\2\2\2\u00aa\u00a8\3\2\2\2\u00aa\u00ab\3\2\2")
        buf.write(u"\2\u00ab<\3\2\2\2\u00ac\u00b1\5%\23\2\u00ad\u00b1\5\'")
        buf.write(u"\24\2\u00ae\u00b1\5#\22\2\u00af\u00b1\7a\2\2\u00b0\u00ac")
        buf.write(u"\3\2\2\2\u00b0\u00ad\3\2\2\2\u00b0\u00ae\3\2\2\2\u00b0")
        buf.write(u"\u00af\3\2\2\2\u00b1\u00b2\3\2\2\2\u00b2\u00b0\3\2\2")
        buf.write(u"\2\u00b2\u00b3\3\2\2\2\u00b3>\3\2\2\2\r\2\u008d\u0092")
        buf.write(u"\u0098\u009a\u00a1\u00a4\u00a8\u00aa\u00b0\u00b2\2")
        return buf.getvalue()


class MetricAlertConditionLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    WHERE = 3
    AND = 4
    INCLUDES = 5
    EXCLUDES = 6
    OR = 7
    OPERATOR = 8
    NUMBER = 9
    QUOTE = 10
    WHITESPACE = 11
    NEWLINE = 12
    WORD = 13

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"','" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"A", u"C", u"D", u"E", u"H", u"I", 
                  u"L", u"N", u"O", u"R", u"S", u"U", u"W", u"X", u"DIGIT", 
                  u"LOWERCASE", u"UPPERCASE", u"WHERE", u"AND", u"INCLUDES", 
                  u"EXCLUDES", u"OR", u"OPERATOR", u"NUMBER", u"QUOTE", 
                  u"WHITESPACE", u"NEWLINE", u"WORD" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


