/* PARSER RULES */

grammar AutoscaleCondition ;

/* Main Rules */

expression          : (QUOTE namespace QUOTE WHITESPACE)* (metric WHITESPACE) operator threshold aggregation period (WHITESPACE dimensions)* NEWLINE* ;

aggregation         : WORD WHITESPACE ;

namespace           : (WORD | WHITESPACE | '/' | '.' | '*' | '-' | '_' | ':' | '%' | '#' | '@')+;

metric              : (WORD | WHITESPACE | '.' | '/' | '_' | '\\' | ':' | '%' | '-' | ',' | '|')+;

operator            : OPERATOR WHITESPACE ;

threshold           : NUMBER WHITESPACE ;

period              : WORD ;

/* Dimensions */

where               : WHERE WHITESPACE ;

dimensions          : where dimension (dim_separator dimension)* ;

dimension           : dim_name dim_operator dim_values ;

dim_separator       : (AND | ',') WHITESPACE ;

dim_operator        : ('==' | '!=') WHITESPACE ;

dim_val_separator   : (OR | ',') WHITESPACE ;

dim_name            : WORD WHITESPACE ;

dim_values          : dim_value (dim_val_separator dim_value)* ;

dim_value           : (NUMBER | WORD | '-' | '.' | '*' | WHITESPACE | ':'| '~')+ ;

/* LEXER RULES */

fragment A          : ('a'|'A') ;
fragment C          : ('c'|'C') ;
fragment D          : ('d'|'D') ;
fragment E          : ('e'|'E') ;
fragment H          : ('h'|'H') ;
fragment I          : ('i'|'I') ;
fragment L          : ('l'|'L') ;
fragment N          : ('n'|'N') ;
fragment O          : ('o'|'O') ;
fragment R          : ('r'|'R') ;
fragment S          : ('s'|'S') ;
fragment U          : ('u'|'U') ;
fragment W          : ('w'|'W') ;
fragment X          : ('x'|'X') ;

fragment DIGIT      : [0-9] ;
fragment LOWERCASE  : [a-z] ;
fragment UPPERCASE  : [A-Z] ;

WHERE               : W H E R E ;
AND                 : A N D ;
INCLUDES            : I N C L U D E S ;
EXCLUDES            : E X C L U D E S ;
OR                  : O R ;

OPERATOR            : ('<' | '<=' | '==' | '>=' | '>' | '!=') ;
NUMBER              : DIGIT+ ([.,] DIGIT+)? ;
QUOTE               : ('\'' | '"') ;
WHITESPACE          : (' ' | '\t')+ ;
NEWLINE             : ('\r'? '\n' | '\r')+ ;
WORD                : (LOWERCASE | UPPERCASE | DIGIT | '_')+ ;

