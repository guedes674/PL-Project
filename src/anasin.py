import ply.yacc as yacc
from analex import tokens
from ast_nodes import *
from ast_nodes import ForStatement # Make sure ForStatement is imported
from ast_nodes import ArrayAccess # Add this if not present

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
    '''function_declaration : FUNCTION ID parameter_list COLON type SEMICOLON block SEMICOLON''' # Added SEMICOLON at the end
    # p[3] is parameter_list, p[5] is type, p[7] is block, p[8] is the new SEMICOLON
    # The AST node still uses p[7] for the block.
    params_ast = []
    if p[3]: # p[3] is the list of ('param', 'value'/'ref', id_list, type_node)
        for param_data in p[3]:
            # Assuming Parameter AST node takes id_list, param_type, is_var
            # param_data[0] is 'param', param_data[1] is 'value' or 'ref'
            # param_data[2] is id_list, param_data[3] is type_node
            params_ast.append(Parameter(id_list=param_data[2], param_type=param_data[3], is_var=(param_data[1] == 'ref')))

    p[0] = FunctionDeclaration(name=p[2], parameter_list=params_ast, 
                             return_type=p[5], block=p[7])

def p_procedure_declaration(p):
    '''procedure_declaration : PROCEDURE ID parameter_list SEMICOLON block SEMICOLON''' # Added SEMICOLON at the end
    # p[3] is parameter_list, p[5] is block, p[6] is the new SEMICOLON
    # The AST node still uses p[5] for the block.
    params_ast = []
    if p[3]: # p[3] is the list of ('param', 'value'/'ref', id_list, type_node)
        for param_data in p[3]:
            params_ast.append(Parameter(id_list=param_data[2], param_type=param_data[3], is_var=(param_data[1] == 'ref')))
    
    p[0] = ProcedureDeclaration(name=p[2], parameter_list=params_ast, block=p[5])

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
    p[0] = Variable(id_list=p[1], var_type=p[3]) # Changed from tuple to AST Node
    # If p_variable_declaration expects a list of tuples like ('variable', id_list, type),
    # then p[0] = ('variable', p[1], p[3]) was fine, but the iteration in p_variable_declaration
    # "variables = [Variable(id_list=var[1], var_type=var[2]) for var in p[2]]"
    # would need var[1] for id_list and var[2] for type from that tuple.
    # Let's assume Variable AST node is preferred directly from p_variable if p_variable_list just collects them.

# Adjust p_variable_declaration if p_variable now returns Variable AST nodes
def p_variable_declaration(p):
    '''variable_declaration : VAR variable_list SEMICOLON'''
    # If p_variable_list (p[2]) is now a list of Variable AST nodes (due to change in p_variable)
    # then no further list comprehension is needed here.
    p[0] = VariableDeclaration(variable_list=p[2]) # p[2] is already a list of Variable AST nodes

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
                 | if_statement        
                 | while_statement     
                 | repeat_statement    
                 | for_statement       
                 | empty'''
    p[0] = p[1]

# rule for IO statements
def p_io_statement(p):
    '''io_statement : WRITE LPAREN expression_list RPAREN
                    | WRITELN LPAREN expression_list RPAREN
                    | READ LPAREN expression_list RPAREN
                    | READLN LPAREN expression_list RPAREN'''
    # p[1] is 'WRITE', 'WRITELN', 'READ', or 'READLN' token
    # p[3] is the list of expression AST nodes (should be variable identifiers for READ/READLN)
    p[0] = IOCall(operation=p[1].lower(), arguments=p[3])

# rule for assignment statement
def p_assignment_statement(p):
    '''assignment_statement : ID ASSIGN expression'''
    # Assuming ast_nodes.Identifier exists and p[1] is the variable name string
    # Assuming p[3] is already an AST node for the expression
    variable_node = Identifier(name=p[1])
    p[0] = AssignmentStatement(variable=variable_node, expression=p[3])

# rule for FOR statement
def p_for_statement(p):
    '''for_statement : FOR ID ASSIGN expression TO expression DO statement
                     | FOR ID ASSIGN expression DOWNTO expression DO statement'''
    control_var_name = p[2]
    start_expr = p[4]
    end_expr = p[6]
    loop_statement = p[8]
    is_downto = (p[5].lower() == 'downto')

    p[0] = ForStatement(control_variable=Identifier(name=control_var_name),
                        start_expression=start_expr,
                        end_expression=end_expr,
                        statement=loop_statement,
                        downto=is_downto)

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
def p_expression(p):
    '''expression : additive_expression
                  | expression EQUALS additive_expression
                  | expression NE additive_expression
                  | expression LT additive_expression
                  | expression GT additive_expression
                  | expression LE additive_expression
                  | expression GE additive_expression
                  | expression IN additive_expression''' # Assuming IN compares with an additive_expression
    if len(p) == 2: p[0] = p[1]
    else: p[0] = BinaryOperation(left=p[1], operator=p[2], right=p[3])

# Next level (additive operators: +, -, OR, ORELSE)
def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression PLUS multiplicative_expression
                           | additive_expression MINUS multiplicative_expression
                           | additive_expression OR multiplicative_expression
                           | additive_expression ORELSE multiplicative_expression'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = BinaryOperation(left=p[1], operator=p[2], right=p[3])

# Next level (multiplicative operators: *, /, DIV, MOD, AND, ANDTHEN)
def p_multiplicative_expression(p):
    '''multiplicative_expression : factor 
                                 | multiplicative_expression TIMES factor
                                 | multiplicative_expression DIVIDE factor
                                 | multiplicative_expression DIV factor
                                 | multiplicative_expression MOD factor
                                 | multiplicative_expression AND factor
                                 | multiplicative_expression ANDTHEN factor'''
    if len(p) == 2: p[0] = p[1]
    else: p[0] = BinaryOperation(left=p[1], operator=p[2], right=p[3])

# Highest precedence (literals, identifiers, unary, parens, array access, function call)
def p_factor(p):
    '''factor : NUMBER
              | STRING
              | ID
              | LPAREN expression RPAREN
              | factor LBRACKET expression RBRACKET  
              | ID LPAREN expression_list RPAREN  
              | MINUS factor %prec UMINUS          
              | NOT factor                         
              '''
    if len(p) == 2: # NUMBER, STRING, ID
        if isinstance(p[1], (int, float, str)) and p.slice[1].type in ('NUMBER', 'STRING'):
            p[0] = Literal(value=p[1])
        elif p.slice[1].type == 'ID':
            p[0] = Identifier(name=p[1])
        else: # Should be factor from unary op
            p[0] = p[1] 
    elif p.slice[1].type == 'LPAREN': # ( expression )
        p[0] = p[2]
    elif p.slice[2].type == 'LBRACKET': # factor [ expression ]
        p[0] = ArrayAccess(array=p[1], index=p[3])
    elif p.slice[2].type == 'LPAREN': # ID ( expression_list )
         p[0] = FunctionCall(name=p[1], arguments=p[3])
    elif len(p) == 3: # Unary ops
        p[0] = UnaryOperation(operator=p[1], operand=p[2])


# Then remove p_expression_literal, p_expression_variable, p_expression_group,
# p_expression_array_access, p_expression_function_call, p_expression_unary
# and ensure p_expression_binop is replaced by the new structure.
def p_if_statement(p):
    '''if_statement : IF expression THEN statement ELSE statement
                    | IF expression THEN statement'''
    if len(p) == 7:  # IF expr THEN stmt ELSE stmt
        p[0] = IfStatement(condition=p[2], then_statement=p[4], else_statement=p[6])
    else:  # IF expr THEN stmt
        p[0] = IfStatement(condition=p[2], then_statement=p[4], else_statement=None)

def p_while_statement(p):
    '''while_statement : WHILE expression DO statement'''
    p[0] = WhileStatement(condition=p[2], statement=p[4])

def p_repeat_statement(p):
    '''repeat_statement : REPEAT statement_list UNTIL expression'''
    # p[2] is statement_list, p[4] is expression
    p[0] = RepeatStatement(statement_list=p[2], condition=p[4])

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

# Make sure your precedence rules are set up if not already, especially if expressions can be complex.
# Example precedence (add this towards the end of anasin.py, before build_parser):
precedence = (
    ('left', 'OR', 'ORELSE'), # ORELSE from analex.py
    ('left', 'AND', 'ANDTHEN'),# ANDTHEN from analex.py
    ('nonassoc', 'EQUALS', 'NE', 'LT', 'GT', 'LE', 'GE', 'IN'), # Corrected token names, added IN
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD'), 
    ('right', 'UMINUS', 'NOT'), 
)