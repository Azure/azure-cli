from enum import Enum


class Symbol(Enum):
    WHITE_SPACE = ' '
    QUOTE = '"'
    COLON = ':'
    LEFT_SQUARE_BRACKET = '['
    RIGHT_SQUARE_BRACKET = ']'
    DOT = '.'
    EQUAL = '='
    ASTERISK = '*'
    PLUS = '+'
    MINUS = '-'
    TILDE = '~'
    EXCLAMATION_POINT = '!'

    def __str__(self):
        return self.value
