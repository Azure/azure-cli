# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from MetricAlertCondition.g4 by ANTLR 4.7.2
# encoding: utf-8
# pylint: disable=all
from __future__ import print_function
from antlr4 import *
from io import StringIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2")
        buf.write(u"\34\u0107\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4")
        buf.write(u",\t,\4-\t-\4.\t.\4/\t/\3\2\3\2\3\3\3\3\3\4\3\4\3\5\3")
        buf.write(u"\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n\3\13\3\13")
        buf.write(u"\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20\3\20\3\21\3")
        buf.write(u"\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3\25\3\26\3\26")
        buf.write(u"\3\27\3\27\3\30\3\30\3\31\3\31\3\32\3\32\3\33\3\33\3")
        buf.write(u"\34\3\34\3\35\3\35\3\36\3\36\3\37\3\37\3 \3 \3!\3!\3")
        buf.write(u"!\3!\3!\3!\3\"\3\"\3\"\3\"\3#\3#\3#\3#\3#\3#\3#\3#\3")
        buf.write(u"#\3$\3$\3$\3$\3$\3$\3$\3$\3$\3%\3%\3%\3&\3&\3&\3&\3&")
        buf.write(u"\3&\3&\3&\3\'\3\'\3\'\3(\3(\3(\3(\3(\3(\3)\3)\3)\3)\3")
        buf.write(u")\3)\3)\3)\3)\3)\3)\5)\u00d9\n)\3*\6*\u00dc\n*\r*\16")
        buf.write(u"*\u00dd\3*\3*\6*\u00e2\n*\r*\16*\u00e3\5*\u00e6\n*\3")
        buf.write(u"+\3+\3,\6,\u00eb\n,\r,\16,\u00ec\3-\5-\u00f0\n-\3-\3")
        buf.write(u"-\6-\u00f4\n-\r-\16-\u00f5\3.\3.\3.\3.\6.\u00fc\n.\r")
        buf.write(u".\16.\u00fd\3/\3/\3/\3/\6/\u0104\n/\r/\16/\u0105\2\2")
        buf.write(u"\60\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27")
        buf.write(u"\r\31\2\33\2\35\2\37\2!\2#\2%\2\'\2)\2+\2-\2/\2\61\2")
        buf.write(u"\63\2\65\2\67\29\2;\2=\2?\2A\16C\17E\20G\21I\22K\23M")
        buf.write(u"\24O\25Q\26S\27U\30W\31Y\32[\33]\34\3\2\32\4\2CCcc\4")
        buf.write(u"\2EEee\4\2FFff\4\2GGgg\4\2HHhh\4\2JJjj\4\2KKkk\4\2NN")
        buf.write(u"nn\4\2OOoo\4\2PPpp\4\2QQqq\4\2TTtt\4\2UUuu\4\2WWww\4")
        buf.write(u"\2YYyy\4\2ZZzz\4\2[[{{\3\2\62;\3\2c|\3\2C\\\4\2..\60")
        buf.write(u"\60\4\2$$))\4\2\13\13\"\"\4\2//<<\2\u0107\2\3\3\2\2\2")
        buf.write(u"\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r")
        buf.write(u"\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25")
        buf.write(u"\3\2\2\2\2\27\3\2\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2")
        buf.write(u"\2\2G\3\2\2\2\2I\3\2\2\2\2K\3\2\2\2\2M\3\2\2\2\2O\3\2")
        buf.write(u"\2\2\2Q\3\2\2\2\2S\3\2\2\2\2U\3\2\2\2\2W\3\2\2\2\2Y\3")
        buf.write(u"\2\2\2\2[\3\2\2\2\2]\3\2\2\2\3_\3\2\2\2\5a\3\2\2\2\7")
        buf.write(u"c\3\2\2\2\te\3\2\2\2\13g\3\2\2\2\ri\3\2\2\2\17k\3\2\2")
        buf.write(u"\2\21m\3\2\2\2\23o\3\2\2\2\25q\3\2\2\2\27s\3\2\2\2\31")
        buf.write(u"u\3\2\2\2\33w\3\2\2\2\35y\3\2\2\2\37{\3\2\2\2!}\3\2\2")
        buf.write(u"\2#\177\3\2\2\2%\u0081\3\2\2\2\'\u0083\3\2\2\2)\u0085")
        buf.write(u"\3\2\2\2+\u0087\3\2\2\2-\u0089\3\2\2\2/\u008b\3\2\2\2")
        buf.write(u"\61\u008d\3\2\2\2\63\u008f\3\2\2\2\65\u0091\3\2\2\2\67")
        buf.write(u"\u0093\3\2\2\29\u0095\3\2\2\2;\u0097\3\2\2\2=\u0099\3")
        buf.write(u"\2\2\2?\u009b\3\2\2\2A\u009d\3\2\2\2C\u00a3\3\2\2\2E")
        buf.write(u"\u00a7\3\2\2\2G\u00b0\3\2\2\2I\u00b9\3\2\2\2K\u00bc\3")
        buf.write(u"\2\2\2M\u00c4\3\2\2\2O\u00c7\3\2\2\2Q\u00d8\3\2\2\2S")
        buf.write(u"\u00db\3\2\2\2U\u00e7\3\2\2\2W\u00ea\3\2\2\2Y\u00f3\3")
        buf.write(u"\2\2\2[\u00fb\3\2\2\2]\u0103\3\2\2\2_`\7\60\2\2`\4\3")
        buf.write(u"\2\2\2ab\7\61\2\2b\6\3\2\2\2cd\7a\2\2d\b\3\2\2\2ef\7")
        buf.write(u"^\2\2f\n\3\2\2\2gh\7<\2\2h\f\3\2\2\2ij\7\'\2\2j\16\3")
        buf.write(u"\2\2\2kl\7/\2\2l\20\3\2\2\2mn\7.\2\2n\22\3\2\2\2op\7")
        buf.write(u"~\2\2p\24\3\2\2\2qr\7,\2\2r\26\3\2\2\2st\7\u0080\2\2")
        buf.write(u"t\30\3\2\2\2uv\t\2\2\2v\32\3\2\2\2wx\t\3\2\2x\34\3\2")
        buf.write(u"\2\2yz\t\4\2\2z\36\3\2\2\2{|\t\5\2\2| \3\2\2\2}~\t\6")
        buf.write(u"\2\2~\"\3\2\2\2\177\u0080\t\7\2\2\u0080$\3\2\2\2\u0081")
        buf.write(u"\u0082\t\b\2\2\u0082&\3\2\2\2\u0083\u0084\t\t\2\2\u0084")
        buf.write(u"(\3\2\2\2\u0085\u0086\t\n\2\2\u0086*\3\2\2\2\u0087\u0088")
        buf.write(u"\t\13\2\2\u0088,\3\2\2\2\u0089\u008a\t\f\2\2\u008a.\3")
        buf.write(u"\2\2\2\u008b\u008c\t\r\2\2\u008c\60\3\2\2\2\u008d\u008e")
        buf.write(u"\t\16\2\2\u008e\62\3\2\2\2\u008f\u0090\t\17\2\2\u0090")
        buf.write(u"\64\3\2\2\2\u0091\u0092\t\20\2\2\u0092\66\3\2\2\2\u0093")
        buf.write(u"\u0094\t\21\2\2\u00948\3\2\2\2\u0095\u0096\t\22\2\2\u0096")
        buf.write(u":\3\2\2\2\u0097\u0098\t\23\2\2\u0098<\3\2\2\2\u0099\u009a")
        buf.write(u"\t\24\2\2\u009a>\3\2\2\2\u009b\u009c\t\25\2\2\u009c@")
        buf.write(u"\3\2\2\2\u009d\u009e\5\65\33\2\u009e\u009f\5#\22\2\u009f")
        buf.write(u"\u00a0\5\37\20\2\u00a0\u00a1\5/\30\2\u00a1\u00a2\5\37")
        buf.write(u"\20\2\u00a2B\3\2\2\2\u00a3\u00a4\5\31\r\2\u00a4\u00a5")
        buf.write(u"\5+\26\2\u00a5\u00a6\5\35\17\2\u00a6D\3\2\2\2\u00a7\u00a8")
        buf.write(u"\5%\23\2\u00a8\u00a9\5+\26\2\u00a9\u00aa\5\33\16\2\u00aa")
        buf.write(u"\u00ab\5\'\24\2\u00ab\u00ac\5\63\32\2\u00ac\u00ad\5\35")
        buf.write(u"\17\2\u00ad\u00ae\5\37\20\2\u00ae\u00af\5\61\31\2\u00af")
        buf.write(u"F\3\2\2\2\u00b0\u00b1\5\37\20\2\u00b1\u00b2\5\67\34\2")
        buf.write(u"\u00b2\u00b3\5\33\16\2\u00b3\u00b4\5\'\24\2\u00b4\u00b5")
        buf.write(u"\5\63\32\2\u00b5\u00b6\5\35\17\2\u00b6\u00b7\5\37\20")
        buf.write(u"\2\u00b7\u00b8\5\61\31\2\u00b8H\3\2\2\2\u00b9\u00ba\5")
        buf.write(u"-\27\2\u00ba\u00bb\5/\30\2\u00bbJ\3\2\2\2\u00bc\u00bd")
        buf.write(u"\5\35\17\2\u00bd\u00be\59\35\2\u00be\u00bf\5+\26\2\u00bf")
        buf.write(u"\u00c0\5\31\r\2\u00c0\u00c1\5)\25\2\u00c1\u00c2\5%\23")
        buf.write(u"\2\u00c2\u00c3\5\33\16\2\u00c3L\3\2\2\2\u00c4\u00c5\5")
        buf.write(u"-\27\2\u00c5\u00c6\5!\21\2\u00c6N\3\2\2\2\u00c7\u00c8")
        buf.write(u"\5\61\31\2\u00c8\u00c9\5%\23\2\u00c9\u00ca\5+\26\2\u00ca")
        buf.write(u"\u00cb\5\33\16\2\u00cb\u00cc\5\37\20\2\u00ccP\3\2\2\2")
        buf.write(u"\u00cd\u00d9\7>\2\2\u00ce\u00cf\7>\2\2\u00cf\u00d9\7")
        buf.write(u"?\2\2\u00d0\u00d9\7?\2\2\u00d1\u00d2\7@\2\2\u00d2\u00d9")
        buf.write(u"\7?\2\2\u00d3\u00d9\7@\2\2\u00d4\u00d5\7#\2\2\u00d5\u00d9")
        buf.write(u"\7?\2\2\u00d6\u00d7\7@\2\2\u00d7\u00d9\7>\2\2\u00d8\u00cd")
        buf.write(u"\3\2\2\2\u00d8\u00ce\3\2\2\2\u00d8\u00d0\3\2\2\2\u00d8")
        buf.write(u"\u00d1\3\2\2\2\u00d8\u00d3\3\2\2\2\u00d8\u00d4\3\2\2")
        buf.write(u"\2\u00d8\u00d6\3\2\2\2\u00d9R\3\2\2\2\u00da\u00dc\5;")
        buf.write(u"\36\2\u00db\u00da\3\2\2\2\u00dc\u00dd\3\2\2\2\u00dd\u00db")
        buf.write(u"\3\2\2\2\u00dd\u00de\3\2\2\2\u00de\u00e5\3\2\2\2\u00df")
        buf.write(u"\u00e1\t\26\2\2\u00e0\u00e2\5;\36\2\u00e1\u00e0\3\2\2")
        buf.write(u"\2\u00e2\u00e3\3\2\2\2\u00e3\u00e1\3\2\2\2\u00e3\u00e4")
        buf.write(u"\3\2\2\2\u00e4\u00e6\3\2\2\2\u00e5\u00df\3\2\2\2\u00e5")
        buf.write(u"\u00e6\3\2\2\2\u00e6T\3\2\2\2\u00e7\u00e8\t\27\2\2\u00e8")
        buf.write(u"V\3\2\2\2\u00e9\u00eb\t\30\2\2\u00ea\u00e9\3\2\2\2\u00eb")
        buf.write(u"\u00ec\3\2\2\2\u00ec\u00ea\3\2\2\2\u00ec\u00ed\3\2\2")
        buf.write(u"\2\u00edX\3\2\2\2\u00ee\u00f0\7\17\2\2\u00ef\u00ee\3")
        buf.write(u"\2\2\2\u00ef\u00f0\3\2\2\2\u00f0\u00f1\3\2\2\2\u00f1")
        buf.write(u"\u00f4\7\f\2\2\u00f2\u00f4\7\17\2\2\u00f3\u00ef\3\2\2")
        buf.write(u"\2\u00f3\u00f2\3\2\2\2\u00f4\u00f5\3\2\2\2\u00f5\u00f3")
        buf.write(u"\3\2\2\2\u00f5\u00f6\3\2\2\2\u00f6Z\3\2\2\2\u00f7\u00fc")
        buf.write(u"\5=\37\2\u00f8\u00fc\5? \2\u00f9\u00fc\5;\36\2\u00fa")
        buf.write(u"\u00fc\7a\2\2\u00fb\u00f7\3\2\2\2\u00fb\u00f8\3\2\2\2")
        buf.write(u"\u00fb\u00f9\3\2\2\2\u00fb\u00fa\3\2\2\2\u00fc\u00fd")
        buf.write(u"\3\2\2\2\u00fd\u00fb\3\2\2\2\u00fd\u00fe\3\2\2\2\u00fe")
        buf.write(u"\\\3\2\2\2\u00ff\u0104\5=\37\2\u0100\u0104\5? \2\u0101")
        buf.write(u"\u0104\5;\36\2\u0102\u0104\t\31\2\2\u0103\u00ff\3\2\2")
        buf.write(u"\2\u0103\u0100\3\2\2\2\u0103\u0101\3\2\2\2\u0103\u0102")
        buf.write(u"\3\2\2\2\u0104\u0105\3\2\2\2\u0105\u0103\3\2\2\2\u0105")
        buf.write(u"\u0106\3\2\2\2\u0106^\3\2\2\2\17\2\u00d8\u00dd\u00e3")
        buf.write(u"\u00e5\u00ec\u00ef\u00f3\u00f5\u00fb\u00fd\u0103\u0105")
        buf.write(u"\2")
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
    T__9 = 10
    T__10 = 11
    WHERE = 12
    AND = 13
    INCLUDES = 14
    EXCLUDES = 15
    OR = 16
    DYNAMIC = 17
    OF = 18
    SINCE = 19
    OPERATOR = 20
    NUMBER = 21
    QUOTE = 22
    WHITESPACE = 23
    NEWLINE = 24
    WORD = 25
    DATETIME = 26

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", u"'%'", u"'-'", u"','", 
            u"'|'", u"'*'", u"'~'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"DYNAMIC", 
            u"OF", u"SINCE", u"OPERATOR", u"NUMBER", u"QUOTE", u"WHITESPACE", 
            u"NEWLINE", u"WORD", u"DATETIME" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"T__8", u"T__9", u"T__10", u"A", u"C", 
                  u"D", u"E", u"F", u"H", u"I", u"L", u"M", u"N", u"O", 
                  u"R", u"S", u"U", u"W", u"X", u"Y", u"DIGIT", u"LOWERCASE", 
                  u"UPPERCASE", u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", 
                  u"OR", u"DYNAMIC", u"OF", u"SINCE", u"OPERATOR", u"NUMBER", 
                  u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD", u"DATETIME" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


