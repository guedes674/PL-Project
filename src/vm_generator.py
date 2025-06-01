import ast_nodes
from anasem import Symbol, SymbolTable, register_builtin_functions


code = [] # List to hold generated VM code
label_count = 0 # Counter for unique label generation
current_scope = SymbolTable(scope_name="global_init_phase") # Initial phase for global setup
temp_var_count = 0 # Counter for temporary variable offsets
globals_handled_pre_start = set() # To track globals processed before START

# Register built-in functions in the initial global scope
register_builtin_functions(current_scope)

# Switch to the main global scope after built-ins
current_scope = SymbolTable(parent=current_scope, scope_name="global")

def new_label(prefix="L"):
    label_count += 1
    return f"{prefix}{label_count - 1}"

# Generates a new temporary variable offset
def new_temp_var_offset(self):
    offset = current_scope.get_local_var_offset()
    emit(f"PUSHI 0", f"Allocate temp var at FP+{offset}")
    return offset

# Emits a VM instruction with an optional comment
def emit(instruction, comment=None):
    indent = "    " 
    if comment:
        code.append(f"{indent}{instruction} // {comment}")
    else:
        code.append(f"{indent}{instruction}")

# Emits a label for jumps
def emit_label(label):
    code.append(f"{label}:")

# Pushes a new scope onto the stack
def push_scope(scope_name="local"):
    new_scope = SymbolTable(parent=current_scope, scope_name=scope_name)
    current_scope = new_scope

# Pops the current scope, returning to the parent scope
def pop_scope(self):
    if current_scope.parent:
        # Ensure we don't pop past the main global scope established after builtins
        if current_scope.parent.scope_name == "global_init_phase":
            pass  # effectively at main global, parent is the init_phase sentinel
        else:
            current_scope = current_scope.parent
    else:
        print("Warning: Popping global scope (should not happen).")

# Generates the VM code for the entire AST
def generate(node):
    visit(node)
    return code

# Visitor pattern to traverse the AST
def visit(node):
    if node is None:
        return
    method_name = f'visit_{type(node).__name__}'
    visitor = getattr(method_name, generic_visit)
    return visitor(node)

# Generic visitor method for nodes without a specific visit method
def generic_visit(node):
    print(f"Warning: No visitor method for {type(node).__name__}")
    if hasattr(node, '__dict__'):
        for _, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, '__class__'): # Basic check for AST nodes
                        visit(item)
            elif hasattr(value, '__class__'): # Basic check for AST nodes
                visit(value)

def process_array_type(var_type_node): # var_type_node is now expected to be an AST node
    is_array_type = False
    array_size = 1
    lower_bound = 0
    element_type_str = None # To store the element type string

    if isinstance(var_type_node, ast_nodes.ArrayType):
        start_node = var_type_node.index_range[0] # Should be a Literal node
        end_node = var_type_node.index_range[1]   # Should be a Literal node
        
        if isinstance(start_node, ast_nodes.Literal) and isinstance(start_node.value, int) and \
            isinstance(end_node, ast_nodes.Literal) and isinstance(end_node.value, int):
            
            low = start_node.value
            high = end_node.value
            if high < low:
                raise ValueError(f"Array upper bound {high} less than lower bound {low}")
            array_size = high - low + 1
            lower_bound = low
            is_array_type = True
            
            # Extract element type (assuming it's stored as a string in ArrayType)
            if isinstance(var_type_node.element_type, str):
                element_type_str = var_type_node.element_type.upper()
            # Add more sophisticated handling if element_type can be other AST nodes
        else:
            raise TypeError("Array bounds in ast_nodes.ArrayType must be integer literals.")
    # You can remove the `elif isinstance(var_type_node, str):` block 
    # if anasin.py now reliably produces ArrayType nodes.
    
    return is_array_type, array_size, lower_bound, element_type_str # Return element_type_str

def type_node_to_string(var_type_node):
    """
    Helper function to convert a variable type AST node or string to a string representation.
    This is useful for symbol creation where we need a clear type string.
    """
    if isinstance(var_type_node, ast_nodes.ArrayType):
        # For array types, we might want to show the element type and bounds
        is_array, size, low_b, elem_type = process_array_type(var_type_node)
        if is_array and elem_type: # Ensure elem_type is not None
            return f"ARRAY OF {elem_type.upper()}" 
        elif is_array:
            return "ARRAY OF UNKNOWN_ELEMENT_TYPE" # Fallback if element type couldn't be determined
    elif isinstance(var_type_node, str): # Handle scalar types passed as strings
        return var_type_node.upper() # e.g., "INTEGER", "REAL"
    # Add more cases as needed for other complex type nodes if you introduce them
    # e.g., elif isinstance(var_type_node, ast_nodes.RecordType):
    #          return "RECORD" 

    # Fallback if it's an AST node type not handled above or an unexpected type
    if hasattr(var_type_node, '__class__'):
        # Attempt to get a string representation if it's some other AST node
        # This might need refinement based on your other AST node types
        type_name_guess = str(var_type_node) 
        # Avoid overly long or complex default strings from __repr__
        if len(type_name_guess) > 30: # Arbitrary length limit
                return f"COMPLEX_TYPE_{var_type_node.__class__.__name__.upper()}"
        return type_name_guess.upper()

    return "UNKNOWN_TYPE"

def visit_Program(node):
    # Phase 1: Define global symbols and emit PUSHI 0 for global variables BEFORE START.

    if node.block and node.block.declarations:
        # Handle global variable declarations before START
        for decl in node.block.declarations:

            # Check if the declaration is a VariableDeclaration
            if isinstance(decl, ast_nodes.VariableDeclaration):

                # Process each variable in the declaration list
                for var_info in decl.variable_list:
                    # Use type_node_to_string for a consistent sym_type string
                    var_type_for_symbol_str = type_node_to_string(var_info.var_type) 
                    
                    is_array_type, array_size, lower_bound, actual_element_type_str = process_array_type(var_info.var_type)
                    
                    # Now process each variable ID in the declaration
                    for var_id_str in var_info.id_list:

                        offset = current_scope.get_local_var_offset(count=array_size)
                        sym = Symbol(var_id_str, 
                                        var_type_for_symbol_str, # Use consistent type string
                                        'variable', 
                                        offset, 
                                        scope_level=0,
                                        is_array=is_array_type, 
                                        array_lower_bound=lower_bound if is_array_type else None,
                                        array_element_count=array_size if is_array_type else None,
                                        element_type=actual_element_type_str if is_array_type else None) # Pass element_type
                        current_scope.define(sym)
                        globals_handled_pre_start.add(var_id_str)

                        # Emit code to initialize global variables
                        if is_array_type:
                            emit(f"PUSHN {array_size}", f"Reserve space for global array '{var_id_str}' (gp[{offset}..])")
                        else:
                            emit(f"PUSHI 0", f"Initial stack value for global '{var_id_str}' (gp[{offset}])")
    
    # Emit START instruction
    emit("START", "Initialize Frame Pointer = Stack Pointer")
    
    # Phase 2: Process the rest of the block (constants, functions, main compound statement)
    visit(node.block)
    
    emit("STOP", "End of program")

def visit_ProgramHeader(node):
    pass

# ────────  Blocks ─────────────────────────────────────────────
def visit_Block(node):
    function_procedure_nodes = []
    declarations_for_this_block_pass = []

    # Handle declarations in the block
    if node.declarations:
        for decl in node.declarations:

            # Handle function/procedure declarations separately
            if isinstance(decl, (ast_nodes.FunctionDeclaration, ast_nodes.ProcedureDeclaration)):
                function_procedure_nodes.append(decl)
            else:
                # All other declarations (Variables, Constants, Types, etc.)
                # The actual filtering for variables will happen in visit_VariableDeclaration using globals_handled_pre_start
                declarations_for_this_block_pass.append(decl)
    
    # Process declarations not handled pre-START (e.g., constants)
    for decl_node in declarations_for_this_block_pass:
        visit(decl_node) # This calls visit_VariableDeclaration, visit_ConstantDeclaration etc.

    main_code_label = None
    # If there are function/procedure declarations, we need to jump over them
    if function_procedure_nodes:
        main_code_label = new_label("mainLabel")
        emit(f"JUMP {main_code_label}", "Jump over nested function/proc definitions")

    # Now visit all function/procedure declarations
    for fp_node in function_procedure_nodes:
        visit(fp_node)

    # If we have a main code label, emit it now
    if main_code_label:
        emit_label(main_code_label)
    
    # Finally, visit the main compound statement of the block
    if node.compound_statement:
        visit(node.compound_statement)

# ────────  Declarations ──────────────────────────────────────
def visit_VariableDeclaration(node):
    for var_info in node.variable_list:

        # Use type_node_to_string for a consistent sym_type string
        var_type_for_symbol_str = type_node_to_string(var_info.var_type)
        
        is_array_type, array_size, lower_bound, actual_element_type_str = process_array_type(var_info.var_type)

        # Now process each variable ID in the declaration
        for var_id_str in var_info.id_list:

            # Check if this variable was already handled pre-START
            if var_id_str in globals_handled_pre_start:
                continue 

            if current_scope.parent is None or current_scope.parent.scope_name == "global_init_phase":
                # This path for globals not handled pre-start (should be rare with new logic)
                offset = current_scope.get_local_var_offset(count=array_size)
                sym_check = current_scope.resolve(var_id_str)
                if not sym_check:
                    sym = Symbol(var_id_str, 
                                    var_type_for_symbol_str, 
                                    'variable', 
                                    offset, 
                                    scope_level=0,
                                    is_array=is_array_type, 
                                    array_lower_bound=lower_bound if is_array_type else None,
                                    array_element_count=array_size if is_array_type else None,
                                    element_type=actual_element_type_str if is_array_type else None) # Pass element_type
                    current_scope.define(sym)
                
                if is_array_type:
                    emit(f"// Global array '{var_id_str}' (gp[{offset}..]) defined (post-START init)", "")
                    # Allocation for globals should ideally happen via PUSHN before START
                    # or by VM convention for global memory. STOREG would be for individual elements.
                    # For simplicity, if we reach here, we might assume it's already "allocated"
                    # and PUSHI 0 / STOREG is for initializing first element, which is not right for arrays.
                    # This branch needs careful review if hit for arrays.
                    emit(f"// Warning: Post-START global array declaration for {var_id_str} - review allocation")

                else: # Scalar global not handled pre-start
                    emit(f"PUSHI 0", f"Default value for global '{var_id_str}'")
                    emit(f"STOREG {offset}", f"Initialize global '{var_id_str}' to 0")
            else: # Local variable (inside function/procedure)
                offset = current_scope.get_local_var_offset(count=array_size)
                sym = Symbol(var_id_str, 
                                var_type_for_symbol_str, 
                                'variable', 
                                offset, 
                                scope_level=1, # Corrected scope_level for local vars
                                is_array=is_array_type, 
                                array_lower_bound=lower_bound if is_array_type else None,
                                array_element_count=array_size if is_array_type else None,
                                element_type=actual_element_type_str if is_array_type else None) # Pass element_type
                current_scope.define(sym)
                if is_array_type:
                    emit(f"PUSHN {array_size}", f"Allocate {array_size} slots for local array '{var_id_str}' at FP+{offset}")
                else:
                    emit(f"PUSHI 0", f"Allocate space for local var '{var_id_str}' at FP+{offset}")

def visit_ConstantDeclaration(node):
    for const_def in node.constant_list:
        raw_value = const_def.value.value # Assuming const_def.value is a Literal AST node
        typ = str(type(raw_value).__name__).upper() # Or derive from const_def.value.type if available
        sym = Symbol(const_def.name, typ, 'constant', raw_value, current_scope.scope_level)
        current_scope.define(sym)
        emit(f"// Constant '{const_def.name}' defined as {raw_value}", "") # No PUSHI for const declaration

def visit_FunctionDeclaration(node):
    func_label = new_label(f"func{node.name}") # Changed from func_
    return_type_str = str(node.return_type) if node.return_type else "VOID"

    # 1) Build parameter‐signature symbols (in parent scope) so that calls to this function will resolve
    param_symbols_for_signature = []
    if node.parameter_list:
        for param_group in node.parameter_list:
            param_type_str = str(param_group.param_type)
            for pid in param_group.id_list:
                param_symbols_for_signature.append(
                    Symbol(pid, param_type_str, 'parameter', 0, is_var_param=param_group.is_var)
                )

    func_sym = Symbol(
        node.name,
        return_type_str,
        'function',
        func_label,
        params_info=param_symbols_for_signature,
        return_type=return_type_str
    )
    current_scope.define(func_sym)

    # 2) Emit the function label + open a new scope
    emit_label(func_label)
    push_scope(scope_name=f"func_{node.name}")

    # 3) In the new scope, define each parameter at a negative offset
    if node.parameter_list:
        for param_group in reversed(node.parameter_list):
            for param_id_str in reversed(param_group.id_list):
                param_type_str = str(param_group.param_type)
                offset = current_scope.get_param_offset()
                param_sym = Symbol(
                    param_id_str,
                    param_type_str,
                    'parameter',
                    offset,
                    scope_level=1,
                    is_var_param=param_group.is_var
                )
                current_scope.define(param_sym)
                emit(f"// Param '{param_id_str}' at FP{offset}", "")

    # 4) Allocate space for local variables in the function
    if node.block:
        for decl in node.block.declarations:
            if isinstance(decl, ast_nodes.VariableDeclaration):
                visit(decl)

    # 5) Emit the function body
    if node.block:
        visit(node.block.compound_statement)

    # 6) Emit RETURN and pop the function’s scope
    emit("RETURN", f"Return from function {node.name}")
    pop_scope()

def visit_ProcedureDeclaration(node):
    proc_label = new_label(f"proc{node.name}") # Changed from proc_

    param_symbols_for_signature = []
    if node.parameter_list:
        for param_group in node.parameter_list:
            param_type_str = str(param_group.param_type)
            for pid in param_group.id_list:
                param_symbols_for_signature.append(
                    Symbol(pid, param_type_str, 'parameter', 0, is_var_param=param_group.is_var)
                )

    proc_sym = Symbol(node.name, "VOID", 'procedure', proc_label, params_info=param_symbols_for_signature)
    current_scope.define(proc_sym)

    emit_label(proc_label)
    push_scope(scope_name=f"proc_{node.name}")

    if node.parameter_list:
        for param_group in reversed(node.parameter_list):
            for param_id_str in reversed(param_group.id_list):
                param_type_str = str(param_group.param_type)
                offset = current_scope.get_param_offset()
                param_sym = Symbol(
                    param_id_str,
                    param_type_str,
                    'parameter',
                    offset,
                    scope_level=1,
                    is_var_param=param_group.is_var
                )
                current_scope.define(param_sym)
                emit(f"// Param '{param_id_str}' at FP{offset}", "")

    if node.block:
        for decl in node.block.declarations:
            if isinstance(decl, ast_nodes.VariableDeclaration):
                visit(decl)

    if node.block:
        visit(node.block.compound_statement)

    emit("RETURN", f"Return from procedure {node.name}")
    pop_scope()

# ────────  Statements ─────────────────────────────────────────
def visit_CompoundStatement(node):
    for stmt in node.statement_list:
        visit(stmt)

def visit_AssignmentStatement(node):
    if isinstance(node.variable, ast_nodes.ArrayAccess):
        # Array assignment: MyArray[index] := expression
        # Stack for STOREN: base_address, adjusted_index, value_RHS

        # 1. Evaluate RHS and it will be on top of stack
        visit(node.expression) # Stack: [..., value_RHS]

        # 2. Calculate base address of array
        array_node_for_addr = node.variable.array # This is usually an Identifier
        if not isinstance(array_node_for_addr, ast_nodes.Identifier):
            raise NotImplementedError("Assignment to non-identifier array base not implemented")
        
        array_name = array_node_for_addr.name
        sym_array = current_scope.resolve(array_name)
        if not sym_array or not sym_array.is_array:
            raise ValueError(f"'{array_name}' is not a defined array for assignment.")

        if sym_array.scope_level == 0: # Global array
            emit("PUSHGP", f"Push GP for global array '{array_name}' base")
            emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of global array '{array_name}'")
            emit("PADD", f"Calculate base address of global array '{array_name}'")
        else: # Local array
            emit("PUSHFP", f"Push FP for local array '{array_name}' base")
            emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of local array '{array_name}'")
            emit("PADD", f"Calculate base address of local array '{array_name}'")
        # Stack: [..., value_RHS, calculated_base_address]

        # 3. Evaluate and adjust index
        visit(node.variable.index) # Stack: [..., value_RHS, calculated_base_address, user_index]
        if sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
            emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
            emit("SUB", "Adjust index to be 0-based for VM")
        # Stack: [..., value_RHS, calculated_base_address, adjusted_index]

        # Reorder stack for STOREN: [base_address, adjusted_index, value_RHS]
        # Current: [value_RHS, base_address, adjusted_index] (TOS)
        # SWAP ->  [value_RHS, adjusted_index, base_address]
        # SWAP (top two again, effectively rotating value_RHS to bottom of these three)
        # This needs careful stack manipulation or temporary storage.
        # Let's use a temp var for RHS value as it's safer.

        # Re-evaluate with temp storage for RHS for clarity and safety:
        # 1. Evaluate RHS and store it temporarily
        visit(node.expression) # value_RHS on stack
        temp_rhs_offset = new_temp_var_offset() # Allocates PUSHI 0, returns offset
        emit(f"STOREL {temp_rhs_offset}", "Store RHS temporarily for array assignment")

        # 2. Calculate base address of array (as above)
        if sym_array.scope_level == 0:
            emit("PUSHGP", f"Push GP for global array '{array_name}' base")
            emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of global array '{array_name}'")
            emit("PADD", f"Calculate base address of global array '{array_name}'")
        else:
            emit("PUSHFP", f"Push FP for local array '{array_name}' base")
            emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of local array '{array_name}'")
            emit("PADD", f"Calculate base address of local array '{array_name}'")
        # Stack: [..., calculated_base_address]

        # 3. Evaluate and adjust index (as above)
        visit(node.variable.index) # Stack: [..., calculated_base_address, user_index]
        if sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
            emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
            emit("SUB", "Adjust index to be 0-based for VM")
        # Stack: [..., calculated_base_address, adjusted_index]

        # 4. Reload RHS value
        emit(f"PUSHL {temp_rhs_offset}", "Reload RHS for array assignment")
        # Stack: [..., calculated_base_address, adjusted_index, value_RHS]
        
        emit("STOREN", "Store to array element")
        # Deallocate temp_rhs_offset? If new_temp_var_offset just uses current_scope.get_local_var_offset,
        # it's part of the frame and will be popped. If it's a dedicated temp area, manage it.
        # Assuming it's part of the local frame for now.

    elif isinstance(node.variable, ast_nodes.Identifier):
        # First, evaluate the right-hand side expression to get its value on the stack
        visit(node.expression)
        
        var_name = node.variable.name
        sym = current_scope.resolve(var_name)
        if not sym:
            raise ValueError(f"Undefined variable '{var_name}' in assignment.")

        is_function_return_assignment = False
        if sym.kind == 'function':
            if current_scope.scope_name == f"func_{sym.name}":
                is_function_return_assignment = True
        
        if is_function_return_assignment:
            emit(f"// Assignment to function name '{var_name}', value on TOS for return", "")
        elif sym.is_var_param:
            emit(f"PUSHL {sym.address_or_offset}", f"Load address from VAR param '{var_name}'") 
            emit("SWAP") 
            emit(f"STORE 0", f"Store value into address pointed by VAR param '{var_name}'")
        elif sym.scope_level == 0: 
            emit(f"STOREG {sym.address_or_offset}", f"Store to global variable '{var_name}'")
        else: 
            emit(f"STOREL {sym.address_or_offset}", f"Store to local/value_param '{var_name}'")
    else:
        emit(f"// Assignment to {type(node.variable).__name__} not implemented", "")

def visit_IfStatement(node):
    visit(node.condition)
    else_label = new_label("else")
    endif_label = new_label("endif")

    if node.else_statement:
        emit(f"JZ {else_label}", "If condition is false, jump to else")
    else:
        emit(f"JZ {endif_label}", "If condition is false (no else), jump to endif")

    visit(node.then_statement)
    if node.else_statement:
        emit(f"JUMP {endif_label}", "Skip else block")
        emit_label(else_label)
        visit(node.else_statement)

    emit_label(endif_label)

def visit_WhileStatement(node):
    loop_start_label = new_label("whilestart")
    loop_end_label = new_label("whileend")

    emit_label(loop_start_label)
    visit(node.condition)
    emit(f"JZ {loop_end_label}", "If condition is false, exit while loop")
    visit(node.statement)
    emit(f"JUMP {loop_start_label}", "Repeat while loop")
    emit_label(loop_end_label)

def visit_ForStatement(node):
    # Resolve control variable
    control_var_name = node.control_variable.name
    sym_control_var = current_scope.resolve(control_var_name)

    if not sym_control_var:
        raise ValueError(f"FOR loop control variable '{control_var_name}' not defined.")
    if sym_control_var.kind not in ['variable', 'parameter'] or sym_control_var.is_var_param:
        # Parameters can be loop counters if they are value parameters. VAR parameters cannot.
        raise ValueError(f"FOR loop control variable '{control_var_name}' must be a non-VAR variable or value parameter.")

    is_global_control_var = (sym_control_var.scope_level == 0)
    control_var_offset = sym_control_var.address_or_offset

    # Labels for the loop
    loop_check_label = new_label("forcheck")
    loop_end_label = new_label("forend")

    # 1. Evaluate and store the end expression value using new_temp_var_offset
    # This method properly allocates space and returns the offset
    temp_end_val_storage_offset = new_temp_var_offset()
    
    visit(node.end_expression) # Evaluate the end expression, its value is now on TOS
    emit(f"STOREL {temp_end_val_storage_offset}", f"Store evaluated end value of FOR loop for '{control_var_name}'")

    # 2. Initialize control variable with the start expression's value
    visit(node.start_expression) # Evaluate start expression, value on TOS

    if is_global_control_var:
        emit(f"STOREG {control_var_offset}", f"Initialize FOR global control var '{control_var_name}'")
    else:
        emit(f"STOREL {control_var_offset}", f"Initialize FOR local control var '{control_var_name}'")

    # 3. Loop check point (label for the start of each iteration's check)
    emit_label(loop_check_label)

    # 4. Load current value of control variable onto stack
    if is_global_control_var:
        emit(f"PUSHG {control_var_offset}", f"Load global control var '{control_var_name}' for check")
    else:
        emit(f"PUSHL {control_var_offset}", f"Load local control var '{control_var_name}' for check")

    # 5. Load stored end expression value onto stack
    emit(f"PUSHL {temp_end_val_storage_offset}", "Load stored end value for check")

    # 6. Perform comparison. Stack: [control_var_current_value, stored_end_value]
    #    If the condition for continuing the loop is false (0), jump to loop_end_label.
    if not node.downto:  # TO loop: continues if control_var <= end_value
        emit("INFEQ", f"Check {control_var_name} <= end_value") # Pushes 1 if true, 0 if false
        emit(f"JZ {loop_end_label}", f"If not ({control_var_name} <= end_value), exit loop")
    else:  # DOWNTO loop: continues if control_var >= end_value
        emit("SUPEQ", f"Check {control_var_name} >= end_value") # Pushes 1 if true, 0 if false
        emit(f"JZ {loop_end_label}", f"If not ({control_var_name} >= end_value), exit loop")

    # 7. Execute loop body
    visit(node.statement)

    # 8. Increment/Decrement control variable
    # Load current value of control variable
    if is_global_control_var:
        emit(f"PUSHG {control_var_offset}", f"Load global control var '{control_var_name}' for update")
    else:
        emit(f"PUSHL {control_var_offset}", f"Load local control var '{control_var_name}' for update")
    
    emit("PUSHI 1") # Push 1 for increment/decrement
    if not node.downto:
        emit("ADD", f"Increment {control_var_name}")
    else:
        emit("SUB", f"Decrement {control_var_name}")
    
    # Store updated value back into control variable
    if is_global_control_var:
        emit(f"STOREG {control_var_offset}", f"Store updated global control var '{control_var_name}'")
    else:
        emit(f"STOREL {control_var_offset}", f"Store updated local control var '{control_var_name}'")

    # 9. Jump back to the loop check
    emit(f"JUMP {loop_check_label}")

    # 10. Loop end point
    emit_label(loop_end_label)

    # The temporary variable for the end_value (temp_end_val_storage_offset) was allocated
    # on the current function's stack frame. It will be deallocated automatically when
    # the function returns and its stack frame is popped.

def visit_FieldAccess(node):
    emit("# FieldAccess not fully implemented", "")

# ────────  Expressions ────────────────────────────────────────
def visit_Literal(node):
    value = node.value
    if isinstance(value, bool):  # Check for bool first
        emit(f"PUSHI {1 if value else 0}")
    elif isinstance(value, int): # Now, this will only catch non-boolean integers
        emit(f"PUSHI {value}")
    elif isinstance(value, float):
        emit(f"PUSHF {value}")
    elif isinstance(value, str):
        escaped_value = value.replace('"', '\\"')
        emit(f'PUSHS "{escaped_value}"')
    else:
        raise TypeError(f"Unsupported literal type: {type(value)} for value {value}")

def visit_Identifier(node):
    var_name = node.name
    sym = current_scope.resolve(var_name)
    if not sym:
        raise ValueError(f"Undefined identifier '{var_name}' used as a value.")

    if sym.kind == 'variable':
        if sym.is_array:
            # When an array identifier is used directly as a value, it means its base address.
            # This is consistent with how visit_ArrayAccess now expects the base address.
            if sym.scope_level == 0: # Global array
                emit("PUSHGP", f"Push GP for global array '{var_name}' base address")
                emit(f"PUSHI {sym.address_or_offset}", f"Offset of global array '{var_name}'")
                emit("PADD", f"Calculate base address of global array '{var_name}'")
            else: # Local array
                emit("PUSHFP", f"Push FP for local array '{var_name}' base address")
                emit(f"PUSHI {sym.address_or_offset}", f"Offset of local array '{var_name}'")
                emit("PADD", f"Calculate base address of local array '{var_name}'")
        else: # Scalar variable
            if sym.scope_level == 0:
                emit(f"PUSHG {sym.address_or_offset}", f"Push global '{var_name}'")
            else:
                emit(f"PUSHL {sym.address_or_offset}", f"Push local '{var_name}'")
    elif sym.kind == 'parameter':
        if sym.is_var_param: # VAR param could be an array passed by reference
            emit(f"PUSHL {sym.address_or_offset}", f"Push address from VAR param '{var_name}'")
            # If this VAR param is an array and is being used in ArrayAccess, PUSHL gives its address.
            # If it's being dereferenced for its value (e.g. x := var_param_array[i] is not this path,
            # but if it was simple_var := var_param_scalar), then LOAD 0 is needed.
            # Context is key. For ArrayAccess, visit_Identifier for the array name should push its base address.
            # If a VAR param *IS* an array, PUSHL pushes the address of that original array. This is correct.
        else: # Value parameter
            if sym.is_array: # Value parameter that is an array (Pascal copies arrays for value params)
                # This implies the array data itself is at FP+offset.
                # So, we need its base address.
                emit("PUSHFP", f"Push FP for value param array '{var_name}' base address")
                emit(f"PUSHI {sym.address_or_offset}", f"Offset of value param array '{var_name}'")
                emit("PADD", f"Calculate base address of value param array '{var_name}'")
            else: # Scalar value parameter
                emit(f"PUSHL {sym.address_or_offset}", f"Push value of param '{var_name}'")
    elif sym.kind == 'constant':
        val = sym.address_or_offset
        if isinstance(val, int): emit(f"PUSHI {val}")
        elif isinstance(val, float): emit(f"PUSHF {val}")
        elif isinstance(val, str): emit(f'PUSHS "{val.replace("\"", "\\\"")}"')
        else: emit(f"PUSHI {1 if val else 0}") # boolean
    elif sym.kind == 'function':
        emit(f"PUSHA {sym.address_or_offset}", f"Push address of function '{var_name}'")
    else:
        raise ValueError(f"Cannot use identifier '{var_name}' of kind '{sym.kind}' as a value here.")


def visit_ArrayAccess(node):
    # Check if we're accessing a string variable
    is_string_access = False
    string_sym = None
    if isinstance(node.array, ast_nodes.Identifier):
        string_sym = current_scope.resolve(node.array.name)
        if string_sym and string_sym.sym_type.upper() == 'STRING':
            is_string_access = True
    
    if is_string_access:
        # For string character access, we need to use CHARAT instead of LOADN
        var_name = node.array.name
        
        # Push the string value (heap address)
        if string_sym.scope_level == 0:  # Global string
            emit(f"PUSHG {string_sym.address_or_offset}", f"Push global string '{var_name}'")
        else:  # Local string
            emit(f"PUSHL {string_sym.address_or_offset}", f"Push local string '{var_name}'")
        
        # Push the index
        visit(node.index)
        
        # Adjust for 1-based string indexing in Pascal if needed
        emit("PUSHI 1", "Adjust for 1-based string indexing in Pascal")
        emit("SUB", "Convert to 0-based for VM")
        
        # Use CHARAT for string character access
        emit("CHARAT", "Get character at index from string")
    else:
        # Original array access code
        visit(node.array)
        visit(node.index)
        
        sym_array = None
        if isinstance(node.array, ast_nodes.Identifier):
            sym_array = current_scope.resolve(node.array.name)
        
        if sym_array and sym_array.is_array and sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
            emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
            emit("SUB", "Adjust index to be 0-based for VM")
        
        emit("LOADN", "Load value from array element")

def visit_UnaryOperation(node):
    visit(node.operand)
    op = node.operator
    if op == 'NOT':
        emit("NOT")
    elif op == '-':
        emit("PUSHI 0")
        emit("SWAP")
        emit("SUB")
    elif op == '+':
        pass
    else:
        raise ValueError(f"Unsupported unary operator: {op}")

def visit_BinaryOperation(node):
    # Handle special case for string character comparison
    if node.operator == '=' and isinstance(node.right, ast_nodes.Literal) and isinstance(node.right.value, str) and len(node.right.value) == 1:
        # Check if left is a string character access
        if isinstance(node.left, ast_nodes.ArrayAccess) and isinstance(node.left.array, ast_nodes.Identifier):
            left_sym = current_scope.resolve(node.left.array.name)
            if left_sym and left_sym.sym_type.upper() == 'STRING':
                # This is a comparison of a string character with a character literal
                # First push the string address
                var_name = node.left.array.name
                if left_sym.scope_level == 0:  # Global string
                    emit(f"PUSHG {left_sym.address_or_offset}", f"Push global string '{var_name}'")
                else:  # Local string
                    emit(f"PUSHL {left_sym.address_or_offset}", f"Push local string '{var_name}'")
                
                # Push and adjust index
                visit(node.left.index)
                emit("PUSHI 1", "Adjust for 1-based string indexing in Pascal")
                emit("SUB", "Convert to 0-based for VM")
                
                # Get character ASCII value
                emit("CHARAT", "Get character at index from string")
                
                # Push ASCII code of right-hand character for comparison
                char_code = ord(node.right.value)
                emit(f"PUSHI {char_code}", f"ASCII code for '{node.right.value}' ({char_code})")
                
                # Compare the character codes
                emit("EQUAL", "Compare character codes")
                return

    # Normal processing for other cases
    visit(node.left)
    visit(node.right)
    
    original_op = node.operator # Keep original for error message
    op = original_op.upper()    # Convert operator to uppercase for consistent checks
    
    left_expr_type = determine_expression_type(node.left)
    right_expr_type = determine_expression_type(node.right)
    
    is_float_operation = left_expr_type == 'REAL' or right_expr_type == 'REAL'

    if op == '+':
        emit("FADD" if is_float_operation else "ADD")
    elif op == '-':
        emit("FSUB" if is_float_operation else "SUB")
    elif op == '*':
        emit("FMUL" if is_float_operation else "MUL")
    elif op == '/': # Pascal '/' is typically real division
        emit("FDIV")
    elif op == 'DIV': # Integer division
        emit("DIV")
    elif op == 'MOD': # Integer modulo
        emit("MOD")
    elif op == '=':
        # This section handles general equality.
        # The specific char comparison for '=' is handled at the top of this method.
        is_char_comparison = False
        char_value = None
        if isinstance(node.right, ast_nodes.Literal) and isinstance(node.right.value, str) and len(node.right.value) == 1:
            is_char_comparison = True
            char_value = ord(node.right.value)
        
        is_string_access = False
        if isinstance(node.left, ast_nodes.ArrayAccess) and isinstance(node.left.array, ast_nodes.Identifier):
            left_sym = current_scope.resolve(node.left.array.name)
            if left_sym and left_sym.sym_type.upper() == 'STRING':
                is_string_access = True
        
        if is_char_comparison and is_string_access: # This condition might be unreachable if the top char comparison returns
            emit(f"PUSHI {char_value}", f"ASCII code for '{node.right.value}'")
            emit("EQUAL", "Compare character codes")
        else:
            emit("EQUAL")
    elif op == '<':
        emit("FINF" if is_float_operation else "INF")
    elif op == '<=':
        emit("FINFEQ" if is_float_operation else "INFEQ")
    elif op == '>':
        emit("FSUP" if is_float_operation else "SUP")
    elif op == '>=':
        emit("FSUPEQ" if is_float_operation else "SUPEQ")
    elif op == '<>':
        emit("EQUAL") 
        emit("NOT")   
    elif op == 'AND':
        emit("AND")
    elif op == 'OR':
        emit("OR")
    else:
        raise ValueError(f"Unsupported binary operator: {original_op}")

def visit_FunctionCall(node):
    func_name_original = node.name
    func_name_lower = func_name_original.lower()

    # Try resolving with lowercase name first (catches built-ins like "length")
    func_sym = current_scope.resolve(func_name_lower)

    if not func_sym:
        # If lowercase didn't find it, try original casing.
        func_sym = current_scope.resolve(func_name_original)

    if not func_sym:
        raise ValueError(f"Call to undefined function/procedure '{func_name_original}'.")
    
    if func_sym.kind not in ['function', 'procedure']:
        raise ValueError(f"'{func_name_original}' is not a callable function or procedure (kind: {func_sym.kind}). It might be a variable or constant.")

    # --- Argument Processing for Built-ins (common checks) ---
    num_actual_args = len(node.arguments) if node.arguments else 0
    
    # Helper for argument checking
    def check_args(expected_count, func_display_name):
        if num_actual_args != expected_count:
            raise ValueError(f"Function '{func_display_name}' expects {expected_count} argument(s), got {num_actual_args}.")
        if expected_count > 0:
            return node.arguments[0] # Return first arg for convenience
        return None

    # --- SPECIAL CASE: built‐in routines ---
    if func_sym.address_or_offset and isinstance(func_sym.address_or_offset, str) and func_sym.address_or_offset.startswith("BUILTIN_"):
        builtin_name = func_sym.address_or_offset
        
        if builtin_name == "BUILTIN_WRITELN": # Technically a procedure
            if not node.arguments:
                emit("WRITELN")
            else:
                for arg_expr in node.arguments:
                    visit(arg_expr)
                    arg_type = determine_expression_type(arg_expr)
                    if arg_type == 'STRING': emit("WRITES")
                    elif arg_type == 'REAL': emit("WRITEF")
                    elif arg_type == 'INTEGER': emit("WRITEI")
                    elif arg_type == 'BOOLEAN': emit("WRITEI") # VM prints 0 or 1
                    else: emit("WRITEI", f"Write argument (defaulting to integer for unknown type: {arg_type})")
                emit("WRITELN")
            return

        elif builtin_name == "BUILTIN_LENGTH":
            arg = check_args(1, func_name_original)
            # Folding lenght in case string is constant - Ex : Length('Pascal')
            if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str):
                emit(f"PUSHI {len(arg.value)}", f"Folded Length('{arg.value}')")
                return
            # For string variables - Ex : Length(myString)
            visit(arg) # Pushes string address
            emit("STRLEN", f"VM STRLEN for {func_name_original}")
            return

        elif builtin_name == "BUILTIN_UPPERCASE":
            arg = check_args(1, func_name_original)
            if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str):
                folded_val = arg.value.upper()
                emit(f'PUSHS "{folded_val.replace("\"", "\\\"")}"', f"Folded {func_name_original}('{arg.value}')")
                return
            visit(arg)
            emit("UPPER", f"VM UPPER for {func_name_original} (VM dependent)")
            return

        elif builtin_name == "BUILTIN_LOWERCASE":
            arg = check_args(1, func_name_original)
            if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str):
                folded_val = arg.value.lower()
                emit(f'PUSHS "{folded_val.replace("\"", "\\\"")}"', f"Folded {func_name_original}('{arg.value}')")
                return
            visit(arg)
            emit("LOWER", f"VM LOWER for {func_name_original} (VM dependent)")
            return

        elif builtin_name == "BUILTIN_ABS":
            arg = check_args(1, func_name_original)
            visit(arg)
            arg_type = determine_expression_type(arg)
            abs_end_label = new_label("abs_end")
            if arg_type == "INTEGER":
                emit("DUP 0", "Duplicate value for abs check") # val, val
                emit("PUSHI 0") # val, val, 0
                emit("INF")     # val, (val < 0)
                emit(f"JZ {abs_end_label}") # val is on stack if val >= 0
                # val < 0, so val is on stack. Negate it.
                emit("PUSHI 0") # val, 0
                emit("SWAP")    # 0, val
                emit("SUB")     # -val
            elif arg_type == "REAL":
                emit("DUP 0")
                emit("PUSHF 0.0") # Assuming PUSHF for float 0.0
                emit("FINF")
                emit(f"JZ {abs_end_label}")
                emit("PUSHF 0.0")
                emit("SWAP")
                emit("FSUB")
            else:
                raise TypeError(f"Unsupported type {arg_type} for ABS function.")
            emit_label(abs_end_label)
            return

        elif builtin_name == "BUILTIN_SQR":
            arg = check_args(1, func_name_original)
            visit(arg)
            arg_type = determine_expression_type(arg)
            emit("DUP 0", "Duplicate value for sqr")
            if arg_type == "INTEGER": emit("MUL")
            elif arg_type == "REAL": emit("FMUL")
            else: raise TypeError(f"Unsupported type {arg_type} for SQR function.")
            return

        elif builtin_name == "BUILTIN_SQRT":
            arg = check_args(1, func_name_original)
            visit(arg) # Pushes argument
            # Ensure it's float for FSQRT (hypothetical)
            arg_type = determine_expression_type(arg)
            if arg_type == "INTEGER": emit("ITOF")
            emit("FSQRT", f"VM FSQRT for {func_name_original} (VM dependent or needs polyfill)") # Assuming FSQRT exists
            return

        elif builtin_name == "BUILTIN_PRED":
            arg = check_args(1, func_name_original)
            visit(arg) # Pushes integer
            emit("PUSHI 1")
            emit("SUB", f"VM SUB for {func_name_original}")
            return

        elif builtin_name == "BUILTIN_SUCC":
            arg = check_args(1, func_name_original)
            visit(arg) # Pushes integer
            emit("PUSHI 1")
            emit("ADD", f"VM ADD for {func_name_original}")
            return

    # --- User-defined function/procedure ---
    # 1. Check argument count matches the symbol’s signature
    num_expected_params = len(func_sym.params_info)
    num_actual_args = len(node.arguments) if node.arguments else 0
    if num_expected_params != num_actual_args:
        raise ValueError(
            f"Argument count mismatch for {func_name_original}: expected {num_expected_params}, got {num_actual_args}"
        )

    # 2. Push each argument in left‐to‐right order
    if node.arguments:
        for i, arg_expr in enumerate(node.arguments):
            param_info = func_sym.params_info[i]
            if param_info.is_var_param:
                if not isinstance(arg_expr, ast_nodes.Identifier):
                    raise ValueError(f"VAR-parameter argument for '{param_info.name}' must be a variable.")
                arg_sym = current_scope.resolve(arg_expr.name)
                if not arg_sym:
                    raise ValueError(f"Undefined variable '{arg_expr.name}' in VAR call to {func_name_original}.")

                if arg_sym.scope_level == 0: # Global var
                    emit("PUSHGP", "Push global base")
                    emit(f"PUSHI {arg_sym.address_or_offset}", f"Offset of global var '{arg_expr.name}'")
                    emit("PADD", f"Compute address of global var '{arg_expr.name}'")
                else: # Local variable or another VAR param
                    if arg_sym.is_var_param: # Passing a VAR param to another VAR param
                        emit(f"PUSHL {arg_sym.address_or_offset}", f"Pass address from VAR param '{arg_expr.name}'")
                    else: # Local variable
                        emit("PUSHFP", "Push FP (local base)")
                        emit(f"PUSHI {arg_sym.address_or_offset}", f"Offset of local var '{arg_expr.name}'")
                        emit("PADD", f"Compute address of local var '{arg_expr.name}'")
            else: # Value parameter
                visit(arg_expr)

    # Call the function/procedure
    emit(f"PUSHA {func_sym.address_or_offset}", f"Push address of {func_name_original}")
    emit("CALL")
    # If it's a procedure called as a statement and it's a function (Pascal allows this, value discarded)
    # and if the VM leaves a return value for all functions, we might need to POP it if func_sym.return_type != "VOID"
    # and this FunctionCall node is a statement itself (not part of an expression).
    # For now, assume caller or callee handles this as per convention.

def visit_IOCall(node):
    op = node.operation.lower()
    if op in ["write", "writeln"]: # This logic is now duplicated in visit_FunctionCall for 'writeln'
        if op == "writeln" and not node.arguments:
            emit("WRITELN")
            return

        for arg_expr in node.arguments:
            visit(arg_expr)
            arg_type = determine_expression_type(arg_expr)
            if arg_type == 'STRING':
                emit("WRITES")
            elif arg_type == 'REAL':
                emit("WRITEF")
            elif arg_type == 'INTEGER':
                emit("WRITEI")
            elif arg_type == 'BOOLEAN':
                emit("WRITEI") # Assuming boolean prints as 0 or 1
            else:
                emit("WRITEI", f"Write argument (defaulting to integer for unknown type: {arg_type})")
        
        if op == "writeln":
            emit("WRITELN")

    elif op in ["read", "readln"]:
        for arg_var_node in node.arguments:
            if isinstance(arg_var_node, ast_nodes.Identifier):
                var_name = arg_var_node.name
                sym = current_scope.resolve(var_name)
                if not sym:
                    raise ValueError(f"Undefined variable '{var_name}' in {op}.")

                emit("READ", f"Read string from input for '{var_name}'") # Pushes string address

                target_var_type = sym.sym_type.upper() if sym.sym_type else 'UNKNOWN'
                if target_var_type == 'INTEGER':
                    emit("ATOI", f"Convert to integer for '{var_name}'")
                elif target_var_type == 'REAL':
                    emit("ATOF", f"Convert to real for '{var_name}'")
                elif target_var_type == 'STRING':
                    pass # String address from READ is already on stack, ready for storing
                else: # Default or error
                    emit("ATOI", f"Convert to integer (default for unknown type {target_var_type}) for '{var_name}'")
                
                # Value to store is now on TOS.
                if sym.is_var_param:
                    emit(f"PUSHL {sym.address_or_offset}", f"Load address from VAR param '{var_name}'")
                    emit("SWAP") 
                    emit("STORE 0", f"Store into VAR param '{var_name}'")
                elif sym.scope_level == 0: # Global
                    emit(f"STOREG {sym.address_or_offset}", f"Store to global '{var_name}'")
                else: # Local
                    emit(f"STOREL {sym.address_or_offset}", f"Store to local '{var_name}'")

            elif isinstance(arg_var_node, ast_nodes.ArrayAccess):
                array_ast_node = arg_var_node.array # This should be an Identifier node
                index_ast_node = arg_var_node.index

                if not isinstance(array_ast_node, ast_nodes.Identifier):
                    raise NotImplementedError(f"Reading into a non-identifier array base in {op} is not implemented.")
                
                array_name = array_ast_node.name
                sym_array = current_scope.resolve(array_name)

                if not sym_array or not sym_array.is_array:
                    raise ValueError(f"'{array_name}' is not a defined array for {op}.")

                # 1. Calculate base address of the array and push it onto the stack
                if sym_array.scope_level == 0: # Global array
                    emit("PUSHGP", f"Push GP for global array '{array_name}' base")
                    emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of global array '{array_name}'")
                    emit("PADD", f"Calculate base address of global array '{array_name}'")
                else: # Local array or VAR parameter array
                    if sym_array.is_var_param: # VAR parameter that is an array
                            emit(f"PUSHL {sym_array.address_or_offset}", f"Push address from VAR param array '{array_name}'")
                    else: # Regular local array
                        emit("PUSHFP", f"Push FP for local array '{array_name}' base")
                        emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of local array '{array_name}'")
                        emit("PADD", f"Calculate base address of local array '{array_name}'")
                # Stack: [..., base_address]

                # 2. Evaluate the index expression and adjust it to be 0-based
                visit(index_ast_node) # Stack: [..., base_address, user_provided_index]
                if sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
                    emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
                    emit("SUB", "Adjust index to be 0-based for VM")
                # Stack: [..., base_address, adjusted_0_based_index]

                # 3. Perform the read operation (VM's READ pushes string_address)
                emit("READ", f"Read string from input for {array_name}[index]")
                # Stack: [..., base_address, adjusted_index, string_address_from_read]
                
                # 4. Convert the read string to the array's element type
                element_type_str = 'UNKNOWN'
                # Attempt to get element_type from the symbol. This relies on anasem.py setting it.
                if hasattr(sym_array, 'element_type') and sym_array.element_type:
                    element_type_str = str(sym_array.element_type).upper()
                elif sym_array.sym_type: # Fallback: try to parse from sym_type if it's like "ARRAY OF INTEGER"
                    st = sym_array.sym_type.upper()
                    if st.startswith("ARRAY") and " OF " in st:
                        element_type_str = st.split(" OF ")[-1].strip()
                    # else: assume sym_type might be the element type directly (less robust)
                    #    element_type_str = st 
                
                if element_type_str == 'UNKNOWN':
                        # If element_type is crucial and not found, it's better to error.
                        raise ValueError(f"Cannot determine element type for array '{array_name}' for {op}. Ensure 'element_type' is set in its symbol.")

                if element_type_str == 'INTEGER':
                    emit("ATOI", f"Convert to integer for {array_name}[index]")
                elif element_type_str == 'REAL':
                    emit("ATOF", f"Convert to real for {array_name}[index]")
                elif element_type_str == 'STRING':
                    # Assuming STOREN can handle storing a string address if the array is of strings
                    pass 
                else:
                    # Defaulting to ATOI might be risky, consider raising an error for unsupported element types
                    emit("ATOI", f"Convert to integer (default for unknown element type {element_type_str}) for {array_name}[index]")
                # Stack: [..., base_address, adjusted_index, converted_value_to_store]

                # 5. Emit STOREN to store the converted value into the array element
                emit("STOREN", f"Store read value into {array_name}[index]")
            
            else:
                raise ValueError(f"Argument to {op} must be a variable identifier or an array element. Got {type(arg_var_node).__name__}.")
        # Note: If 'readln' needs to consume the rest of the input line after variables,
        # and 'READ' doesn't do that, a separate VM instruction or convention is needed.
        # The VM doc only lists 'READ'.

def determine_expression_type(expr_node):
    """
    Tries to determine the type of an expression node.
    Returns 'INTEGER', 'REAL', 'STRING', 'BOOLEAN', or 'UNKNOWN'.
    """
    if isinstance(expr_node, ast_nodes.Literal):
        if isinstance(expr_node.value, str):
            return 'STRING'
        elif isinstance(expr_node.value, int):
            return 'INTEGER'
        elif isinstance(expr_node.value, float):
            return 'REAL'
        elif isinstance(expr_node.value, bool):
            return 'BOOLEAN' # VM might map this to INTEGER (0 or 1) for printing
    elif isinstance(expr_node, ast_nodes.Identifier):
        sym = current_scope.resolve(expr_node.name)
        if sym:
            # Assuming sym.sym_type stores 'INTEGER', 'REAL', 'STRING', etc.
            return sym.sym_type.upper() if sym.sym_type else 'UNKNOWN'
    elif isinstance(expr_node, ast_nodes.FunctionCall):
        func_sym = current_scope.resolve(expr_node.name)
        if func_sym and hasattr(func_sym, 'return_type'):
            # Assuming func_sym.return_type stores 'INTEGER', 'REAL', 'STRING', etc.
            return func_sym.return_type.upper() if func_sym.return_type else 'UNKNOWN'
    elif isinstance(expr_node, ast_nodes.BinaryOperation):
        # Basic type inference for binary operations
        # This is a simplification; a full type system would be more robust.
        if expr_node.operator == '/': # Real division
            return 'REAL'
        # For other ops, could try to infer from operands, but let's default for now
        # left_type = determine_expression_type(expr_node.left)
        # right_type = determine_expression_type(expr_node.right)
        # if left_type == 'REAL' or right_type == 'REAL': return 'REAL'
        # if left_type == 'INTEGER' and right_type == 'INTEGER': return 'INTEGER'
        # For simplicity, default to INTEGER or UNKNOWN if not division
        return 'INTEGER' # Or 'UNKNOWN'
    
    return 'UNKNOWN'