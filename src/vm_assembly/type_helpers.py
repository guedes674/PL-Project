import ast_nodes
from . import generation_context as generation_context # For current_scope in determine_expression_type

def process_array_type(var_type_node):
    """Processes an AST node representing an array type."""
    is_array_type = False
    array_size = 1
    lower_bound = 0
    element_type_str = None

    if isinstance(var_type_node, ast_nodes.ArrayType):
        start_node = var_type_node.index_range[0]
        end_node = var_type_node.index_range[1]

        if isinstance(start_node, ast_nodes.Literal) and isinstance(start_node.value, int) and \
            isinstance(end_node, ast_nodes.Literal) and isinstance(end_node.value, int):

            low = start_node.value
            high = end_node.value
            if high < low:
                raise ValueError(f"Array upper bound {high} less than lower bound {low}")
            array_size = high - low + 1
            lower_bound = low
            is_array_type = True

            if isinstance(var_type_node.element_type, str):
                element_type_str = var_type_node.element_type.upper()
            elif hasattr(var_type_node.element_type, '__class__'): # If element_type is another AST node
                element_type_str = type_node_to_string(var_type_node.element_type)

        else:
            raise TypeError("Array bounds in ast_nodes.ArrayType must be integer literals.")
    return is_array_type, array_size, lower_bound, element_type_str

def type_node_to_string(var_type_node):
    """Converts a variable type AST node or string to a string representation."""
    if isinstance(var_type_node, ast_nodes.ArrayType):
        is_array, _, _, elem_type = process_array_type(var_type_node)
        if is_array and elem_type:
            return f"ARRAY OF {elem_type.upper()}"
        elif is_array:
            return "ARRAY OF UNKNOWN_ELEMENT_TYPE"
    elif isinstance(var_type_node, str):
        return var_type_node.upper()
    
    if hasattr(var_type_node, '__class__'):
        # Fallback for other AST node types (e.g. SimpleType)
        if hasattr(var_type_node, 'name'): # e.g. SimpleType has a 'name' attribute
            return str(var_type_node.name).upper()
        type_name_guess = str(var_type_node)
        if len(type_name_guess) > 30:
            return f"COMPLEX_TYPE_{var_type_node.__class__.__name__.upper()}"
        return type_name_guess.upper()

    return "UNKNOWN_TYPE"

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
            return 'BOOLEAN'
    elif isinstance(expr_node, ast_nodes.Identifier):
        sym = generation_context.current_scope.resolve(expr_node.name)
        if sym:
            return sym.sym_type.upper() if sym.sym_type else 'UNKNOWN'
    elif isinstance(expr_node, ast_nodes.FunctionCall):
        # Resolve function name (handle potential case differences for builtins)
        func_name_original = expr_node.name
        func_name_lower = func_name_original.lower()
        func_sym = generation_context.current_scope.resolve(func_name_lower)
        if not func_sym:
            func_sym = generation_context.current_scope.resolve(func_name_original)

        if func_sym and hasattr(func_sym, 'return_type'):
            return func_sym.return_type.upper() if func_sym.return_type else 'UNKNOWN'
    elif isinstance(expr_node, ast_nodes.BinaryOperation):
        if expr_node.operator == '/':
            return 'REAL'
        # More sophisticated type inference could be added here
        # For now, try to infer from operands or default
        left_type = determine_expression_type(expr_node.left)
        right_type = determine_expression_type(expr_node.right)
        if left_type == 'REAL' or right_type == 'REAL':
            return 'REAL'
        if expr_node.operator in ['<', '>', '<=', '>=', '=', '<>', 'AND', 'OR', 'NOT']: # Relational/Logical ops return BOOLEAN
            return 'BOOLEAN'
        if left_type == 'INTEGER' and right_type == 'INTEGER':
             # For ops like +, -, *, DIV, MOD if both are int, result is int
            if expr_node.operator.upper() in ['+', '-', '*', 'DIV', 'MOD']:
                return 'INTEGER'
        return 'INTEGER' # Default for other binary ops, or 'UNKNOWN'
    elif isinstance(expr_node, ast_nodes.UnaryOperation):
        if expr_node.operator.upper() == 'NOT':
            return 'BOOLEAN'
        return determine_expression_type(expr_node.operand) # Type is same as operand for unary +/-
    elif isinstance(expr_node, ast_nodes.ArrayAccess):
        # Determine type from array's element type
        if isinstance(expr_node.array, ast_nodes.Identifier):
            array_sym = generation_context.current_scope.resolve(expr_node.array.name)
            if array_sym and array_sym.is_array and hasattr(array_sym, 'element_type'):
                return str(array_sym.element_type).upper() if array_sym.element_type else 'UNKNOWN'
            elif array_sym and array_sym.sym_type and array_sym.sym_type.upper() == 'STRING': # String char access
                return 'CHAR' # Or 'STRING' if single char is treated as string
    return 'UNKNOWN'