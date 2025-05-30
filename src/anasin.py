import ply.yacc as yacc
from analex import tokens
from ast_nodes import *

# Add missing tokens to the lexer - you need to add these to analex.py
# 'READ', 'READLN', 'WRITE', 'WRITELN', 'NOTEQUAL'

# rule for the entire program structure
def p_program(p):
    '''program : header block DOT'''
    p[0] = Program(header=p[1], block=p[2])

# rule for the program header
def p_header(p):
    '''header : PROGRAM ID LPAREN id_list RPAREN SEMICOLON
              | PROGRAM ID SEMICOLON'''
    if len(p) == 7:
        p[0] = ProgramHeader(name=p[2], id_list=p[4])
    else:
        p[0] = ProgramHeader(name=p[2], id_list=[])

# rule for id_list (MISSING RULE)
def p_id_list(p):
    '''id_list : id_list COMMA ID
               | ID'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# rule for declarations (MISSING RULE)
def p_declarations(p):
    '''declarations : declarations variable_declaration
                   | declarations function_declaration
                   | declarations procedure_declaration
                   | empty'''
    if len(p) == 3:  # A declaration item is added to the list of declarations
        # p[1] is the existing list (could be [] from 'empty' on first real item)
        # p[2] is the new declaration item (e.g., VariableDeclaration object)
        p[0] = p[1] + [p[2]]
    else:  # empty
        p[0] = []

# rule for empty production (MISSING RULE)
def p_empty(p):
    '''empty :'''
    pass

# rule for a block
def p_block(p):
    '''block : declarations compound_statement'''
    p[0] = Block(declarations=p[1], compound_statement=p[2])

# rule for variable declaration
def p_variable_declaration(p):
    '''variable_declaration : VAR variable_list SEMICOLON'''  # Added SEMICOLON here
    # p[2] is the result of variable_list
    # p[3] is the SEMICOLON token
    variables = [Variable(id_list=var[1], var_type=var[2]) for var in p[2]]
    p[0] = VariableDeclaration(variable_list=variables)
# rule for function/procedure declaration
def p_function_declaration(p):
    '''function_declaration : FUNCTION ID parameter_list COLON type SEMICOLON block'''
    params = [Parameter(id_list=param[2], param_type=param[3], is_var=(param[1] == 'ref')) 
             for param in p[3]]
    p[0] = FunctionDeclaration(name=p[2], parameter_list=params, 
                             return_type=p[5], block=p[7])

def p_procedure_declaration(p):
    '''procedure_declaration : PROCEDURE ID parameter_list SEMICOLON block'''
    params = [Parameter(id_list=param[2], param_type=param[3], is_var=(param[1] == 'ref')) 
             for param in p[3]]
    p[0] = ProcedureDeclaration(name=p[2], parameter_list=params, block=p[5])

# rule for a list of variables
def p_variable_list(p):
    '''variable_list : variable_list SEMICOLON variable
                     | variable'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# rule for each variable
def p_variable(p):
    '''variable : id_list COLON type'''
    p[0] = ('variable', p[1], p[3])

# rule for type
# rule for type
def p_type(p):
    '''type : ID
            | INTEGER
            | REAL
            | BOOLEAN
            | CHAR
            | BYTE
            | WORD
            | LONGINT
            | SHORTINT
            | SINGLE
            | DOUBLE
            | EXTENDED
            | COMP
            | CURRENCY
            | STRING
            | ARRAY LBRACKET NUMBER DOT DOT NUMBER RBRACKET OF type
            | RECORD field_list END'''
    if len(p) == 2:  # Handles ID and all the single-token built-in types like INTEGER, REAL, etc.
        p[0] = p[1]  # p[1] is the token value (e.g., "Integer" or "MyCustomType")
    elif len(p) == 10:  # array type: ARRAY LBRACKET NUMBER DOT DOT NUMBER RBRACKET OF type
        # p[1] is 'ARRAY', p[3] is start NUMBER, p[6] is end NUMBER, p[9] is the element type
        p[0] = ('array_type', (p[3], p[6]), p[9]) # Or use your ArrayType AST node
    elif len(p) == 4:  # record type: RECORD field_list END
        # p[1] is 'RECORD', p[2] is the parsed field_list
        p[0] = ('record_type', p[2]) # Or use your RecordType AST node
    # Ensure your AST node creation logic here is consistent with what p_variable and VariableDeclaration expect.
    # The current tuple-based assignment should work with your existing p_variable.

# rule for a field_list
def p_field_list(p):
    '''field_list : field_list SEMICOLON field
                  | field'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# rule for a single field
def p_field(p):
    '''field : id_list COLON type'''
    p[0] = ('field', p[1], p[3])

# rule for a parameter_list
def p_parameter_list(p):
    '''parameter_list : LPAREN parameter_section_list RPAREN
                      | empty'''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = []

# rule for a list of parameter sections
def p_parameter_section_list(p):
    '''parameter_section_list : parameter_section_list SEMICOLON parameter_section
                              | parameter_section'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# rule for each parameter
def p_parameter_section(p):
    '''parameter_section : id_list COLON type
                         | VAR id_list COLON type'''
    if len(p) == 4:
        p[0] = ('param', 'value', p[1], p[3])
    else:
        p[0] = ('param', 'ref', p[2], p[4])

# rule for a compound_statement
def p_compound_statement(p):
    '''compound_statement : BEGIN statement_list END'''
    p[0] = CompoundStatement(statement_list=p[2])

# rule for statement list
def p_statement_list(p):
    '''statement_list : statement_list SEMICOLON statement
                      | statement'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# rule for each statement
def p_statement(p):
    '''statement : assignment_statement
                 | expression
                 | compound_statement
                 | io_statement
                 | empty'''
    p[0] = p[1]

# rule for IO statements
def p_io_statement(p):
    '''io_statement : WRITE LPAREN expression_list RPAREN
                    | WRITELN LPAREN expression_list RPAREN'''
    p[0] = ('io_call', p[1].lower(), p[3])

# rule for assignment statement
def p_assignment_statement(p):
    '''assignment_statement : ID ASSIGN expression'''
    p[0] = ('assignment_statement', p[1], p[3])

# rule for expression list
def p_expression_list(p):
    '''expression_list : expression_list COMMA expression
                       | expression
                       | empty''' # Allow empty expression list for calls like Func()
    if len(p) == 4: # expression_list COMMA expression
        p[0] = p[1] + [p[3]]
    elif p[1] is None: # empty
        p[0] = []
    else: # expression
        p[0] = [p[1]]

# rule for expressions
def p_expression_literal(p):
    '''expression : NUMBER
                  | STRING'''
    p[0] = ('literal', p[1])

def p_expression_variable(p):
    '''expression : ID'''
    p[0] = ('variable', p[1])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_function_call(p):  # This rule now handles all function calls
    '''expression : ID LPAREN expression_list RPAREN'''
    # p[3] will be an empty list if no arguments, due to updated p_expression_list
    p[0] = ('function_procedure_call', p[1], p[3])

def p_error(p):
    if p:
        print(f"Syntax error at token {p.type} ('{p.value}') at line {p.lineno}")
    else:
        print("Syntax error at EOF")

def build_parser():
    """Build and return the parser."""
    return yacc.yacc()

def parse_program(input_text):
    """Parse input text and return the AST."""
    from analex import build_lexer
    
    lexer = build_lexer()
    parser = build_parser()
    
    try:
        ast = parser.parse(input_text, lexer=lexer)
        return ast
    except Exception as e:
        print(f"Parse error: {e}")
        return None