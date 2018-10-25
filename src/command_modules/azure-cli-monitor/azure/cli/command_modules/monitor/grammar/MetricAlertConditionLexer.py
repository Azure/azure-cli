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
        buf.write(u"\20\u00b8\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \3\2\3\2\3\3\3\3\3")
        buf.write(u"\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3")
        buf.write(u"\n\3\13\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20")
        buf.write(u"\3\20\3\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3")
        buf.write(u"\25\3\26\3\26\3\26\3\26\3\26\3\26\3\27\3\27\3\27\3\27")
        buf.write(u"\3\30\3\30\3\30\3\30\3\30\3\30\3\30\3\30\3\30\3\31\3")
        buf.write(u"\31\3\31\3\31\3\31\3\31\3\31\3\31\3\31\3\32\3\32\3\32")
        buf.write(u"\3\33\3\33\3\33\3\33\3\33\3\33\3\33\3\33\3\33\5\33\u0092")
        buf.write(u"\n\33\3\34\6\34\u0095\n\34\r\34\16\34\u0096\3\34\3\34")
        buf.write(u"\6\34\u009b\n\34\r\34\16\34\u009c\5\34\u009f\n\34\3\35")
        buf.write(u"\3\35\3\36\6\36\u00a4\n\36\r\36\16\36\u00a5\3\37\5\37")
        buf.write(u"\u00a9\n\37\3\37\3\37\6\37\u00ad\n\37\r\37\16\37\u00ae")
        buf.write(u"\3 \3 \3 \3 \6 \u00b5\n \r \16 \u00b6\2\2!\3\3\5\4\7")
        buf.write(u"\5\t\2\13\2\r\2\17\2\21\2\23\2\25\2\27\2\31\2\33\2\35")
        buf.write(u"\2\37\2!\2#\2%\2\'\2)\2+\6-\7/\b\61\t\63\n\65\13\67\f")
        buf.write(u"9\r;\16=\17?\20\3\2\26\4\2CCcc\4\2EEee\4\2FFff\4\2GG")
        buf.write(u"gg\4\2JJjj\4\2KKkk\4\2NNnn\4\2PPpp\4\2QQqq\4\2TTtt\4")
        buf.write(u"\2UUuu\4\2WWww\4\2YYyy\4\2ZZzz\3\2\62;\3\2c|\3\2C\\\4")
        buf.write(u"\2..\60\60\4\2$$))\4\2\13\13\"\"\2\u00b6\2\3\3\2\2\2")
        buf.write(u"\2\5\3\2\2\2\2\7\3\2\2\2\2+\3\2\2\2\2-\3\2\2\2\2/\3\2")
        buf.write(u"\2\2\2\61\3\2\2\2\2\63\3\2\2\2\2\65\3\2\2\2\2\67\3\2")
        buf.write(u"\2\2\29\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2\2?\3\2\2\2\3A\3")
        buf.write(u"\2\2\2\5C\3\2\2\2\7E\3\2\2\2\tG\3\2\2\2\13I\3\2\2\2\r")
        buf.write(u"K\3\2\2\2\17M\3\2\2\2\21O\3\2\2\2\23Q\3\2\2\2\25S\3\2")
        buf.write(u"\2\2\27U\3\2\2\2\31W\3\2\2\2\33Y\3\2\2\2\35[\3\2\2\2")
        buf.write(u"\37]\3\2\2\2!_\3\2\2\2#a\3\2\2\2%c\3\2\2\2\'e\3\2\2\2")
        buf.write(u")g\3\2\2\2+i\3\2\2\2-o\3\2\2\2/s\3\2\2\2\61|\3\2\2\2")
        buf.write(u"\63\u0085\3\2\2\2\65\u0091\3\2\2\2\67\u0094\3\2\2\29")
        buf.write(u"\u00a0\3\2\2\2;\u00a3\3\2\2\2=\u00ac\3\2\2\2?\u00b4\3")
        buf.write(u"\2\2\2AB\7\60\2\2B\4\3\2\2\2CD\7\61\2\2D\6\3\2\2\2EF")
        buf.write(u"\7.\2\2F\b\3\2\2\2GH\t\2\2\2H\n\3\2\2\2IJ\t\3\2\2J\f")
        buf.write(u"\3\2\2\2KL\t\4\2\2L\16\3\2\2\2MN\t\5\2\2N\20\3\2\2\2")
        buf.write(u"OP\t\6\2\2P\22\3\2\2\2QR\t\7\2\2R\24\3\2\2\2ST\t\b\2")
        buf.write(u"\2T\26\3\2\2\2UV\t\t\2\2V\30\3\2\2\2WX\t\n\2\2X\32\3")
        buf.write(u"\2\2\2YZ\t\13\2\2Z\34\3\2\2\2[\\\t\f\2\2\\\36\3\2\2\2")
        buf.write(u"]^\t\r\2\2^ \3\2\2\2_`\t\16\2\2`\"\3\2\2\2ab\t\17\2\2")
        buf.write(u"b$\3\2\2\2cd\t\20\2\2d&\3\2\2\2ef\t\21\2\2f(\3\2\2\2")
        buf.write(u"gh\t\22\2\2h*\3\2\2\2ij\5!\21\2jk\5\21\t\2kl\5\17\b\2")
        buf.write(u"lm\5\33\16\2mn\5\17\b\2n,\3\2\2\2op\5\t\5\2pq\5\27\f")
        buf.write(u"\2qr\5\r\7\2r.\3\2\2\2st\5\23\n\2tu\5\27\f\2uv\5\13\6")
        buf.write(u"\2vw\5\25\13\2wx\5\37\20\2xy\5\r\7\2yz\5\17\b\2z{\5\35")
        buf.write(u"\17\2{\60\3\2\2\2|}\5\17\b\2}~\5#\22\2~\177\5\13\6\2")
        buf.write(u"\177\u0080\5\25\13\2\u0080\u0081\5\37\20\2\u0081\u0082")
        buf.write(u"\5\r\7\2\u0082\u0083\5\17\b\2\u0083\u0084\5\35\17\2\u0084")
        buf.write(u"\62\3\2\2\2\u0085\u0086\5\31\r\2\u0086\u0087\5\33\16")
        buf.write(u"\2\u0087\64\3\2\2\2\u0088\u0092\7>\2\2\u0089\u008a\7")
        buf.write(u">\2\2\u008a\u0092\7?\2\2\u008b\u0092\7?\2\2\u008c\u008d")
        buf.write(u"\7@\2\2\u008d\u0092\7?\2\2\u008e\u0092\7@\2\2\u008f\u0090")
        buf.write(u"\7#\2\2\u0090\u0092\7?\2\2\u0091\u0088\3\2\2\2\u0091")
        buf.write(u"\u0089\3\2\2\2\u0091\u008b\3\2\2\2\u0091\u008c\3\2\2")
        buf.write(u"\2\u0091\u008e\3\2\2\2\u0091\u008f\3\2\2\2\u0092\66\3")
        buf.write(u"\2\2\2\u0093\u0095\5%\23\2\u0094\u0093\3\2\2\2\u0095")
        buf.write(u"\u0096\3\2\2\2\u0096\u0094\3\2\2\2\u0096\u0097\3\2\2")
        buf.write(u"\2\u0097\u009e\3\2\2\2\u0098\u009a\t\23\2\2\u0099\u009b")
        buf.write(u"\5%\23\2\u009a\u0099\3\2\2\2\u009b\u009c\3\2\2\2\u009c")
        buf.write(u"\u009a\3\2\2\2\u009c\u009d\3\2\2\2\u009d\u009f\3\2\2")
        buf.write(u"\2\u009e\u0098\3\2\2\2\u009e\u009f\3\2\2\2\u009f8\3\2")
        buf.write(u"\2\2\u00a0\u00a1\t\24\2\2\u00a1:\3\2\2\2\u00a2\u00a4")
        buf.write(u"\t\25\2\2\u00a3\u00a2\3\2\2\2\u00a4\u00a5\3\2\2\2\u00a5")
        buf.write(u"\u00a3\3\2\2\2\u00a5\u00a6\3\2\2\2\u00a6<\3\2\2\2\u00a7")
        buf.write(u"\u00a9\7\17\2\2\u00a8\u00a7\3\2\2\2\u00a8\u00a9\3\2\2")
        buf.write(u"\2\u00a9\u00aa\3\2\2\2\u00aa\u00ad\7\f\2\2\u00ab\u00ad")
        buf.write(u"\7\17\2\2\u00ac\u00a8\3\2\2\2\u00ac\u00ab\3\2\2\2\u00ad")
        buf.write(u"\u00ae\3\2\2\2\u00ae\u00ac\3\2\2\2\u00ae\u00af\3\2\2")
        buf.write(u"\2\u00af>\3\2\2\2\u00b0\u00b5\5\'\24\2\u00b1\u00b5\5")
        buf.write(u")\25\2\u00b2\u00b5\5%\23\2\u00b3\u00b5\7a\2\2\u00b4\u00b0")
        buf.write(u"\3\2\2\2\u00b4\u00b1\3\2\2\2\u00b4\u00b2\3\2\2\2\u00b4")
        buf.write(u"\u00b3\3\2\2\2\u00b5\u00b6\3\2\2\2\u00b6\u00b4\3\2\2")
        buf.write(u"\2\u00b6\u00b7\3\2\2\2\u00b7@\3\2\2\2\r\2\u0091\u0096")
        buf.write(u"\u009c\u009e\u00a5\u00a8\u00ac\u00ae\u00b4\u00b6\2")
        return buf.getvalue()


class MetricAlertConditionLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    WHERE = 4
    AND = 5
    INCLUDES = 6
    EXCLUDES = 7
    OR = 8
    OPERATOR = 9
    NUMBER = 10
    QUOTE = 11
    WHITESPACE = 12
    NEWLINE = 13
    WORD = 14

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"','" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"A", u"C", u"D", u"E", u"H", 
                  u"I", u"L", u"N", u"O", u"R", u"S", u"U", u"W", u"X", 
                  u"DIGIT", u"LOWERCASE", u"UPPERCASE", u"WHERE", u"AND", 
                  u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", u"NUMBER", 
                  u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


