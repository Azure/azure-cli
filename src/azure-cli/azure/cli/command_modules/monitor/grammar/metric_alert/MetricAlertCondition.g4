/* PARSER RULES */

grammar MetricAlertCondition ;

/* Main Rules */

expression          : aggregation (namespace '.')* (QUOTE metric QUOTE WHITESPACE | metric) operator (threshold | dynamics) (WHITESPACE dimensions)* (WHITESPACE options_)? NEWLINE* ;

aggregation         : WORD WHITESPACE ;

namespace           : (NUMBER | WORD | '/' | '.')+;

metric              : (NUMBER | WORD | WHITESPACE | '.' | '/' | '_' | '\\' | ':' | '%' | '-' | ',' | '|')+;

operator            : OPERATOR WHITESPACE ;

/* Statics */

threshold           : NUMBER ;

/* Dynamics */

dynamic             : DYNAMIC WHITESPACE ;

dynamics            : dynamic dyn_sensitivity dyn_violations dyn_of_separator dyn_windows (WHITESPACE dyn_since_seperator dyn_datetime)* ;

dyn_sensitivity     : WORD WHITESPACE ;

dyn_violations      : NUMBER WHITESPACE ;

dyn_of_separator    : OF WHITESPACE ;

dyn_windows         : NUMBER ;

dyn_since_seperator : SINCE WHITESPACE ;

dyn_datetime        : (NUMBER | WORD | '.' | '-' | ':' | '+')+;

/* Dimensions */

where               : WHERE WHITESPACE ;

dimensions          : where dimension (dim_separator dimension)* ;

dimension           : dim_name dim_operator dim_values ;

dim_separator       : (AND | ',') WHITESPACE ;

dim_operator        : (INCLUDES | EXCLUDES) WHITESPACE ;

dim_val_separator   : (OR | ',') WHITESPACE ;

dim_name            : WORD WHITESPACE ;

dim_values          : dim_value (dim_val_separator dim_value)* ;

dim_value           : (NUMBER | WORD | '-' | '.' | '*' | WHITESPACE | ':'| '~' | ',' | '|' | '%' | '_')+ ;

/* Options */

options_            : with_ option ;

with_               : WITH WHITESPACE ;

option              : SKIPMETRICVALIDATION ;

/* LEXER RULES */

fragment A          : ('a'|'A') ;
fragment C          : ('c'|'C') ;
fragment D          : ('d'|'D') ;
fragment E          : ('e'|'E') ;
fragment F          : ('f'|'F') ;
fragment H          : ('h'|'H') ;
fragment I          : ('i'|'I') ;
fragment K          : ('k'|'K') ;
fragment L          : ('l'|'L') ;
fragment M          : ('m'|'M') ;
fragment N          : ('n'|'N') ;
fragment O          : ('o'|'O') ;
fragment P          : ('p'|'P') ;
fragment R          : ('r'|'R') ;
fragment S          : ('s'|'S') ;
fragment T          : ('t'|'T') ;
fragment U          : ('u'|'U') ;
fragment V          : ('v'|'V') ;
fragment W          : ('w'|'W') ;
fragment X          : ('x'|'X') ;
fragment Y          : ('y'|'Y') ;

fragment DIGIT      : [0-9] ;
fragment LOWERCASE  : [a-z] ;
fragment UPPERCASE  : [A-Z] ;

WHERE               : W H E R E ;
AND                 : A N D ;
INCLUDES            : I N C L U D E S ;
EXCLUDES            : E X C L U D E S ;
OR                  : O R ;
DYNAMIC             : D Y N A M I C ;
OF                  : O F ;
SINCE               : S I N C E ;
WITH                : W I T H ;
SKIPMETRICVALIDATION : S K I P M E T R I C V A L I D A T I O N ;

OPERATOR            : ('<' | '<=' | '=' | '>=' | '>' | '!=' | '><') ;
NUMBER              : DIGIT+ ([.,] DIGIT+)? ;
QUOTE               : ('\'' | '"') ;
WHITESPACE          : (' ' | '\t')+ ;
NEWLINE             : ('\r'? '\n' | '\r')+ ;
WORD                : (LOWERCASE | UPPERCASE | DIGIT | '_' )+ ;
