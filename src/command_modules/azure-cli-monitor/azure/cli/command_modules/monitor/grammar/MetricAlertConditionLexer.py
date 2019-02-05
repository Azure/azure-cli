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
        buf.write(u"\26\u00d0\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\4&\t&\3\2\3\2\3\3\3\3\3\4\3\4\3\5\3\5\3")
        buf.write(u"\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n\3\13\3\13\3\f")
        buf.write(u"\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20\3\20\3\21\3\21")
        buf.write(u"\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3\25\3\26\3\26\3")
        buf.write(u"\27\3\27\3\30\3\30\3\31\3\31\3\32\3\32\3\33\3\33\3\34")
        buf.write(u"\3\34\3\34\3\34\3\34\3\34\3\35\3\35\3\35\3\35\3\36\3")
        buf.write(u"\36\3\36\3\36\3\36\3\36\3\36\3\36\3\36\3\37\3\37\3\37")
        buf.write(u"\3\37\3\37\3\37\3\37\3\37\3\37\3 \3 \3 \3!\3!\3!\3!\3")
        buf.write(u"!\3!\3!\3!\3!\5!\u00aa\n!\3\"\6\"\u00ad\n\"\r\"\16\"")
        buf.write(u"\u00ae\3\"\3\"\6\"\u00b3\n\"\r\"\16\"\u00b4\5\"\u00b7")
        buf.write(u"\n\"\3#\3#\3$\6$\u00bc\n$\r$\16$\u00bd\3%\5%\u00c1\n")
        buf.write(u"%\3%\3%\6%\u00c5\n%\r%\16%\u00c6\3&\3&\3&\3&\6&\u00cd")
        buf.write(u"\n&\r&\16&\u00ce\2\2\'\3\3\5\4\7\5\t\6\13\7\r\b\17\t")
        buf.write(u"\21\n\23\13\25\2\27\2\31\2\33\2\35\2\37\2!\2#\2%\2\'")
        buf.write(u"\2)\2+\2-\2/\2\61\2\63\2\65\2\67\f9\r;\16=\17?\20A\21")
        buf.write(u"C\22E\23G\24I\25K\26\3\2\26\4\2CCcc\4\2EEee\4\2FFff\4")
        buf.write(u"\2GGgg\4\2JJjj\4\2KKkk\4\2NNnn\4\2PPpp\4\2QQqq\4\2TT")
        buf.write(u"tt\4\2UUuu\4\2WWww\4\2YYyy\4\2ZZzz\3\2\62;\3\2c|\3\2")
        buf.write(u"C\\\4\2..\60\60\4\2$$))\4\2\13\13\"\"\2\u00ce\2\3\3\2")
        buf.write(u"\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2")
        buf.write(u"\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2")
        buf.write(u"\67\3\2\2\2\29\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2\2?\3\2\2")
        buf.write(u"\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2\2I\3\2")
        buf.write(u"\2\2\2K\3\2\2\2\3M\3\2\2\2\5O\3\2\2\2\7Q\3\2\2\2\tS\3")
        buf.write(u"\2\2\2\13U\3\2\2\2\rW\3\2\2\2\17Y\3\2\2\2\21[\3\2\2\2")
        buf.write(u"\23]\3\2\2\2\25_\3\2\2\2\27a\3\2\2\2\31c\3\2\2\2\33e")
        buf.write(u"\3\2\2\2\35g\3\2\2\2\37i\3\2\2\2!k\3\2\2\2#m\3\2\2\2")
        buf.write(u"%o\3\2\2\2\'q\3\2\2\2)s\3\2\2\2+u\3\2\2\2-w\3\2\2\2/")
        buf.write(u"y\3\2\2\2\61{\3\2\2\2\63}\3\2\2\2\65\177\3\2\2\2\67\u0081")
        buf.write(u"\3\2\2\29\u0087\3\2\2\2;\u008b\3\2\2\2=\u0094\3\2\2\2")
        buf.write(u"?\u009d\3\2\2\2A\u00a9\3\2\2\2C\u00ac\3\2\2\2E\u00b8")
        buf.write(u"\3\2\2\2G\u00bb\3\2\2\2I\u00c4\3\2\2\2K\u00cc\3\2\2\2")
        buf.write(u"MN\7\60\2\2N\4\3\2\2\2OP\7\61\2\2P\6\3\2\2\2QR\7a\2\2")
        buf.write(u"R\b\3\2\2\2ST\7^\2\2T\n\3\2\2\2UV\7<\2\2V\f\3\2\2\2W")
        buf.write(u"X\7\'\2\2X\16\3\2\2\2YZ\7.\2\2Z\20\3\2\2\2[\\\7/\2\2")
        buf.write(u"\\\22\3\2\2\2]^\7,\2\2^\24\3\2\2\2_`\t\2\2\2`\26\3\2")
        buf.write(u"\2\2ab\t\3\2\2b\30\3\2\2\2cd\t\4\2\2d\32\3\2\2\2ef\t")
        buf.write(u"\5\2\2f\34\3\2\2\2gh\t\6\2\2h\36\3\2\2\2ij\t\7\2\2j ")
        buf.write(u"\3\2\2\2kl\t\b\2\2l\"\3\2\2\2mn\t\t\2\2n$\3\2\2\2op\t")
        buf.write(u"\n\2\2p&\3\2\2\2qr\t\13\2\2r(\3\2\2\2st\t\f\2\2t*\3\2")
        buf.write(u"\2\2uv\t\r\2\2v,\3\2\2\2wx\t\16\2\2x.\3\2\2\2yz\t\17")
        buf.write(u"\2\2z\60\3\2\2\2{|\t\20\2\2|\62\3\2\2\2}~\t\21\2\2~\64")
        buf.write(u"\3\2\2\2\177\u0080\t\22\2\2\u0080\66\3\2\2\2\u0081\u0082")
        buf.write(u"\5-\27\2\u0082\u0083\5\35\17\2\u0083\u0084\5\33\16\2")
        buf.write(u"\u0084\u0085\5\'\24\2\u0085\u0086\5\33\16\2\u00868\3")
        buf.write(u"\2\2\2\u0087\u0088\5\25\13\2\u0088\u0089\5#\22\2\u0089")
        buf.write(u"\u008a\5\31\r\2\u008a:\3\2\2\2\u008b\u008c\5\37\20\2")
        buf.write(u"\u008c\u008d\5#\22\2\u008d\u008e\5\27\f\2\u008e\u008f")
        buf.write(u"\5!\21\2\u008f\u0090\5+\26\2\u0090\u0091\5\31\r\2\u0091")
        buf.write(u"\u0092\5\33\16\2\u0092\u0093\5)\25\2\u0093<\3\2\2\2\u0094")
        buf.write(u"\u0095\5\33\16\2\u0095\u0096\5/\30\2\u0096\u0097\5\27")
        buf.write(u"\f\2\u0097\u0098\5!\21\2\u0098\u0099\5+\26\2\u0099\u009a")
        buf.write(u"\5\31\r\2\u009a\u009b\5\33\16\2\u009b\u009c\5)\25\2\u009c")
        buf.write(u">\3\2\2\2\u009d\u009e\5%\23\2\u009e\u009f\5\'\24\2\u009f")
        buf.write(u"@\3\2\2\2\u00a0\u00aa\7>\2\2\u00a1\u00a2\7>\2\2\u00a2")
        buf.write(u"\u00aa\7?\2\2\u00a3\u00aa\7?\2\2\u00a4\u00a5\7@\2\2\u00a5")
        buf.write(u"\u00aa\7?\2\2\u00a6\u00aa\7@\2\2\u00a7\u00a8\7#\2\2\u00a8")
        buf.write(u"\u00aa\7?\2\2\u00a9\u00a0\3\2\2\2\u00a9\u00a1\3\2\2\2")
        buf.write(u"\u00a9\u00a3\3\2\2\2\u00a9\u00a4\3\2\2\2\u00a9\u00a6")
        buf.write(u"\3\2\2\2\u00a9\u00a7\3\2\2\2\u00aaB\3\2\2\2\u00ab\u00ad")
        buf.write(u"\5\61\31\2\u00ac\u00ab\3\2\2\2\u00ad\u00ae\3\2\2\2\u00ae")
        buf.write(u"\u00ac\3\2\2\2\u00ae\u00af\3\2\2\2\u00af\u00b6\3\2\2")
        buf.write(u"\2\u00b0\u00b2\t\23\2\2\u00b1\u00b3\5\61\31\2\u00b2\u00b1")
        buf.write(u"\3\2\2\2\u00b3\u00b4\3\2\2\2\u00b4\u00b2\3\2\2\2\u00b4")
        buf.write(u"\u00b5\3\2\2\2\u00b5\u00b7\3\2\2\2\u00b6\u00b0\3\2\2")
        buf.write(u"\2\u00b6\u00b7\3\2\2\2\u00b7D\3\2\2\2\u00b8\u00b9\t\24")
        buf.write(u"\2\2\u00b9F\3\2\2\2\u00ba\u00bc\t\25\2\2\u00bb\u00ba")
        buf.write(u"\3\2\2\2\u00bc\u00bd\3\2\2\2\u00bd\u00bb\3\2\2\2\u00bd")
        buf.write(u"\u00be\3\2\2\2\u00beH\3\2\2\2\u00bf\u00c1\7\17\2\2\u00c0")
        buf.write(u"\u00bf\3\2\2\2\u00c0\u00c1\3\2\2\2\u00c1\u00c2\3\2\2")
        buf.write(u"\2\u00c2\u00c5\7\f\2\2\u00c3\u00c5\7\17\2\2\u00c4\u00c0")
        buf.write(u"\3\2\2\2\u00c4\u00c3\3\2\2\2\u00c5\u00c6\3\2\2\2\u00c6")
        buf.write(u"\u00c4\3\2\2\2\u00c6\u00c7\3\2\2\2\u00c7J\3\2\2\2\u00c8")
        buf.write(u"\u00cd\5\63\32\2\u00c9\u00cd\5\65\33\2\u00ca\u00cd\5")
        buf.write(u"\61\31\2\u00cb\u00cd\7a\2\2\u00cc\u00c8\3\2\2\2\u00cc")
        buf.write(u"\u00c9\3\2\2\2\u00cc\u00ca\3\2\2\2\u00cc\u00cb\3\2\2")
        buf.write(u"\2\u00cd\u00ce\3\2\2\2\u00ce\u00cc\3\2\2\2\u00ce\u00cf")
        buf.write(u"\3\2\2\2\u00cfL\3\2\2\2\r\2\u00a9\u00ae\u00b4\u00b6\u00bd")
        buf.write(u"\u00c0\u00c4\u00c6\u00cc\u00ce\2")
        return buf.getvalue()


class MetricAlertConditionLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    T__7 = 8
    T__8 = 9
    WHERE = 10
    AND = 11
    INCLUDES = 12
    EXCLUDES = 13
    OR = 14
    OPERATOR = 15
    NUMBER = 16
    QUOTE = 17
    WHITESPACE = 18
    NEWLINE = 19
    WORD = 20

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", u"'%'", u"','", u"'-'", 
            u"'*'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"T__8", u"A", u"C", u"D", u"E", u"H", 
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


