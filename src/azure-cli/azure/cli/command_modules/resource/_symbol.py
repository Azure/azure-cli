# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum


class Symbol(Enum):
    WHITE_SPACE = " "
    QUOTE = '"'
    COLON = ":"
    LEFT_SQUARE_BRACKET = "["
    RIGHT_SQUARE_BRACKET = "]"
    DOT = "."
    EQUAL = "="
    ASTERISK = "*"
    PLUS = "+"
    MINUS = "-"
    TILDE = "~"
    EXCLAMATION_POINT = "!"
    CROSS = "x"

    def __str__(self):
        return self.value
