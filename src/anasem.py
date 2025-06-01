from ast_nodes import *

class Symbol:
    def __init__(self,
                name,
                sym_type,
                kind,                              # 'variable' | 'constant' | 'function' | 'procedure' | 'parameter'
                address_or_offset,                 # For vars: integer offset. For consts: the literal value. For procs/funcs: a label or runtime‐routine name.
                scope_level=0,                     # scope level of the symbol (0 for global, 1 for local, etc.)
                params_info=None,                  # [Symbol, …] for each parameter (if any)
                return_type=None,                  # e.g. 'INTEGER' or 'STRING'
                is_var_param=False,                # true if it is a VAR‐parameter slot
                is_array=False,                    # true if it is an array
                array_lower_bound=None,            # lower bound of the array (if it is an array)
                array_element_count=None,          # number of elements in the array (if it is an array)
                element_type=None):                # Add element_type parameter
        self.name = name
        self.sym_type = sym_type
        self.kind = kind
        self.address_or_offset = address_or_offset
        self.scope_level = scope_level
        self.params_info = params_info if params_info is not None else []
        self.return_type = return_type
        self.is_var_param = is_var_param
        self.is_array = is_array
        self.array_lower_bound = array_lower_bound
        self.array_element_count = array_element_count
        self.element_type = element_type

    def __str__(self):
        return f"Symbol(name={self.name}, sym_type={self.sym_type}, kind={self.kind}, address_or_offset={self.address_or_offset}, scope_level={self.scope_level}, params_info={self.params_info}, return_type={self.return_type}, is_var_param={self.is_var_param}, is_array={self.is_array}, array_lower_bound={self.array_lower_bound}, array_element_count={self.array_element_count}, element_type={self.element_type})"

class SymbolTable:
    def __init__(self, parent=None, scope_name="global"):
        self.symbols = {}                                # dictionary to hold symbols in this scope
        self.parent = parent                             # parent symbol table (for nested scopes)
        self.scope_name = scope_name                     # name of the scope (e.g., 'global', 'function_name', etc.)
        self.current_local_offset = 0                    # current offset for local variables
        self.current_param_offset = -1                   # current offset for parameters (negative to count downwards)
        if parent is None:
            self.scope_level = 0
        else:
            self.scope_level = parent.scope_level + 1

    # define a new symbol in the current scope
    def define(self, symbol):
        if symbol.name in self.symbols and self.scope_name != "global_init_phase":
            print(f"Warning: Redefining symbol '{symbol.name}' in scope '{self.scope_name}'.")
        self.symbols[symbol.name] = symbol

    # resolve a symbol by its name in the current scope or parent scopes
    def resolve(self, name):
        sym = self.symbols.get(name) # try to find the symbol in the current scope
        if sym is not None: # found in current scope
            return sym
        if self.parent: # if not found, check the parent scope
            return self.parent.resolve(name)
        return None

    # get the offset for local variables (incrementing the offset)
    def get_local_var_offset(self, count=1):
        offset = self.current_local_offset
        self.current_local_offset += count
        return offset

    # get the offset for parameters (counting downwards)
    def get_param_offset(self):
        offset = self.current_param_offset
        self.current_param_offset -= 1
        return offset

# helper function that extracts type information from an AST node
def extract_type_info_from_ast(type_ast_node, line_info_for_error, context_name="Variable"):
    is_array = isinstance(type_ast_node, ArrayType)
    symbol_type_str = None
    element_type_str = None

    if is_array:
        symbol_type_str = "ARRAY"
        if not isinstance(type_ast_node.element_type, str):
            raise Exception(f"{line_info_for_error}{context_name} array element type is not a simple type string.")
        element_type_str = type_ast_node.element_type
    else:
        if not isinstance(type_ast_node, str):
            raise Exception(f"{line_info_for_error}{context_name} type ('{type(type_ast_node)}') is not a simple type string or recognized array type.")
        symbol_type_str = type_ast_node
    
    return is_array, symbol_type_str, element_type_str

# helper to create a symbol for a function or procedure
def create_callable_symbol(name_lower, kind_str, defining_symbol_table, return_type_str=None):
    return Symbol(
        name=name_lower,
        sym_type=kind_str,                        # for callables, sym_type can be the same as kind
        kind=kind_str,
        address_or_offset='label_' + name_lower,  # standard labeling convention
        return_type=return_type_str,
        params_info=[],                           # initialized empty, filled by process_parameters_semantic_check
        scope_level=defining_symbol_table.scope_level
    )

# helper to create a symbol for a variable or parameter
def create_variable_or_param_symbol(name_lower, symbol_data_type_str, kind_str, target_symbol_table, is_array=False, element_type_str=None, is_var_param=False):
    offset = None
    if kind_str == 'variable': # variable symbol
        offset = target_symbol_table.get_local_var_offset()
    elif kind_str == 'parameter': # parameter symbol
        offset = target_symbol_table.get_param_offset()
    else: # unsupported kind for this helper
        raise ValueError(f"Unsupported kind '{kind_str}' for _create_variable_or_param_symbol")

    return Symbol(
        name=name_lower,
        sym_type=symbol_data_type_str,                                     # data type of the variable or parameter
        kind=kind_str,
        address_or_offset=offset,                                          # offset for the variable or parameter
        scope_level=target_symbol_table.scope_level,
        is_array=is_array,                                                 # true if it is an array
        element_type=element_type_str,                                     # type of the elements in the array (if it is an array)
        is_var_param=is_var_param if kind_str == 'parameter' else False    # true if it is a VAR-parameter slot (only for parameters)
    )

# perform semantic checks on the AST nodes for the given symbol table
def semantic_check(node, symbol_table):
    if node is None:
        return

    if symbol_table.parent is None and not hasattr(symbol_table, "_builtins_registered"):
        register_builtin_functions(symbol_table)
        symbol_table._builtins_registered = True

    if isinstance(node, Program): # for program node
        semantic_check(node.header, symbol_table) # check program header
        semantic_check(node.block, symbol_table) # check program block

    elif isinstance(node, Block): # for block node
        for decl in node.declarations: # check each declaration in the block
            semantic_check(decl, symbol_table)
        semantic_check(node.compound_statement, symbol_table) # check the compound statement in the block

    elif isinstance(node, ProgramHeader): # for program header node
        prog_header_lineno = getattr(node, 'lineno', None)
        line_info_header = format_line_info(prog_header_lineno)
        for ident_original in node.id_list: # check each identifier in the program header
            ident_lower = ident_original.lower()
            if symbol_table.resolve(ident_lower): # identifier already exists
                raise Exception(f"{line_info_header}Identifier '{ident_original}' already declared in program header.")
            symbol_table.define(Symbol(name=ident_lower, sym_type='parameter', kind='program_param', address_or_offset=0, scope_level=symbol_table.scope_level)) # define as program parameter

    elif isinstance(node, VariableDeclaration): # for variable declaration node
        var_decl_group_lineno = getattr(node, 'lineno', None)
        for var_ast_node in node.variable_list: # check each variable in the declaration
            var_decl_specific_lineno = getattr(var_ast_node, 'lineno', var_decl_group_lineno)
            line_info_decl = format_line_info(var_decl_specific_lineno)

            is_an_array_decl, symbol_type_str, symbol_element_type_str = extract_type_info_from_ast(var_ast_node.var_type, line_info_decl, "Variable")

            for var_name_original in var_ast_node.id_list: # check each identifier in the variable declaration
                var_name_lower = var_name_original.lower()
                if symbol_table.resolve(var_name_lower): # if the variable already exists
                    raise Exception(f"{line_info_decl}Variable '{var_name_original}' already declared.")
                
                symbol = create_variable_or_param_symbol(var_name_lower, symbol_type_str, 'variable', symbol_table, is_an_array_decl, symbol_element_type_str)
                symbol_table.define(symbol)

    elif isinstance(node, AssignmentStatement): # for assignment statement node
        semantic_check(node.variable, symbol_table) # check the variable on the left-hand side

        var_name_original = node.variable.name
        var_name_lower = var_name_original.lower()
        var_symbol = symbol_table.resolve(var_name_lower)

        assign_stmt_lineno = getattr(node, 'lineno', None)
        var_ident_lineno = getattr(node.variable, 'lineno', assign_stmt_lineno)

        line_info_assign = format_line_info(assign_stmt_lineno)
        line_info_var_lhs = format_line_info(var_ident_lineno)

        declared_lhs_type = None # initialize the declared type of the LHS variable
        if var_symbol.kind == 'variable': # if the variable is a regular variable
            declared_lhs_type = var_symbol.sym_type
        elif var_symbol.kind == 'parameter': # if the variable is a parameter
            if var_symbol.is_var_param: # if it is a VAR parameter
                declared_lhs_type = var_symbol.sym_type
            else:
                raise Exception(f"{line_info_var_lhs}Cannot assign to a value parameter '{var_name_original}'.")
        elif var_symbol.kind == 'function' and symbol_table.scope_name == var_name_lower: # if assigning to a function name in its own scope
            declared_lhs_type = var_symbol.return_type
        else: # if the variable is not assignable (e.g., constant, procedure, etc.)
            raise Exception(
                f"{line_info_var_lhs}Identifier '{var_name_original}' on LHS is not an assignable variable, "
                f"VAR parameter, or function return. Kind: '{var_symbol.kind}'."
            )

        if declared_lhs_type is None: # if we could not determine the type of the LHS variable
             raise Exception(f"{line_info_var_lhs}Could not determine type for LHS variable '{var_name_original}'.")

        lhs_type_for_comparison = declared_lhs_type.upper()

        # recursively check the expression on the RHS
        semantic_check(node.expression, symbol_table)
        rhs_type = get_expression_type(node.expression, symbol_table)
        
        compatible = (lhs_type_for_comparison == rhs_type) or \
                     (lhs_type_for_comparison == "REAL" and rhs_type == "INTEGER") # allow INTEGER to be assigned to REAL

        if not compatible: # if the types are not compatible
            raise Exception(
                f"{line_info_assign}Type mismatch: Cannot assign expression of type '{rhs_type}' "
                f"to variable '{var_name_original}' of type '{declared_lhs_type}'."
            )

    elif isinstance(node, CompoundStatement): # for compound statement node
        for stmt in node.statement_list: # check each statement in the compound statement
            semantic_check(stmt, symbol_table)

    elif isinstance(node, Identifier): # for identifier node
        check_identifier_exists(node, symbol_table) # check if the identifier exists in the symbol table

    elif isinstance(node, Literal): # for literal node
        pass  # literals are inherently valid

    elif isinstance(node, BinaryOperation): # for binary operation node
        semantic_check(node.left, symbol_table) # check the left operand
        semantic_check(node.right, symbol_table) # check the right operand

    elif isinstance(node, UnaryOperation): # for unary operation node
        semantic_check(node.operand, symbol_table) # check the operand of the unary operation

    elif isinstance(node, ArrayAccess): # for array access node
        semantic_check(node.array, symbol_table) # check the array being accessed
        semantic_check(node.index, symbol_table) # check the index used for accessing the array

    elif isinstance(node, FunctionCall): # for function call node
        func_name_original = node.name
        func_name_lower = func_name_original.lower()
        symbol = symbol_table.resolve(func_name_lower)
        
        call_lineno = getattr(node, 'lineno', None)
        line_info_call = format_line_info(call_lineno)

        if not symbol: # if the function or procedure is not found in the symbol table
            raise Exception(f"{line_info_call}Function or Procedure '{func_name_original}' not declared.")
        if symbol.kind != 'function' and symbol.kind != 'procedure': # if the symbol is not a function or procedure
            raise Exception(f"{line_info_call}'{func_name_original}' is not a function or procedure.")
        if len(node.arguments) != len(symbol.params_info): # if the number of arguments does not match the number of parameters
            raise Exception(f"{line_info_call}Function/Procedure '{func_name_original}' expects {len(symbol.params_info)} arguments, but {len(node.arguments)} were provided.")
        for arg in node.arguments: # check each argument in the function call
            semantic_check(arg, symbol_table)

    elif isinstance(node, FunctionDeclaration): # for function declaration node
        func_name_original = node.name
        func_name_lower = func_name_original.lower()
        
        decl_lineno = getattr(node, 'lineno', None)
        line_info_decl = format_line_info(decl_lineno)

        if symbol_table.resolve(func_name_lower): # if the function is already declared
            raise Exception(f"{line_info_decl}Identifier '{func_name_original}' already declared.")

        func_symbol = create_callable_symbol(func_name_lower, 'function', symbol_table, node.return_type) # create a symbol for the function with its return type
        symbol_table.define(func_symbol) # define the function in the symbol table

        local_table = SymbolTable(parent=symbol_table, scope_name=func_name_lower) # create a new local symbol table for the function

        implicit_return_var = create_variable_or_param_symbol(func_name_lower, node.return_type, 'variable',local_table)
        local_table.define(implicit_return_var)

        process_parameters_semantic_check(node.parameter_list, local_table, func_symbol, func_name_original, "function") # process parameters for the function
        
        semantic_check(node.block, local_table) # check the block of the function

    elif isinstance(node, ProcedureDeclaration): # for procedure declaration node (similar to function)
        proc_name_original = node.name
        proc_name_lower = proc_name_original.lower()

        decl_lineno = getattr(node, 'lineno', None)
        line_info_decl = format_line_info(decl_lineno)

        if symbol_table.resolve(proc_name_lower): # if the procedure is already declared
            raise Exception(f"{line_info_decl}Identifier '{proc_name_original}' already declared.")

        proc_symbol = create_callable_symbol(proc_name_lower, 'procedure', symbol_table) # same as function but without return type
        symbol_table.define(proc_symbol) # define the procedure in the symbol table

        local_table = SymbolTable(parent=symbol_table, scope_name=proc_name_lower) # create a new local symbol table for the procedure

        process_parameters_semantic_check(node.parameter_list, local_table, proc_symbol, proc_name_original, "procedure") # process parameters for the procedure

        semantic_check(node.block, local_table) # check the block of the procedure

    elif isinstance(node, IOCall): # for IO call node (input/output operations)
        for arg in node.arguments: # check each argument in the IO call
            semantic_check(arg, symbol_table) # check the argument for type correctness

    elif isinstance(node, IfStatement): # for if statement node
        semantic_check(node.condition, symbol_table) # check the condition of the if statement
        semantic_check(node.then_statement, symbol_table) # check the then statement of the if statement
        if node.else_statement: # if there is an else statement
            semantic_check(node.else_statement, symbol_table) # check the else statement of the if statement

    elif isinstance(node, WhileStatement): # for while statement node
        semantic_check(node.condition, symbol_table) # check the condition of the while statement
        semantic_check(node.statement, symbol_table) # check the statement inside the while loop

    elif isinstance(node, RepeatStatement): # for repeat statement node
        for stmt in node.statement_list: # check each statement in the repeat statement
            semantic_check(stmt, symbol_table) # check the statement inside the repeat
        semantic_check(node.condition, symbol_table) # check the condition of the repeat statement

    elif isinstance(node, ForStatement): # for for statement node
        check_identifier_exists(node.control_variable, symbol_table) # check if the control variable exists
        semantic_check(node.start_expression, symbol_table) # check the start expression of the for loop
        semantic_check(node.end_expression, symbol_table) # check the end expression of the for loop
        semantic_check(node.statement, symbol_table) # check the statement inside the for loop

    else: # if the node is of an unknown type
        unknown_node_lineno = getattr(node, 'lineno', None) # get the line number of the unknown node
        line_info_unknown = format_line_info(unknown_node_lineno) # format line info for the unknown node
        raise Exception(f"{line_info_unknown}Unknown AST node type for semantic check: {type(node)}")

# check if an identifier exists in the symbol table
def check_identifier_exists(identifier_node, symbol_table):
    assert isinstance(identifier_node, Identifier)
    identifier_name_original = identifier_node.name
    identifier_name_lower = identifier_name_original.lower()
    if not symbol_table.resolve(identifier_name_lower): # if the identifier is not found in the symbol table
        ident_lineno = getattr(identifier_node, 'lineno', None) # get the line number of the identifier node
        line_info = format_line_info(ident_lineno) # format line info for the identifier
        raise Exception(f"{line_info}Identifier '{identifier_name_original}' not declared in this scope.")

# get the type of an expression node based on the symbol table
def get_expression_type(node, symbol_table):
    node_lineno = getattr(node, 'lineno', None)
    line_info = format_line_info(node_lineno)

    if isinstance(node, Identifier): # if the node is an identifier
        symbol = symbol_table.resolve(node.name.lower())
        if not symbol: # if the identifier is not found in the symbol table
            raise Exception(f"{line_info}Identifier '{node.name}' not declared.")
        
        if symbol.kind in ['variable', 'parameter', 'constant']: # these can be used as values in expressions
            if symbol.sym_type is None: # if the symbol has no type information
                 raise Exception(f"{line_info}Identifier '{node.name}' has no type information.")
            return symbol.sym_type.upper()
        else: # if the symbol is not a variable, parameter, or constant
            raise Exception(f"{line_info}Identifier '{node.name}' of kind '{symbol.kind}' cannot be used as a value in an expression.")

    elif isinstance(node, FunctionCall): # if the node is a function call
        func_name_lower = node.name.lower()
        symbol = symbol_table.resolve(func_name_lower)
        if not symbol: # if the function or procedure is not found in the symbol table
            raise Exception(f"{line_info}Function or Procedure '{node.name}' not declared.")
        
        if symbol.kind == 'procedure': # if it's a procedure, it cannot be used in an expression
            raise Exception(f"{line_info}Procedure '{node.name}' does not return a value and cannot be used in an expression.")
        elif symbol.kind == 'function': # if it's a function, check its return type
            if symbol.return_type is None:
                 raise Exception(f"{line_info}Function '{node.name}' does not have a defined return type.")
            return symbol.return_type.upper()
        else: # if it's not a function or procedure
            raise Exception(f"{line_info}'{node.name}' is not a function or procedure.")

    elif isinstance(node, BinaryOperation): # if the node is a binary operation
        left_type = get_expression_type(node.left, symbol_table)
        right_type = get_expression_type(node.right, symbol_table)
        op = node.operator.upper()

        if op in ['+', '-', '*', '/']: # arithmetic operations
            if op == '/' and (left_type in ["INTEGER", "REAL"]) and (right_type in ["INTEGER", "REAL"]): # division
                return "REAL"
            elif (left_type == "INTEGER" and right_type == "INTEGER"): # integer addition/subtraction/multiplication
                return "INTEGER"
            elif (left_type in ["INTEGER", "REAL"] and right_type in ["INTEGER", "REAL"]): # mixed arithmetic
                return "REAL"
            elif op == '+' and left_type == "STRING" and right_type == "STRING": # string concatenation
                return "STRING"
            else: # unsupported operation
                raise Exception(f"{line_info}Operator '{node.operator}' cannot be applied to types '{left_type}' and '{right_type}'.")

        elif op in ['DIV', 'MOD']: # integer division and modulus
            if left_type == "INTEGER" and right_type == "INTEGER": # both operands must be INTEGER
                return "INTEGER"
            else: # if not both operands are INTEGER
                raise Exception(f"{line_info}Operator '{node.operator}' requires INTEGER operands, got '{left_type}' and '{right_type}'.")

        elif op in ['=', '<>', '<', '<=', '>', '>=']: # comparison operators
            if (left_type in ["INTEGER", "REAL"] and right_type in ["INTEGER", "REAL"]) or \
               (left_type == "STRING" and right_type == "STRING") or \
               (left_type == "BOOLEAN" and right_type == "BOOLEAN"): # valid comparison types
                return "BOOLEAN"
            else: # if the types are not compatible for comparison
                raise Exception(f"{line_info}Cannot compare types '{left_type}' and '{right_type}' with operator '{node.operator}'.")

        elif op in ['AND', 'OR']: # logical operators
            if left_type == "BOOLEAN" and right_type == "BOOLEAN": # both operands must be BOOLEAN
                return "BOOLEAN"
            else: # if not both operands are BOOLEAN
                raise Exception(f"{line_info}Logical operator '{node.operator}' requires BOOLEAN operands, got '{left_type}' and '{right_type}'.")
        else: # unsupported binary operator
            raise Exception(f"{line_info}Unsupported binary operator '{node.operator}' for type checking.")

    elif isinstance(node, UnaryOperation): # if the node is a unary operation
        operand_type = get_expression_type(node.operand, symbol_table)
        op = node.operator.upper()

        if op == 'NOT': # logical NOT operator
            if operand_type == "BOOLEAN": # operand must be BOOLEAN
                return "BOOLEAN"
            else: # if the operand is not BOOLEAN
                raise Exception(f"{line_info}Unary 'NOT' operator requires a BOOLEAN operand, got {operand_type}.")
        elif op in ['+', '-']: # arithmetic unary operators
            if operand_type == "INTEGER": # unary plus/minus on INTEGER
                return "INTEGER"
            elif operand_type == "REAL": # unary plus/minus on REAL
                return "REAL"
            else: # if the operand is not INTEGER or REAL
                raise Exception(f"{line_info}Unary '{node.operator}' operator requires INTEGER or REAL operand, got {operand_type}.")
        else: # unsupported unary operator
            raise Exception(f"{line_info}Unknown unary operator '{node.operator}' for type checking.")

    elif isinstance(node, ArrayAccess): # if the node is an array access
        if not isinstance(node.array, Identifier): # array access must be on an identifier
            raise Exception(f"{line_info}Array access must be on an identifier.")
            
        array_symbol = symbol_table.resolve(node.array.name.lower())
        if not array_symbol or not array_symbol.is_array: # if the array symbol is not found or not an array
            raise Exception(f"{line_info}Identifier '{node.array.name}' is not an array or not declared.")
        if not array_symbol.element_type: # if the array does not have a defined element type
             raise Exception(f"{line_info}Array '{node.array.name}' does not have a defined element type.")
        index_type = get_expression_type(node.index, symbol_table)
        if index_type != "INTEGER": # the index must be an INTEGER
            raise Exception(f"{line_info}Array index for '{node.array.name}' must be an INTEGER, got {index_type}.")
        return array_symbol.element_type.upper()

    elif isinstance(node, Literal): # if the node is a generic Literal
        if hasattr(node, 'literal_type') and node.literal_type: # if the node has a literal_type attribute
            return node.literal_type.upper() 
        else: # if the node has no literal_type attribute
            if hasattr(node, 'value'): # if the node has a value attribute
                if isinstance(node.value, bool): return "BOOLEAN" 
                if isinstance(node.value, int): return "INTEGER" 
                if isinstance(node.value, str): return "STRING" 
                if isinstance(node.value, float): return "REAL" 
            # If literal_type is not present and value type is not recognized
            raise Exception(f"{line_info}Literal node has no 'literal_type' or its type cannot be inferred from its value.")

    else: # if the node is of an unsupported type
        raise Exception(f"{line_info}Cannot determine type for expression node: {type(node)}.")

# helper function to process parameters for functions and procedures
def process_parameters_semantic_check(parameter_list_ast, local_table, callable_symbol, callable_name_original, callable_kind_str):
    for param_ast_node in parameter_list_ast: # param_ast_node is a ParameterDeclaration node
        param_decl_lineno = getattr(param_ast_node, 'lineno', None)

        for param_name_original in param_ast_node.id_list: # param_name_original is the original name of the parameter
            param_name_lower = param_name_original.lower()
            
            line_info_param = format_line_info(param_decl_lineno)

            if local_table.resolve(param_name_lower): # parameter already defined in this scope
                raise Exception(f"{line_info_param}Parameter '{param_name_original}' redefined in {callable_kind_str} '{callable_name_original}'.")

            is_array_param, param_symbol_type_str, param_element_type_str = extract_type_info_from_ast(param_ast_node.param_type, line_info_param, "Parameter")

            param_sym = create_variable_or_param_symbol( param_name_lower, param_symbol_type_str, 'parameter', local_table, is_array_param, param_element_type_str, param_ast_node.is_var)
            local_table.define(param_sym) # define the parameter in the local symbol table
            callable_symbol.params_info.append(param_sym) # append the parameter symbol to the callable's params_info

# Helper to format line information for error messages
def format_line_info(lineno):
    return f"Line {lineno}: " if lineno is not None else ""

# register built-in functions and procedures in the global symbol table
def register_builtin_functions(symbol_table):
    builtins = [
        ("length", "INTEGER", [("STRING", False)]),
        ("uppercase", "STRING", [("STRING", False)]),
        ("lowercase", "STRING", [("STRING", False)]),
        ("abs", "INTEGER", [("INTEGER", False)]),
        ("sqr", "INTEGER", [("INTEGER", False)]),
        ("sqrt", "REAL", [("REAL", False)]),
        ("pred", "INTEGER", [("INTEGER", False)]),
        ("succ", "INTEGER", [("INTEGER", False)]),
    ]

    for name, return_type, params in builtins: # register each built-in function
        param_symbols = []
        for i, (ptype, is_var) in enumerate(params):
            param_symbols.append(Symbol(
                name=f"param{i}",
                sym_type=ptype,
                kind="parameter",
                address_or_offset=i,
                is_var_param=is_var
            ))

        builtin_symbol = Symbol(
            name=name.lower(),
            sym_type="function",
            kind="function",
            address_or_offset=f"BUILTIN_{name.upper()}",
            return_type=return_type,
            params_info=param_symbols
        )
        symbol_table.define(builtin_symbol)