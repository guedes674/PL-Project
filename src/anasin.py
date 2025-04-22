import ply.yacc as yacc
from analex import tokens

# rule for the entire program structure
def p_program(p):
    # program : header block DOT
    p[0] = ('program', p[1], p[2])

# rule for the program header
def p_header(p):
    # header : PROGRAM ID LPAREN id_list RPAREN SEMICOLON
    if len(p) == 7:
        p[0] = ('header', p[2], p[4]) # the program has a list of identifiers
    # | PROGRAM ID SEMICOLON
    else:
        p[0] = ('header', p[2], []) # list of identifiers is empty

# rule for a list of identifiers
def p_id_list(p):
    # id_list : ID
    if len(p) == 2:
        p[0] = [p[1]] # single identifier
    # | id_list COMMA ID
    else:
        p[0] = p[1] + [p[3]] # multiple identifiers

# rule for a block (can be the program block, the function block, the procedure block, etc...)
def p_block(p):
    # block : declarations compound_statement
    p[0] = ('block', p[1], p[2])

# rule for declarations
def p_declarations(p):
    # declarations : declarations declaration
    if len(p) == 3:
        p[0] = p[1] + [p[2]] # multiple declarations
    # | declaration
    else:
        p[0] = [p[1]] # single declaration

# rule for each declaration
def p_declaration(p):
    ''' declaration : variable_declaration
                    | function_declaration
                    | procedure_declaration
                    | constant_type_declaration '''
    # to be updated because maybe there are more than this
    p[0] = p[1]

# types of declarations
# rule for variable declaration
def p_variable_declaration(p):
    ''' variable_declaration : VAR variable_list SEMICOLON '''
    p[0] = ('variable_declaration', p[2])

# rule for a constant/type declaration
def p_constant_type_declaration(p):
    # constant_type_declaration : CONST constant_list
    if p[1] == 'CONST':
        p[0] = ('constant_declaration', p[2]) # for a constant declaration
    else:
        p[0] = ('type_declaration', p[2]) # for a type declaration

# rule for function/procedure declaration
def p_function_procedure_declaration(p):
    # function_declaration : FUNCTION ID parameter_list COLON type SEMICOLON block
    if len(p) == 8:
        p[0] = ('function_declaration', p[2], p[3], p[5], p[7]) # for function declaration because have return
    else:
        p[0] = ('procedure_declaration', p[2], p[3], p[5]) # for procedure declaration because doesn't have return

# rule for a list of variables
def p_variable_list(p):
    # variable_list : variable_list SEMICOLON variable
    if len(p) == 4:
        p[0] = p[1] + [p[3]] # multiple variables
    # | variable
    else:
        p[0] = [p[1]] # single variable

# rule for each variable
def p_variable(p):
    ''' variable : id_list COLON type'''
    p[0] = ('variable', p[1], p[3])

# rule for type (an identifier like: "integer", "float", "string")
# review this one because not clear if we need it or not
def p_type(p):
    ''' type : ID '''
    p[0] = p[1]

# rule for a parameter_list
def p_parameter_list(p):
    # parameter_list : LPAREN parameter_section_list RPAREN
    if len(p) == 4:
        p[0] = p[1] # can exist the parameter list
    # | EPSYLON
    else:
        p[0] = [] # no parameter list

# rule for a list of parameter sections
def p_parameter_section_list(p):
    # parameter_section_list : parameter_section_list SEMICOLON parameter_section
    if len(p) == 4:
        p[0] = p[1] + [p[3]] # more than one parameter
    # | parameter_section
    else:
        p[0] = [p[1]] # only one parameter

# rule for each parameter
def p_parameter_section(p):
    ''' parameter_section : id_list COLON type '''
    p[0] = ('parameter_section', p[1], p[3])

# rule for a constant list
def p_constant_list(p):
    # constant_list : constant_list constant
    if len(p) == 2:
        p[0] = p[1] + [p[2]] # more than one constant
    # | constant
    else:
        p[0] = [p[1]] # only one constant

# rule for each constant
def p_constant(p):
    ''' constant : ID EQUALS constant_value SEMICOLON '''
    p[0] = ('constant', p[1], p[3])

# rule for a constant value
def p_constant_value(p):
    ''' constant_value : NUMBER 
                       | STRING
                       | ID '''
    p[0] = p[1]

# rule for a type list
def p_type_list(p):
    # type_list : type_list type_definition
    if len(p) == 2:
        p[0] = p[1] + [p[2]] # more than one type definition
    # | type_definition
    else:
        p[0] = [p[1]] # only one type definition

# rule for a type definition
def p_type_definition(p):
    ''' type_definition : ID EQUALS type SEMICOLON'''
    p[0] = ('type_definition', p[1], p[3])

# compound statements
# derived on block
# rule for a compound_statement (main program)
def p_compound_statement(p):
    ''' compound_statement : BEGIN statement_list END '''
    p[0] = ('compound_statement', p[2])

# rule for statement list
def p_statement_list(p):
    # statement_list : statement_list SEMICOLON statement
    if len(p) == 4:
        p[0] = p[1] + [p[3]] # more than one statement
    # | statement
    else:
        p[0] = [p[1]] # only one statement

# rule for each statement
def p_statement(p):
    ''' statement : assignment_statement
                  | function_procedure_call
                  | if_statement
                  | while_statement
                  | repeat_statement
                  | for_statement
                  | case_statement
                  | compound_statement
                  | EPSYLON '''
    p[0] = p[1]

# rule for assignment statement
def p_assignment_statement(p):
    ''' assignment_statement : ID ASSIGN expression '''
    p[0] = ('assignment_statement', p[1], p[3])

# rule for a function/procedure call
def p_function_procedure_call(p):
    ''' function_procedure_call : ID LPAREN expression_list RPAREN '''
    p[0] = ('function_procedure_call', p[1], p[3])

# rule for expression list
def p_expression_list(p):
    # expression_list : expression_list COMMA expression
    if len(p) == 4:
        p[0] = p[1] + [p[3]] # more than one expression
    # | expression
    else:
        p[0] = [p[1]] # only one expression

# rule for each expression
def p_expression(p):
    # expression : ID                             # variable
    #            | NUMBER                         # number
    #            | STRING                         # string
    if len(p) == 2:
        p[0] = p[1]
    #            | LPAREN expression RPAREN       # expression between parentheses
    elif len(p) == 4:
        p[0] = p[2]
    #            | expression PLUS expression     # addition
    #            | expression MINUS expression    # subtraction
    #            | expression TIMES expression    # multiplication
    #            | expression DIVIDE expression   # division
    #            | expression GT expression       # greater than (>)
    #            | expression LT expression       # less than (<)
    #            | expression GE expression       # greater or equals (>=)
    #            | expression LE expression       # less or equals (<=)
    #            | expression EQ expression       # equivalent (=)
    #            | expression NE expression       # not equals (<>)
    #            | function_procedure_call        # function call
    else:
        p[0] = (p[2], p[1], p[3])