# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# encoding: utf-8

# pylint: disable=all
# Generated from MetricAlertCondition.g4 by ANTLR 4.7.2
from __future__ import print_function
from antlr4 import *
from io import StringIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2")
        buf.write(u"\27\u00d4\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\4&\t&\4\'\t\'\3\2\3\2\3\3\3\3\3\4\3\4\3")
        buf.write(u"\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n\3\13\3")
        buf.write(u"\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17\3\17\3\20\3\20\3\21")
        buf.write(u"\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\25\3\25\3\26\3")
        buf.write(u"\26\3\27\3\27\3\30\3\30\3\31\3\31\3\32\3\32\3\33\3\33")
        buf.write(u"\3\34\3\34\3\35\3\35\3\35\3\35\3\35\3\35\3\36\3\36\3")
        buf.write(u"\36\3\36\3\37\3\37\3\37\3\37\3\37\3\37\3\37\3\37\3\37")
        buf.write(u"\3 \3 \3 \3 \3 \3 \3 \3 \3 \3!\3!\3!\3\"\3\"\3\"\3\"")
        buf.write(u"\3\"\3\"\3\"\3\"\3\"\5\"\u00ae\n\"\3#\6#\u00b1\n#\r#")
        buf.write(u"\16#\u00b2\3#\3#\6#\u00b7\n#\r#\16#\u00b8\5#\u00bb\n")
        buf.write(u"#\3$\3$\3%\6%\u00c0\n%\r%\16%\u00c1\3&\5&\u00c5\n&\3")
        buf.write(u"&\3&\6&\u00c9\n&\r&\16&\u00ca\3\'\3\'\3\'\3\'\6\'\u00d1")
        buf.write(u"\n\'\r\'\16\'\u00d2\2\2(\3\3\5\4\7\5\t\6\13\7\r\b\17")
        buf.write(u"\t\21\n\23\13\25\f\27\2\31\2\33\2\35\2\37\2!\2#\2%\2")
        buf.write(u"\'\2)\2+\2-\2/\2\61\2\63\2\65\2\67\29\r;\16=\17?\20A")
        buf.write(u"\21C\22E\23G\24I\25K\26M\27\3\2\26\4\2CCcc\4\2EEee\4")
        buf.write(u"\2FFff\4\2GGgg\4\2JJjj\4\2KKkk\4\2NNnn\4\2PPpp\4\2QQ")
        buf.write(u"qq\4\2TTtt\4\2UUuu\4\2WWww\4\2YYyy\4\2ZZzz\3\2\62;\3")
        buf.write(u"\2c|\3\2C\\\4\2..\60\60\4\2$$))\4\2\13\13\"\"\2\u00d2")
        buf.write(u"\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13")
        buf.write(u"\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3")
        buf.write(u"\2\2\2\2\25\3\2\2\2\29\3\2\2\2\2;\3\2\2\2\2=\3\2\2\2")
        buf.write(u"\2?\3\2\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2")
        buf.write(u"\2\2I\3\2\2\2\2K\3\2\2\2\2M\3\2\2\2\3O\3\2\2\2\5Q\3\2")
        buf.write(u"\2\2\7S\3\2\2\2\tU\3\2\2\2\13W\3\2\2\2\rY\3\2\2\2\17")
        buf.write(u"[\3\2\2\2\21]\3\2\2\2\23_\3\2\2\2\25a\3\2\2\2\27c\3\2")
        buf.write(u"\2\2\31e\3\2\2\2\33g\3\2\2\2\35i\3\2\2\2\37k\3\2\2\2")
        buf.write(u"!m\3\2\2\2#o\3\2\2\2%q\3\2\2\2\'s\3\2\2\2)u\3\2\2\2+")
        buf.write(u"w\3\2\2\2-y\3\2\2\2/{\3\2\2\2\61}\3\2\2\2\63\177\3\2")
        buf.write(u"\2\2\65\u0081\3\2\2\2\67\u0083\3\2\2\29\u0085\3\2\2\2")
        buf.write(u";\u008b\3\2\2\2=\u008f\3\2\2\2?\u0098\3\2\2\2A\u00a1")
        buf.write(u"\3\2\2\2C\u00ad\3\2\2\2E\u00b0\3\2\2\2G\u00bc\3\2\2\2")
        buf.write(u"I\u00bf\3\2\2\2K\u00c8\3\2\2\2M\u00d0\3\2\2\2OP\7\60")
        buf.write(u"\2\2P\4\3\2\2\2QR\7\61\2\2R\6\3\2\2\2ST\7a\2\2T\b\3\2")
        buf.write(u"\2\2UV\7^\2\2V\n\3\2\2\2WX\7<\2\2X\f\3\2\2\2YZ\7\'\2")
        buf.write(u"\2Z\16\3\2\2\2[\\\7/\2\2\\\20\3\2\2\2]^\7.\2\2^\22\3")
        buf.write(u"\2\2\2_`\7,\2\2`\24\3\2\2\2ab\7\u0080\2\2b\26\3\2\2\2")
        buf.write(u"cd\t\2\2\2d\30\3\2\2\2ef\t\3\2\2f\32\3\2\2\2gh\t\4\2")
        buf.write(u"\2h\34\3\2\2\2ij\t\5\2\2j\36\3\2\2\2kl\t\6\2\2l \3\2")
        buf.write(u"\2\2mn\t\7\2\2n\"\3\2\2\2op\t\b\2\2p$\3\2\2\2qr\t\t\2")
        buf.write(u"\2r&\3\2\2\2st\t\n\2\2t(\3\2\2\2uv\t\13\2\2v*\3\2\2\2")
        buf.write(u"wx\t\f\2\2x,\3\2\2\2yz\t\r\2\2z.\3\2\2\2{|\t\16\2\2|")
        buf.write(u"\60\3\2\2\2}~\t\17\2\2~\62\3\2\2\2\177\u0080\t\20\2\2")
        buf.write(u"\u0080\64\3\2\2\2\u0081\u0082\t\21\2\2\u0082\66\3\2\2")
        buf.write(u"\2\u0083\u0084\t\22\2\2\u00848\3\2\2\2\u0085\u0086\5")
        buf.write(u"/\30\2\u0086\u0087\5\37\20\2\u0087\u0088\5\35\17\2\u0088")
        buf.write(u"\u0089\5)\25\2\u0089\u008a\5\35\17\2\u008a:\3\2\2\2\u008b")
        buf.write(u"\u008c\5\27\f\2\u008c\u008d\5%\23\2\u008d\u008e\5\33")
        buf.write(u"\16\2\u008e<\3\2\2\2\u008f\u0090\5!\21\2\u0090\u0091")
        buf.write(u"\5%\23\2\u0091\u0092\5\31\r\2\u0092\u0093\5#\22\2\u0093")
        buf.write(u"\u0094\5-\27\2\u0094\u0095\5\33\16\2\u0095\u0096\5\35")
        buf.write(u"\17\2\u0096\u0097\5+\26\2\u0097>\3\2\2\2\u0098\u0099")
        buf.write(u"\5\35\17\2\u0099\u009a\5\61\31\2\u009a\u009b\5\31\r\2")
        buf.write(u"\u009b\u009c\5#\22\2\u009c\u009d\5-\27\2\u009d\u009e")
        buf.write(u"\5\33\16\2\u009e\u009f\5\35\17\2\u009f\u00a0\5+\26\2")
        buf.write(u"\u00a0@\3\2\2\2\u00a1\u00a2\5\'\24\2\u00a2\u00a3\5)\25")
        buf.write(u"\2\u00a3B\3\2\2\2\u00a4\u00ae\7>\2\2\u00a5\u00a6\7>\2")
        buf.write(u"\2\u00a6\u00ae\7?\2\2\u00a7\u00ae\7?\2\2\u00a8\u00a9")
        buf.write(u"\7@\2\2\u00a9\u00ae\7?\2\2\u00aa\u00ae\7@\2\2\u00ab\u00ac")
        buf.write(u"\7#\2\2\u00ac\u00ae\7?\2\2\u00ad\u00a4\3\2\2\2\u00ad")
        buf.write(u"\u00a5\3\2\2\2\u00ad\u00a7\3\2\2\2\u00ad\u00a8\3\2\2")
        buf.write(u"\2\u00ad\u00aa\3\2\2\2\u00ad\u00ab\3\2\2\2\u00aeD\3\2")
        buf.write(u"\2\2\u00af\u00b1\5\63\32\2\u00b0\u00af\3\2\2\2\u00b1")
        buf.write(u"\u00b2\3\2\2\2\u00b2\u00b0\3\2\2\2\u00b2\u00b3\3\2\2")
        buf.write(u"\2\u00b3\u00ba\3\2\2\2\u00b4\u00b6\t\23\2\2\u00b5\u00b7")
        buf.write(u"\5\63\32\2\u00b6\u00b5\3\2\2\2\u00b7\u00b8\3\2\2\2\u00b8")
        buf.write(u"\u00b6\3\2\2\2\u00b8\u00b9\3\2\2\2\u00b9\u00bb\3\2\2")
        buf.write(u"\2\u00ba\u00b4\3\2\2\2\u00ba\u00bb\3\2\2\2\u00bbF\3\2")
        buf.write(u"\2\2\u00bc\u00bd\t\24\2\2\u00bdH\3\2\2\2\u00be\u00c0")
        buf.write(u"\t\25\2\2\u00bf\u00be\3\2\2\2\u00c0\u00c1\3\2\2\2\u00c1")
        buf.write(u"\u00bf\3\2\2\2\u00c1\u00c2\3\2\2\2\u00c2J\3\2\2\2\u00c3")
        buf.write(u"\u00c5\7\17\2\2\u00c4\u00c3\3\2\2\2\u00c4\u00c5\3\2\2")
        buf.write(u"\2\u00c5\u00c6\3\2\2\2\u00c6\u00c9\7\f\2\2\u00c7\u00c9")
        buf.write(u"\7\17\2\2\u00c8\u00c4\3\2\2\2\u00c8\u00c7\3\2\2\2\u00c9")
        buf.write(u"\u00ca\3\2\2\2\u00ca\u00c8\3\2\2\2\u00ca\u00cb\3\2\2")
        buf.write(u"\2\u00cbL\3\2\2\2\u00cc\u00d1\5\65\33\2\u00cd\u00d1\5")
        buf.write(u"\67\34\2\u00ce\u00d1\5\63\32\2\u00cf\u00d1\7a\2\2\u00d0")
        buf.write(u"\u00cc\3\2\2\2\u00d0\u00cd\3\2\2\2\u00d0\u00ce\3\2\2")
        buf.write(u"\2\u00d0\u00cf\3\2\2\2\u00d1\u00d2\3\2\2\2\u00d2\u00d0")
        buf.write(u"\3\2\2\2\u00d2\u00d3\3\2\2\2\u00d3N\3\2\2\2\r\2\u00ad")
        buf.write(u"\u00b2\u00b8\u00ba\u00c1\u00c4\u00c8\u00ca\u00d0\u00d2")
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
    WHERE = 11
    AND = 12
    INCLUDES = 13
    EXCLUDES = 14
    OR = 15
    OPERATOR = 16
    NUMBER = 17
    QUOTE = 18
    WHITESPACE = 19
    NEWLINE = 20
    WORD = 21

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", u"'%'", u"'-'", u"','", 
            u"'*'", u"'~'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"T__8", u"T__9", u"A", u"C", u"D", 
                  u"E", u"H", u"I", u"L", u"N", u"O", u"R", u"S", u"U", 
                  u"W", u"X", u"DIGIT", u"LOWERCASE", u"UPPERCASE", u"WHERE", 
                  u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
                  u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


