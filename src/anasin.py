import ply.yacc as yacc
from analex import tokens, precedence
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
        # header : PROGRAM ID LPAREN id_list RPAREN SEMICOLON
        p[0] = ProgramHeader(name=p[2], id_list=p[4])
    else:
        # | PROGRAM ID SEMICOLON
        p[0] = ProgramHeader(name=p[2], id_list=[])

# rule for id_list
def p_id_list(p):
    '''id_list : id_list COMMA ID
               | ID'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# rule for empty production
def p_empty(p):
    '''empty :'''
    pass

# rule for a block
def p_block(p):
    '''block : declarations compound_statement'''
    p[0] = Block(declarations=p[1], compound_statement=p[2])

# rule for declarations
def p_declarations(p):
    '''declarations : declarations variable_declaration
                    | declarations function_declaration
                    | declarations procedure_declaration
                    | empty'''
    if len(p) == 3:
       # declarations : declarations variable_declaration
       #              | declarations function_declaration
       #              | declarations procedure_declaration
        p[0] = p[1] + [p[2]]
    else:
        # | empty
        p[0] = []

# rule for variable declaration
def p_variable_declaration(p):
    '''variable_declaration : VAR variable_list SEMICOLON'''
    variables = p[2] # p[2] is the list of Variable AST nodes
    p[0] = VariableDeclaration(variable_list=variables)

# rule for function/procedure declaration
def p_function_declaration(p):
    '''function_declaration : FUNCTION ID parameter_list COLON type SEMICOLON block SEMICOLON'''
    params_ast = []
    if p[3]: # p[3] is the list of ('param', 'value'/'ref', id_list, type_node)
        for param_data in p[3]:
            params_ast.append(Parameter(id_list=param_data[2], param_type=param_data[3], is_var=(param_data[1] == 'ref')))
    p[0] = FunctionDeclaration(name=p[2], parameter_list=params_ast, return_type=p[5], block=p[7])

def p_procedure_declaration(p):
    '''procedure_declaration : PROCEDURE ID parameter_list SEMICOLON block SEMICOLON''' # Added SEMICOLON at the end
    params_ast = []
    if p[3]: # p[3] is the list of ('param', 'value'/'ref', id_list, type_node)
        for param_data in p[3]:
            params_ast.append(Parameter(id_list=param_data[2], param_type=param_data[3], is_var=(param_data[1] == 'ref')))
    p[0] = ProcedureDeclaration(name=p[2], parameter_list=params_ast, block=p[5]) # equal to FunctionDeclaration but without return_type

# rule for a list of variables
def p_variable_list(p):
    '''variable_list : variable_list SEMICOLON variable
                     | variable'''
    if len(p) == 4:
        # variable_list : variable_list SEMICOLON variable
        p[0] = p[1] + [p[3]]
    else:
        # | variable
        p[0] = [p[1]]

# rule for each variable
def p_variable(p):
    '''variable : id_list COLON type'''
    p[0] = Variable(id_list=p[1], var_type=p[3])

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
    if len(p) == 2: # for simple types like INTEGER, REAL, BOOLEAN, etc.
        p[0] = p[1]
    elif len(p) == 10: # for ARRAY type, for example: ARRAY [3..5] OF INTEGER
        lower_bound_literal = Literal(p[3]) # assuming p[3] is a number literal for lower bound
        upper_bound_literal = Literal(p[6]) # assuming p[6] is a number literal for upper bound

        element_type_val = p[9]
        p[0] = ArrayType(index_range=(lower_bound_literal, upper_bound_literal), element_type=element_type_val)
    elif len(p) == 4: # for RECORD type, for example: RECORD field_list END
        p[0] = ('record_type', p[2])

# rule for a field_list
def p_field_list(p):
    '''field_list : field_list SEMICOLON field
                  | field'''
    if len(p) == 4:
        # field_list : field_list SEMICOLON field
        p[0] = p[1] + [p[3]]
    else:
        # | field
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
        # parameter_list : LPAREN parameter_section_list RPAREN
        p[0] = p[2]
    else:
        # | empty
        p[0] = []

# rule for a list of parameter sections
def p_parameter_section_list(p):
    '''parameter_section_list : parameter_section_list SEMICOLON parameter_section
                              | parameter_section'''
    if len(p) == 4:
        # parameter_section_list : parameter_section_list SEMICOLON parameter_section
        p[0] = p[1] + [p[3]]
    else:
        # | parameter_section
        p[0] = [p[1]]

# rule for each parameter
def p_parameter_section(p):
    '''parameter_section : id_list COLON type
                         | VAR id_list COLON type'''
    if len(p) == 4:
        # parameter_section : id_list COLON type
        p[0] = ('param', 'value', p[1], p[3])
    else:
        # | VAR id_list COLON type
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
        # statement_list : statement_list SEMICOLON statement
        p[0] = p[1] + [p[3]]
    else:
        # | statement
        p[0] = [p[1]]

# rule for each statement
def p_statement(p):
    '''statement : assignment_statement
                 | expression
                 | compound_statement
                 | io_statement
                 | if_statement        
                 | while_statement     
                 | repeat_statement    
                 | for_statement       
                 | empty'''
    p[0] = p[1]

# rule for assignment statement
def p_assignment_statement(p):
    '''assignment_statement : ID ASSIGN expression'''
    variable_node = Identifier(name=p[1], lineno=p.lineno(1))
    p[0] = AssignmentStatement(variable=variable_node, expression=p[3], lineno=p.lineno(2)) # Pass lineno

# rule for expressions
def p_expression(p):
    '''expression : additive_expression
                  | expression EQUALS additive_expression
                  | expression NE additive_expression
                  | expression LT additive_expression
                  | expression GT additive_expression
                  | expression LE additive_expression
                  | expression GE additive_expression
                  | expression IN additive_expression'''
    if len(p) == 2:
        # expression : additive_expression
         p[0] = p[1]
    else:
        # expression : expression operator additive_expression, where operator can be EQUALS, NE, LT, GT, LE, GE, IN
        p[0] = BinaryOperation(left=p[1], operator=p[2], right=p[3])

# rule for additive expressions
def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression PLUS multiplicative_expression
                           | additive_expression MINUS multiplicative_expression
                           | additive_expression OR multiplicative_expression
                           | additive_expression ORELSE multiplicative_expression'''
    if len(p) == 2:
        # additive_expression : multiplicative_expression
         p[0] = p[1]
    else:
        # additive_expression : additive_expression operator multiplicative_expression, where operator can be PLUS, MINUS, OR, ORELSE
        p[0] = BinaryOperation(left=p[1], operator=p[2], right=p[3])

# rule for multiplicative expressions
def p_multiplicative_expression(p):
    '''multiplicative_expression : factor 
                                 | multiplicative_expression TIMES factor
                                 | multiplicative_expression DIVIDE factor
                                 | multiplicative_expression DIV factor
                                 | multiplicative_expression MOD factor
                                 | multiplicative_expression AND factor
                                 | multiplicative_expression ANDTHEN factor'''
    if len(p) == 2:
        # multiplicative_expression : factor
        p[0] = p[1]
    else:
        # multiplicative_expression : multiplicative_expression operator factor, where operator can be TIMES, DIVIDE, DIV, MOD, AND, ANDTHEN
        p[0] = BinaryOperation(left=p[1], operator=p[2], right=p[3])

# rule for a factor
def p_factor(p):
    '''factor : NUMBER
              | STRING
              | ID
              | TRUE
              | FALSE
              | LPAREN expression RPAREN
              | factor LBRACKET expression RBRACKET  
              | ID LPAREN expression_list RPAREN  
              | MINUS factor %prec UMINUS          
              | NOT factor                         
              '''
    if len(p) == 2:
        # factor : NUMBER | STRING | ID
        if len(p) == 2:
            if p.slice[1].type == 'NUMBER': # for NUMBER token
                p[0] = Literal(p[1])
            elif p.slice[1].type == 'STRING': # for STRING token
                p[0] = Literal(p[1])
            elif p.slice[1].type == 'TRUE': # for TRUE token
                p[0] = Literal(True)
            elif p.slice[1].type == 'FALSE': # for FALSE token
                p[0] = Literal(False)
            elif p.slice[1].type == 'ID': # for ID token
                p[0] = Identifier(name=p[1], lineno=p.lineno(1))
    elif p.slice[1].type == 'LPAREN':
        # | LPAREN expression RPAREN
        p[0] = p[2]
    elif p.slice[2].type == 'LBRACKET':
        # | factor LBRACKET expression RBRACKET
        p[0] = ArrayAccess(array=p[1], index=p[3])
    elif len(p) == 5 and p.slice[1].type == 'ID' and p.slice[2].type == 'LPAREN':
        # | ID LPAREN expression_list RPAREN
         p[0] = FunctionCall(name=p[1], arguments=p[3], lineno=p.lineno(1))
    elif len(p) == 3:
        # | MINUS factor %prec UMINUS
        p[0] = UnaryOperation(operator=p[1], operand=p[2])

# rule for expression list
def p_expression_list(p):
    '''expression_list : expression_list COMMA expression
                       | expression
                       | empty'''
    if len(p) == 4: # expression_list COMMA expression
        p[0] = p[1] + [p[3]]
    elif p[1] is None: # | empty
        p[0] = []
    else: # | expression
        p[0] = [p[1]]

# rule for IO statements
def p_io_statement(p):
    '''io_statement : WRITE LPAREN expression_list RPAREN
                    | WRITELN LPAREN expression_list RPAREN
                    | READ LPAREN expression_list RPAREN
                    | READLN LPAREN expression_list RPAREN'''
    p[0] = IOCall(operation=p[1].lower(), arguments=p[3])

# rule for IF statement
def p_if_statement(p):
    '''if_statement : IF expression THEN statement ELSE statement
                    | IF expression THEN statement'''
    if len(p) == 7:
        # if_statement : IF expression THEN statement ELSE statement
        p[0] = IfStatement(condition=p[2], then_statement=p[4], else_statement=p[6])
    else:
        # | IF expression THEN statement
        p[0] = IfStatement(condition=p[2], then_statement=p[4], else_statement=None)

# rule for WHILE statement
def p_while_statement(p):
    '''while_statement : WHILE expression DO statement'''
    p[0] = WhileStatement(condition=p[2], statement=p[4])

# rule for REPEAT statement
def p_repeat_statement(p):
    '''repeat_statement : REPEAT statement_list UNTIL expression'''
    # p[2] is statement_list, p[4] is expression
    p[0] = RepeatStatement(statement_list=p[2], condition=p[4])

# rule for FOR statement
def p_for_statement(p):
    '''for_statement : FOR ID ASSIGN expression TO expression DO statement
                     | FOR ID ASSIGN expression DOWNTO expression DO statement'''
    control_var_name = p[2]
    start_expr = p[4]
    end_expr = p[6]
    loop_statement = p[8]
    is_downto = (p[5].lower() == 'downto') # | FOR ID ASSIGN expression DOWNTO expression DO statement if 'DOWNTO' is used

    p[0] = ForStatement(control_variable=Identifier(name=control_var_name),
                        start_expression=start_expr,
                        end_expression=end_expr,
                        statement=loop_statement,
                        downto=is_downto)

def p_error(p):
    if p:
        print(f"Syntax error at token {p.type} ('{p.value}') at line {p.lineno}")
    else:
        print("Syntax error at EOF")

def build_parser():
    return yacc.yacc()

def parse_program(input_text):
    from analex import build_lexer

    lexer = build_lexer()
    parser = build_parser()

    try:
        ast = parser.parse(input_text, lexer=lexer)
        return ast
    except Exception as e:
        print(f"Parse error: {e}")
        return None