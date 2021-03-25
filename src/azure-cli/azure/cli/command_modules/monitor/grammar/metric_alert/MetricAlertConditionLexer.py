# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from MetricAlertCondition.g4 by ANTLR 4.7.2
# encoding: utf-8
# pylint: disable=all
from antlr4 import *
from io import StringIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2")
        buf.write(u"\34\u0101\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
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
        buf.write(u"\"\3\"\3\"\3\"\3\"\3\"\3#\3#\3#\3#\3$\3$\3$\3$\3$\3$")
        buf.write(u"\3$\3$\3$\3%\3%\3%\3%\3%\3%\3%\3%\3%\3&\3&\3&\3\'\3\'")
        buf.write(u"\3\'\3\'\3\'\3\'\3\'\3\'\3(\3(\3(\3)\3)\3)\3)\3)\3)\3")
        buf.write(u"*\3*\3*\3*\3*\3*\3*\3*\3*\3*\3*\5*\u00db\n*\3+\6+\u00de")
        buf.write(u"\n+\r+\16+\u00df\3+\3+\6+\u00e4\n+\r+\16+\u00e5\5+\u00e8")
        buf.write(u"\n+\3,\3,\3-\6-\u00ed\n-\r-\16-\u00ee\3.\5.\u00f2\n.")
        buf.write(u"\3.\3.\6.\u00f6\n.\r.\16.\u00f7\3/\3/\3/\3/\6/\u00fe")
        buf.write(u"\n/\r/\16/\u00ff\2\2\60\3\3\5\4\7\5\t\6\13\7\r\b\17\t")
        buf.write(u"\21\n\23\13\25\f\27\r\31\16\33\2\35\2\37\2!\2#\2%\2\'")
        buf.write(u"\2)\2+\2-\2/\2\61\2\63\2\65\2\67\29\2;\2=\2?\2A\2C\17")
        buf.write(u"E\20G\21I\22K\23M\24O\25Q\26S\27U\30W\31Y\32[\33]\34")
        buf.write(u"\3\2\31\4\2CCcc\4\2EEee\4\2FFff\4\2GGgg\4\2HHhh\4\2J")
        buf.write(u"Jjj\4\2KKkk\4\2NNnn\4\2OOoo\4\2PPpp\4\2QQqq\4\2TTtt\4")
        buf.write(u"\2UUuu\4\2WWww\4\2YYyy\4\2ZZzz\4\2[[{{\3\2\62;\3\2c|")
        buf.write(u"\3\2C\\\4\2..\60\60\4\2$$))\4\2\13\13\"\"\2\u00fd\2\3")
        buf.write(u"\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2")
        buf.write(u"\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2")
        buf.write(u"\2\2\25\3\2\2\2\2\27\3\2\2\2\2\31\3\2\2\2\2C\3\2\2\2")
        buf.write(u"\2E\3\2\2\2\2G\3\2\2\2\2I\3\2\2\2\2K\3\2\2\2\2M\3\2\2")
        buf.write(u"\2\2O\3\2\2\2\2Q\3\2\2\2\2S\3\2\2\2\2U\3\2\2\2\2W\3\2")
        buf.write(u"\2\2\2Y\3\2\2\2\2[\3\2\2\2\2]\3\2\2\2\3_\3\2\2\2\5a\3")
        buf.write(u"\2\2\2\7c\3\2\2\2\te\3\2\2\2\13g\3\2\2\2\ri\3\2\2\2\17")
        buf.write(u"k\3\2\2\2\21m\3\2\2\2\23o\3\2\2\2\25q\3\2\2\2\27s\3\2")
        buf.write(u"\2\2\31u\3\2\2\2\33w\3\2\2\2\35y\3\2\2\2\37{\3\2\2\2")
        buf.write(u"!}\3\2\2\2#\177\3\2\2\2%\u0081\3\2\2\2\'\u0083\3\2\2")
        buf.write(u"\2)\u0085\3\2\2\2+\u0087\3\2\2\2-\u0089\3\2\2\2/\u008b")
        buf.write(u"\3\2\2\2\61\u008d\3\2\2\2\63\u008f\3\2\2\2\65\u0091\3")
        buf.write(u"\2\2\2\67\u0093\3\2\2\29\u0095\3\2\2\2;\u0097\3\2\2\2")
        buf.write(u"=\u0099\3\2\2\2?\u009b\3\2\2\2A\u009d\3\2\2\2C\u009f")
        buf.write(u"\3\2\2\2E\u00a5\3\2\2\2G\u00a9\3\2\2\2I\u00b2\3\2\2\2")
        buf.write(u"K\u00bb\3\2\2\2M\u00be\3\2\2\2O\u00c6\3\2\2\2Q\u00c9")
        buf.write(u"\3\2\2\2S\u00da\3\2\2\2U\u00dd\3\2\2\2W\u00e9\3\2\2\2")
        buf.write(u"Y\u00ec\3\2\2\2[\u00f5\3\2\2\2]\u00fd\3\2\2\2_`\7\60")
        buf.write(u"\2\2`\4\3\2\2\2ab\7\61\2\2b\6\3\2\2\2cd\7a\2\2d\b\3\2")
        buf.write(u"\2\2ef\7^\2\2f\n\3\2\2\2gh\7<\2\2h\f\3\2\2\2ij\7\'\2")
        buf.write(u"\2j\16\3\2\2\2kl\7/\2\2l\20\3\2\2\2mn\7.\2\2n\22\3\2")
        buf.write(u"\2\2op\7~\2\2p\24\3\2\2\2qr\7-\2\2r\26\3\2\2\2st\7,\2")
        buf.write(u"\2t\30\3\2\2\2uv\7\u0080\2\2v\32\3\2\2\2wx\t\2\2\2x\34")
        buf.write(u"\3\2\2\2yz\t\3\2\2z\36\3\2\2\2{|\t\4\2\2| \3\2\2\2}~")
        buf.write(u"\t\5\2\2~\"\3\2\2\2\177\u0080\t\6\2\2\u0080$\3\2\2\2")
        buf.write(u"\u0081\u0082\t\7\2\2\u0082&\3\2\2\2\u0083\u0084\t\b\2")
        buf.write(u"\2\u0084(\3\2\2\2\u0085\u0086\t\t\2\2\u0086*\3\2\2\2")
        buf.write(u"\u0087\u0088\t\n\2\2\u0088,\3\2\2\2\u0089\u008a\t\13")
        buf.write(u"\2\2\u008a.\3\2\2\2\u008b\u008c\t\f\2\2\u008c\60\3\2")
        buf.write(u"\2\2\u008d\u008e\t\r\2\2\u008e\62\3\2\2\2\u008f\u0090")
        buf.write(u"\t\16\2\2\u0090\64\3\2\2\2\u0091\u0092\t\17\2\2\u0092")
        buf.write(u"\66\3\2\2\2\u0093\u0094\t\20\2\2\u00948\3\2\2\2\u0095")
        buf.write(u"\u0096\t\21\2\2\u0096:\3\2\2\2\u0097\u0098\t\22\2\2\u0098")
        buf.write(u"<\3\2\2\2\u0099\u009a\t\23\2\2\u009a>\3\2\2\2\u009b\u009c")
        buf.write(u"\t\24\2\2\u009c@\3\2\2\2\u009d\u009e\t\25\2\2\u009eB")
        buf.write(u"\3\2\2\2\u009f\u00a0\5\67\34\2\u00a0\u00a1\5%\23\2\u00a1")
        buf.write(u"\u00a2\5!\21\2\u00a2\u00a3\5\61\31\2\u00a3\u00a4\5!\21")
        buf.write(u"\2\u00a4D\3\2\2\2\u00a5\u00a6\5\33\16\2\u00a6\u00a7\5")
        buf.write(u"-\27\2\u00a7\u00a8\5\37\20\2\u00a8F\3\2\2\2\u00a9\u00aa")
        buf.write(u"\5\'\24\2\u00aa\u00ab\5-\27\2\u00ab\u00ac\5\35\17\2\u00ac")
        buf.write(u"\u00ad\5)\25\2\u00ad\u00ae\5\65\33\2\u00ae\u00af\5\37")
        buf.write(u"\20\2\u00af\u00b0\5!\21\2\u00b0\u00b1\5\63\32\2\u00b1")
        buf.write(u"H\3\2\2\2\u00b2\u00b3\5!\21\2\u00b3\u00b4\59\35\2\u00b4")
        buf.write(u"\u00b5\5\35\17\2\u00b5\u00b6\5)\25\2\u00b6\u00b7\5\65")
        buf.write(u"\33\2\u00b7\u00b8\5\37\20\2\u00b8\u00b9\5!\21\2\u00b9")
        buf.write(u"\u00ba\5\63\32\2\u00baJ\3\2\2\2\u00bb\u00bc\5/\30\2\u00bc")
        buf.write(u"\u00bd\5\61\31\2\u00bdL\3\2\2\2\u00be\u00bf\5\37\20\2")
        buf.write(u"\u00bf\u00c0\5;\36\2\u00c0\u00c1\5-\27\2\u00c1\u00c2")
        buf.write(u"\5\33\16\2\u00c2\u00c3\5+\26\2\u00c3\u00c4\5\'\24\2\u00c4")
        buf.write(u"\u00c5\5\35\17\2\u00c5N\3\2\2\2\u00c6\u00c7\5/\30\2\u00c7")
        buf.write(u"\u00c8\5#\22\2\u00c8P\3\2\2\2\u00c9\u00ca\5\63\32\2\u00ca")
        buf.write(u"\u00cb\5\'\24\2\u00cb\u00cc\5-\27\2\u00cc\u00cd\5\35")
        buf.write(u"\17\2\u00cd\u00ce\5!\21\2\u00ceR\3\2\2\2\u00cf\u00db")
        buf.write(u"\7>\2\2\u00d0\u00d1\7>\2\2\u00d1\u00db\7?\2\2\u00d2\u00db")
        buf.write(u"\7?\2\2\u00d3\u00d4\7@\2\2\u00d4\u00db\7?\2\2\u00d5\u00db")
        buf.write(u"\7@\2\2\u00d6\u00d7\7#\2\2\u00d7\u00db\7?\2\2\u00d8\u00d9")
        buf.write(u"\7@\2\2\u00d9\u00db\7>\2\2\u00da\u00cf\3\2\2\2\u00da")
        buf.write(u"\u00d0\3\2\2\2\u00da\u00d2\3\2\2\2\u00da\u00d3\3\2\2")
        buf.write(u"\2\u00da\u00d5\3\2\2\2\u00da\u00d6\3\2\2\2\u00da\u00d8")
        buf.write(u"\3\2\2\2\u00dbT\3\2\2\2\u00dc\u00de\5=\37\2\u00dd\u00dc")
        buf.write(u"\3\2\2\2\u00de\u00df\3\2\2\2\u00df\u00dd\3\2\2\2\u00df")
        buf.write(u"\u00e0\3\2\2\2\u00e0\u00e7\3\2\2\2\u00e1\u00e3\t\26\2")
        buf.write(u"\2\u00e2\u00e4\5=\37\2\u00e3\u00e2\3\2\2\2\u00e4\u00e5")
        buf.write(u"\3\2\2\2\u00e5\u00e3\3\2\2\2\u00e5\u00e6\3\2\2\2\u00e6")
        buf.write(u"\u00e8\3\2\2\2\u00e7\u00e1\3\2\2\2\u00e7\u00e8\3\2\2")
        buf.write(u"\2\u00e8V\3\2\2\2\u00e9\u00ea\t\27\2\2\u00eaX\3\2\2\2")
        buf.write(u"\u00eb\u00ed\t\30\2\2\u00ec\u00eb\3\2\2\2\u00ed\u00ee")
        buf.write(u"\3\2\2\2\u00ee\u00ec\3\2\2\2\u00ee\u00ef\3\2\2\2\u00ef")
        buf.write(u"Z\3\2\2\2\u00f0\u00f2\7\17\2\2\u00f1\u00f0\3\2\2\2\u00f1")
        buf.write(u"\u00f2\3\2\2\2\u00f2\u00f3\3\2\2\2\u00f3\u00f6\7\f\2")
        buf.write(u"\2\u00f4\u00f6\7\17\2\2\u00f5\u00f1\3\2\2\2\u00f5\u00f4")
        buf.write(u"\3\2\2\2\u00f6\u00f7\3\2\2\2\u00f7\u00f5\3\2\2\2\u00f7")
        buf.write(u"\u00f8\3\2\2\2\u00f8\\\3\2\2\2\u00f9\u00fe\5? \2\u00fa")
        buf.write(u"\u00fe\5A!\2\u00fb\u00fe\5=\37\2\u00fc\u00fe\7a\2\2\u00fd")
        buf.write(u"\u00f9\3\2\2\2\u00fd\u00fa\3\2\2\2\u00fd\u00fb\3\2\2")
        buf.write(u"\2\u00fd\u00fc\3\2\2\2\u00fe\u00ff\3\2\2\2\u00ff\u00fd")
        buf.write(u"\3\2\2\2\u00ff\u0100\3\2\2\2\u0100^\3\2\2\2\r\2\u00da")
        buf.write(u"\u00df\u00e5\u00e7\u00ee\u00f1\u00f5\u00f7\u00fd\u00ff")
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
    T__11 = 12
    WHERE = 13
    AND = 14
    INCLUDES = 15
    EXCLUDES = 16
    OR = 17
    DYNAMIC = 18
    OF = 19
    SINCE = 20
    OPERATOR = 21
    NUMBER = 22
    QUOTE = 23
    WHITESPACE = 24
    NEWLINE = 25
    WORD = 26

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", u"'%'", u"'-'", u"','", 
            u"'|'", u"'+'", u"'*'", u"'~'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"DYNAMIC", 
            u"OF", u"SINCE", u"OPERATOR", u"NUMBER", u"QUOTE", u"WHITESPACE", 
            u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"T__8", u"T__9", u"T__10", u"T__11", 
                  u"A", u"C", u"D", u"E", u"F", u"H", u"I", u"L", u"M", 
                  u"N", u"O", u"R", u"S", u"U", u"W", u"X", u"Y", u"DIGIT", 
                  u"LOWERCASE", u"UPPERCASE", u"WHERE", u"AND", u"INCLUDES", 
                  u"EXCLUDES", u"OR", u"DYNAMIC", u"OF", u"SINCE", u"OPERATOR", 
                  u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


