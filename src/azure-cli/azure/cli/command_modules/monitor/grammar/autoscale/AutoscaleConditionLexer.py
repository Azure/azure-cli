# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated from AutoscaleCondition.g4 by ANTLR 4.7.2
# encoding: utf-8
# pylint: disable=all
from __future__ import print_function
from antlr4 import *
from io import StringIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2")
        buf.write(u"\32\u00e3\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\3\2\3\2")
        buf.write(u"\3\3\3\3\3\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t")
        buf.write(u"\3\t\3\n\3\n\3\13\3\13\3\13\3\f\3\f\3\f\3\r\3\r\3\16")
        buf.write(u"\3\16\3\17\3\17\3\20\3\20\3\21\3\21\3\22\3\22\3\23\3")
        buf.write(u"\23\3\24\3\24\3\25\3\25\3\26\3\26\3\27\3\27\3\30\3\30")
        buf.write(u"\3\31\3\31\3\32\3\32\3\33\3\33\3\34\3\34\3\35\3\35\3")
        buf.write(u"\36\3\36\3\37\3\37\3 \3 \3 \3 \3 \3 \3!\3!\3!\3!\3\"")
        buf.write(u"\3\"\3\"\3\"\3\"\3\"\3\"\3\"\3\"\3#\3#\3#\3#\3#\3#\3")
        buf.write(u"#\3#\3#\3$\3$\3$\3%\3%\3%\3%\3%\3%\3%\3%\3%\3%\5%\u00bd")
        buf.write(u"\n%\3&\6&\u00c0\n&\r&\16&\u00c1\3&\3&\6&\u00c6\n&\r&")
        buf.write(u"\16&\u00c7\5&\u00ca\n&\3\'\3\'\3(\6(\u00cf\n(\r(\16(")
        buf.write(u"\u00d0\3)\5)\u00d4\n)\3)\3)\6)\u00d8\n)\r)\16)\u00d9")
        buf.write(u"\3*\3*\3*\3*\6*\u00e0\n*\r*\16*\u00e1\2\2+\3\3\5\4\7")
        buf.write(u"\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27\r\31\16\33\17")
        buf.write(u"\35\2\37\2!\2#\2%\2\'\2)\2+\2-\2/\2\61\2\63\2\65\2\67")
        buf.write(u"\29\2;\2=\2?\20A\21C\22E\23G\24I\25K\26M\27O\30Q\31S")
        buf.write(u"\32\3\2\26\4\2CCcc\4\2EEee\4\2FFff\4\2GGgg\4\2JJjj\4")
        buf.write(u"\2KKkk\4\2NNnn\4\2PPpp\4\2QQqq\4\2TTtt\4\2UUuu\4\2WW")
        buf.write(u"ww\4\2YYyy\4\2ZZzz\3\2\62;\3\2c|\3\2C\\\4\2..\60\60\4")
        buf.write(u"\2$$))\4\2\13\13\"\"\2\u00e1\2\3\3\2\2\2\2\5\3\2\2\2")
        buf.write(u"\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2\2\17")
        buf.write(u"\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2\27")
        buf.write(u"\3\2\2\2\2\31\3\2\2\2\2\33\3\2\2\2\2?\3\2\2\2\2A\3\2")
        buf.write(u"\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2\2I\3\2\2\2\2K\3")
        buf.write(u"\2\2\2\2M\3\2\2\2\2O\3\2\2\2\2Q\3\2\2\2\2S\3\2\2\2\3")
        buf.write(u"U\3\2\2\2\5W\3\2\2\2\7Y\3\2\2\2\t[\3\2\2\2\13]\3\2\2")
        buf.write(u"\2\r_\3\2\2\2\17a\3\2\2\2\21c\3\2\2\2\23e\3\2\2\2\25")
        buf.write(u"g\3\2\2\2\27j\3\2\2\2\31m\3\2\2\2\33o\3\2\2\2\35q\3\2")
        buf.write(u"\2\2\37s\3\2\2\2!u\3\2\2\2#w\3\2\2\2%y\3\2\2\2\'{\3\2")
        buf.write(u"\2\2)}\3\2\2\2+\177\3\2\2\2-\u0081\3\2\2\2/\u0083\3\2")
        buf.write(u"\2\2\61\u0085\3\2\2\2\63\u0087\3\2\2\2\65\u0089\3\2\2")
        buf.write(u"\2\67\u008b\3\2\2\29\u008d\3\2\2\2;\u008f\3\2\2\2=\u0091")
        buf.write(u"\3\2\2\2?\u0093\3\2\2\2A\u0099\3\2\2\2C\u009d\3\2\2\2")
        buf.write(u"E\u00a6\3\2\2\2G\u00af\3\2\2\2I\u00bc\3\2\2\2K\u00bf")
        buf.write(u"\3\2\2\2M\u00cb\3\2\2\2O\u00ce\3\2\2\2Q\u00d7\3\2\2\2")
        buf.write(u"S\u00df\3\2\2\2UV\7\61\2\2V\4\3\2\2\2WX\7\60\2\2X\6\3")
        buf.write(u"\2\2\2YZ\7a\2\2Z\b\3\2\2\2[\\\7^\2\2\\\n\3\2\2\2]^\7")
        buf.write(u"<\2\2^\f\3\2\2\2_`\7\'\2\2`\16\3\2\2\2ab\7/\2\2b\20\3")
        buf.write(u"\2\2\2cd\7.\2\2d\22\3\2\2\2ef\7~\2\2f\24\3\2\2\2gh\7")
        buf.write(u"?\2\2hi\7?\2\2i\26\3\2\2\2jk\7#\2\2kl\7?\2\2l\30\3\2")
        buf.write(u"\2\2mn\7,\2\2n\32\3\2\2\2op\7\u0080\2\2p\34\3\2\2\2q")
        buf.write(u"r\t\2\2\2r\36\3\2\2\2st\t\3\2\2t \3\2\2\2uv\t\4\2\2v")
        buf.write(u"\"\3\2\2\2wx\t\5\2\2x$\3\2\2\2yz\t\6\2\2z&\3\2\2\2{|")
        buf.write(u"\t\7\2\2|(\3\2\2\2}~\t\b\2\2~*\3\2\2\2\177\u0080\t\t")
        buf.write(u"\2\2\u0080,\3\2\2\2\u0081\u0082\t\n\2\2\u0082.\3\2\2")
        buf.write(u"\2\u0083\u0084\t\13\2\2\u0084\60\3\2\2\2\u0085\u0086")
        buf.write(u"\t\f\2\2\u0086\62\3\2\2\2\u0087\u0088\t\r\2\2\u0088\64")
        buf.write(u"\3\2\2\2\u0089\u008a\t\16\2\2\u008a\66\3\2\2\2\u008b")
        buf.write(u"\u008c\t\17\2\2\u008c8\3\2\2\2\u008d\u008e\t\20\2\2\u008e")
        buf.write(u":\3\2\2\2\u008f\u0090\t\21\2\2\u0090<\3\2\2\2\u0091\u0092")
        buf.write(u"\t\22\2\2\u0092>\3\2\2\2\u0093\u0094\5\65\33\2\u0094")
        buf.write(u"\u0095\5%\23\2\u0095\u0096\5#\22\2\u0096\u0097\5/\30")
        buf.write(u"\2\u0097\u0098\5#\22\2\u0098@\3\2\2\2\u0099\u009a\5\35")
        buf.write(u"\17\2\u009a\u009b\5+\26\2\u009b\u009c\5!\21\2\u009cB")
        buf.write(u"\3\2\2\2\u009d\u009e\5\'\24\2\u009e\u009f\5+\26\2\u009f")
        buf.write(u"\u00a0\5\37\20\2\u00a0\u00a1\5)\25\2\u00a1\u00a2\5\63")
        buf.write(u"\32\2\u00a2\u00a3\5!\21\2\u00a3\u00a4\5#\22\2\u00a4\u00a5")
        buf.write(u"\5\61\31\2\u00a5D\3\2\2\2\u00a6\u00a7\5#\22\2\u00a7\u00a8")
        buf.write(u"\5\67\34\2\u00a8\u00a9\5\37\20\2\u00a9\u00aa\5)\25\2")
        buf.write(u"\u00aa\u00ab\5\63\32\2\u00ab\u00ac\5!\21\2\u00ac\u00ad")
        buf.write(u"\5#\22\2\u00ad\u00ae\5\61\31\2\u00aeF\3\2\2\2\u00af\u00b0")
        buf.write(u"\5-\27\2\u00b0\u00b1\5/\30\2\u00b1H\3\2\2\2\u00b2\u00bd")
        buf.write(u"\7>\2\2\u00b3\u00b4\7>\2\2\u00b4\u00bd\7?\2\2\u00b5\u00b6")
        buf.write(u"\7?\2\2\u00b6\u00bd\7?\2\2\u00b7\u00b8\7@\2\2\u00b8\u00bd")
        buf.write(u"\7?\2\2\u00b9\u00bd\7@\2\2\u00ba\u00bb\7#\2\2\u00bb\u00bd")
        buf.write(u"\7?\2\2\u00bc\u00b2\3\2\2\2\u00bc\u00b3\3\2\2\2\u00bc")
        buf.write(u"\u00b5\3\2\2\2\u00bc\u00b7\3\2\2\2\u00bc\u00b9\3\2\2")
        buf.write(u"\2\u00bc\u00ba\3\2\2\2\u00bdJ\3\2\2\2\u00be\u00c0\59")
        buf.write(u"\35\2\u00bf\u00be\3\2\2\2\u00c0\u00c1\3\2\2\2\u00c1\u00bf")
        buf.write(u"\3\2\2\2\u00c1\u00c2\3\2\2\2\u00c2\u00c9\3\2\2\2\u00c3")
        buf.write(u"\u00c5\t\23\2\2\u00c4\u00c6\59\35\2\u00c5\u00c4\3\2\2")
        buf.write(u"\2\u00c6\u00c7\3\2\2\2\u00c7\u00c5\3\2\2\2\u00c7\u00c8")
        buf.write(u"\3\2\2\2\u00c8\u00ca\3\2\2\2\u00c9\u00c3\3\2\2\2\u00c9")
        buf.write(u"\u00ca\3\2\2\2\u00caL\3\2\2\2\u00cb\u00cc\t\24\2\2\u00cc")
        buf.write(u"N\3\2\2\2\u00cd\u00cf\t\25\2\2\u00ce\u00cd\3\2\2\2\u00cf")
        buf.write(u"\u00d0\3\2\2\2\u00d0\u00ce\3\2\2\2\u00d0\u00d1\3\2\2")
        buf.write(u"\2\u00d1P\3\2\2\2\u00d2\u00d4\7\17\2\2\u00d3\u00d2\3")
        buf.write(u"\2\2\2\u00d3\u00d4\3\2\2\2\u00d4\u00d5\3\2\2\2\u00d5")
        buf.write(u"\u00d8\7\f\2\2\u00d6\u00d8\7\17\2\2\u00d7\u00d3\3\2\2")
        buf.write(u"\2\u00d7\u00d6\3\2\2\2\u00d8\u00d9\3\2\2\2\u00d9\u00d7")
        buf.write(u"\3\2\2\2\u00d9\u00da\3\2\2\2\u00daR\3\2\2\2\u00db\u00e0")
        buf.write(u"\5;\36\2\u00dc\u00e0\5=\37\2\u00dd\u00e0\59\35\2\u00de")
        buf.write(u"\u00e0\7a\2\2\u00df\u00db\3\2\2\2\u00df\u00dc\3\2\2\2")
        buf.write(u"\u00df\u00dd\3\2\2\2\u00df\u00de\3\2\2\2\u00e0\u00e1")
        buf.write(u"\3\2\2\2\u00e1\u00df\3\2\2\2\u00e1\u00e2\3\2\2\2\u00e2")
        buf.write(u"T\3\2\2\2\r\2\u00bc\u00c1\u00c7\u00c9\u00d0\u00d3\u00d7")
        buf.write(u"\u00d9\u00df\u00e1\2")
        return buf.getvalue()


class AutoscaleConditionLexer(Lexer):

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
    WHERE = 14
    AND = 15
    INCLUDES = 16
    EXCLUDES = 17
    OR = 18
    OPERATOR = 19
    NUMBER = 20
    QUOTE = 21
    WHITESPACE = 22
    NEWLINE = 23
    WORD = 24

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'/'", u"'.'", u"'_'", u"'\\'", u"':'", u"'%'", u"'-'", u"','", 
            u"'|'", u"'=='", u"'!='", u"'*'", u"'~'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"T__8", u"T__9", u"T__10", u"T__11", 
                  u"T__12", u"A", u"C", u"D", u"E", u"H", u"I", u"L", u"N", 
                  u"O", u"R", u"S", u"U", u"W", u"X", u"DIGIT", u"LOWERCASE", 
                  u"UPPERCASE", u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", 
                  u"OR", u"OPERATOR", u"NUMBER", u"QUOTE", u"WHITESPACE", 
                  u"NEWLINE", u"WORD" ]

    grammarFileName = u"AutoscaleCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(AutoscaleConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


