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
                 array_element_count=None):         # number of elements in the array (if it is an array)
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

class SymbolTable:
    def __init__(self, parent=None, scope_name="global"):
        self.symbols = {}                                # dictionary to hold symbols in this scope
        self.parent = parent                             # parent symbol table (for nested scopes)
        self.scope_name = scope_name                     # name of the scope (e.g., 'global', 'function_name', etc.)
        self.current_local_offset = 0                    # current offset for local variables
        self.current_param_offset = -1                   # current offset for parameters (negative to count downwards)

    def define(self, symbol):
        if symbol.name in self.symbols and self.scope_name != "global_init_phase":
            print(f"Warning: Redefining symbol '{symbol.name}' in scope '{self.scope_name}'.")
        self.symbols[symbol.name] = symbol

    def resolve(self, name):
        sym = self.symbols.get(name) # try to find the symbol in the current scope
        if sym is not None: # found in current scope
            return sym
        if self.parent: # if not found, check the parent scope
            return self.parent.resolve(name)
        return None

    def get_local_var_offset(self, count=1):
        offset = self.current_local_offset # get the current offset for local variables
        self.current_local_offset += count
        return offset

    def get_param_offset(self):
        offset = self.current_param_offset # get the current offset for parameters
        self.current_param_offset -= 1
        return offset

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
        for ident_original in node.id_list: # check each identifier in the program header
            ident_lower = ident_original.lower()
            if symbol_table.resolve(ident_lower): # identifier already exists
                raise Exception(f"Identifier '{ident_original}' already declared.")
            symbol_table.define(Symbol(name=ident_lower, sym_type='parameter', kind='program_param', address_or_offset=0)) # define the identifier as a program parameter

    elif isinstance(node, VariableDeclaration): # for variable declaration node
        for var in node.variable_list: # check each variable in the declaration
            for var_name_original in var.id_list: # check each identifier in the variable
                var_name_lower = var_name_original.lower()
                if symbol_table.resolve(var_name_lower): # if the variable already exists
                    raise Exception(f"Variable '{var_name_original}' already declared.")
                offset = symbol_table.get_local_var_offset()
                symbol = Symbol(
                    name=var_name_lower,
                    sym_type=var.var_type,
                    kind='variable',
                    address_or_offset=offset
                )
                symbol_table.define(symbol) # define the variable in the symbol table

    elif isinstance(node, AssignmentStatement): # for assignment statement node
        check_identifier_exists(node.variable, symbol_table) # check if the identifier exists
        semantic_check(node.expression, symbol_table) # check the expression on the right side of the assignment

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
        if not symbol: # if the function is not declared
            raise Exception(f"Function '{func_name_original}' not declared.")
        if symbol.kind != 'function' and symbol.kind != 'procedure': # if the symbol is not a function or procedure
            raise Exception(f"'{func_name_original}' is not a function or procedure.")
        if len(node.arguments) != len(symbol.params_info): # check if the number of arguments matches the function's parameters
            raise Exception(f"Function '{func_name_original}' expects {len(symbol.params_info)} arguments, but {len(node.arguments)} were provided.")
        for arg in node.arguments: # check each argument in the function call
            semantic_check(arg, symbol_table)

    elif isinstance(node, FunctionDeclaration): # for function declaration node
        func_name_original = node.name
        func_name_lower = func_name_original.lower()

        if symbol_table.resolve(func_name_lower):
            raise Exception(f"Identifier '{func_name_original}' already declared.")

        symbol = Symbol(
            name=func_name_lower,
            sym_type='function',
            kind='function',
            address_or_offset='label_' + func_name_lower,
            return_type=node.return_type,
            params_info=[]
        )
        symbol_table.define(symbol)
        local_table = SymbolTable(parent=symbol_table, scope_name=func_name_lower) 

        # Define implicit variable for function return value
        implicit_return_var = Symbol(
            name=func_name_lower,
            sym_type=node.return_type,
            kind='variable',
            address_or_offset=local_table.get_local_var_offset(), # Or a dedicated offset for return values
            scope_level=1 # Local to function
        )
        local_table.define(implicit_return_var)

        for param in node.parameter_list: # check each parameter in the function declaration
            for param_name_original in param.id_list: # check each identifier in the parameter
                param_name_lower = param_name_original.lower()
                if local_table.resolve(param_name_lower): # Check for redefinition in local scope
                    raise Exception(f"Parameter '{param_name_original}' redefined in function '{func_name_original}'.")
                param_sym = Symbol(
                    name=param_name_lower,
                    sym_type=param.param_type,
                    kind='parameter',
                    address_or_offset=local_table.get_param_offset(),
                    is_var_param=param.is_var
                )
                local_table.define(param_sym)
                symbol.params_info.append(param_sym) # add the parameter symbol to the function's parameters info

        semantic_check(node.block, local_table) # check the block of the function

    elif isinstance(node, ProcedureDeclaration): # for procedure declaration node (similar to function)
        proc_name_original = node.name
        proc_name_lower = proc_name_original.lower()

        if symbol_table.resolve(proc_name_lower):
            raise Exception(f"Identifier '{proc_name_original}' already declared.")

        symbol = Symbol(
            name=proc_name_lower,
            sym_type='procedure',
            kind='procedure',
            address_or_offset='label_' + proc_name_lower,
            params_info=[]
        )
        symbol_table.define(symbol)
        local_table = SymbolTable(parent=symbol_table, scope_name=proc_name_lower)

        for param in node.parameter_list: # check each parameter in the procedure declaration
            for param_name_original in param.id_list: # check each identifier in the parameter
                param_name_lower = param_name_original.lower()
                if local_table.resolve(param_name_lower): # Check for redefinition in local scope
                    raise Exception(f"Parameter '{param_name_original}' redefined in procedure '{proc_name_original}'.")
                param_sym = Symbol(
                    name=param_name_lower,
                    sym_type=param.param_type,
                    kind='parameter',
                    address_or_offset=local_table.get_param_offset(),
                    is_var_param=param.is_var
                )
                local_table.define(param_sym)
                symbol.params_info.append(param_sym) # add the parameter symbol to the procedure's parameters info

        semantic_check(node.block, local_table) # check the block of the procedure

    elif isinstance(node, IOCall): # for IO call node (input/output operations)
        for arg in node.arguments: # check each argument in the IO call
            semantic_check(arg, symbol_table)

    elif isinstance(node, IfStatement): # for if statement node
        semantic_check(node.condition, symbol_table) # check the condition of the if statement
        semantic_check(node.then_statement, symbol_table) # check the then statement of the if statement
        if node.else_statement: # if there is an else statement
            semantic_check(node.else_statement, symbol_table)

    elif isinstance(node, WhileStatement): # for while statement node
        semantic_check(node.condition, symbol_table) # check the condition of the while statement
        semantic_check(node.statement, symbol_table) # check the statement inside the while loop

    elif isinstance(node, RepeatStatement): # for repeat statement node
        for stmt in node.statement_list: # check each statement in the repeat statement
            semantic_check(stmt, symbol_table) 
        semantic_check(node.condition, symbol_table) # check the condition of the repeat statement

    elif isinstance(node, ForStatement):
        check_identifier_exists(node.control_variable, symbol_table) # check if the control variable exists
        semantic_check(node.start_expression, symbol_table) # check the start expression of the for loop
        semantic_check(node.end_expression, symbol_table) # check the end expression of the for loop
        semantic_check(node.statement, symbol_table) # check the statement inside the for loop

    else:
        raise Exception(f"Unknown AST node type: {type(node)}") # raise an exception for unknown node types
    
# check if an identifier exists in the symbol table
def check_identifier_exists(identifier_node, symbol_table):
    assert isinstance(identifier_node, Identifier)
    identifier_name_original = identifier_node.name
    identifier_name_lower = identifier_name_original.lower()
    if not symbol_table.resolve(identifier_name_lower):
        raise Exception(f"Identifier '{identifier_name_original}' not declared in this scope.")

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

    for name, return_type, params in builtins:
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