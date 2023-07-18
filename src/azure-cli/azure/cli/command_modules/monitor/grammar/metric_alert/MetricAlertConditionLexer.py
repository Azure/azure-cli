# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from MetricAlertCondition.g4 by ANTLR 4.9.3
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
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2 ")
        buf.write("\u0137\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7")
        buf.write("\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r")
        buf.write("\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23")
        buf.write("\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30")
        buf.write("\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\4\36")
        buf.write("\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t#\4$\t$\4%\t%")
        buf.write("\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4,\t,\4-\t-\4.")
        buf.write("\t.\4/\t/\4\60\t\60\4\61\t\61\4\62\t\62\4\63\t\63\4\64")
        buf.write("\t\64\4\65\t\65\4\66\t\66\4\67\t\67\3\2\3\2\3\3\3\3\3")
        buf.write("\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n")
        buf.write("\3\13\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20\3")
        buf.write("\20\3\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3\25")
        buf.write("\3\26\3\26\3\27\3\27\3\30\3\30\3\31\3\31\3\32\3\32\3\33")
        buf.write("\3\33\3\34\3\34\3\35\3\35\3\36\3\36\3\37\3\37\3 \3 \3")
        buf.write("!\3!\3\"\3\"\3#\3#\3$\3$\3%\3%\3&\3&\3\'\3\'\3(\3(\3(")
        buf.write("\3(\3(\3(\3)\3)\3)\3)\3*\3*\3*\3*\3*\3*\3*\3*\3*\3+\3")
        buf.write("+\3+\3+\3+\3+\3+\3+\3+\3,\3,\3,\3-\3-\3-\3-\3-\3-\3-\3")
        buf.write("-\3.\3.\3.\3/\3/\3/\3/\3/\3/\3\60\3\60\3\60\3\60\3\60")
        buf.write("\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61")
        buf.write("\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\62")
        buf.write("\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\3\62\5\62")
        buf.write("\u0111\n\62\3\63\6\63\u0114\n\63\r\63\16\63\u0115\3\63")
        buf.write("\3\63\6\63\u011a\n\63\r\63\16\63\u011b\5\63\u011e\n\63")
        buf.write("\3\64\3\64\3\65\6\65\u0123\n\65\r\65\16\65\u0124\3\66")
        buf.write("\5\66\u0128\n\66\3\66\3\66\6\66\u012c\n\66\r\66\16\66")
        buf.write("\u012d\3\67\3\67\3\67\3\67\6\67\u0134\n\67\r\67\16\67")
        buf.write("\u0135\2\28\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25")
        buf.write("\f\27\r\31\16\33\17\35\20\37\2!\2#\2%\2\'\2)\2+\2-\2/")
        buf.write("\2\61\2\63\2\65\2\67\29\2;\2=\2?\2A\2C\2E\2G\2I\2K\2M")
        buf.write("\2O\21Q\22S\23U\24W\25Y\26[\27]\30_\31a\32c\33e\34g\35")
        buf.write("i\36k\37m \3\2\35\4\2CCcc\4\2EEee\4\2FFff\4\2GGgg\4\2")
        buf.write("HHhh\4\2JJjj\4\2KKkk\4\2MMmm\4\2NNnn\4\2OOoo\4\2PPpp\4")
        buf.write("\2QQqq\4\2RRrr\4\2TTtt\4\2UUuu\4\2VVvv\4\2WWww\4\2XXx")
        buf.write("x\4\2YYyy\4\2ZZzz\4\2[[{{\3\2\62;\3\2c|\3\2C\\\4\2..\60")
        buf.write("\60\4\2$$))\4\2\13\13\"\"\2\u012f\2\3\3\2\2\2\2\5\3\2")
        buf.write("\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2")
        buf.write("\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2")
        buf.write("\27\3\2\2\2\2\31\3\2\2\2\2\33\3\2\2\2\2\35\3\2\2\2\2O")
        buf.write("\3\2\2\2\2Q\3\2\2\2\2S\3\2\2\2\2U\3\2\2\2\2W\3\2\2\2\2")
        buf.write("Y\3\2\2\2\2[\3\2\2\2\2]\3\2\2\2\2_\3\2\2\2\2a\3\2\2\2")
        buf.write("\2c\3\2\2\2\2e\3\2\2\2\2g\3\2\2\2\2i\3\2\2\2\2k\3\2\2")
        buf.write("\2\2m\3\2\2\2\3o\3\2\2\2\5q\3\2\2\2\7s\3\2\2\2\tu\3\2")
        buf.write("\2\2\13w\3\2\2\2\ry\3\2\2\2\17{\3\2\2\2\21}\3\2\2\2\23")
        buf.write("\177\3\2\2\2\25\u0081\3\2\2\2\27\u0083\3\2\2\2\31\u0085")
        buf.write("\3\2\2\2\33\u0087\3\2\2\2\35\u0089\3\2\2\2\37\u008b\3")
        buf.write("\2\2\2!\u008d\3\2\2\2#\u008f\3\2\2\2%\u0091\3\2\2\2\'")
        buf.write("\u0093\3\2\2\2)\u0095\3\2\2\2+\u0097\3\2\2\2-\u0099\3")
        buf.write("\2\2\2/\u009b\3\2\2\2\61\u009d\3\2\2\2\63\u009f\3\2\2")
        buf.write("\2\65\u00a1\3\2\2\2\67\u00a3\3\2\2\29\u00a5\3\2\2\2;\u00a7")
        buf.write("\3\2\2\2=\u00a9\3\2\2\2?\u00ab\3\2\2\2A\u00ad\3\2\2\2")
        buf.write("C\u00af\3\2\2\2E\u00b1\3\2\2\2G\u00b3\3\2\2\2I\u00b5\3")
        buf.write("\2\2\2K\u00b7\3\2\2\2M\u00b9\3\2\2\2O\u00bb\3\2\2\2Q\u00c1")
        buf.write("\3\2\2\2S\u00c5\3\2\2\2U\u00ce\3\2\2\2W\u00d7\3\2\2\2")
        buf.write("Y\u00da\3\2\2\2[\u00e2\3\2\2\2]\u00e5\3\2\2\2_\u00eb\3")
        buf.write("\2\2\2a\u00f0\3\2\2\2c\u0110\3\2\2\2e\u0113\3\2\2\2g\u011f")
        buf.write("\3\2\2\2i\u0122\3\2\2\2k\u012b\3\2\2\2m\u0133\3\2\2\2")
        buf.write("op\7\60\2\2p\4\3\2\2\2qr\7\61\2\2r\6\3\2\2\2st\7/\2\2")
        buf.write("t\b\3\2\2\2uv\7a\2\2v\n\3\2\2\2wx\7^\2\2x\f\3\2\2\2yz")
        buf.write("\7<\2\2z\16\3\2\2\2{|\7\'\2\2|\20\3\2\2\2}~\7.\2\2~\22")
        buf.write("\3\2\2\2\177\u0080\7~\2\2\u0080\24\3\2\2\2\u0081\u0082")
        buf.write("\7*\2\2\u0082\26\3\2\2\2\u0083\u0084\7+\2\2\u0084\30\3")
        buf.write("\2\2\2\u0085\u0086\7-\2\2\u0086\32\3\2\2\2\u0087\u0088")
        buf.write("\7,\2\2\u0088\34\3\2\2\2\u0089\u008a\7\u0080\2\2\u008a")
        buf.write("\36\3\2\2\2\u008b\u008c\t\2\2\2\u008c \3\2\2\2\u008d\u008e")
        buf.write("\t\3\2\2\u008e\"\3\2\2\2\u008f\u0090\t\4\2\2\u0090$\3")
        buf.write("\2\2\2\u0091\u0092\t\5\2\2\u0092&\3\2\2\2\u0093\u0094")
        buf.write("\t\6\2\2\u0094(\3\2\2\2\u0095\u0096\t\7\2\2\u0096*\3\2")
        buf.write("\2\2\u0097\u0098\t\b\2\2\u0098,\3\2\2\2\u0099\u009a\t")
        buf.write("\t\2\2\u009a.\3\2\2\2\u009b\u009c\t\n\2\2\u009c\60\3\2")
        buf.write("\2\2\u009d\u009e\t\13\2\2\u009e\62\3\2\2\2\u009f\u00a0")
        buf.write("\t\f\2\2\u00a0\64\3\2\2\2\u00a1\u00a2\t\r\2\2\u00a2\66")
        buf.write("\3\2\2\2\u00a3\u00a4\t\16\2\2\u00a48\3\2\2\2\u00a5\u00a6")
        buf.write("\t\17\2\2\u00a6:\3\2\2\2\u00a7\u00a8\t\20\2\2\u00a8<\3")
        buf.write("\2\2\2\u00a9\u00aa\t\21\2\2\u00aa>\3\2\2\2\u00ab\u00ac")
        buf.write("\t\22\2\2\u00ac@\3\2\2\2\u00ad\u00ae\t\23\2\2\u00aeB\3")
        buf.write("\2\2\2\u00af\u00b0\t\24\2\2\u00b0D\3\2\2\2\u00b1\u00b2")
        buf.write("\t\25\2\2\u00b2F\3\2\2\2\u00b3\u00b4\t\26\2\2\u00b4H\3")
        buf.write("\2\2\2\u00b5\u00b6\t\27\2\2\u00b6J\3\2\2\2\u00b7\u00b8")
        buf.write("\t\30\2\2\u00b8L\3\2\2\2\u00b9\u00ba\t\31\2\2\u00baN\3")
        buf.write("\2\2\2\u00bb\u00bc\5C\"\2\u00bc\u00bd\5)\25\2\u00bd\u00be")
        buf.write("\5%\23\2\u00be\u00bf\59\35\2\u00bf\u00c0\5%\23\2\u00c0")
        buf.write("P\3\2\2\2\u00c1\u00c2\5\37\20\2\u00c2\u00c3\5\63\32\2")
        buf.write("\u00c3\u00c4\5#\22\2\u00c4R\3\2\2\2\u00c5\u00c6\5+\26")
        buf.write("\2\u00c6\u00c7\5\63\32\2\u00c7\u00c8\5!\21\2\u00c8\u00c9")
        buf.write("\5/\30\2\u00c9\u00ca\5? \2\u00ca\u00cb\5#\22\2\u00cb\u00cc")
        buf.write("\5%\23\2\u00cc\u00cd\5;\36\2\u00cdT\3\2\2\2\u00ce\u00cf")
        buf.write("\5%\23\2\u00cf\u00d0\5E#\2\u00d0\u00d1\5!\21\2\u00d1\u00d2")
        buf.write("\5/\30\2\u00d2\u00d3\5? \2\u00d3\u00d4\5#\22\2\u00d4\u00d5")
        buf.write("\5%\23\2\u00d5\u00d6\5;\36\2\u00d6V\3\2\2\2\u00d7\u00d8")
        buf.write("\5\65\33\2\u00d8\u00d9\59\35\2\u00d9X\3\2\2\2\u00da\u00db")
        buf.write("\5#\22\2\u00db\u00dc\5G$\2\u00dc\u00dd\5\63\32\2\u00dd")
        buf.write("\u00de\5\37\20\2\u00de\u00df\5\61\31\2\u00df\u00e0\5+")
        buf.write("\26\2\u00e0\u00e1\5!\21\2\u00e1Z\3\2\2\2\u00e2\u00e3\5")
        buf.write("\65\33\2\u00e3\u00e4\5\'\24\2\u00e4\\\3\2\2\2\u00e5\u00e6")
        buf.write("\5;\36\2\u00e6\u00e7\5+\26\2\u00e7\u00e8\5\63\32\2\u00e8")
        buf.write("\u00e9\5!\21\2\u00e9\u00ea\5%\23\2\u00ea^\3\2\2\2\u00eb")
        buf.write("\u00ec\5C\"\2\u00ec\u00ed\5+\26\2\u00ed\u00ee\5=\37\2")
        buf.write("\u00ee\u00ef\5)\25\2\u00ef`\3\2\2\2\u00f0\u00f1\5;\36")
        buf.write("\2\u00f1\u00f2\5-\27\2\u00f2\u00f3\5+\26\2\u00f3\u00f4")
        buf.write("\5\67\34\2\u00f4\u00f5\5\61\31\2\u00f5\u00f6\5%\23\2\u00f6")
        buf.write("\u00f7\5=\37\2\u00f7\u00f8\59\35\2\u00f8\u00f9\5+\26\2")
        buf.write("\u00f9\u00fa\5!\21\2\u00fa\u00fb\5A!\2\u00fb\u00fc\5\37")
        buf.write("\20\2\u00fc\u00fd\5/\30\2\u00fd\u00fe\5+\26\2\u00fe\u00ff")
        buf.write("\5#\22\2\u00ff\u0100\5\37\20\2\u0100\u0101\5=\37\2\u0101")
        buf.write("\u0102\5+\26\2\u0102\u0103\5\65\33\2\u0103\u0104\5\63")
        buf.write("\32\2\u0104b\3\2\2\2\u0105\u0111\7>\2\2\u0106\u0107\7")
        buf.write(">\2\2\u0107\u0111\7?\2\2\u0108\u0111\7?\2\2\u0109\u010a")
        buf.write("\7@\2\2\u010a\u0111\7?\2\2\u010b\u0111\7@\2\2\u010c\u010d")
        buf.write("\7#\2\2\u010d\u0111\7?\2\2\u010e\u010f\7@\2\2\u010f\u0111")
        buf.write("\7>\2\2\u0110\u0105\3\2\2\2\u0110\u0106\3\2\2\2\u0110")
        buf.write("\u0108\3\2\2\2\u0110\u0109\3\2\2\2\u0110\u010b\3\2\2\2")
        buf.write("\u0110\u010c\3\2\2\2\u0110\u010e\3\2\2\2\u0111d\3\2\2")
        buf.write("\2\u0112\u0114\5I%\2\u0113\u0112\3\2\2\2\u0114\u0115\3")
        buf.write("\2\2\2\u0115\u0113\3\2\2\2\u0115\u0116\3\2\2\2\u0116\u011d")
        buf.write("\3\2\2\2\u0117\u0119\t\32\2\2\u0118\u011a\5I%\2\u0119")
        buf.write("\u0118\3\2\2\2\u011a\u011b\3\2\2\2\u011b\u0119\3\2\2\2")
        buf.write("\u011b\u011c\3\2\2\2\u011c\u011e\3\2\2\2\u011d\u0117\3")
        buf.write("\2\2\2\u011d\u011e\3\2\2\2\u011ef\3\2\2\2\u011f\u0120")
        buf.write("\t\33\2\2\u0120h\3\2\2\2\u0121\u0123\t\34\2\2\u0122\u0121")
        buf.write("\3\2\2\2\u0123\u0124\3\2\2\2\u0124\u0122\3\2\2\2\u0124")
        buf.write("\u0125\3\2\2\2\u0125j\3\2\2\2\u0126\u0128\7\17\2\2\u0127")
        buf.write("\u0126\3\2\2\2\u0127\u0128\3\2\2\2\u0128\u0129\3\2\2\2")
        buf.write("\u0129\u012c\7\f\2\2\u012a\u012c\7\17\2\2\u012b\u0127")
        buf.write("\3\2\2\2\u012b\u012a\3\2\2\2\u012c\u012d\3\2\2\2\u012d")
        buf.write("\u012b\3\2\2\2\u012d\u012e\3\2\2\2\u012el\3\2\2\2\u012f")
        buf.write("\u0134\5K&\2\u0130\u0134\5M\'\2\u0131\u0134\5I%\2\u0132")
        buf.write("\u0134\7a\2\2\u0133\u012f\3\2\2\2\u0133\u0130\3\2\2\2")
        buf.write("\u0133\u0131\3\2\2\2\u0133\u0132\3\2\2\2\u0134\u0135\3")
        buf.write("\2\2\2\u0135\u0133\3\2\2\2\u0135\u0136\3\2\2\2\u0136n")
        buf.write("\3\2\2\2\r\2\u0110\u0115\u011b\u011d\u0124\u0127\u012b")
        buf.write("\u012d\u0133\u0135\2")
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
    T__12 = 13
    T__13 = 14
    WHERE = 15
    AND = 16
    INCLUDES = 17
    EXCLUDES = 18
    OR = 19
    DYNAMIC = 20
    OF = 21
    SINCE = 22
    WITH = 23
    SKIPMETRICVALIDATION = 24
    OPERATOR = 25
    NUMBER = 26
    QUOTE = 27
    WHITESPACE = 28
    NEWLINE = 29
    WORD = 30

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'.'", "'/'", "'-'", "'_'", "'\\'", "':'", "'%'", "','", "'|'", 
            "'('", "')'", "'+'", "'*'", "'~'" ]

    symbolicNames = [ "<INVALID>",
            "WHERE", "AND", "INCLUDES", "EXCLUDES", "OR", "DYNAMIC", "OF", 
            "SINCE", "WITH", "SKIPMETRICVALIDATION", "OPERATOR", "NUMBER", 
            "QUOTE", "WHITESPACE", "NEWLINE", "WORD" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "T__8", "T__9", "T__10", "T__11", "T__12", "T__13", 
                  "A", "C", "D", "E", "F", "H", "I", "K", "L", "M", "N", 
                  "O", "P", "R", "S", "T", "U", "V", "W", "X", "Y", "DIGIT", 
                  "LOWERCASE", "UPPERCASE", "WHERE", "AND", "INCLUDES", 
                  "EXCLUDES", "OR", "DYNAMIC", "OF", "SINCE", "WITH", "SKIPMETRICVALIDATION", 
                  "OPERATOR", "NUMBER", "QUOTE", "WHITESPACE", "NEWLINE", 
                  "WORD" ]

    grammarFileName = "MetricAlertCondition.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.3")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


