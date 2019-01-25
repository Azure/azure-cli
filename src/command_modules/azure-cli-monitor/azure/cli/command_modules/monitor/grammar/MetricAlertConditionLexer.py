# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=all

# Generated from MetricAlertCondition.g4 by ANTLR 4.7.2
# encoding: utf-8
from __future__ import print_function
from antlr4 import *
from io import StringIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write(u"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2")
        buf.write(u"\25\u00cc\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6")
        buf.write(u"\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4")
        buf.write(u"\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t")
        buf.write(u"\22\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27")
        buf.write(u"\4\30\t\30\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4")
        buf.write(u"\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t")
        buf.write(u"#\4$\t$\4%\t%\3\2\3\2\3\3\3\3\3\4\3\4\3\5\3\5\3\6\3\6")
        buf.write(u"\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n\3\13\3\13\3\f\3\f\3")
        buf.write(u"\r\3\r\3\16\3\16\3\17\3\17\3\20\3\20\3\21\3\21\3\22\3")
        buf.write(u"\22\3\23\3\23\3\24\3\24\3\25\3\25\3\26\3\26\3\27\3\27")
        buf.write(u"\3\30\3\30\3\31\3\31\3\32\3\32\3\33\3\33\3\33\3\33\3")
        buf.write(u"\33\3\33\3\34\3\34\3\34\3\34\3\35\3\35\3\35\3\35\3\35")
        buf.write(u"\3\35\3\35\3\35\3\35\3\36\3\36\3\36\3\36\3\36\3\36\3")
        buf.write(u"\36\3\36\3\36\3\37\3\37\3\37\3 \3 \3 \3 \3 \3 \3 \3 ")
        buf.write(u"\3 \5 \u00a6\n \3!\6!\u00a9\n!\r!\16!\u00aa\3!\3!\6!")
        buf.write(u"\u00af\n!\r!\16!\u00b0\5!\u00b3\n!\3\"\3\"\3#\6#\u00b8")
        buf.write(u"\n#\r#\16#\u00b9\3$\5$\u00bd\n$\3$\3$\6$\u00c1\n$\r$")
        buf.write(u"\16$\u00c2\3%\3%\3%\3%\6%\u00c9\n%\r%\16%\u00ca\2\2&")
        buf.write(u"\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\2\25\2\27\2\31")
        buf.write(u"\2\33\2\35\2\37\2!\2#\2%\2\'\2)\2+\2-\2/\2\61\2\63\2")
        buf.write(u"\65\13\67\f9\r;\16=\17?\20A\21C\22E\23G\24I\25\3\2\26")
        buf.write(u"\4\2CCcc\4\2EEee\4\2FFff\4\2GGgg\4\2JJjj\4\2KKkk\4\2")
        buf.write(u"NNnn\4\2PPpp\4\2QQqq\4\2TTtt\4\2UUuu\4\2WWww\4\2YYyy")
        buf.write(u"\4\2ZZzz\3\2\62;\3\2c|\3\2C\\\4\2..\60\60\4\2$$))\4\2")
        buf.write(u"\13\13\"\"\2\u00ca\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2")
        buf.write(u"\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2")
        buf.write(u"\2\21\3\2\2\2\2\65\3\2\2\2\2\67\3\2\2\2\29\3\2\2\2\2")
        buf.write(u";\3\2\2\2\2=\3\2\2\2\2?\3\2\2\2\2A\3\2\2\2\2C\3\2\2\2")
        buf.write(u"\2E\3\2\2\2\2G\3\2\2\2\2I\3\2\2\2\3K\3\2\2\2\5M\3\2\2")
        buf.write(u"\2\7O\3\2\2\2\tQ\3\2\2\2\13S\3\2\2\2\rU\3\2\2\2\17W\3")
        buf.write(u"\2\2\2\21Y\3\2\2\2\23[\3\2\2\2\25]\3\2\2\2\27_\3\2\2")
        buf.write(u"\2\31a\3\2\2\2\33c\3\2\2\2\35e\3\2\2\2\37g\3\2\2\2!i")
        buf.write(u"\3\2\2\2#k\3\2\2\2%m\3\2\2\2\'o\3\2\2\2)q\3\2\2\2+s\3")
        buf.write(u"\2\2\2-u\3\2\2\2/w\3\2\2\2\61y\3\2\2\2\63{\3\2\2\2\65")
        buf.write(u"}\3\2\2\2\67\u0083\3\2\2\29\u0087\3\2\2\2;\u0090\3\2")
        buf.write(u"\2\2=\u0099\3\2\2\2?\u00a5\3\2\2\2A\u00a8\3\2\2\2C\u00b4")
        buf.write(u"\3\2\2\2E\u00b7\3\2\2\2G\u00c0\3\2\2\2I\u00c8\3\2\2\2")
        buf.write(u"KL\7\60\2\2L\4\3\2\2\2MN\7\61\2\2N\6\3\2\2\2OP\7a\2\2")
        buf.write(u"P\b\3\2\2\2QR\7^\2\2R\n\3\2\2\2ST\7<\2\2T\f\3\2\2\2U")
        buf.write(u"V\7\'\2\2V\16\3\2\2\2WX\7.\2\2X\20\3\2\2\2YZ\7/\2\2Z")
        buf.write(u"\22\3\2\2\2[\\\t\2\2\2\\\24\3\2\2\2]^\t\3\2\2^\26\3\2")
        buf.write(u"\2\2_`\t\4\2\2`\30\3\2\2\2ab\t\5\2\2b\32\3\2\2\2cd\t")
        buf.write(u"\6\2\2d\34\3\2\2\2ef\t\7\2\2f\36\3\2\2\2gh\t\b\2\2h ")
        buf.write(u"\3\2\2\2ij\t\t\2\2j\"\3\2\2\2kl\t\n\2\2l$\3\2\2\2mn\t")
        buf.write(u"\13\2\2n&\3\2\2\2op\t\f\2\2p(\3\2\2\2qr\t\r\2\2r*\3\2")
        buf.write(u"\2\2st\t\16\2\2t,\3\2\2\2uv\t\17\2\2v.\3\2\2\2wx\t\20")
        buf.write(u"\2\2x\60\3\2\2\2yz\t\21\2\2z\62\3\2\2\2{|\t\22\2\2|\64")
        buf.write(u"\3\2\2\2}~\5+\26\2~\177\5\33\16\2\177\u0080\5\31\r\2")
        buf.write(u"\u0080\u0081\5%\23\2\u0081\u0082\5\31\r\2\u0082\66\3")
        buf.write(u"\2\2\2\u0083\u0084\5\23\n\2\u0084\u0085\5!\21\2\u0085")
        buf.write(u"\u0086\5\27\f\2\u00868\3\2\2\2\u0087\u0088\5\35\17\2")
        buf.write(u"\u0088\u0089\5!\21\2\u0089\u008a\5\25\13\2\u008a\u008b")
        buf.write(u"\5\37\20\2\u008b\u008c\5)\25\2\u008c\u008d\5\27\f\2\u008d")
        buf.write(u"\u008e\5\31\r\2\u008e\u008f\5\'\24\2\u008f:\3\2\2\2\u0090")
        buf.write(u"\u0091\5\31\r\2\u0091\u0092\5-\27\2\u0092\u0093\5\25")
        buf.write(u"\13\2\u0093\u0094\5\37\20\2\u0094\u0095\5)\25\2\u0095")
        buf.write(u"\u0096\5\27\f\2\u0096\u0097\5\31\r\2\u0097\u0098\5\'")
        buf.write(u"\24\2\u0098<\3\2\2\2\u0099\u009a\5#\22\2\u009a\u009b")
        buf.write(u"\5%\23\2\u009b>\3\2\2\2\u009c\u00a6\7>\2\2\u009d\u009e")
        buf.write(u"\7>\2\2\u009e\u00a6\7?\2\2\u009f\u00a6\7?\2\2\u00a0\u00a1")
        buf.write(u"\7@\2\2\u00a1\u00a6\7?\2\2\u00a2\u00a6\7@\2\2\u00a3\u00a4")
        buf.write(u"\7#\2\2\u00a4\u00a6\7?\2\2\u00a5\u009c\3\2\2\2\u00a5")
        buf.write(u"\u009d\3\2\2\2\u00a5\u009f\3\2\2\2\u00a5\u00a0\3\2\2")
        buf.write(u"\2\u00a5\u00a2\3\2\2\2\u00a5\u00a3\3\2\2\2\u00a6@\3\2")
        buf.write(u"\2\2\u00a7\u00a9\5/\30\2\u00a8\u00a7\3\2\2\2\u00a9\u00aa")
        buf.write(u"\3\2\2\2\u00aa\u00a8\3\2\2\2\u00aa\u00ab\3\2\2\2\u00ab")
        buf.write(u"\u00b2\3\2\2\2\u00ac\u00ae\t\23\2\2\u00ad\u00af\5/\30")
        buf.write(u"\2\u00ae\u00ad\3\2\2\2\u00af\u00b0\3\2\2\2\u00b0\u00ae")
        buf.write(u"\3\2\2\2\u00b0\u00b1\3\2\2\2\u00b1\u00b3\3\2\2\2\u00b2")
        buf.write(u"\u00ac\3\2\2\2\u00b2\u00b3\3\2\2\2\u00b3B\3\2\2\2\u00b4")
        buf.write(u"\u00b5\t\24\2\2\u00b5D\3\2\2\2\u00b6\u00b8\t\25\2\2\u00b7")
        buf.write(u"\u00b6\3\2\2\2\u00b8\u00b9\3\2\2\2\u00b9\u00b7\3\2\2")
        buf.write(u"\2\u00b9\u00ba\3\2\2\2\u00baF\3\2\2\2\u00bb\u00bd\7\17")
        buf.write(u"\2\2\u00bc\u00bb\3\2\2\2\u00bc\u00bd\3\2\2\2\u00bd\u00be")
        buf.write(u"\3\2\2\2\u00be\u00c1\7\f\2\2\u00bf\u00c1\7\17\2\2\u00c0")
        buf.write(u"\u00bc\3\2\2\2\u00c0\u00bf\3\2\2\2\u00c1\u00c2\3\2\2")
        buf.write(u"\2\u00c2\u00c0\3\2\2\2\u00c2\u00c3\3\2\2\2\u00c3H\3\2")
        buf.write(u"\2\2\u00c4\u00c9\5\61\31\2\u00c5\u00c9\5\63\32\2\u00c6")
        buf.write(u"\u00c9\5/\30\2\u00c7\u00c9\7a\2\2\u00c8\u00c4\3\2\2\2")
        buf.write(u"\u00c8\u00c5\3\2\2\2\u00c8\u00c6\3\2\2\2\u00c8\u00c7")
        buf.write(u"\3\2\2\2\u00c9\u00ca\3\2\2\2\u00ca\u00c8\3\2\2\2\u00ca")
        buf.write(u"\u00cb\3\2\2\2\u00cbJ\3\2\2\2\r\2\u00a5\u00aa\u00b0\u00b2")
        buf.write(u"\u00b9\u00bc\u00c0\u00c2\u00c8\u00ca\2")
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
    WHERE = 9
    AND = 10
    INCLUDES = 11
    EXCLUDES = 12
    OR = 13
    OPERATOR = 14
    NUMBER = 15
    QUOTE = 16
    WHITESPACE = 17
    NEWLINE = 18
    WORD = 19

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ u"DEFAULT_MODE" ]

    literalNames = [ u"<INVALID>",
            u"'.'", u"'/'", u"'_'", u"'\\'", u"':'", u"'%'", u"','", u"'-'" ]

    symbolicNames = [ u"<INVALID>",
            u"WHERE", u"AND", u"INCLUDES", u"EXCLUDES", u"OR", u"OPERATOR", 
            u"NUMBER", u"QUOTE", u"WHITESPACE", u"NEWLINE", u"WORD" ]

    ruleNames = [ u"T__0", u"T__1", u"T__2", u"T__3", u"T__4", u"T__5", 
                  u"T__6", u"T__7", u"A", u"C", u"D", u"E", u"H", u"I", 
                  u"L", u"N", u"O", u"R", u"S", u"U", u"W", u"X", u"DIGIT", 
                  u"LOWERCASE", u"UPPERCASE", u"WHERE", u"AND", u"INCLUDES", 
                  u"EXCLUDES", u"OR", u"OPERATOR", u"NUMBER", u"QUOTE", 
                  u"WHITESPACE", u"NEWLINE", u"WORD" ]

    grammarFileName = u"MetricAlertCondition.g4"

    def __init__(self, input=None, output=sys.stdout):
        super(MetricAlertConditionLexer, self).__init__(input, output=output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


