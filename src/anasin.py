import ply.yacc as yacc
from analex import tokens
from ast_nodes import *

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

# rule for a block
def p_block(p):
    '''block : declarations compound_statement'''
    p[0] = Block(declarations=p[1], compound_statement=p[2])

# rule for variable declaration
def p_variable_declaration(p):
    '''variable_declaration : VAR variable_list'''
    variables = [Variable(id_list=var[1], var_type=var[2]) for var in p[2]]
    p[0] = VariableDeclaration(variable_list=variables)

# rule for function/procedure declaration
def p_function_procedure_declaration(p):
    '''function_declaration : FUNCTION ID parameter_list COLON type SEMICOLON block
       procedure_declaration : PROCEDURE ID parameter_list SEMICOLON block'''
    if len(p) == 8:  # Function
        params = [Parameter(id_list=param[2], param_type=param[3], is_var=(param[1] == 'ref')) 
                 for param in p[3]]
        p[0] = FunctionDeclaration(name=p[2], parameter_list=params, 
                                 return_type=p[5], block=p[7])
    else:  # Procedure
        params = [Parameter(id_list=param[2], param_type=param[3], is_var=(param[1] == 'ref')) 
                 for param in p[3]]
        p[0] = ProcedureDeclaration(name=p[2], parameter_list=params, block=p[5])

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

# rule for array type
def p_type_array(p):
    ''' type : ARRAY LBRACKET NUMBER DOT DOT NUMBER RBRACKET OF type '''
    p[0] = ('array_type', (p[3], p[5]), p[8])

# rule for record type
def p_type_record(p):
    ''' type : RECORD field_list END '''
    p[0] = ('record_type', p[2])

# rule for a field_list to use on a record
def p_field_list(p):
    # field_list : field_list SEMICOLON field
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    # | field
    else:
        p[0] = [p[1]]

# rule for a single field
def p_field(p):
    ''' field : id_list COLON type '''
    p[0] = ('field', p[1], p[3])

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
    # parameter_section : id_list COLON type
    if len(p) == 4:
        p[0] = ('param', 'value', p[1], p[3])
    # | VAR id_list COLON type
    else:
        p[0] = ('param', 'ref', p[2], p[4])

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

# rule for a io call (for example WriteLn or Write)
def p_statement_io_call(p):
    ''' statement : READ LPAREN id_list RPAREN
                  | READLN LPAREN id_list RPAREN
                  | WRITE LPAREN expression_list RPAREN
                  | WRITELN LPAREN expression_list RPAREN '''
    p[0] = ('io_call', p[1].lower(), p[3])

# rule for assignment statement
def p_assignment_statement(p):
    ''' assignment_statement : ID ASSIGN expression '''
    p[0] = ('assignment_statement', p[1], p[3])

# rule for a function/procedure call
def p_function_procedure_call(p):
    ''' function_procedure_call : ID LPAREN expression_list RPAREN '''
    p[0] = ('function_procedure_call', p[1], p[3])

# rule for a case statement
def p_case_statement(p):
    ''' case_statement : CASE expression OF case_list END '''
    p[0] = ('case', p[2], p[4])

# rule for a list of cases inside a case statement
def p_case_list(p):
    # case_list : case_list case_element
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    # | case_element
    else:
        p[0] = [p[1]]

# rule for a simple case inside a list of cases
def p_case_element(p):
    ''' case_element : constant_list COLON statement SEMICOLON '''
    p[0] = ('case_element', p[1], p[3])

# rule for expression list
def p_expression_list(p):
    # expression_list : expression_list COMMA expression
    if len(p) == 4:
        p[0] = p[1] + [p[3]] # more than one expression
    # | expression
    else:
        p[0] = [p[1]] # only one expression

# rule for each expression
# rule for a literal (number, string, etc..)
def p_expression_literal(p):
    ''' expression : NUMBER
                   | STRING '''
    # needs to be updated for more types
    p[0] = ('literal', p[1])

# rule for a variable
def p_expression_variable(p):
    ''' expression : ID '''
    p[0] = ('variable', p[1])

# rule for grouped expressions
def p_expression_group(p):
    ''' expression : LPAREN expression RPAREN '''
    p[0] = p[2]

# rule for unary operations
def p_expression_unop(p):
    ''' expression : NOT expression 
                   | TILDE expression '''
    p[0] = ('unop', p[1], p[2])

# rule for binary operations
def p_expression_binop(p):
    ''' expression : expression PLUS expression              # addition
                   | expression MINUS expression             # subtraction
                   | expression TIMES expression             # multiplication
                   | expression DIVIDE expression            # division (real)
                   | expression DIV expression               # integer division
                   | expression MOD expression               # modulo
                   | expression AND expression               # logical and
                   | expression AMPERSAND expression         # bitwise and
                   | expression OR expression                # logical or
                   | expression PIPE expression              # bitwise or
                   | expression EXCLAMATION expression       # bitwise not or logical negation (depending on context)
                   | expression EQUALS expression            # equals (=)
                   | expression NOTEQUAL expression          # not equals (<>)
                   | expression LT expression                # less than (<)
                   | expression LE expression                # less than or equal (<=)
                   | expression GT expression                # greater than (>)
                   | expression GE expression                # greater than or equal (>=)
                   | expression IN expression                # membership (in)
                   | expression ORELSE expression            # short-circuit logical or
                   | expression ANDTHEN expression           # short-circuit logical and '''
    p[0] = ('binop', p[2], p[1], p[3])

# rule for access a index of array (like a[2] for example)
def p_expression_indexing(p):
    ''' expression : expression LBRACKET expression RBRACKET '''
    p[0] = ('indexing', p[1], p[3])

# rule for access a field (for example a.name)
def p_expression_field_access(p):
    ''' expression : expression DOT ID '''
    p[0] = ('field_access', p[1], p[3])

# rule for a function/procedure call inside a expression (essentially for the case of having system calls inside expressions)
def p_expression_function_procedure_call(p):
    '''expression : ID LPAREN expression_list RPAREN'''
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