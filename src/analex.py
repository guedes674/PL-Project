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
    'UMINUS',
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
    'EXCLAMATION',
    'READ',
    'READLN', 
    'WRITE',
    'WRITELN',
    'TRUE',
    'FALSE',
]

precedence = (
    ('left', 'OR', 'ORELSE'),
    ('left', 'AND', 'ANDTHEN'),
    ('nonassoc', 'EQUALS', 'NE', 'LT', 'GT', 'LE', 'GE', 'IN'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD'), 
    ('right', 'UMINUS', 'NOT'), 
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

# list of reserved words defined in the tokens list
# and the corresponding regex patterns
def t_AND(t):
    r'AND'
    return t

def t_ANDTHEN(t):
    r'ANDTHEN'
    return t

def t_ARRAY(t):
    r'ARRAY'
    return t

def t_BEGIN(t):
    r'BEGIN'
    return t

def t_CASE(t):
    r'CASE'
    return t

def t_CONST(t):
    r'CONST'
    return t

def t_DIV(t):
    r'DIV'
    return t

def t_DO(t):
    r'DO'
    return t

def t_DOWNTO(t):
    r'DOWNTO'
    return t

def t_ELSE(t):
    r'ELSE'
    return t

def t_END(t):
    r'END'
    return t

def t_FILE(t):
    r'FILE'
    return t

def t_FOR(t):
    r'FOR'
    return t

def t_FUNCTION(t):
    r'FUNCTION'
    return t

def t_GOTO(t):
    r'GOTO'
    return t

def t_IF(t):
    r'IF'
    return t

def t_IN(t):
    r'IN'
    return t

def t_LABEL(t):
    r'LABEL'
    return t

def t_MOD(t):
    r'MOD'
    return t

def t_NIL(t):
    r'NIL'
    return t

def t_NOT(t):
    r'NOT'
    return t

def t_OF(t):
    r'OF'
    return t

def t_OR(t):
    r'OR'
    return t

def t_ORELSE(t):
    r'ORELSE'
    return t

def t_PACKED(t):
    r'PACKED'
    return t

def t_PROCEDURE(t):
    r'PROCEDURE'
    return t

def t_PROGRAM(t):
    r'PROGRAM'
    return t

def t_RECORD(t):
    r'RECORD'
    return t

def t_REPEAT(t):
    r'REPEAT'
    return t

def t_SET(t):
    r'SET'
    return t

def t_THEN(t):
    r'THEN'
    return t

def t_TO(t):
    r'TO'
    return t

def t_TYPE(t):
    r'TYPE'
    return t

def t_UNTIL(t):
    r'UNTIL'
    return t

def t_VAR(t):
    r'VAR'
    return t

def t_WHILE(t):
    r'WHILE'
    return t

def t_WITH(t):
    r'WITH'
    return t

def t_INTEGER(t):
    r'INTEGER'
    return t

def t_REAL(t):
    r'REAL'
    return t

def t_BOOLEAN(t):
    r'BOOLEAN'
    return t

def t_CHAR(t):
    r'CHAR'
    return t

def t_BYTE(t):
    r'BYTE'
    return t

def t_WORD(t):
    r'WORD'
    return t

def t_LONGINT(t):
    r'LONGINT'
    return t

def t_SHORTINT(t):
    r'SHORTINT'
    return t

def t_SINGLE(t):
    r'SINGLE'
    return t

def t_DOUBLE(t):
    r'DOUBLE'
    return t

def t_EXTENDED(t):
    r'EXTENDED'
    return t

def t_COMP(t):
    r'COMP'
    return t

def t_CURRENCY(t):
    r'CURRENCY'
    return t

def t_READ(t):
    r'READ'
    return t

def t_READLN(t):
    r'READLN'
    return t

def t_WRITE(t):
    r'WRITE'
    return t

def t_WRITELN(t):
    r'WRITELN'
    return t

def t_TRUE(t):
    r'TRUE'
    t.value = True
    return t

def t_FALSE(t):
    r'FALSE'
    t.value = False
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

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    val = t.value.upper()
    if val in tokens:
        t.type = val
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