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
        buf.write(u"\30\u00d8\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\3\2\3\2\3\3\3\3\3\4")
        buf.write(u"\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n")
        buf.write(u"\3\13\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20\3")
        buf.write(u"\20\3\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3\25")
        buf.write(u"\3\26\3\26\3\27\3\27\3\30\3\30\3\31\3\31\3\32\3\32\3")
        buf.write(u"\33\3\33\3\34\3\34\3\35\3\35\3\36\3\36\3\36\3\36\3\36")
        buf.write(u"\3\36\3\37\3\37\3\37\3\37\3 \3 \3 \3 \3 \3 \3 \3 \3 ")
        buf.write(u"\3!\3!\3!\3!\3!\3!\3!\3!\3!\3\"\3\"\3\"\3#\3#\3#\3#\3")
        buf.write(u"#\3#\3#\3#\3#\5#\u00b2\n#\3$\6$\u00b5\n$\r$\16$\u00b6")
        buf.write(u"\3$\3$\6$\u00bb\n$\r$\16$\u00bc\5$\u00bf\n$\3%\3%\3&")
        buf.write(u"\6&\u00c4\n&\r&\16&\u00c5\3\'\5\'\u00c9\n\'\3\'\3\'\6")
        buf.write(u"\'\u00cd\n\'\r\'\16\'\u00ce\3(\3(\3(\3(\6(\u00d5\n(\r")
        buf.write(u"(\16(\u00d6\2\2)\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23")
        buf.write(u"\13\25\f\27\r\31\2\33\2\35\2\37\2!\2#\2%\2\'\2)\2+\2")
        buf.write(u"-\2/\2\61\2\63\2\65\2\67\29\2;\16=\17?\20A\21C\22E\23")
        buf.write(u"G\24I\25K\26M\27O\30\3\2\26\4\2CCcc\4\2EEee\4\2FFff\4")
        buf.write(u"\2GGgg\4\2JJjj\4\2KKkk\4\2NNnn\4\2PPpp\4\2QQqq\4\2TT")
        buf.write(u"tt\4\2UUuu\4\2WWww\4\2YYyy\4\2ZZzz\3\2\62;\3\2c|\3\2")
        buf.write(u"C\\\4\2..\60\60\4\2$$))\4\2\13\13\"\"\2\u00d6\2\3\3\2")
        buf.write(u"\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2")
        buf.write(u"\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2")
        buf.write(u"\25\3\2\2\2\2\27\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2\2?\3\2")
        buf.write(u"\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2\2I\3")
        buf.write(u"\2\2\2\2K\3\2\2\2\2M\3\2\2\2\2O\3\2\2\2\3Q\3\2\2\2\5")
        buf.write(u"S\3\2\2\2\7U\3\2\2\2\tW\3\2\2\2\13Y\3\2\2\2\r[\3\2\2")
        buf.write(u"\2\17]\3\2\2\2\21_\3\2\2\2\23a\3\2\2\2\25c\3\2\2\2\27")
        buf.write(u"e\3\2\2\2\31g\3\2\2\2\33i\3\2\2\2\35k\3\2\2\2\37m\3\2")
        buf.write(u"\2\2!o\3\2\2\2#q\3\2\2\2%s\3\2\2\2\'u\3\2\2\2)w\3\2\2")
        buf.write(u"\2+y\3\2\2\2-{\3\2\2\2/}\3\2\2\2\61\177\3\2\2\2\63\u0081")
        buf.write(u"\3\2\2\2\65\u0083\3\2\2\2\67\u0085\3\2\2\29\u0087\3\2")
        buf.write(u"\2\2;\u0089\3\2\2\2=\u008f\3\2\2\2?\u0093\3\2\2\2A\u009c")
        buf.write(u"\3\2\2\2C\u00a5\3\2\2\2E\u00b1\3\2\2\2G\u00b4\3\2\2\2")
        buf.write(u"I\u00c0\3\2\2\2K\u00c3\3\2\2\2M\u00cc\3\2\2\2O\u00d4")
        buf.write(u"\3\2\2\2QR\7\60\2\2R\4\3\2\2\2ST\7\61\2\2T\6\3\2\2\2")
        buf.write(u"UV\7a\2\2V\b\3\2\2\2WX\7^\2\2X\n\3\2\2\2YZ\7<\2\2Z\f")
        buf.write(u"\3\2\2\2[\\\7\'\2\2\\\16\3\2\2\2]^\7/\2\2^\20\3\2\2\2")
        buf.write(u"_`\7.\2\2`\22\3\2\2\2ab\7~\2\2b\24\3\2\2\2cd\7,\2\2d")
        buf.write(u"\26\3\2\2\2ef\7\u0080\2\2f\30\3\2\2\2gh\t\2\2\2h\32\3")
        buf.write(u"\2\2\2ij\t\3\2\2j\34\3\2\2\2kl\t\4\2\2l\36\3\2\2\2mn")
        buf.write(u"\t\5\2\2n \3\2\2\2op\t\6\2\2p\"\3\2\2\2qr\t\7\2\2r$\3")
        buf.write(u"\2\2\2st\t\b\2\2t&\3\2\2\2uv\t\t\2\2v(\3\2\2\2wx\t\n")
        buf.write(u"\2\2x*\3\2\2\2yz\t\13\2\2z,\3\2\2\2{|\t\f\2\2|.\3\2\2")
        buf.write(u"\2}~\t\r\2\2~\60\3\2\2\2\177\u0080\t\16\2\2\u0080\62")
        buf.write(u"\3\2\2\2\u0081\u0082\t\17\2\2\u0082\64\3\2\2\2\u0083")
        buf.write(u"\u0084\t\20\2\2\u0084\66\3\2\2\2\u0085\u0086\t\21\2\2")
        buf.write(u"\u00868\3\2\2\2\u0087\u0088\t\22\2\2\u0088:\3\2\2\2\u0089")
        buf.write(u"\u008a\5\61\31\2\u008a\u008b\5!\21\2\u008b\u008c\5\37")
        buf.write(u"\20\2\u008c\u008d\5+\26\2\u008d\u008e\5\37\20\2\u008e")
        buf.write(u"<\3\2\2\2\u008f\u0090\5\31\r\2\u0090\u0091\5\'\24\2\u0091")
        buf.write(u"\u0092\5\35\17\2\u0092>\3\2\2\2\u0093\u0094\5#\22\2\u0094")
        buf.write(u"\u0095\5\'\24\2\u0095\u0096\5\33\16\2\u0096\u0097\5%")
        buf.write(u"\23\2\u0097\u0098\5/\30\2\u0098\u0099\5\35\17\2\u0099")
        buf.write(u"\u009a\5\37\20\2\u009a\u009b\5-\27\2\u009b@\3\2\2\2\u009c")
        buf.write(u"\u009d\5\37\20\2\u009d\u009e\5\63\32\2\u009e\u009f\5")
        buf.write(u"\33\16\2\u009f\u00a0\5%\23\2\u00a0\u00a1\5/\30\2\u00a1")
        buf.write(u"\u00a2\5\35\17\2\u00a2\u00a3\5\37\20\2\u00a3\u00a4\5")
        buf.write(u"-\27\2\u00a4B\3\2\2\2\u00a5\u00a6\5)\25\2\u00a6\u00a7")
        buf.write(u"\5+\26\2\u00a7D\3\2\2\2\u00a8\u00b2\7>\2\2\u00a9\u00aa")
        buf.write(u"\7>\2\2\u00aa\u00b2\7?\2\2\u00ab\u00b2\7?\2\2\u00ac\u00ad")
        buf.write(u"\7@\2\2\u00ad\u00b2\7?\2\2\u00ae\u00b2\7@\2\2\u00af\u00b0")
        buf.write(u"\7#\2\2\u00b0\u00b2\7?\2\2\u00b1\u00a8\3\2\2\2\u00b1")
        buf.write(u"\u00a9\3\2\2\2\u00b1\u00ab\3\2\2\2\u00b1\u00ac\3\2\2")
        buf.write(u"\2\u00b1\u00ae\3\2\2\2\u00b1\u00af\3\2\2\2\u00b2F\3\2")
        buf.write(u"\2\2\u00b3\u00b5\5\65\33\2\u00b4\u00b3\3\2\2\2\u00b5")
        buf.write(u"\u00b6\3\2\2\2\u00b6\u00b4\3\2\2\2\u00b6\u00b7\3\2\2")
        buf.write(u"\2\u00b7\u00be\3\2\2\2\u00b8\u00ba\t\23\2\2\u00b9\u00bb")
        buf.write(u"\5\65\33\2\u00ba\u00b9\3\2\2\2\u00bb\u00bc\3\2\2\2\u00bc")
        buf.write(u"\u00ba\3\2\2\2\u00bc\u00bd\3\2\2\2\u00bd\u00bf\3\2\2")
        buf.write(u"\2\u00be\u00b8\3\2\2\2\u00be\u00bf\3\2\2\2\u00bfH\3\2")
        buf.write(u"\2\2\u00c0\u00c1\t\24\2\2\u00c1J\3\2\2\2\u00c2\u00c4")
        buf.write(u"\t\25\2\2\u00c3\u00c2\3\2\2\2\u00c4\u00c5\3\2\2\2\u00c5")
        buf.write(u"\u00c3\3\2\2\2\u00c5\u00c6\3\2\2\2\u00c6L\3\2\2\2\u00c7")
        buf.write(u"\u00c9\7\17\2\2\u00c8\u00c7\3\2\2\2\u00c8\u00c9\3\2\2")
        buf.write(u"\2\u00c9\u00ca\3\2\2\2\u00ca\u00cd\7\f\2\2\u00cb\u00cd")
        buf.write(u"\7\17\2\2\u00cc\u00c8\3\2\2\2\u00cc\u00cb\3\2\2\2\u00cd")
        buf.write(u"\u00ce\3\2\2\2\u00ce\u00cc\3\2\2\2\u00ce\u00cf\3\2\2")
        buf.write(u"\2\u00cfN\3\2\2\2\u00d0\u00d5\5\67\34\2\u00d1\u00d5\5")
        buf.write(u"9\35\2\u00d2\u00d5\5\65\33\2\u00d3\u00d5\7a\2\2\u00d4")
        buf.write(u"\u00d0\3\2\2\2\u00d4\u00d1\3\2\2\2\u00d4\u00d2\3\2\2")
        buf.write(u"\2\u00d4\u00d3\3\2\2\2\u00d5\u00d6\3\2\2\2\u00d6\u00d4")
        buf.write(u"\3\2\2\2\u00d6\u00d7\3\2\2\2\u00d7P\3\2\2\2\r\2\u00b1")
        buf.write(u"\u00b6\u00bc\u00be\u00c5\u00c8\u00cc\u00ce\u00d4\u00d6")
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
    OPERATOR = 17
    NUMBER = 18
    QUOTE = 19
    WHITESPACE = 20
    NEWLINE = 21
    WORD = 22

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", u"'%'", u"'-'", u"','", 
            u"'|'", u"'*'", u"'~'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"T__8", u"T__9", u"T__10", u"A", u"C", 
                  u"D", u"E", u"H", u"I", u"L", u"N", u"O", u"R", u"S", 
                  u"U", u"W", u"X", u"DIGIT", u"LOWERCASE", u"UPPERCASE", 
                  u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
                  u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


