import ast_nodes
from anasem import Symbol # SymbolTable is not directly used here, but Symbol is
# MODIFIED: Use relative import for generation_context
from . import generation_context as ctx # Alias for brevity
from . import type_helpers as th

# Visitor dispatcher
_visitors = {}

def visit(node):
    if node is None:
        return
    method_name = f'visit_{type(node).__name__}'
    visitor = _visitors.get(method_name, generic_visit)
    return visitor(node)

def generic_visit(node):
    print(f"Warning: No visitor method for {type(node).__name__}")
    if hasattr(node, '__dict__'):
        for _, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, '__class__') and isinstance(item, ast_nodes.ASTNode): # Check if it's an ASTNode
                        visit(item)
            elif hasattr(value, '__class__') and isinstance(value, ast_nodes.ASTNode): # Check if it's an ASTNode
                visit(value)

# Helper to register visitor methods
def register_visitor(node_type_name):
    def decorator(func):
        _visitors[f'visit_{node_type_name}'] = func
        return func
    return decorator

# Generates a new temporary variable offset
def new_temp_var_offset():
    offset = ctx.current_scope.get_local_var_offset()
    ctx.emit(f"PUSHI 0", f"Allocate temp var at FP+{offset}")
    return offset

@register_visitor("Program")
def visit_Program(node):
    if node.block and node.block.declarations:
        for decl in node.block.declarations:
            if isinstance(decl, ast_nodes.VariableDeclaration):
                for var_info in decl.variable_list:
                    var_type_for_symbol_str = th.type_node_to_string(var_info.var_type)
                    is_array_type, array_size, lower_bound, actual_element_type_str = th.process_array_type(var_info.var_type)
                    for var_id_str in var_info.id_list:
                        offset = ctx.current_scope.get_local_var_offset(count=array_size)
                        sym = Symbol(var_id_str,
                                    var_type_for_symbol_str,
                                    'variable',
                                    offset,
                                    scope_level=0,
                                    is_array=is_array_type,
                                    array_lower_bound=lower_bound if is_array_type else None,
                                    array_element_count=array_size if is_array_type else None,
                                    element_type=actual_element_type_str if is_array_type else None)
                        ctx.current_scope.define(sym)
                        ctx.globals_handled_pre_start.add(var_id_str)
                        if is_array_type:
                            ctx.emit(f"PUSHN {array_size}", f"Reserve space for global array '{var_id_str}' (gp[{offset}..])")
                        else:
                            ctx.emit(f"PUSHI 0", f"Initial stack value for global '{var_id_str}' (gp[{offset}])")
    ctx.emit("START", "Initialize Frame Pointer = Stack Pointer")
    visit(node.block)
    ctx.emit("STOP", "End of program")

@register_visitor("ProgramHeader")
def visit_ProgramHeader(node):
    pass

@register_visitor("Block")
def visit_Block(node):
    function_procedure_nodes = []
    declarations_for_this_block_pass = []
    if node.declarations:
        for decl in node.declarations:
            if isinstance(decl, (ast_nodes.FunctionDeclaration, ast_nodes.ProcedureDeclaration)):
                function_procedure_nodes.append(decl)
            else:
                declarations_for_this_block_pass.append(decl)
    for decl_node in declarations_for_this_block_pass:
        visit(decl_node)
    main_code_label = None
    if function_procedure_nodes:
        main_code_label = ctx.new_label("mainLabel")
        ctx.emit(f"JUMP {main_code_label}", "Jump over nested function/proc definitions")
    for fp_node in function_procedure_nodes:
        visit(fp_node)
    if main_code_label:
        ctx.emit_label(main_code_label)
    if node.compound_statement:
        visit(node.compound_statement)

@register_visitor("VariableDeclaration")
def visit_VariableDeclaration(node):
    for var_info in node.variable_list:
        var_type_for_symbol_str = th.type_node_to_string(var_info.var_type)
        is_array_type, array_size, lower_bound, actual_element_type_str = th.process_array_type(var_info.var_type)
        for var_id_str in var_info.id_list:
            if var_id_str in ctx.globals_handled_pre_start:
                continue
            if ctx.current_scope.parent is None or ctx.current_scope.parent.scope_name == "global_init_phase":
                offset = ctx.current_scope.get_local_var_offset(count=array_size)
                sym_check = ctx.current_scope.resolve(var_id_str)
                if not sym_check: # Define only if not somehow already defined (e.g. forward decl)
                    sym = Symbol(var_id_str,
                                var_type_for_symbol_str,
                                'variable',
                                offset,
                                scope_level=0,
                                is_array=is_array_type,
                                array_lower_bound=lower_bound if is_array_type else None,
                                array_element_count=array_size if is_array_type else None,
                                element_type=actual_element_type_str if is_array_type else None)
                    ctx.current_scope.define(sym)
                if is_array_type:
                    ctx.emit(f"// Global array '{var_id_str}' (gp[{offset}..]) defined (post-START init)", "")
                    ctx.emit(f"// Warning: Post-START global array declaration for {var_id_str} - review allocation")
                else:
                    ctx.emit(f"PUSHI 0", f"Default value for global '{var_id_str}'")
                    ctx.emit(f"STOREG {offset}", f"Initialize global '{var_id_str}' to 0")
            else: # Local variable
                offset = ctx.current_scope.get_local_var_offset(count=array_size)
                sym = Symbol(var_id_str,
                            var_type_for_symbol_str,
                            'variable',
                            offset,
                            scope_level=ctx.current_scope.scope_level, # Use dynamic scope level
                            is_array=is_array_type,
                            array_lower_bound=lower_bound if is_array_type else None,
                            array_element_count=array_size if is_array_type else None,
                            element_type=actual_element_type_str if is_array_type else None)
                ctx.current_scope.define(sym)
                if is_array_type:
                    ctx.emit(f"PUSHN {array_size}", f"Allocate {array_size} slots for local array '{var_id_str}' at FP+{offset}")
                else:
                    ctx.emit(f"PUSHI 0", f"Allocate space for local var '{var_id_str}' at FP+{offset}")

@register_visitor("ConstantDeclaration")
def visit_ConstantDeclaration(node):
    for const_def in node.constant_list:
        raw_value = const_def.value.value
        # Infer type from raw_value for symbol, or use type from AST if available
        typ_str = th.type_node_to_string(const_def.value.type if hasattr(const_def.value, 'type') else type(raw_value).__name__)
        sym = Symbol(const_def.name, typ_str, 'constant', raw_value, ctx.current_scope.scope_level)
        ctx.current_scope.define(sym)
        ctx.emit(f"// Constant '{const_def.name}' defined as {raw_value}", "")

@register_visitor("FunctionDeclaration")
def visit_FunctionDeclaration(node):
    func_label = ctx.new_label(f"func{node.name}")
    return_type_str = th.type_node_to_string(node.return_type) if node.return_type else "VOID"
    param_symbols_for_signature = []
    if node.parameter_list:
        for param_group in node.parameter_list:
            param_type_str = th.type_node_to_string(param_group.param_type)
            for pid in param_group.id_list:
                param_symbols_for_signature.append(
                    Symbol(pid, param_type_str, 'parameter', 0, is_var_param=param_group.is_var)
                )
    func_sym = Symbol(node.name, return_type_str, 'function', func_label,
                        params_info=param_symbols_for_signature, return_type=return_type_str)
    ctx.current_scope.define(func_sym)
    ctx.emit_label(func_label)
    ctx.push_scope(scope_name=f"func_{node.name}")
    if node.parameter_list:
        for param_group in reversed(node.parameter_list): # Process in reverse for correct offset calculation
            param_type_str = th.type_node_to_string(param_group.param_type)
            for param_id_str in reversed(param_group.id_list):
                offset = ctx.current_scope.get_param_offset()
                param_sym = Symbol(param_id_str, param_type_str, 'parameter', offset,
                                    scope_level=ctx.current_scope.scope_level, is_var_param=param_group.is_var)
                ctx.current_scope.define(param_sym)
                ctx.emit(f"// Param '{param_id_str}' at FP{offset}", "")
    # Allocate space for local variables by visiting their declarations
    if node.block and node.block.declarations:
        for decl in node.block.declarations:
            if isinstance(decl, ast_nodes.VariableDeclaration):
                visit(decl) # This will emit PUSHN/PUSHI for locals
    if node.block:
        visit(node.block.compound_statement) # Visit the function body
    # Ensure a return path if not explicitly returned, especially for functions that should return a value
    # For now, relying on explicit return or letting VM handle it.
    # If function has a non-VOID return type, and no explicit return for function name assignment,
    # it might be an issue. Pascal often uses assignment to function name for return.
    ctx.emit("RETURN", f"Return from function {node.name}")
    ctx.pop_scope()

@register_visitor("ProcedureDeclaration")
def visit_ProcedureDeclaration(node):
    proc_label = ctx.new_label(f"proc{node.name}")
    param_symbols_for_signature = []
    if node.parameter_list:
        for param_group in node.parameter_list:
            param_type_str = th.type_node_to_string(param_group.param_type)
            for pid in param_group.id_list:
                param_symbols_for_signature.append(
                    Symbol(pid, param_type_str, 'parameter', 0, is_var_param=param_group.is_var)
                )
    proc_sym = Symbol(node.name, "VOID", 'procedure', proc_label, params_info=param_symbols_for_signature)
    ctx.current_scope.define(proc_sym)
    ctx.emit_label(proc_label)
    ctx.push_scope(scope_name=f"proc_{node.name}")
    if node.parameter_list:
        for param_group in reversed(node.parameter_list):
            param_type_str = th.type_node_to_string(param_group.param_type)
            for param_id_str in reversed(param_group.id_list):
                offset = ctx.current_scope.get_param_offset()
                param_sym = Symbol(param_id_str, param_type_str, 'parameter', offset,
                                    scope_level=ctx.current_scope.scope_level, is_var_param=param_group.is_var)
                ctx.current_scope.define(param_sym)
                ctx.emit(f"// Param '{param_id_str}' at FP{offset}", "")
    if node.block and node.block.declarations:
        for decl in node.block.declarations:
            if isinstance(decl, ast_nodes.VariableDeclaration):
                visit(decl)
    if node.block:
        visit(node.block.compound_statement)
    ctx.emit("RETURN", f"Return from procedure {node.name}")
    ctx.pop_scope()

@register_visitor("CompoundStatement")
def visit_CompoundStatement(node):
    for stmt in node.statement_list:
        visit(stmt)

@register_visitor("AssignmentStatement")
def visit_AssignmentStatement(node):
    if isinstance(node.variable, ast_nodes.ArrayAccess):
        # RHS first, store temporarily
        visit(node.expression)
        temp_rhs_offset = new_temp_var_offset()
        ctx.emit(f"STOREL {temp_rhs_offset}", "Store RHS temporarily for array assignment")

        # Base address of array
        array_node_for_addr = node.variable.array
        if not isinstance(array_node_for_addr, ast_nodes.Identifier):
            raise NotImplementedError("Assignment to non-identifier array base not implemented")
        array_name = array_node_for_addr.name
        sym_array = ctx.current_scope.resolve(array_name)
        if not sym_array or not sym_array.is_array:
            # Check if it's a VAR parameter that's an array
            if sym_array and sym_array.is_var_param: # It's an address
                ctx.emit(f"PUSHL {sym_array.address_or_offset}", f"Load address from VAR param array '{array_name}'")
            else:
                raise ValueError(f"'{array_name}' is not a defined array or VAR param array for assignment.")
        elif sym_array.scope_level == 0:
            ctx.emit("PUSHGP", f"Push GP for global array '{array_name}' base")
            ctx.emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of global array '{array_name}'")
            ctx.emit("PADD", f"Calculate base address of global array '{array_name}'")
        else: # Local array
            ctx.emit("PUSHFP", f"Push FP for local array '{array_name}' base")
            ctx.emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of local array '{array_name}'")
            ctx.emit("PADD", f"Calculate base address of local array '{array_name}'")
        
        # Index
        visit(node.variable.index)
        if sym_array and sym_array.is_array and sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
            ctx.emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
            ctx.emit("SUB", "Adjust index to be 0-based for VM")
        
        # Reload RHS
        ctx.emit(f"PUSHL {temp_rhs_offset}", "Reload RHS for array assignment")
        ctx.emit("STOREN", "Store to array element")

    elif isinstance(node.variable, ast_nodes.Identifier):
        visit(node.expression) # Value to be assigned is on TOS
        var_name = node.variable.name
        sym = ctx.current_scope.resolve(var_name)
        if not sym:
            raise ValueError(f"Undefined variable '{var_name}' in assignment.")

        is_function_return_assignment = False
        if sym.kind == 'function' and ctx.current_scope.scope_name == f"func_{sym.name}":
            is_function_return_assignment = True
        
        if is_function_return_assignment:
            # Value is on TOS, will be picked up by RETURN or handled by VM convention
            ctx.emit(f"// Assignment to function name '{var_name}', value on TOS for return", "")
            # Depending on VM, might need STOREL to a dedicated return value slot if not implicit
        elif sym.is_var_param:
            ctx.emit(f"PUSHL {sym.address_or_offset}", f"Load address from VAR param '{var_name}'")
            ctx.emit("SWAP") # value, address -> address, value
            ctx.emit(f"STORE 0", f"Store value into address pointed by VAR param '{var_name}'")
        elif sym.scope_level == 0:
            ctx.emit(f"STOREG {sym.address_or_offset}", f"Store to global variable '{var_name}'")
        else:
            ctx.emit(f"STOREL {sym.address_or_offset}", f"Store to local/value_param '{var_name}'")
    else:
        ctx.emit(f"// Assignment to {type(node.variable).__name__} not implemented", "")


@register_visitor("IfStatement")
def visit_IfStatement(node):
    visit(node.condition)
    else_label = ctx.new_label("else")
    endif_label = ctx.new_label("endif")
    if node.else_statement:
        ctx.emit(f"JZ {else_label}", "If condition is false, jump to else")
    else:
        ctx.emit(f"JZ {endif_label}", "If condition is false (no else), jump to endif")
    visit(node.then_statement)
    if node.else_statement:
        ctx.emit(f"JUMP {endif_label}", "Skip else block")
        ctx.emit_label(else_label)
        visit(node.else_statement)
    ctx.emit_label(endif_label)

@register_visitor("WhileStatement")
def visit_WhileStatement(node):
    loop_start_label = ctx.new_label("whilestart")
    loop_end_label = ctx.new_label("whileend")
    ctx.emit_label(loop_start_label)
    visit(node.condition)
    ctx.emit(f"JZ {loop_end_label}", "If condition is false, exit while loop")
    visit(node.statement)
    ctx.emit(f"JUMP {loop_start_label}", "Repeat while loop")
    ctx.emit_label(loop_end_label)

@register_visitor("ForStatement")
def visit_ForStatement(node):
    control_var_name = node.control_variable.name
    sym_control_var = ctx.current_scope.resolve(control_var_name)
    if not sym_control_var:
        raise ValueError(f"FOR loop control variable '{control_var_name}' not defined.")
    if sym_control_var.kind not in ['variable', 'parameter'] or sym_control_var.is_var_param:
        raise ValueError(f"FOR loop control variable '{control_var_name}' must be a non-VAR variable or value parameter.")
    is_global_control_var = (sym_control_var.scope_level == 0)
    control_var_offset = sym_control_var.address_or_offset
    loop_check_label = ctx.new_label("forcheck")
    loop_end_label = ctx.new_label("forend")
    temp_end_val_storage_offset = new_temp_var_offset()
    visit(node.end_expression)
    ctx.emit(f"STOREL {temp_end_val_storage_offset}", f"Store evaluated end value of FOR loop for '{control_var_name}'")
    visit(node.start_expression)
    if is_global_control_var:
        ctx.emit(f"STOREG {control_var_offset}", f"Initialize FOR global control var '{control_var_name}'")
    else:
        ctx.emit(f"STOREL {control_var_offset}", f"Initialize FOR local control var '{control_var_name}'")
    ctx.emit_label(loop_check_label)
    if is_global_control_var:
        ctx.emit(f"PUSHG {control_var_offset}", f"Load global control var '{control_var_name}' for check")
    else:
        ctx.emit(f"PUSHL {control_var_offset}", f"Load local control var '{control_var_name}' for check")
    ctx.emit(f"PUSHL {temp_end_val_storage_offset}", "Load stored end value for check")
    if not node.downto:
        ctx.emit("INFEQ", f"Check {control_var_name} <= end_value")
        ctx.emit(f"JZ {loop_end_label}", f"If not ({control_var_name} <= end_value), exit loop")
    else:
        ctx.emit("SUPEQ", f"Check {control_var_name} >= end_value")
        ctx.emit(f"JZ {loop_end_label}", f"If not ({control_var_name} >= end_value), exit loop")
    visit(node.statement)
    if is_global_control_var:
        ctx.emit(f"PUSHG {control_var_offset}", f"Load global control var '{control_var_name}' for update")
    else:
        ctx.emit(f"PUSHL {control_var_offset}", f"Load local control var '{control_var_name}' for update")
    ctx.emit("PUSHI 1")
    if not node.downto:
        ctx.emit("ADD", f"Increment {control_var_name}")
    else:
        ctx.emit("SUB", f"Decrement {control_var_name}")
    if is_global_control_var:
        ctx.emit(f"STOREG {control_var_offset}", f"Store updated global control var '{control_var_name}'")
    else:
        ctx.emit(f"STOREL {control_var_offset}", f"Store updated local control var '{control_var_name}'")
    ctx.emit(f"JUMP {loop_check_label}")
    ctx.emit_label(loop_end_label)

@register_visitor("FieldAccess") # Assuming this is for records/objects, not implemented yet
def visit_FieldAccess(node):
    ctx.emit("# FieldAccess not fully implemented", "")

@register_visitor("Literal")
def visit_Literal(node):
    value = node.value
    if isinstance(value, bool):
        ctx.emit(f"PUSHI {1 if value else 0}")
    elif isinstance(value, int):
        ctx.emit(f"PUSHI {value}")
    elif isinstance(value, float):
        ctx.emit(f"PUSHF {value}")
    elif isinstance(value, str):
        escaped_value = value.replace('"', '\\"') # Basic escaping for quotes in string
        ctx.emit(f'PUSHS "{escaped_value}"')
    else:
        raise TypeError(f"Unsupported literal type: {type(value)} for value {value}")

@register_visitor("Identifier")
def visit_Identifier(node):
    var_name = node.name
    sym = ctx.current_scope.resolve(var_name)
    if not sym:
        raise ValueError(f"Undefined identifier '{var_name}' used as a value.")

    if sym.kind == 'variable':
        if sym.is_array: # Pushing base address of an array
            if sym.scope_level == 0:
                ctx.emit("PUSHGP", f"Push GP for global array '{var_name}' base address")
                ctx.emit(f"PUSHI {sym.address_or_offset}", f"Offset of global array '{var_name}'")
                ctx.emit("PADD", f"Calculate base address of global array '{var_name}'")
            else:
                ctx.emit("PUSHFP", f"Push FP for local array '{var_name}' base address")
                ctx.emit(f"PUSHI {sym.address_or_offset}", f"Offset of local array '{var_name}'")
                ctx.emit("PADD", f"Calculate base address of local array '{var_name}'")
        else: # Scalar variable
            if sym.scope_level == 0:
                ctx.emit(f"PUSHG {sym.address_or_offset}", f"Push global '{var_name}'")
            else:
                ctx.emit(f"PUSHL {sym.address_or_offset}", f"Push local '{var_name}'")
    elif sym.kind == 'parameter':
        if sym.is_var_param:
            # For VAR parameters, we push their address first.
            ctx.emit(f"PUSHL {sym.address_or_offset}", f"Push address from VAR param '{var_name}'")
            # If it's a scalar VAR parameter (not an array whose base address is needed by ArrayAccess),
            # its value is typically needed when it appears in an expression. So, dereference it.
            if not sym.is_array:
                ctx.emit(f"LOAD 0", f"Dereference scalar VAR param '{var_name}' to get its value")
        else: # Value parameter
            if sym.is_array: # Value parameter that is an array (copied)
                # Push the base address of the copied array on the stack frame
                ctx.emit("PUSHFP", f"Push FP for value param array '{var_name}' base address")
                ctx.emit(f"PUSHI {sym.address_or_offset}", f"Offset of value param array '{var_name}'")
                ctx.emit("PADD", f"Calculate base address of value param array '{var_name}'")
            else: # Scalar value parameter
                ctx.emit(f"PUSHL {sym.address_or_offset}", f"Push value of param '{var_name}'")
    elif sym.kind == 'constant':
        val = sym.address_or_offset # For constants, address_or_offset stores the actual value
        if isinstance(val, int): ctx.emit(f"PUSHI {val}")
        elif isinstance(val, float): ctx.emit(f"PUSHF {val}")
        elif isinstance(val, str): ctx.emit(f'PUSHS "{val.replace("\"", "\\\"")}"') # Basic escaping
        elif isinstance(val, bool): ctx.emit(f"PUSHI {1 if val else 0}")
        else: raise TypeError(f"Unsupported constant type for '{var_name}': {type(val)}")
    elif sym.kind == 'function': # Pushing function address (e.g. for passing as param, not direct call)
        ctx.emit(f"PUSHA {sym.address_or_offset}", f"Push address of function '{var_name}'")
    else:
        raise ValueError(f"Cannot use identifier '{var_name}' of kind '{sym.kind}' as a value here.")

@register_visitor("ArrayAccess")
def visit_ArrayAccess(node):
    # Check if accessing a string variable for CHARAT
    is_string_access = False
    string_sym = None
    if isinstance(node.array, ast_nodes.Identifier):
        string_sym = ctx.current_scope.resolve(node.array.name)
        if string_sym and string_sym.sym_type and string_sym.sym_type.upper() == 'STRING':
            is_string_access = True

    if is_string_access:
        var_name = node.array.name
        # Push the string value (heap address)
        if string_sym.scope_level == 0:
            ctx.emit(f"PUSHG {string_sym.address_or_offset}", f"Push global string '{var_name}'")
        else: # Local or param
            if string_sym.is_var_param: # VAR param string
                ctx.emit(f"PUSHL {string_sym.address_or_offset}", f"Load address from VAR param string '{var_name}'")
                ctx.emit("LOAD 0", f"Dereference VAR param to get string address for '{var_name}'")
            else: # Regular local string
                ctx.emit(f"PUSHL {string_sym.address_or_offset}", f"Push local string '{var_name}'")
        visit(node.index)
        # Assuming Pascal 1-based indexing for strings, adjust to 0-based for CHARAT
        ctx.emit("PUSHI 1", "Adjust for 1-based string indexing")
        ctx.emit("SUB", "Convert to 0-based for VM")
        ctx.emit("CHARAT", "Get character at index from string")
    else: # Regular array access
        # 1. Push base address of the array
        # visit(node.array) will push the base address if node.array is an Identifier of an array type
        # or if it's a VAR param that is an array (it pushes the address stored in the VAR param).
        visit(node.array) # Stack: [..., base_address]

        # 2. Push index value
        visit(node.index) # Stack: [..., base_address, user_index]

        # 3. Adjust index if array is not 0-indexed
        sym_array = None
        if isinstance(node.array, ast_nodes.Identifier): # Get symbol to check lower_bound
            sym_array = ctx.current_scope.resolve(node.array.name)
        
        # If sym_array is a VAR param, its .is_array, .array_lower_bound might not be directly set.
        # This needs careful handling in symbol table / type system for VAR params that are arrays.
        # For now, assume sym_array (if resolved) has the necessary info.
        if sym_array and sym_array.is_array and sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
            ctx.emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
            ctx.emit("SUB", "Adjust index to be 0-based for VM")
        # Stack: [..., base_address, adjusted_index]
        
        ctx.emit("LOADN", "Load value from array element")


@register_visitor("UnaryOperation")
def visit_UnaryOperation(node):
    visit(node.operand)
    op = node.operator.upper() # Standardize operator
    if op == 'NOT':
        ctx.emit("NOT")
    elif op == '-': # Negation
        # Check type of operand to decide if FNEG or integer negation
        operand_type = th.determine_expression_type(node.operand)
        if operand_type == 'REAL':
            # Assuming FNEG exists or use PUSHF 0.0, SWAP, FSUB
            ctx.emit("PUSHF 0.0")
            ctx.emit("SWAP")
            ctx.emit("FSUB", "Floating point negation")
        else: # Integer negation
            ctx.emit("PUSHI 0")
            ctx.emit("SWAP")
            ctx.emit("SUB", "Integer negation")
    elif op == '+': # Unary plus (no-op)
        pass
    else:
        raise ValueError(f"Unsupported unary operator: {node.operator}")

@register_visitor("BinaryOperation")
def visit_BinaryOperation(node):
    # Special handling for string char comparison: char_var = 'a'
    if node.operator == '=' and isinstance(node.right, ast_nodes.Literal) and \
        isinstance(node.right.value, str) and len(node.right.value) == 1:
        if isinstance(node.left, ast_nodes.ArrayAccess) and isinstance(node.left.array, ast_nodes.Identifier):
            left_array_sym = ctx.current_scope.resolve(node.left.array.name)
            if left_array_sym and left_array_sym.sym_type and left_array_sym.sym_type.upper() == 'STRING':
                # This is string_var[index] = 'char_literal'
                # Push char from string_var[index] (CHARAT gives ASCII)
                visit(node.left) # This will use visit_ArrayAccess for string, leaving ASCII on stack
                
                # Push ASCII of the char literal
                char_code = ord(node.right.value)
                ctx.emit(f"PUSHI {char_code}", f"ASCII for char literal '{node.right.value}'")
                
                ctx.emit("EQUAL", "Compare character ASCII codes")
                return # Handled

    visit(node.left)
    visit(node.right)
    
    original_op = node.operator
    op = original_op.upper()
    
    # Determine if float operation is needed
    # More robust type checking might be needed if types are mixed (e.g. INT + REAL)
    # For now, if either operand is REAL, assume float operation.
    left_expr_type = th.determine_expression_type(node.left)
    right_expr_type = th.determine_expression_type(node.right)
    
    # Promote to float if one is float and op supports it
    is_float_operation = False
    if op in ['+', '-', '*', '/']: # Arithmetic ops that have float versions
        if left_expr_type == 'REAL' or right_expr_type == 'REAL':
            is_float_operation = True
            # Implicit ITOF conversion if one is INT and other is REAL
            if left_expr_type == 'INTEGER' and right_expr_type == 'REAL':
                # Right is already on top. Left needs conversion.
                # Stack: [left_val(int), right_val(real)]
                # Need to convert left_val. This requires stack manipulation.
                # SWAP, ITOF, SWAP
                ctx.emit("SWAP") # [right_val(real), left_val(int)]
                ctx.emit("ITOF", "Convert left operand to float") # [right_val(real), left_val(float)]
                ctx.emit("SWAP") # [left_val(float), right_val(real)]
            elif left_expr_type == 'REAL' and right_expr_type == 'INTEGER':
                # Stack: [left_val(real), right_val(int)]
                ctx.emit("ITOF", "Convert right operand to float") # [left_val(real), right_val(float)]

    # Relational operators also need type-aware versions
    is_float_comparison = False
    if op in ['<', '<=', '>', '>=', '=', '<>']:
        if left_expr_type == 'REAL' or right_expr_type == 'REAL':
            is_float_comparison = True
            # Similar ITOF logic as above if types are mixed
            if left_expr_type == 'INTEGER' and right_expr_type == 'REAL':
                ctx.emit("SWAP"); ctx.emit("ITOF"); ctx.emit("SWAP")
            elif left_expr_type == 'REAL' and right_expr_type == 'INTEGER':
                ctx.emit("ITOF")


    if op == '+': ctx.emit("FADD" if is_float_operation else "ADD")
    elif op == '-': ctx.emit("FSUB" if is_float_operation else "SUB")
    elif op == '*': ctx.emit("FMUL" if is_float_operation else "MUL")
    elif op == '/': ctx.emit("FDIV") # Pascal '/' is always real division
    elif op == 'DIV': ctx.emit("DIV") # Integer division
    elif op == 'MOD': ctx.emit("MOD")
    elif op == '=':
        # String equality check (if not char comparison handled above)
        if left_expr_type == 'STRING' and right_expr_type == 'STRING':
            ctx.emit("EQUAL", "String comparison (EQUAL assumes addresses or specific VM support)") # Or STRCMP if available
        else:
            ctx.emit("FEQUAL" if is_float_comparison else "EQUAL")
    elif op == '<': ctx.emit("FINF" if is_float_comparison else "INF")
    elif op == '<=': ctx.emit("FINFEQ" if is_float_comparison else "INFEQ")
    elif op == '>': ctx.emit("FSUP" if is_float_comparison else "SUP")
    elif op == '>=': ctx.emit("FSUPEQ" if is_float_comparison else "SUPEQ")
    elif op == '<>':
        if left_expr_type == 'STRING' and right_expr_type == 'STRING':
            ctx.emit("EQUAL") # Or STRCMP
        else:
            ctx.emit("FEQUAL" if is_float_comparison else "EQUAL")
        ctx.emit("NOT")
    elif op == 'AND': ctx.emit("AND")
    elif op == 'OR': ctx.emit("OR")
    else:
        raise ValueError(f"Unsupported binary operator: {original_op}")

@register_visitor("FunctionCall")
def visit_FunctionCall(node):
    func_name_original = node.name
    func_name_lower = func_name_original.lower()
    func_sym = ctx.current_scope.resolve(func_name_lower) # Try lowercase for builtins
    if not func_sym:
        func_sym = ctx.current_scope.resolve(func_name_original) # Try original case
    if not func_sym:
        raise ValueError(f"Call to undefined function/procedure '{func_name_original}'.")
    if func_sym.kind not in ['function', 'procedure']:
        raise ValueError(f"'{func_name_original}' is not callable (kind: {func_sym.kind}).")

    num_actual_args = len(node.arguments) if node.arguments else 0
    def check_args(expected_count, func_display_name):
        if num_actual_args != expected_count:
            raise ValueError(f"Function '{func_display_name}' expects {expected_count} argument(s), got {num_actual_args}.")
        return node.arguments[0] if expected_count > 0 else None

    # Built-in routines
    if func_sym.address_or_offset and isinstance(func_sym.address_or_offset, str) and func_sym.address_or_offset.startswith("BUILTIN_"):
        builtin_name = func_sym.address_or_offset
        if builtin_name == "BUILTIN_WRITELN":
            if not node.arguments: ctx.emit("WRITELN")
            else:
                for arg_expr in node.arguments:
                    visit(arg_expr)
                    arg_type = th.determine_expression_type(arg_expr)
                    if arg_type == 'STRING': ctx.emit("WRITES")
                    elif arg_type == 'REAL': ctx.emit("WRITEF")
                    elif arg_type == 'INTEGER': ctx.emit("WRITEI")
                    elif arg_type == 'BOOLEAN': ctx.emit("WRITEI") # 0 or 1
                    elif arg_type == 'CHAR': ctx.emit("WRITECHR") # Assuming WRITECHR for ASCII value
                    else: ctx.emit("WRITEI", f"Defaulting to WRITEI for unknown type {arg_type}")
                ctx.emit("WRITELN")
            return
        elif builtin_name == "BUILTIN_LENGTH":
            arg = check_args(1, func_name_original)
            if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str): # Constant folding
                ctx.emit(f"PUSHI {len(arg.value)}", f"Folded Length('{arg.value}')")
            else:
                visit(arg); ctx.emit("STRLEN", f"VM STRLEN for {func_name_original}")
            return
        # Add other builtins like UPPERCASE, LOWERCASE, ABS, SQR, SQRT, PRED, SUCC here
        # Example for ABS:
        elif builtin_name == "BUILTIN_ABS":
            arg_node = check_args(1, func_name_original)
            visit(arg_node) # Value on stack
            arg_type = th.determine_expression_type(arg_node)
            abs_end_label = ctx.new_label("abs_end")
            if arg_type == "INTEGER":
                ctx.emit("DUP 0"); ctx.emit("PUSHI 0"); ctx.emit("INF") # val, (val < 0)
                ctx.emit(f"JZ {abs_end_label}") # If not (val < 0), jump to end
                ctx.emit("PUSHI 0"); ctx.emit("SWAP"); ctx.emit("SUB") # Negate
            elif arg_type == "REAL":
                ctx.emit("DUP 0"); ctx.emit("PUSHF 0.0"); ctx.emit("FINF")
                ctx.emit(f"JZ {abs_end_label}")
                ctx.emit("PUSHF 0.0"); ctx.emit("SWAP"); ctx.emit("FSUB")
            else: raise TypeError(f"Unsupported type {arg_type} for ABS.")
            ctx.emit_label(abs_end_label)
            return
        # SQR
        elif builtin_name == "BUILTIN_SQR":
            arg_node = check_args(1, func_name_original)
            visit(arg_node)
            arg_type = th.determine_expression_type(arg_node)
            ctx.emit("DUP 0")
            if arg_type == "INTEGER": ctx.emit("MUL")
            elif arg_type == "REAL": ctx.emit("FMUL")
            else: raise TypeError(f"Unsupported type {arg_type} for SQR.")
            return
        # PRED
        elif builtin_name == "BUILTIN_PRED":
            arg_node = check_args(1, func_name_original)
            visit(arg_node) # Pushes integer or char (ASCII)
            ctx.emit("PUSHI 1"); ctx.emit("SUB")
            return
        # SUCC
        elif builtin_name == "BUILTIN_SUCC":
            arg_node = check_args(1, func_name_original)
            visit(arg_node) # Pushes integer or char (ASCII)
            ctx.emit("PUSHI 1"); ctx.emit("ADD")
            return
        else:
            ctx.emit(f"// Builtin {builtin_name} call not fully implemented in generator", "")
            if node.arguments:
                for arg_expr in node.arguments: visit(arg_expr)
            return

    # User-defined function/procedure
    num_expected_params = len(func_sym.params_info)
    if num_expected_params != num_actual_args:
        raise ValueError(f"Arg count mismatch for {func_name_original}: expected {num_expected_params}, got {num_actual_args}")
    if node.arguments:
        for i, arg_expr in enumerate(node.arguments):
            param_info = func_sym.params_info[i]
            if param_info.is_var_param:
                if not isinstance(arg_expr, ast_nodes.Identifier): # VAR param must be an l-value (identifier for now)
                    # Could also be ArrayAccess or FieldAccess if those are assignable
                    raise ValueError(f"VAR-parameter argument for '{param_info.name}' must be an assignable variable, not {type(arg_expr).__name__}.")
                arg_sym = ctx.current_scope.resolve(arg_expr.name)
                if not arg_sym:
                    raise ValueError(f"Undefined variable '{arg_expr.name}' for VAR param.")
                if arg_sym.scope_level == 0: # Global var
                    ctx.emit("PUSHGP", "Push global base for VAR param")
                    ctx.emit(f"PUSHI {arg_sym.address_or_offset}", f"Offset of global var '{arg_expr.name}'")
                    ctx.emit("PADD", f"Compute address of global var '{arg_expr.name}'")
                else: # Local variable or another VAR param
                    if arg_sym.is_var_param: # Passing a VAR param to another VAR param
                        ctx.emit(f"PUSHL {arg_sym.address_or_offset}", f"Pass address from VAR param '{arg_expr.name}'")
                    else: # Regular local variable
                        ctx.emit("PUSHFP", "Push FP for VAR param")
                        ctx.emit(f"PUSHI {arg_sym.address_or_offset}", f"Offset of local var '{arg_expr.name}'")
                        ctx.emit("PADD", f"Compute address of local var '{arg_expr.name}'")
            else: # Value parameter
                visit(arg_expr)
    ctx.emit(f"PUSHA {func_sym.address_or_offset}", f"Push address of {func_name_original}")
    ctx.emit("CALL")


@register_visitor("IOCall") # Handles read, readln, write, writeln if they are distinct AST nodes
def visit_IOCall(node):
    op = node.operation.lower()
    if op in ["write", "writeln"]:
        if op == "writeln" and not node.arguments:
            ctx.emit("WRITELN")
            return
        for arg_expr in node.arguments:
            visit(arg_expr)
            arg_type = th.determine_expression_type(arg_expr)
            if arg_type == 'STRING': ctx.emit("WRITES")
            elif arg_type == 'REAL': ctx.emit("WRITEF")
            elif arg_type == 'INTEGER': ctx.emit("WRITEI")
            elif arg_type == 'BOOLEAN': ctx.emit("WRITEI")
            elif arg_type == 'CHAR': ctx.emit("WRITECHR") # Assuming WRITECHR for ASCII value
            else: ctx.emit("WRITEI", f"Defaulting WRITEI for unknown type {arg_type} in {op}")
        if op == "writeln":
            ctx.emit("WRITELN")

    elif op in ["read", "readln"]:
        for arg_var_node in node.arguments:
            # READ expects an l-value (variable, array element)
            # The VM's READ instruction likely pushes the string address read from input.
            # Then, conversion (ATOI, ATOF) happens, then STORE.

            if isinstance(arg_var_node, ast_nodes.Identifier):
                var_name = arg_var_node.name
                sym = ctx.current_scope.resolve(var_name)
                if not sym: raise ValueError(f"Undefined var '{var_name}' in {op}.")
                
                ctx.emit("READ", f"Read string input for '{var_name}'") # String address on TOS
                
                target_type = sym.sym_type.upper() if sym.sym_type else 'UNKNOWN'
                if target_type == 'INTEGER': ctx.emit("ATOI")
                elif target_type == 'REAL': ctx.emit("ATOF")
                elif target_type == 'STRING': pass # Already a string address
                elif target_type == 'CHAR': # Read a string, take first char, get ASCII
                    ctx.emit("PUSHI 0"); ctx.emit("CHARAT") # Get ASCII of first char
                else: raise TypeError(f"Unsupported type {target_type} for {op} into '{var_name}'.")

                # Value to store is now on TOS. Store it.
                if sym.is_var_param:
                    ctx.emit(f"PUSHL {sym.address_or_offset}", f"Load address from VAR param '{var_name}'")
                    ctx.emit("SWAP"); ctx.emit("STORE 0", f"Store into VAR param '{var_name}'")
                elif sym.scope_level == 0:
                    ctx.emit(f"STOREG {sym.address_or_offset}", f"Store to global '{var_name}'")
                else:
                    ctx.emit(f"STOREL {sym.address_or_offset}", f"Store to local '{var_name}'")

            elif isinstance(arg_var_node, ast_nodes.ArrayAccess):
                # 1. Calculate base_address and adjusted_index for STOREN
                # Base address
                array_node = arg_var_node.array
                if not isinstance(array_node, ast_nodes.Identifier):
                    raise NotImplementedError(f"Reading into non-identifier array base in {op}")
                array_name = array_node.name
                sym_array = ctx.current_scope.resolve(array_name)
                if not sym_array or not (sym_array.is_array or sym_array.is_var_param): # VAR param could be array
                    raise ValueError(f"'{array_name}' not a defined array/VAR param for {op}.")

                if sym_array.is_var_param: # VAR param that is an array
                    ctx.emit(f"PUSHL {sym_array.address_or_offset}", f"Load address from VAR param array '{array_name}'")
                elif sym_array.scope_level == 0:
                    ctx.emit("PUSHGP"); ctx.emit(f"PUSHI {sym_array.address_or_offset}"); ctx.emit("PADD")
                else:
                    ctx.emit("PUSHFP"); ctx.emit(f"PUSHI {sym_array.address_or_offset}"); ctx.emit("PADD")
                # Stack: [..., base_address]
                
                # Index
                visit(arg_var_node.index) # Stack: [..., base_address, user_index]
                if sym_array.is_array and sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
                    ctx.emit(f"PUSHI {sym_array.array_lower_bound}"); ctx.emit("SUB")
                # Stack: [..., base_address, adjusted_index]

                # 2. Perform READ and convert
                ctx.emit("READ", f"Read string input for {array_name}[index]") # Stack: [..., base_addr, adj_idx, str_addr]
                
                element_type = 'UNKNOWN'
                if hasattr(sym_array, 'element_type') and sym_array.element_type:
                    element_type = str(sym_array.element_type).upper()
                # Add more robust element type detection if needed from sym_array.sym_type ("ARRAY OF ...")

                if element_type == 'INTEGER': ctx.emit("ATOI")
                elif element_type == 'REAL': ctx.emit("ATOF")
                elif element_type == 'STRING': pass
                elif element_type == 'CHAR': ctx.emit("PUSHI 0"); ctx.emit("CHARAT")
                else: raise TypeError(f"Unsupported element type {element_type} for {op} into {array_name}[].")
                # Stack: [..., base_addr, adj_idx, value_to_store]

                # 3. STOREN
                ctx.emit("STOREN", f"Store read value into {array_name}[index]")
            else:
                raise ValueError(f"Argument to {op} must be an identifier or array element. Got {type(arg_var_node).__name__}.")
        
        # If 'readln', consume rest of line. VM might do this with READ, or need separate instruction.
        # Assuming READ consumes the item and stops. If READLN needs to clear buffer, that's VM specific.
        if op == "readln":
            ctx.emit("// READLN might require additional VM op to consume rest of line if READ doesn't", "")