import ply.yacc as yacc
from analex import tokens

def p_program(p):
    # program : header block DOT
    p[0] = ('program', p[1], p[2])

def p_header(p):
    # header : PROGRAM ID LPAREN id_list RPAREN SEMICOLON
    if len(p) == 7:
        p[0] = ('header', p[2], p[4])
    # | PROGRAM ID SEMICOLON
    else:
        p[0] = ('header', p[2], []) # list of identifiers is empty

def p_id_list(p):
    # id_list : ID
    if len(p) == 2:
        p[0] = [p[1]]
    # | id_list COMMA ID
    else:
        p[0] = p[1] + [p[3]]

def p_block(p):
    # block : declarations statement
    p[0] = ('block', p[1], p[2])

def p_declarations(p):
    # declarations : declarations declaration
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    # | declaration
    else:
        p[0] = []

def p_declaration(p):
    ''' declaration : variable_declaration
                    | function_declaration
                    | procedure_declaration'''
    # to be updated because maybe there are more than this
    p[0] = p[1]