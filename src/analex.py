import ply.lex as lex

tokens = [
    'AND',
    'ANDTHEN',
    'ARRAY',
    'BEGIN',
    'CASE',
    'CONST',
    'DIV',
    'DO',
    'DOWNTO',
    'ELSE',
    'END',
    'FILE',
    'FOR',
    'FUNCTION',
    'GOTO',
    'IF',
    'IN',
    'LABEL',
    'MOD',
    'NIL',
    'OF',
    'OR',
    'ORELSE',
    'PACKED',
    'PROCEDURE',
    'PROGRAM',
    'RECORD',
    'REPEAT',
    'SET',
    'THEN',
    'TO',
    'TYPE',
    'UNTIL',
    'VAR',
    'WHILE',
    'WITH',
    'INTEGER',
    'REAL',
    'BOOLEAN',
    'CHAR',
    'BYTE',
    'WORD',
    'LONGINT',
    'SHORTINT',
    'SINGLE',
    'DOUBLE',
    'EXTENDED',
    'COMP',
    'CURRENCY',
    'ID',
    'NUMBER',
    'STRING',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'ASSIGN',
    'PIPE',
    'AMPERSAND',
    'TILDE',
    'NOT',
    'NE',
    'GE',
    'GT',
    'LE',
    'LT',
    'EQ',
    'LBRACKET',
    'RBRACKET',
    'COMMA',
    'SEMICOLON',
    'COLON',
    'DOT',
    'EQUALS',
    'EXCLAMATION'
]

precedence = (
    ('right', 'TILDE', 'NOT'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD', 'AND', 'AMPERSAND'),
    ('left', 'PLUS', 'MINUS', 'OR', 'PIPE', 'EXCLAMATION'),
    ('left', 'EQUALS', 'NOTEQUAL', 'LT', 'LE', 'GT', 'GE', 'IN'),
    ('left', 'ORELSE', 'ANDTHEN'),
)

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ASSIGN = r':='
t_PIPE = r'\|'
t_AMPERSAND = r'&'
t_TILDE = r'~'
t_NE = r'<>'
t_GE = r'>='
t_GT = r'>'
t_LE = r'<='
t_LT = r'<'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_DOT = r'\.'
t_EQUALS = r'='
t_EXCLAMATION = r'!'

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = t.type.upper()
    if t.value in tokens:
        t.type = t.value
    return t

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

def t_STRING(t):
    r'\'([^\\\n]|(\\.))*?\''
    # we do like this on value because we ignore the quotes
    t.value = t.value[1:-1]
    return t

# for comments like this "{ ... }"
def t_COMMENT_BRACE(t):
    r'\{[^}]*\}'
    t.lexer.lineno += t.value.count('\n')
    pass

# for comments like this "(* ... *)"
def t_COMMENT_PAREN(t):
    r'\(\*([^*]|\*+[^)])*\*+\)'
    t.lexer.lineno += t.value.count('\n')
    pass

# list of reserved words defined in the tokens list
# and the corresponding regex patterns
def t_AND(t):
    r'(?i)AND'
    return t

def t_ANDTHEN(t):
    r'(?i)ANDTHEN'
    return t

def t_ARRAY(t):
    r'(?i)ARRAY'
    return t

def t_BEGIN(t):
    r'(?i)BEGIN'
    return t

def t_CASE(t):
    r'(?i)CASE'
    return t

def t_CONST(t):
    r'(?i)CONST'
    return t

def t_DIV(t):
    r'(?i)DIV'
    return t

def t_DO(t):
    r'(?i)DO'
    return t

def t_DOWNTO(t):
    r'(?i)DOWNTO'
    return t

def t_ELSE(t):
    r'(?i)ELSE'
    return t

def t_END(t):
    r'(?i)END'
    return t

def t_FILE(t):
    r'(?i)FILE'
    return t

def t_FOR(t):
    r'(?i)FOR'
    return t

def t_FUNCTION(t):
    r'(?i)FUNCTION'
    return t

def t_GOTO(t):
    r'(?i)GOTO'
    return t

def t_IF(t):
    r'(?i)IF'
    return t

def t_IN(t):
    r'(?i)IN'
    return t

def t_LABEL(t):
    r'(?i)LABEL'
    return t

def t_MOD(t):
    r'(?i)MOD'
    return t

def t_NIL(t):
    r'(?i)NIL'
    return t

def t_NOT(t):
    r'(?i)NOT'
    return t

def t_OF(t):
    r'(?i)OF'
    return t

def t_OR(t):
    r'(?i)OR'
    return t

def t_ORELSE(t):
    r'(?i)ORELSE'
    return t

def t_PACKED(t):
    r'(?i)PACKED'
    return t

def t_PROCEDURE(t):
    r'(?i)PROCEDURE'
    return t

def t_PROGRAM(t):
    r'(?i)PROGRAM'
    return t

def t_RECORD(t):
    r'(?i)RECORD'
    return t

def t_REPEAT(t):
    r'(?i)REPEAT'
    return t

def t_SET(t):
    r'(?i)SET'
    return t

def t_THEN(t):
    r'(?i)THEN'
    return t

def t_TO(t):
    r'(?i)TO'
    return t

def t_TYPE(t):
    r'(?i)TYPE'
    return t

def t_UNTIL(t):
    r'(?i)UNTIL'
    return t

def t_VAR(t):
    r'(?i)VAR'
    return t

def t_WHILE(t):
    r'(?i)WHILE'
    return t

def t_WITH(t):
    r'(?i)WITH'
    return t

def t_INTEGER(t):
    r'(?i)INTEGER'
    return t

def t_REAL(t):
    r'(?i)REAL'
    return t

def t_BOOLEAN(t):
    r'(?i)BOOLEAN'
    return t

def t_CHAR(t):
    r'(?i)CHAR'
    return t

def t_BYTE(t):
    r'(?i)BYTE'
    return t

def t_WORD(t):
    r'(?i)WORD'
    return t

def t_LONGINT(t):
    r'(?i)LONGINT'
    return t

def t_SHORTINT(t):
    r'(?i)SHORTINT'
    return t

def t_SINGLE(t):
    r'(?i)SINGLE'
    return t

def t_DOUBLE(t):
    r'(?i)DOUBLE'
    return t

def t_EXTENDED(t):
    r'(?i)EXTENDED'
    return t

def t_COMP(t):
    r'(?i)COMP'
    return t

def t_CURRENCY(t):
    r'(?i)CURRENCY'
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def build_lexer():
    lexer = lex.lex()
    return lexer