import ply.lex as lex

reserved = {
    'and': 'AND',
    'array': 'ARRAY',
    'begin': 'BEGIN',
    'case': 'CASE',
    'const': 'CONST',
    'div': 'DIV',
    'do': 'DO',
    'downto': 'DOWNTO',
    'else': 'ELSE',
    'end': 'END',
    'file': 'FILE',
    'for': 'FOR',
    'function': 'FUNCTION',
    'goto': 'GOTO',
    'if': 'IF',
    'in': 'IN',
    'label': 'LABEL',
    'mod': 'MOD',
    'nil': 'NIL',
    'not': 'NOT',
    'of': 'OF',
    'or': 'OR',
    'packed': 'PACKED',
    'procedure': 'PROCEDURE',
    'program': 'PROGRAM',
    'record': 'RECORD',
    'repeat': 'REPEAT',
    'set': 'SET',
    'then': 'THEN',
    'to': 'TO',
    'type': 'TYPE',
    'until': 'UNTIL',
    'var': 'VAR',
    'while': 'WHILE',
    'with': 'WITH',
    'integer': 'INTEGER',
    'real': 'REAL',
    'boolean': 'BOOLEAN',
    'char': 'CHAR',
    'string': 'STRING',
    'byte': 'BYTE',
    'word': 'WORD',
    'longint': 'LONGINT',
    'shortint': 'SHORTINT',
    'single': 'SINGLE',
    'double': 'DOUBLE',
    'extended': 'EXTENDED',
    'comp': 'COMP',
    'currency': 'CURRENCY'
}

tokens = [
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
] + list(reserved.values())

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ASSIGN = r':='
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
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')
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