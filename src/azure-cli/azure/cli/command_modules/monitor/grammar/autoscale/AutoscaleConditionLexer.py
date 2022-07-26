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
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\34")
        buf.write("\u00eb\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7")
        buf.write("\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r")
        buf.write("\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23")
        buf.write("\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30")
        buf.write("\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\4\36")
        buf.write("\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t#\4$\t$\4%\t%")
        buf.write("\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4,\t,\3\2\3\2\3")
        buf.write("\3\3\3\3\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t")
        buf.write("\3\n\3\n\3\13\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\16\3\17")
        buf.write("\3\17\3\17\3\20\3\20\3\21\3\21\3\22\3\22\3\23\3\23\3\24")
        buf.write("\3\24\3\25\3\25\3\26\3\26\3\27\3\27\3\30\3\30\3\31\3\31")
        buf.write("\3\32\3\32\3\33\3\33\3\34\3\34\3\35\3\35\3\36\3\36\3\37")
        buf.write("\3\37\3 \3 \3!\3!\3\"\3\"\3\"\3\"\3\"\3\"\3#\3#\3#\3#")
        buf.write("\3$\3$\3$\3$\3$\3$\3$\3$\3$\3%\3%\3%\3%\3%\3%\3%\3%\3")
        buf.write("%\3&\3&\3&\3\'\3\'\3\'\3\'\3\'\3\'\3\'\3\'\3\'\3\'\5\'")
        buf.write("\u00c5\n\'\3(\6(\u00c8\n(\r(\16(\u00c9\3(\3(\6(\u00ce")
        buf.write("\n(\r(\16(\u00cf\5(\u00d2\n(\3)\3)\3*\6*\u00d7\n*\r*\16")
        buf.write("*\u00d8\3+\5+\u00dc\n+\3+\3+\6+\u00e0\n+\r+\16+\u00e1")
        buf.write("\3,\3,\3,\3,\6,\u00e8\n,\r,\16,\u00e9\2\2-\3\3\5\4\7\5")
        buf.write("\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27\r\31\16\33\17\35")
        buf.write("\20\37\21!\2#\2%\2\'\2)\2+\2-\2/\2\61\2\63\2\65\2\67\2")
        buf.write("9\2;\2=\2?\2A\2C\22E\23G\24I\25K\26M\27O\30Q\31S\32U\33")
        buf.write("W\34\3\2\26\4\2CCcc\4\2EEee\4\2FFff\4\2GGgg\4\2JJjj\4")
        buf.write("\2KKkk\4\2NNnn\4\2PPpp\4\2QQqq\4\2TTtt\4\2UUuu\4\2WWw")
        buf.write("w\4\2YYyy\4\2ZZzz\3\2\62;\3\2c|\3\2C\\\4\2..\60\60\4\2")
        buf.write("$$))\4\2\13\13\"\"\2\u00e9\2\3\3\2\2\2\2\5\3\2\2\2\2\7")
        buf.write("\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2\2\17\3\2")
        buf.write("\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2\27\3\2\2")
        buf.write("\2\2\31\3\2\2\2\2\33\3\2\2\2\2\35\3\2\2\2\2\37\3\2\2\2")
        buf.write("\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2\2I\3\2\2\2\2K\3\2\2")
        buf.write("\2\2M\3\2\2\2\2O\3\2\2\2\2Q\3\2\2\2\2S\3\2\2\2\2U\3\2")
        buf.write("\2\2\2W\3\2\2\2\3Y\3\2\2\2\5[\3\2\2\2\7]\3\2\2\2\t_\3")
        buf.write("\2\2\2\13a\3\2\2\2\rc\3\2\2\2\17e\3\2\2\2\21g\3\2\2\2")
        buf.write("\23i\3\2\2\2\25k\3\2\2\2\27m\3\2\2\2\31o\3\2\2\2\33q\3")
        buf.write("\2\2\2\35t\3\2\2\2\37w\3\2\2\2!y\3\2\2\2#{\3\2\2\2%}\3")
        buf.write("\2\2\2\'\177\3\2\2\2)\u0081\3\2\2\2+\u0083\3\2\2\2-\u0085")
        buf.write("\3\2\2\2/\u0087\3\2\2\2\61\u0089\3\2\2\2\63\u008b\3\2")
        buf.write("\2\2\65\u008d\3\2\2\2\67\u008f\3\2\2\29\u0091\3\2\2\2")
        buf.write(";\u0093\3\2\2\2=\u0095\3\2\2\2?\u0097\3\2\2\2A\u0099\3")
        buf.write("\2\2\2C\u009b\3\2\2\2E\u00a1\3\2\2\2G\u00a5\3\2\2\2I\u00ae")
        buf.write("\3\2\2\2K\u00b7\3\2\2\2M\u00c4\3\2\2\2O\u00c7\3\2\2\2")
        buf.write("Q\u00d3\3\2\2\2S\u00d6\3\2\2\2U\u00df\3\2\2\2W\u00e7\3")
        buf.write("\2\2\2YZ\7\61\2\2Z\4\3\2\2\2[\\\7\60\2\2\\\6\3\2\2\2]")
        buf.write("^\7,\2\2^\b\3\2\2\2_`\7/\2\2`\n\3\2\2\2ab\7a\2\2b\f\3")
        buf.write("\2\2\2cd\7<\2\2d\16\3\2\2\2ef\7\'\2\2f\20\3\2\2\2gh\7")
        buf.write("%\2\2h\22\3\2\2\2ij\7B\2\2j\24\3\2\2\2kl\7^\2\2l\26\3")
        buf.write("\2\2\2mn\7.\2\2n\30\3\2\2\2op\7~\2\2p\32\3\2\2\2qr\7?")
        buf.write("\2\2rs\7?\2\2s\34\3\2\2\2tu\7#\2\2uv\7?\2\2v\36\3\2\2")
        buf.write("\2wx\7\u0080\2\2x \3\2\2\2yz\t\2\2\2z\"\3\2\2\2{|\t\3")
        buf.write("\2\2|$\3\2\2\2}~\t\4\2\2~&\3\2\2\2\177\u0080\t\5\2\2\u0080")
        buf.write("(\3\2\2\2\u0081\u0082\t\6\2\2\u0082*\3\2\2\2\u0083\u0084")
        buf.write("\t\7\2\2\u0084,\3\2\2\2\u0085\u0086\t\b\2\2\u0086.\3\2")
        buf.write("\2\2\u0087\u0088\t\t\2\2\u0088\60\3\2\2\2\u0089\u008a")
        buf.write("\t\n\2\2\u008a\62\3\2\2\2\u008b\u008c\t\13\2\2\u008c\64")
        buf.write("\3\2\2\2\u008d\u008e\t\f\2\2\u008e\66\3\2\2\2\u008f\u0090")
        buf.write("\t\r\2\2\u00908\3\2\2\2\u0091\u0092\t\16\2\2\u0092:\3")
        buf.write("\2\2\2\u0093\u0094\t\17\2\2\u0094<\3\2\2\2\u0095\u0096")
        buf.write("\t\20\2\2\u0096>\3\2\2\2\u0097\u0098\t\21\2\2\u0098@\3")
        buf.write("\2\2\2\u0099\u009a\t\22\2\2\u009aB\3\2\2\2\u009b\u009c")
        buf.write("\59\35\2\u009c\u009d\5)\25\2\u009d\u009e\5\'\24\2\u009e")
        buf.write("\u009f\5\63\32\2\u009f\u00a0\5\'\24\2\u00a0D\3\2\2\2\u00a1")
        buf.write("\u00a2\5!\21\2\u00a2\u00a3\5/\30\2\u00a3\u00a4\5%\23\2")
        buf.write("\u00a4F\3\2\2\2\u00a5\u00a6\5+\26\2\u00a6\u00a7\5/\30")
        buf.write("\2\u00a7\u00a8\5#\22\2\u00a8\u00a9\5-\27\2\u00a9\u00aa")
        buf.write("\5\67\34\2\u00aa\u00ab\5%\23\2\u00ab\u00ac\5\'\24\2\u00ac")
        buf.write("\u00ad\5\65\33\2\u00adH\3\2\2\2\u00ae\u00af\5\'\24\2\u00af")
        buf.write("\u00b0\5;\36\2\u00b0\u00b1\5#\22\2\u00b1\u00b2\5-\27\2")
        buf.write("\u00b2\u00b3\5\67\34\2\u00b3\u00b4\5%\23\2\u00b4\u00b5")
        buf.write("\5\'\24\2\u00b5\u00b6\5\65\33\2\u00b6J\3\2\2\2\u00b7\u00b8")
        buf.write("\5\61\31\2\u00b8\u00b9\5\63\32\2\u00b9L\3\2\2\2\u00ba")
        buf.write("\u00c5\7>\2\2\u00bb\u00bc\7>\2\2\u00bc\u00c5\7?\2\2\u00bd")
        buf.write("\u00be\7?\2\2\u00be\u00c5\7?\2\2\u00bf\u00c0\7@\2\2\u00c0")
        buf.write("\u00c5\7?\2\2\u00c1\u00c5\7@\2\2\u00c2\u00c3\7#\2\2\u00c3")
        buf.write("\u00c5\7?\2\2\u00c4\u00ba\3\2\2\2\u00c4\u00bb\3\2\2\2")
        buf.write("\u00c4\u00bd\3\2\2\2\u00c4\u00bf\3\2\2\2\u00c4\u00c1\3")
        buf.write("\2\2\2\u00c4\u00c2\3\2\2\2\u00c5N\3\2\2\2\u00c6\u00c8")
        buf.write("\5=\37\2\u00c7\u00c6\3\2\2\2\u00c8\u00c9\3\2\2\2\u00c9")
        buf.write("\u00c7\3\2\2\2\u00c9\u00ca\3\2\2\2\u00ca\u00d1\3\2\2\2")
        buf.write("\u00cb\u00cd\t\23\2\2\u00cc\u00ce\5=\37\2\u00cd\u00cc")
        buf.write("\3\2\2\2\u00ce\u00cf\3\2\2\2\u00cf\u00cd\3\2\2\2\u00cf")
        buf.write("\u00d0\3\2\2\2\u00d0\u00d2\3\2\2\2\u00d1\u00cb\3\2\2\2")
        buf.write("\u00d1\u00d2\3\2\2\2\u00d2P\3\2\2\2\u00d3\u00d4\t\24\2")
        buf.write("\2\u00d4R\3\2\2\2\u00d5\u00d7\t\25\2\2\u00d6\u00d5\3\2")
        buf.write("\2\2\u00d7\u00d8\3\2\2\2\u00d8\u00d6\3\2\2\2\u00d8\u00d9")
        buf.write("\3\2\2\2\u00d9T\3\2\2\2\u00da\u00dc\7\17\2\2\u00db\u00da")
        buf.write("\3\2\2\2\u00db\u00dc\3\2\2\2\u00dc\u00dd\3\2\2\2\u00dd")
        buf.write("\u00e0\7\f\2\2\u00de\u00e0\7\17\2\2\u00df\u00db\3\2\2")
        buf.write("\2\u00df\u00de\3\2\2\2\u00e0\u00e1\3\2\2\2\u00e1\u00df")
        buf.write("\3\2\2\2\u00e1\u00e2\3\2\2\2\u00e2V\3\2\2\2\u00e3\u00e8")
        buf.write("\5? \2\u00e4\u00e8\5A!\2\u00e5\u00e8\5=\37\2\u00e6\u00e8")
        buf.write("\7a\2\2\u00e7\u00e3\3\2\2\2\u00e7\u00e4\3\2\2\2\u00e7")
        buf.write("\u00e5\3\2\2\2\u00e7\u00e6\3\2\2\2\u00e8\u00e9\3\2\2\2")
        buf.write("\u00e9\u00e7\3\2\2\2\u00e9\u00ea\3\2\2\2\u00eaX\3\2\2")
        buf.write("\2\r\2\u00c4\u00c9\u00cf\u00d1\u00d8\u00db\u00df\u00e1")
        buf.write("\u00e7\u00e9\2")
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
    T__13 = 14
    T__14 = 15
    WHERE = 16
    AND = 17
    INCLUDES = 18
    EXCLUDES = 19
    OR = 20
    OPERATOR = 21
    NUMBER = 22
    QUOTE = 23
    WHITESPACE = 24
    NEWLINE = 25
    WORD = 26

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'/'", "'.'", "'*'", "'-'", "'_'", "':'", "'%'", "'#'", "'@'", 
            "'\\'", "','", "'|'", "'=='", "'!='", "'~'" ]

    symbolicNames = [ "<INVALID>",
            "WHERE", "AND", "INCLUDES", "EXCLUDES", "OR", "OPERATOR", "NUMBER", 
            "QUOTE", "WHITESPACE", "NEWLINE", "WORD" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "T__8", "T__9", "T__10", "T__11", "T__12", "T__13", 
                  "T__14", "A", "C", "D", "E", "H", "I", "L", "N", "O", 
                  "R", "S", "U", "W", "X", "DIGIT", "LOWERCASE", "UPPERCASE", 
                  "WHERE", "AND", "INCLUDES", "EXCLUDES", "OR", "OPERATOR", 
                  "NUMBER", "QUOTE", "WHITESPACE", "NEWLINE", "WORD" ]

    grammarFileName = "AutoscaleCondition.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.3")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


