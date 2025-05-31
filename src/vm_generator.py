import ast_nodes
from anasem import Symbol, SymbolTable

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.label_count = 0
        self.current_scope = SymbolTable(scope_name="global_init_phase") # Initial phase for global setup
        self.temp_var_count = 0
        self.globals_handled_pre_start = set() # To track globals processed before START

        # Predeclare built-in routines
        # Procedures
        self.current_scope.define(Symbol(
            name="writeln", sym_type="VOID", kind="procedure", address_or_offset="BUILTIN_WRITELN",
            params_info=[] # Placeholder, actual handling is dynamic
        ))

        # Functions
        self.current_scope.define(Symbol(
            name="length", sym_type="INTEGER", kind="function", address_or_offset="BUILTIN_LENGTH", return_type="INTEGER",
            params_info=[Symbol(name="s", sym_type="STRING", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="uppercase", sym_type="STRING", kind="function", address_or_offset="BUILTIN_UPPERCASE", return_type="STRING",
            params_info=[Symbol(name="s", sym_type="STRING", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="lowercase", sym_type="STRING", kind="function", address_or_offset="BUILTIN_LOWERCASE", return_type="STRING",
            params_info=[Symbol(name="s", sym_type="STRING", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="abs", sym_type="ANY", kind="function", address_or_offset="BUILTIN_ABS", return_type="ANY", # Type determined at call site
            params_info=[Symbol(name="x", sym_type="ANY", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="sqr", sym_type="ANY", kind="function", address_or_offset="BUILTIN_SQR", return_type="ANY", # Type determined at call site
            params_info=[Symbol(name="x", sym_type="ANY", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="sqrt", sym_type="REAL", kind="function", address_or_offset="BUILTIN_SQRT", return_type="REAL",
            params_info=[Symbol(name="x", sym_type="REAL", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="pred", sym_type="INTEGER", kind="function", address_or_offset="BUILTIN_PRED", return_type="INTEGER",
            params_info=[Symbol(name="x", sym_type="INTEGER", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="succ", sym_type="INTEGER", kind="function", address_or_offset="BUILTIN_SUCC", return_type="INTEGER",
            params_info=[Symbol(name="x", sym_type="INTEGER", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="ord", sym_type="INTEGER", kind="function", address_or_offset="BUILTIN_ORD", return_type="INTEGER",
            params_info=[Symbol(name="c", sym_type="ANY", kind="parameter", address_or_offset=0)] # CHAR or STRING[1]
        ))
        self.current_scope.define(Symbol(
            name="chr", sym_type="CHAR", kind="function", address_or_offset="BUILTIN_CHR", return_type="CHAR", # VM might treat CHAR as INT
            params_info=[Symbol(name="i", sym_type="INTEGER", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="sin", sym_type="REAL", kind="function", address_or_offset="BUILTIN_SIN", return_type="REAL",
            params_info=[Symbol(name="x", sym_type="REAL", kind="parameter", address_or_offset=0)]
        ))
        self.current_scope.define(Symbol(
            name="cos", sym_type="REAL", kind="function", address_or_offset="BUILTIN_COS", return_type="REAL",
            params_info=[Symbol(name="x", sym_type="REAL", kind="parameter", address_or_offset=0)]
        ))

        # Switch to the main global scope after built-ins
        self.current_scope = SymbolTable(parent=self.current_scope, scope_name="global")


    def new_label(self, prefix="L"):
        self.label_count += 1
        return f"{prefix}{self.label_count - 1}"

    def new_temp_var_offset(self):
        offset = self.current_scope.get_local_var_offset()
        self.emit(f"PUSHI 0", f"Allocate temp var at FP+{offset}")
        return offset

    def emit(self, instruction, comment=None):
        indent = "    " 
        if comment:
            self.code.append(f"{indent}{instruction} // {comment}")
        else:
            self.code.append(f"{indent}{instruction}")

    def emit_label(self, label):
        self.code.append(f"{label}:")

    def push_scope(self, scope_name="local"):
        new_scope = SymbolTable(parent=self.current_scope, scope_name=scope_name)
        self.current_scope = new_scope

    def pop_scope(self):
        if self.current_scope.parent:
            # Ensure we don't pop past the main global scope established after builtins
            if self.current_scope.parent.scope_name == "global_init_phase": 
                 pass # effectively at main global, parent is the init_phase sentinel
            else:
                self.current_scope = self.current_scope.parent
        else:
            print("Warning: Popping global scope (should not happen).")

    def generate(self, node):
        self.visit(node)
        return self.code

    def visit(self, node):
        if node is None:
            return
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        print(f"Warning: No visitor method for {type(node).__name__}")
        if hasattr(node, '__dict__'):
            for _, value in node.__dict__.items():
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, '__class__'): # Basic check for AST nodes
                             self.visit(item)
                elif hasattr(value, '__class__'): # Basic check for AST nodes
                    self.visit(value)


    def visit_Program(self, node):
        # Phase 1: Define global symbols and emit PUSHI 0 for global variables BEFORE START.
        # This assumes START or a convention uses these stack values for GP initialization.
        if node.block and node.block.declarations:
            for decl in node.block.declarations:
                if isinstance(decl, ast_nodes.VariableDeclaration):
                    # Process each variable in the declaration list
                    for var_info in decl.variable_list:
                        var_type_str = str(var_info.var_type) # This might be complex type object
                        
                        # Determine if it's an array and its properties
                        is_array_type = False
                        array_size = 1
                        lower_bound = 0 # Default
                        
                        if isinstance(var_info.var_type, ast_nodes.ArrayType):
                            # Assuming ArrayType has index_range with start and end Literal nodes
                            # This requires your parser (anasin.py for p_type) to create ArrayType correctly.
                            # Example: type_node.index_range = (Literal(1), Literal(5))
                            start_node = var_info.var_type.index_range[0]
                            end_node = var_info.var_type.index_range[1]
                            if isinstance(start_node, ast_nodes.Literal) and isinstance(end_node, ast_nodes.Literal) and \
                               isinstance(start_node.value, int) and isinstance(end_node.value, int):
                                low = start_node.value
                                high = end_node.value
                                if high < low:
                                    raise ValueError(f"Array upper bound {high} less than lower bound {low} for {var_info.id_list}")
                                array_size = high - low + 1
                                lower_bound = low
                                is_array_type = True
                            else:
                                raise TypeError(f"Array bounds for {var_info.id_list} must be integer literals.")
                        
                        for var_id_str in var_info.id_list:
                            offset = self.current_scope.get_local_var_offset(count=array_size) # For GP offsets
                            sym = Symbol(var_id_str, var_type_str, 'variable', offset, scope_level=0,
                                         is_array=is_array_type, array_lower_bound=lower_bound if is_array_type else None,
                                         array_element_count=array_size if is_array_type else None)
                            self.current_scope.define(sym)
                            self.globals_handled_pre_start.add(var_id_str)

                            if is_array_type:
                                self.emit(f"PUSHN {array_size}", f"Reserve space for global array '{var_id_str}' (gp[{offset}..])")
                            else:
                                self.emit(f"PUSHI 0", f"Initial stack value for global '{var_id_str}' (gp[{offset}])")
        
        self.emit("START", "Initialize Frame Pointer = Stack Pointer")
        
        # Phase 2: Process the rest of the block (constants, functions, main compound statement)
        self.visit(node.block) # visit_Block will now skip pre-handled globals
        
        self.emit("STOP", "End of program")

    def visit_ProgramHeader(self, node):
        pass

    def visit_Block(self, node):
        function_procedure_nodes = []
        declarations_for_this_block_pass = []

        if node.declarations:
            for decl in node.declarations:
                if isinstance(decl, (ast_nodes.FunctionDeclaration, ast_nodes.ProcedureDeclaration)):
                    function_procedure_nodes.append(decl)
                elif isinstance(decl, ast_nodes.VariableDeclaration):
                    # Only add if *not* handled pre-START. This check is tricky because
                    # a VariableDeclaration node can declare multiple variables.
                    # The actual filtering will happen in visit_VariableDeclaration using the set.
                    declarations_for_this_block_pass.append(decl)
                else: # Constants, Types etc.
                    declarations_for_this_block_pass.append(decl)
        
        # Process declarations not handled pre-START (e.g., constants)
        for decl_node in declarations_for_this_block_pass:
            self.visit(decl_node) # This calls visit_VariableDeclaration, visit_ConstantDeclaration etc.

        main_code_label = None
        if function_procedure_nodes:
            main_code_label = self.new_label("mainLabel")
            self.emit(f"JUMP {main_code_label}", "Jump over nested function/proc definitions")

        for fp_node in function_procedure_nodes:
            self.visit(fp_node)

        if main_code_label:
            self.emit_label(main_code_label)
        
        if node.compound_statement:
            self.visit(node.compound_statement)

    def visit_VariableDeclaration(self, node):
        for var_info in node.variable_list:
            var_type_str = str(var_info.var_type) # Potentially complex type object

            is_array_type = False
            array_size = 1
            lower_bound = 0

            if isinstance(var_info.var_type, ast_nodes.ArrayType):
                start_node = var_info.var_type.index_range[0]
                end_node = var_info.var_type.index_range[1]
                if isinstance(start_node, ast_nodes.Literal) and isinstance(end_node, ast_nodes.Literal) and \
                   isinstance(start_node.value, int) and isinstance(end_node.value, int):
                    low = start_node.value
                    high = end_node.value
                    if high < low:
                        raise ValueError(f"Array upper bound {high} less than lower bound {low} for {var_info.id_list}")
                    array_size = high - low + 1
                    lower_bound = low
                    is_array_type = True
                else:
                    raise TypeError(f"Array bounds for {var_info.id_list} must be integer literals for local variables.")

            for var_id_str in var_info.id_list:
                if var_id_str in self.globals_handled_pre_start:
                    continue 

                if self.current_scope.parent is None or self.current_scope.parent.scope_name == "global_init_phase":
                    # This path for globals not handled pre-start (should be rare with new logic)
                    offset = self.current_scope.get_local_var_offset(count=array_size)
                    sym_check = self.current_scope.resolve(var_id_str)
                    if not sym_check:
                        sym = Symbol(var_id_str, var_type_str, 'variable', offset, scope_level=0,
                                     is_array=is_array_type, array_lower_bound=lower_bound if is_array_type else None,
                                     array_element_count=array_size if is_array_type else None)
                        self.current_scope.define(sym)
                    
                    if is_array_type:
                        self.emit(f"// Global array '{var_id_str}' (gp[{offset}..]) defined (post-START init)", "")
                        # Allocation for globals should ideally happen via PUSHN before START
                        # or by VM convention for global memory. STOREG would be for individual elements.
                        # For simplicity, if we reach here, we might assume it's already "allocated"
                        # and PUSHI 0 / STOREG is for initializing first element, which is not right for arrays.
                        # This branch needs careful review if hit for arrays.
                        self.emit(f"// Warning: Post-START global array declaration for {var_id_str} - review allocation")

                    else: # Scalar global not handled pre-start
                        self.emit(f"PUSHI 0", f"Default value for global '{var_id_str}'")
                        self.emit(f"STOREG {offset}", f"Initialize global '{var_id_str}' to 0")
                else: # Local variable (inside function/procedure)
                    offset = self.current_scope.get_local_var_offset(count=array_size)
                    sym = Symbol(var_id_str, var_type_str, 'variable', offset, scope_level=1,
                                 is_array=is_array_type, array_lower_bound=lower_bound if is_array_type else None,
                                 array_element_count=array_size if is_array_type else None)
                    self.current_scope.define(sym)
                    if is_array_type:
                        self.emit(f"PUSHN {array_size}", f"Allocate {array_size} slots for local array '{var_id_str}' at FP+{offset}")
                    else:
                        self.emit(f"PUSHI 0", f"Allocate space for local var '{var_id_str}' at FP+{offset}")
    
    def visit_ConstantDeclaration(self, node):
        for const_def in node.constant_list:
            raw_value = const_def.value.value # Assuming const_def.value is a Literal AST node
            typ = str(type(raw_value).__name__).upper() # Or derive from const_def.value.type if available
            sym = Symbol(const_def.name, typ, 'constant', raw_value, self.current_scope.scope_level)
            self.current_scope.define(sym)
            self.emit(f"// Constant '{const_def.name}' defined as {raw_value}", "") # No PUSHI for const declaration

    def visit_FunctionDeclaration(self, node):
        func_label = self.new_label(f"func{node.name}") # Changed from func_
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
        self.current_scope.define(func_sym)

        # 2) Emit the function label + open a new scope
        self.emit_label(func_label)
        self.push_scope(scope_name=f"func_{node.name}")

        # 3) In the new scope, define each parameter at a negative offset
        if node.parameter_list:
            for param_group in reversed(node.parameter_list):
                for param_id_str in reversed(param_group.id_list):
                    param_type_str = str(param_group.param_type)
                    offset = self.current_scope.get_param_offset()
                    param_sym = Symbol(
                        param_id_str,
                        param_type_str,
                        'parameter',
                        offset,
                        scope_level=1,
                        is_var_param=param_group.is_var
                    )
                    self.current_scope.define(param_sym)
                    self.emit(f"// Param '{param_id_str}' at FP{offset}", "")

        # 4) Allocate space for local variables in the function
        if node.block:
            for decl in node.block.declarations:
                if isinstance(decl, ast_nodes.VariableDeclaration):
                    self.visit(decl)

        # 5) Emit the function body
        if node.block:
            self.visit(node.block.compound_statement)

        # 6) Emit RETURN and pop the function’s scope
        self.emit("RETURN", f"Return from function {node.name}")
        self.pop_scope()

    def visit_ProcedureDeclaration(self, node):
        proc_label = self.new_label(f"proc{node.name}") # Changed from proc_

        param_symbols_for_signature = []
        if node.parameter_list:
            for param_group in node.parameter_list:
                param_type_str = str(param_group.param_type)
                for pid in param_group.id_list:
                    param_symbols_for_signature.append(
                        Symbol(pid, param_type_str, 'parameter', 0, is_var_param=param_group.is_var)
                    )

        proc_sym = Symbol(node.name, "VOID", 'procedure', proc_label, params_info=param_symbols_for_signature)
        self.current_scope.define(proc_sym)

        self.emit_label(proc_label)
        self.push_scope(scope_name=f"proc_{node.name}")

        if node.parameter_list:
            for param_group in reversed(node.parameter_list):
                for param_id_str in reversed(param_group.id_list):
                    param_type_str = str(param_group.param_type)
                    offset = self.current_scope.get_param_offset()
                    param_sym = Symbol(
                        param_id_str,
                        param_type_str,
                        'parameter',
                        offset,
                        scope_level=1,
                        is_var_param=param_group.is_var
                    )
                    self.current_scope.define(param_sym)
                    self.emit(f"# Param '{param_id_str}' at FP{offset}", "")

        if node.block:
            for decl in node.block.declarations:
                if isinstance(decl, ast_nodes.VariableDeclaration):
                    self.visit(decl)

        if node.block:
            self.visit(node.block.compound_statement)

        self.emit("RETURN", f"Return from procedure {node.name}")
        self.pop_scope()

    # ────────  Statements ─────────────────────────────────────────
    def visit_CompoundStatement(self, node):
        for stmt in node.statement_list:
            self.visit(stmt)

    def visit_AssignmentStatement(self, node):
        if isinstance(node.variable, ast_nodes.ArrayAccess):
            # Array assignment: MyArray[index] := expression
            # Stack for STOREN: base_address, adjusted_index, value_RHS

            # 1. Evaluate RHS and it will be on top of stack
            self.visit(node.expression) # Stack: [..., value_RHS]

            # 2. Calculate base address of array
            array_node_for_addr = node.variable.array # This is usually an Identifier
            if not isinstance(array_node_for_addr, ast_nodes.Identifier):
                raise NotImplementedError("Assignment to non-identifier array base not implemented")
            
            array_name = array_node_for_addr.name
            sym_array = self.current_scope.resolve(array_name)
            if not sym_array or not sym_array.is_array:
                raise ValueError(f"'{array_name}' is not a defined array for assignment.")

            if sym_array.scope_level == 0: # Global array
                self.emit("PUSHGP", f"Push GP for global array '{array_name}' base")
                self.emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of global array '{array_name}'")
                self.emit("PADD", f"Calculate base address of global array '{array_name}'")
            else: # Local array
                self.emit("PUSHFP", f"Push FP for local array '{array_name}' base")
                self.emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of local array '{array_name}'")
                self.emit("PADD", f"Calculate base address of local array '{array_name}'")
            # Stack: [..., value_RHS, calculated_base_address]

            # 3. Evaluate and adjust index
            self.visit(node.variable.index) # Stack: [..., value_RHS, calculated_base_address, user_index]
            if sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
                self.emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
                self.emit("SUB", "Adjust index to be 0-based for VM")
            # Stack: [..., value_RHS, calculated_base_address, adjusted_index]

            # Reorder stack for STOREN: [base_address, adjusted_index, value_RHS]
            # Current: [value_RHS, base_address, adjusted_index] (TOS)
            # SWAP ->  [value_RHS, adjusted_index, base_address]
            # SWAP (top two again, effectively rotating value_RHS to bottom of these three)
            # This needs careful stack manipulation or temporary storage.
            # Let's use a temp var for RHS value as it's safer.

            # Re-evaluate with temp storage for RHS for clarity and safety:
            # 1. Evaluate RHS and store it temporarily
            self.visit(node.expression) # value_RHS on stack
            temp_rhs_offset = self.new_temp_var_offset() # Allocates PUSHI 0, returns offset
            self.emit(f"STOREL {temp_rhs_offset}", "Store RHS temporarily for array assignment")

            # 2. Calculate base address of array (as above)
            if sym_array.scope_level == 0:
                self.emit("PUSHGP", f"Push GP for global array '{array_name}' base")
                self.emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of global array '{array_name}'")
                self.emit("PADD", f"Calculate base address of global array '{array_name}'")
            else:
                self.emit("PUSHFP", f"Push FP for local array '{array_name}' base")
                self.emit(f"PUSHI {sym_array.address_or_offset}", f"Offset of local array '{array_name}'")
                self.emit("PADD", f"Calculate base address of local array '{array_name}'")
            # Stack: [..., calculated_base_address]

            # 3. Evaluate and adjust index (as above)
            self.visit(node.variable.index) # Stack: [..., calculated_base_address, user_index]
            if sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
                self.emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
                self.emit("SUB", "Adjust index to be 0-based for VM")
            # Stack: [..., calculated_base_address, adjusted_index]

            # 4. Reload RHS value
            self.emit(f"PUSHL {temp_rhs_offset}", "Reload RHS for array assignment")
            # Stack: [..., calculated_base_address, adjusted_index, value_RHS]
            
            self.emit("STOREN", "Store to array element")
            # Deallocate temp_rhs_offset? If new_temp_var_offset just uses current_scope.get_local_var_offset,
            # it's part of the frame and will be popped. If it's a dedicated temp area, manage it.
            # Assuming it's part of the local frame for now.

        elif isinstance(node.variable, ast_nodes.Identifier):
            # First, evaluate the right-hand side expression to get its value on the stack
            self.visit(node.expression)
            
            var_name = node.variable.name
            sym = self.current_scope.resolve(var_name)
            if not sym:
                raise ValueError(f"Undefined variable '{var_name}' in assignment.")

            is_function_return_assignment = False
            if sym.kind == 'function':
                if self.current_scope.scope_name == f"func_{sym.name}":
                    is_function_return_assignment = True
            
            if is_function_return_assignment:
                self.emit(f"// Assignment to function name '{var_name}', value on TOS for return", "")
            elif sym.is_var_param:
                self.emit(f"PUSHL {sym.address_or_offset}", f"Load address from VAR param '{var_name}'") 
                self.emit("SWAP") 
                self.emit(f"STORE 0", f"Store value into address pointed by VAR param '{var_name}'")
            elif sym.scope_level == 0: 
                self.emit(f"STOREG {sym.address_or_offset}", f"Store to global variable '{var_name}'")
            else: 
                self.emit(f"STOREL {sym.address_or_offset}", f"Store to local/value_param '{var_name}'")
        else:
            self.emit(f"// Assignment to {type(node.variable).__name__} not implemented", "")

    def visit_IfStatement(self, node):
        self.visit(node.condition)
        else_label = self.new_label("else")
        endif_label = self.new_label("endif")

        if node.else_statement:
            self.emit(f"JZ {else_label}", "If condition is false, jump to else")
        else:
            self.emit(f"JZ {endif_label}", "If condition is false (no else), jump to endif")

        self.visit(node.then_statement)
        if node.else_statement:
            self.emit(f"JUMP {endif_label}", "Skip else block")
            self.emit_label(else_label)
            self.visit(node.else_statement)

        self.emit_label(endif_label)

    def visit_WhileStatement(self, node):
        loop_start_label = self.new_label("whilestart")
        loop_end_label = self.new_label("whileend")

        self.emit_label(loop_start_label)
        self.visit(node.condition)
        self.emit(f"JZ {loop_end_label}", "If condition is false, exit while loop")
        self.visit(node.statement)
        self.emit(f"JUMP {loop_start_label}", "Repeat while loop")
        self.emit_label(loop_end_label)

    def visit_RepeatStatement(self, node):
        loop_start_label = self.new_label("repeatstart")
        self.emit_label(loop_start_label)
        for stmt in node.statement_list:
            self.visit(stmt)
        self.visit(node.condition)
        self.emit(f"JZ {loop_start_label}", "If condition is false, jump back to repeat")

    def visit_ForStatement(self, node):
        # Resolve control variable
        control_var_name = node.control_variable.name
        sym_control_var = self.current_scope.resolve(control_var_name)

        if not sym_control_var:
            raise ValueError(f"FOR loop control variable '{control_var_name}' not defined.")
        if sym_control_var.kind not in ['variable', 'parameter'] or sym_control_var.is_var_param:
            # Parameters can be loop counters if they are value parameters. VAR parameters cannot.
            raise ValueError(f"FOR loop control variable '{control_var_name}' must be a non-VAR variable or value parameter.")

        is_global_control_var = (sym_control_var.scope_level == 0)
        control_var_offset = sym_control_var.address_or_offset

        # Labels for the loop
        loop_check_label = self.new_label("forcheck")
        loop_end_label = self.new_label("forend")

        # 1. Evaluate and store the end expression value using new_temp_var_offset
        # This method properly allocates space and returns the offset
        temp_end_val_storage_offset = self.new_temp_var_offset()
        
        self.visit(node.end_expression) # Evaluate the end expression, its value is now on TOS
        self.emit(f"STOREL {temp_end_val_storage_offset}", f"Store evaluated end value of FOR loop for '{control_var_name}'")

        # 2. Initialize control variable with the start expression's value
        self.visit(node.start_expression) # Evaluate start expression, value on TOS
    
        if is_global_control_var:
            self.emit(f"STOREG {control_var_offset}", f"Initialize FOR global control var '{control_var_name}'")
        else:
            self.emit(f"STOREL {control_var_offset}", f"Initialize FOR local control var '{control_var_name}'")

        # 3. Loop check point (label for the start of each iteration's check)
        self.emit_label(loop_check_label)

        # 4. Load current value of control variable onto stack
        if is_global_control_var:
            self.emit(f"PUSHG {control_var_offset}", f"Load global control var '{control_var_name}' for check")
        else:
            self.emit(f"PUSHL {control_var_offset}", f"Load local control var '{control_var_name}' for check")

        # 5. Load stored end expression value onto stack
        self.emit(f"PUSHL {temp_end_val_storage_offset}", "Load stored end value for check")

        # 6. Perform comparison. Stack: [control_var_current_value, stored_end_value]
        #    If the condition for continuing the loop is false (0), jump to loop_end_label.
        if not node.downto:  # TO loop: continues if control_var <= end_value
            self.emit("INFEQ", f"Check {control_var_name} <= end_value") # Pushes 1 if true, 0 if false
            self.emit(f"JZ {loop_end_label}", f"If not ({control_var_name} <= end_value), exit loop")
        else:  # DOWNTO loop: continues if control_var >= end_value
            self.emit("SUPEQ", f"Check {control_var_name} >= end_value") # Pushes 1 if true, 0 if false
            self.emit(f"JZ {loop_end_label}", f"If not ({control_var_name} >= end_value), exit loop")

        # 7. Execute loop body
        self.visit(node.statement)

        # 8. Increment/Decrement control variable
        # Load current value of control variable
        if is_global_control_var:
            self.emit(f"PUSHG {control_var_offset}", f"Load global control var '{control_var_name}' for update")
        else:
            self.emit(f"PUSHL {control_var_offset}", f"Load local control var '{control_var_name}' for update")
        
        self.emit("PUSHI 1") # Push 1 for increment/decrement
        if not node.downto:
            self.emit("ADD", f"Increment {control_var_name}")
        else:
            self.emit("SUB", f"Decrement {control_var_name}")
        
        # Store updated value back into control variable
        if is_global_control_var:
            self.emit(f"STOREG {control_var_offset}", f"Store updated global control var '{control_var_name}'")
        else:
            self.emit(f"STOREL {control_var_offset}", f"Store updated local control var '{control_var_name}'")

        # 9. Jump back to the loop check
        self.emit(f"JUMP {loop_check_label}")

        # 10. Loop end point
        self.emit_label(loop_end_label)

        # The temporary variable for the end_value (temp_end_val_storage_offset) was allocated
        # on the current function's stack frame. It will be deallocated automatically when
        # the function returns and its stack frame is popped.

    def visit_CaseStatement(self, node):
        self.emit("# CASE statement not fully implemented", "")

    def visit_CaseElement(self, node):
        pass

    def visit_FieldAccess(self, node):
        self.emit("# FieldAccess not fully implemented", "")

    # ────────  Expressions ────────────────────────────────────────
    def visit_Literal(self, node):
        value = node.value
        if isinstance(value, int):
            self.emit(f"PUSHI {value}")
        elif isinstance(value, float):
            self.emit(f"PUSHF {value}")
        elif isinstance(value, str):
            escaped_value = value.replace('"', '\\"')
            self.emit(f'PUSHS "{escaped_value}"')
        elif isinstance(value, bool):
            self.emit(f"PUSHI {1 if value else 0}")
        else:
            raise TypeError(f"Unsupported literal type: {type(value)} for value {value}")

    def visit_Identifier(self, node):
        var_name = node.name
        sym = self.current_scope.resolve(var_name)
        if not sym:
            raise ValueError(f"Undefined identifier '{var_name}' used as a value.")

        if sym.kind == 'variable':
            if sym.is_array:
                # When an array identifier is used directly as a value, it means its base address.
                # This is consistent with how visit_ArrayAccess now expects the base address.
                if sym.scope_level == 0: # Global array
                    self.emit("PUSHGP", f"Push GP for global array '{var_name}' base address")
                    self.emit(f"PUSHI {sym.address_or_offset}", f"Offset of global array '{var_name}'")
                    self.emit("PADD", f"Calculate base address of global array '{var_name}'")
                else: # Local array
                    self.emit("PUSHFP", f"Push FP for local array '{var_name}' base address")
                    self.emit(f"PUSHI {sym.address_or_offset}", f"Offset of local array '{var_name}'")
                    self.emit("PADD", f"Calculate base address of local array '{var_name}'")
            else: # Scalar variable
                if sym.scope_level == 0:
                    self.emit(f"PUSHG {sym.address_or_offset}", f"Push global '{var_name}'")
                else:
                    self.emit(f"PUSHL {sym.address_or_offset}", f"Push local '{var_name}'")
        elif sym.kind == 'parameter':
            if sym.is_var_param: # VAR param could be an array passed by reference
                self.emit(f"PUSHL {sym.address_or_offset}", f"Push address from VAR param '{var_name}'")
                # If this VAR param is an array and is being used in ArrayAccess, PUSHL gives its address.
                # If it's being dereferenced for its value (e.g. x := var_param_array[i] is not this path,
                # but if it was simple_var := var_param_scalar), then LOAD 0 is needed.
                # Context is key. For ArrayAccess, visit_Identifier for the array name should push its base address.
                # If a VAR param *IS* an array, PUSHL pushes the address of that original array. This is correct.
            else: # Value parameter
                if sym.is_array: # Value parameter that is an array (Pascal copies arrays for value params)
                    # This implies the array data itself is at FP+offset.
                    # So, we need its base address.
                    self.emit("PUSHFP", f"Push FP for value param array '{var_name}' base address")
                    self.emit(f"PUSHI {sym.address_or_offset}", f"Offset of value param array '{var_name}'")
                    self.emit("PADD", f"Calculate base address of value param array '{var_name}'")
                else: # Scalar value parameter
                    self.emit(f"PUSHL {sym.address_or_offset}", f"Push value of param '{var_name}'")
        elif sym.kind == 'constant':
            val = sym.address_or_offset
            if isinstance(val, int): self.emit(f"PUSHI {val}")
            elif isinstance(val, float): self.emit(f"PUSHF {val}")
            elif isinstance(val, str): self.emit(f'PUSHS "{val.replace("\"", "\\\"")}"')
            else: self.emit(f"PUSHI {1 if val else 0}") # boolean
        elif sym.kind == 'function':
            self.emit(f"PUSHA {sym.address_or_offset}", f"Push address of function '{var_name}'")
        else:
            raise ValueError(f"Cannot use identifier '{var_name}' of kind '{sym.kind}' as a value here.")


    def visit_ArrayAccess(self, node):
        # Check if we're accessing a string variable
        is_string_access = False
        string_sym = None
        if isinstance(node.array, ast_nodes.Identifier):
            string_sym = self.current_scope.resolve(node.array.name)
            if string_sym and string_sym.sym_type.upper() == 'STRING':
                is_string_access = True
        
        if is_string_access:
            # For string character access, we need to use CHARAT instead of LOADN
            var_name = node.array.name
            
            # Push the string value (heap address)
            if string_sym.scope_level == 0:  # Global string
                self.emit(f"PUSHG {string_sym.address_or_offset}", f"Push global string '{var_name}'")
            else:  # Local string
                self.emit(f"PUSHL {string_sym.address_or_offset}", f"Push local string '{var_name}'")
            
            # Push the index
            self.visit(node.index)
            
            # Adjust for 1-based string indexing in Pascal if needed
            self.emit("PUSHI 1", "Adjust for 1-based string indexing in Pascal")
            self.emit("SUB", "Convert to 0-based for VM")
            
            # Use CHARAT for string character access
            self.emit("CHARAT", "Get character at index from string")
        else:
            # Original array access code
            self.visit(node.array)
            self.visit(node.index)
            
            sym_array = None
            if isinstance(node.array, ast_nodes.Identifier):
                sym_array = self.current_scope.resolve(node.array.name)
            
            if sym_array and sym_array.is_array and sym_array.array_lower_bound is not None and sym_array.array_lower_bound != 0:
                self.emit(f"PUSHI {sym_array.array_lower_bound}", f"Push array lower bound {sym_array.array_lower_bound}")
                self.emit("SUB", "Adjust index to be 0-based for VM")
            
            self.emit("LOADN", "Load value from array element")

    def visit_UnaryOperation(self, node):
        self.visit(node.operand)
        op = node.operator
        if op == 'NOT':
            self.emit("NOT")
        elif op == '-':
            self.emit("PUSHI 0")
            self.emit("SWAP")
            self.emit("SUB")
        elif op == '+':
            pass
        else:
            raise ValueError(f"Unsupported unary operator: {op}")

    def visit_BinaryOperation(self, node):
        # Handle special case for string character comparison
        if node.operator == '=' and isinstance(node.right, ast_nodes.Literal) and isinstance(node.right.value, str) and len(node.right.value) == 1:
            # Check if left is a string character access
            if isinstance(node.left, ast_nodes.ArrayAccess) and isinstance(node.left.array, ast_nodes.Identifier):
                left_sym = self.current_scope.resolve(node.left.array.name)
                if left_sym and left_sym.sym_type.upper() == 'STRING':
                    # This is a comparison of a string character with a character literal
                    # First push the string address
                    var_name = node.left.array.name
                    if left_sym.scope_level == 0:  # Global string
                        self.emit(f"PUSHG {left_sym.address_or_offset}", f"Push global string '{var_name}'")
                    else:  # Local string
                        self.emit(f"PUSHL {left_sym.address_or_offset}", f"Push local string '{var_name}'")
                    
                    # Push and adjust index
                    self.visit(node.left.index)
                    self.emit("PUSHI 1", "Adjust for 1-based string indexing in Pascal")
                    self.emit("SUB", "Convert to 0-based for VM")
                    
                    # Get character ASCII value
                    self.emit("CHARAT", "Get character at index from string")
                    
                    # Push ASCII code of right-hand character for comparison
                    char_code = ord(node.right.value)
                    self.emit(f"PUSHI {char_code}", f"ASCII code for '{node.right.value}' ({char_code})")
                    
                    # Compare the character codes
                    self.emit("EQUAL", "Compare character codes")
                    return
    
        # Normal processing for other cases
        self.visit(node.left)
        self.visit(node.right)
        
        op = node.operator
        
        left_expr_type = self.determine_expression_type(node.left)
        right_expr_type = self.determine_expression_type(node.right)
        
        is_float_operation = left_expr_type == 'REAL' or right_expr_type == 'REAL'

        if op == '+':
            self.emit("FADD" if is_float_operation else "ADD")
        elif op == '-':
            self.emit("FSUB" if is_float_operation else "SUB")
        elif op == '*':
            self.emit("FMUL" if is_float_operation else "MUL")
        elif op == '/': # Pascal '/' is typically real division
            # Ensure operands are float. If not, ITOF would be needed.
            # Assuming they are pushed as floats or ITOF happened during visit_Literal/Identifier if type was known.
            self.emit("FDIV")
        elif op == 'DIV': # Integer division
            self.emit("DIV")
        elif op == 'MOD': # Integer modulo
            self.emit("MOD")
        elif op == '=':
            # Check if this is a character comparison (string[index] = '1')
            is_char_comparison = False
            char_value = None
            
            # Check if right side is a character literal
            if isinstance(node.right, ast_nodes.Literal) and isinstance(node.right.value, str) and len(node.right.value) == 1:
                is_char_comparison = True
                char_value = ord(node.right.value)
            
            # Check if left side is array access to a string
            is_string_access = False
            if isinstance(node.left, ast_nodes.ArrayAccess) and isinstance(node.left.array, ast_nodes.Identifier):
                left_sym = self.current_scope.resolve(node.left.array.name)
                if left_sym and left_sym.sym_type.upper() == 'STRING':
                    is_string_access = True
            
            if is_char_comparison and is_string_access:
                # Replace the string literal with its ASCII code for comparison
                self.emit(f"PUSHI {char_value}", f"ASCII code for '{node.right.value}'")
                self.emit("EQUAL", "Compare character codes")
            else:
                # Regular equality comparison
                self.emit("EQUAL")
        elif op == '<':
            self.emit("FINF" if is_float_operation else "INF")
        elif op == '<=':
            self.emit("FINFEQ" if is_float_operation else "INFEQ")
        elif op == '>':
            self.emit("FSUP" if is_float_operation else "SUP")
        elif op == '>=':
            self.emit("FSUPEQ" if is_float_operation else "SUPEQ")
        elif op == '<>':
            self.emit("EQUAL") # Perform equality check
            self.emit("NOT")   # Negate the result
        elif op == 'AND':
            self.emit("AND")
        elif op == 'OR':
            self.emit("OR")
        else:
            raise ValueError(f"Unsupported binary operator: {op}")

    def visit_FunctionCall(self, node):
        func_name_original = node.name
        func_name_lower = func_name_original.lower()

        # Try resolving with lowercase name first (catches built-ins like "length")
        func_sym = self.current_scope.resolve(func_name_lower)

        if not func_sym:
            # If lowercase didn't find it, try original casing.
            func_sym = self.current_scope.resolve(func_name_original)

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
                    self.emit("WRITELN")
                else:
                    for arg_expr in node.arguments:
                        self.visit(arg_expr)
                        arg_type = self.determine_expression_type(arg_expr)
                        if arg_type == 'STRING': self.emit("WRITES")
                        elif arg_type == 'REAL': self.emit("WRITEF")
                        elif arg_type == 'INTEGER': self.emit("WRITEI")
                        elif arg_type == 'BOOLEAN': self.emit("WRITEI") # VM prints 0 or 1
                        else: self.emit("WRITEI", f"Write argument (defaulting to integer for unknown type: {arg_type})")
                    self.emit("WRITELN")
                return

            elif builtin_name == "BUILTIN_LENGTH":
                arg = check_args(1, func_name_original)
                # Constant folding for length
                if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str):
                    self.emit(f"PUSHI {len(arg.value)}", f"Folded Length('{arg.value}')")
                    return
                self.visit(arg) # Pushes string address
                self.emit("STRLEN", f"VM STRLEN for {func_name_original}")
                return

            elif builtin_name == "BUILTIN_UPPERCASE":
                arg = check_args(1, func_name_original)
                if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str):
                    folded_val = arg.value.upper()
                    self.emit(f'PUSHS "{folded_val.replace("\"", "\\\"")}"', f"Folded {func_name_original}('{arg.value}')")
                    return
                self.visit(arg)
                self.emit("UPPER", f"VM UPPER for {func_name_original} (VM dependent)")
                return

            elif builtin_name == "BUILTIN_LOWERCASE":
                arg = check_args(1, func_name_original)
                if isinstance(arg, ast_nodes.Literal) and isinstance(arg.value, str):
                    folded_val = arg.value.lower()
                    self.emit(f'PUSHS "{folded_val.replace("\"", "\\\"")}"', f"Folded {func_name_original}('{arg.value}')")
                    return
                self.visit(arg)
                self.emit("LOWER", f"VM LOWER for {func_name_original} (VM dependent)")
                return

            elif builtin_name == "BUILTIN_ABS":
                arg = check_args(1, func_name_original)
                self.visit(arg)
                arg_type = self.determine_expression_type(arg)
                abs_end_label = self.new_label("abs_end")
                if arg_type == "INTEGER":
                    self.emit("DUP 0", "Duplicate value for abs check") # val, val
                    self.emit("PUSHI 0") # val, val, 0
                    self.emit("INF")     # val, (val < 0)
                    self.emit(f"JZ {abs_end_label}") # val is on stack if val >= 0
                    # val < 0, so val is on stack. Negate it.
                    self.emit("PUSHI 0") # val, 0
                    self.emit("SWAP")    # 0, val
                    self.emit("SUB")     # -val
                elif arg_type == "REAL":
                    self.emit("DUP 0")
                    self.emit("PUSHF 0.0") # Assuming PUSHF for float 0.0
                    self.emit("FINF")
                    self.emit(f"JZ {abs_end_label}")
                    self.emit("PUSHF 0.0")
                    self.emit("SWAP")
                    self.emit("FSUB")
                else:
                    raise TypeError(f"Unsupported type {arg_type} for ABS function.")
                self.emit_label(abs_end_label)
                return

            elif builtin_name == "BUILTIN_SQR":
                arg = check_args(1, func_name_original)
                self.visit(arg)
                arg_type = self.determine_expression_type(arg)
                self.emit("DUP 0", "Duplicate value for sqr")
                if arg_type == "INTEGER": self.emit("MUL")
                elif arg_type == "REAL": self.emit("FMUL")
                else: raise TypeError(f"Unsupported type {arg_type} for SQR function.")
                return

            elif builtin_name == "BUILTIN_SQRT":
                arg = check_args(1, func_name_original)
                self.visit(arg) # Pushes argument
                # Ensure it's float for FSQRT (hypothetical)
                arg_type = self.determine_expression_type(arg)
                if arg_type == "INTEGER": self.emit("ITOF")
                self.emit("FSQRT", f"VM FSQRT for {func_name_original} (VM dependent or needs polyfill)") # Assuming FSQRT exists
                return

            elif builtin_name == "BUILTIN_PRED":
                arg = check_args(1, func_name_original)
                self.visit(arg) # Pushes integer
                self.emit("PUSHI 1")
                self.emit("SUB", f"VM SUB for {func_name_original}")
                return

            elif builtin_name == "BUILTIN_SUCC":
                arg = check_args(1, func_name_original)
                self.visit(arg) # Pushes integer
                self.emit("PUSHI 1")
                self.emit("ADD", f"VM ADD for {func_name_original}")
                return
            
            elif builtin_name == "BUILTIN_ORD":
                arg = check_args(1, func_name_original)
                self.visit(arg) # Pushes string address (for char/string[1]) or char (as int)
                arg_type = self.determine_expression_type(arg)
                if arg_type == "STRING": # Assuming it's a single char string or we take first char
                    self.emit("CHRCODE", f"VM CHRCODE for {func_name_original}")
                elif arg_type == "CHAR": # If CHAR is a distinct type represented as int, it's already ord
                    pass # Value is already the ordinal
                elif arg_type == "INTEGER": # If it was already an integer (e.g. ord(65))
                    pass # Value is already the ordinal
                else:
                    raise TypeError(f"Unsupported type {arg_type} for ORD function. Expects CHAR or STRING.")
                return

            elif builtin_name == "BUILTIN_CHR":
                arg = check_args(1, func_name_original)
                self.visit(arg) # Pushes integer
                # CHR returns a character. VM's WRITECHR prints.
                # To return a char value (as int/ASCII), it's already on stack.
                # If it needs to be a string of 1 char, that's more complex.
                self.emit(f"# {func_name_original}(int) -> char (ASCII value on stack). VM may need specific handling for char type results.", "")
                return

            elif builtin_name == "BUILTIN_SIN":
                arg = check_args(1, func_name_original)
                self.visit(arg)
                arg_type = self.determine_expression_type(arg)
                if arg_type == "INTEGER": self.emit("ITOF")
                self.emit("FSIN", f"VM FSIN for {func_name_original}")
                return

            elif builtin_name == "BUILTIN_COS":
                arg = check_args(1, func_name_original)
                self.visit(arg)
                arg_type = self.determine_expression_type(arg)
                if arg_type == "INTEGER": self.emit("ITOF")
                self.emit("FCOS", f"VM FCOS for {func_name_original}")
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
                    arg_sym = self.current_scope.resolve(arg_expr.name)
                    if not arg_sym:
                        raise ValueError(f"Undefined variable '{arg_expr.name}' in VAR call to {func_name_original}.")

                    if arg_sym.scope_level == 0: # Global var
                        self.emit("PUSHGP", "Push global base")
                        self.emit(f"PUSHI {arg_sym.address_or_offset}", f"Offset of global var '{arg_expr.name}'")
                        self.emit("PADD", f"Compute address of global var '{arg_expr.name}'")
                    else: # Local variable or another VAR param
                        if arg_sym.is_var_param: # Passing a VAR param to another VAR param
                            self.emit(f"PUSHL {arg_sym.address_or_offset}", f"Pass address from VAR param '{arg_expr.name}'")
                        else: # Local variable
                            self.emit("PUSHFP", "Push FP (local base)")
                            self.emit(f"PUSHI {arg_sym.address_or_offset}", f"Offset of local var '{arg_expr.name}'")
                            self.emit("PADD", f"Compute address of local var '{arg_expr.name}'")
                else: # Value parameter
                    self.visit(arg_expr)

        # Call the function/procedure
        self.emit(f"PUSHA {func_sym.address_or_offset}", f"Push address of {func_name_original}")
        self.emit("CALL")
        # If it's a procedure called as a statement and it's a function (Pascal allows this, value discarded)
        # and if the VM leaves a return value for all functions, we might need to POP it if func_sym.return_type != "VOID"
        # and this FunctionCall node is a statement itself (not part of an expression).
        # For now, assume caller or callee handles this as per convention.

    def visit_IOCall(self, node):
        op = node.operation.lower()
        if op in ["write", "writeln"]: # This logic is now duplicated in visit_FunctionCall for 'writeln'
            if op == "writeln" and not node.arguments:
                self.emit("WRITELN")
                return

            for arg_expr in node.arguments:
                self.visit(arg_expr)
                arg_type = self.determine_expression_type(arg_expr)
                if arg_type == 'STRING':
                    self.emit("WRITES")
                elif arg_type == 'REAL':
                    self.emit("WRITEF")
                elif arg_type == 'INTEGER':
                    self.emit("WRITEI")
                elif arg_type == 'BOOLEAN':
                    self.emit("WRITEI") # Assuming boolean prints as 0 or 1
                else:
                    self.emit("WRITEI", f"Write argument (defaulting to integer for unknown type: {arg_type})")
            
            if op == "writeln":
                self.emit("WRITELN")

        elif op in ["read", "readln"]: # Assuming readln behaves like read for listed vars
            for arg_var_node in node.arguments:
                if not isinstance(arg_var_node, ast_nodes.Identifier):
                    raise ValueError(f"Argument to {op} must be a variable identifier.")
                var_name = arg_var_node.name
                sym = self.current_scope.resolve(var_name)
                if not sym:
                    raise ValueError(f"Undefined variable '{var_name}' in {op}.")

                self.emit("READ", f"Read string from input for '{var_name}'") # Pushes string address

                target_var_type = sym.sym_type.upper() if sym.sym_type else 'UNKNOWN'
                if target_var_type == 'INTEGER':
                    self.emit("ATOI", f"Convert to integer for '{var_name}'")
                elif target_var_type == 'REAL':
                    self.emit("ATOF", f"Convert to real for '{var_name}'")
                elif target_var_type == 'STRING':
                    pass # String address from READ is already on stack, ready for storing
                else: # Default or error
                    self.emit("ATOI", f"Convert to integer (default for unknown type {target_var_type}) for '{var_name}'")
                
                # Value to store is now on TOS.
                if sym.is_var_param:
                    # Stack: [..., value_from_read]
                    self.emit(f"PUSHL {sym.address_or_offset}", f"Load address from VAR param '{var_name}'") # Stack: [..., value_from_read, address_var_points_to]
                    self.emit("SWAP") # Stack: [..., address_var_points_to, value_from_read]
                    self.emit("STORE 0", f"Store into VAR param '{var_name}'")
                elif sym.scope_level == 0: # Global
                    self.emit(f"STOREG {sym.address_or_offset}", f"Store to global '{var_name}'")
                else: # Local
                    self.emit(f"STOREL {sym.address_or_offset}", f"Store to local '{var_name}'")
            # Note: If 'readln' needs to consume the rest of the input line after variables,
            # and 'READ' doesn't do that, a separate VM instruction or convention is needed.
            # The VM doc only lists 'READ'.

    def determine_expression_type(self, expr_node):
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
            sym = self.current_scope.resolve(expr_node.name)
            if sym:
                # Assuming sym.sym_type stores 'INTEGER', 'REAL', 'STRING', etc.
                return sym.sym_type.upper() if sym.sym_type else 'UNKNOWN'
        elif isinstance(expr_node, ast_nodes.FunctionCall):
            func_sym = self.current_scope.resolve(expr_node.name)
            if func_sym and hasattr(func_sym, 'return_type'):
                # Assuming func_sym.return_type stores 'INTEGER', 'REAL', 'STRING', etc.
                return func_sym.return_type.upper() if func_sym.return_type else 'UNKNOWN'
        elif isinstance(expr_node, ast_nodes.BinaryOperation):
            # Basic type inference for binary operations
            # This is a simplification; a full type system would be more robust.
            if expr_node.operator == '/': # Real division
                return 'REAL'
            # For other ops, could try to infer from operands, but let's default for now
            # left_type = self.determine_expression_type(expr_node.left)
            # right_type = self.determine_expression_type(expr_node.right)
            # if left_type == 'REAL' or right_type == 'REAL': return 'REAL'
            # if left_type == 'INTEGER' and right_type == 'INTEGER': return 'INTEGER'
            # For simplicity, default to INTEGER or UNKNOWN if not division
            return 'INTEGER' # Or 'UNKNOWN'
        
        return 'UNKNOWN'

# ────────────────────────────────────────────────────────────────────────────────


if __name__ == '__main__':
    #
    # Suppose you parse “HelloWorld” into an AST called “program_node.”
    #
    # generator = CodeGenerator()
    # vm_code = generator.generate(program_node)
    # for instr in vm_code:
    #     print(instr)
    #
    pass