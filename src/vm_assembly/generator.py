import ast_nodes # Keep if generate() takes an ASTNode directly
from anasem import SymbolTable, register_builtin_functions # For initializing scope

# MODIFIED: Use relative imports for modules within the same package
from . import generation_context as ctx # For accessing shared state and functions
from . import node_visitors # For the visit function
# type_helpers is used by node_visitors, so direct import here might not be needed unless used otherwise

def reset_and_initialize_generator_state():
    """Resets and initializes the generator's context and symbol table."""
    ctx.reset_context() # Reset all variables in generation_context

    # Initialize current_scope and register built-ins
    # Create the initial phase scope for built-ins
    init_phase_scope = SymbolTable(scope_name="global_init_phase") # Removed scope_level argument
    register_builtin_functions(init_phase_scope)
    
    # Create the main global scope, parented by the init_phase_scope
    # Note: main_global_scope.scope_level will be 1 with current SymbolTable logic
    main_global_scope = SymbolTable(parent=init_phase_scope, scope_name="global") # Removed scope_level argument
    
    ctx.current_scope = main_global_scope # Set the active scope in the context

def generate(node: ast_nodes.ASTNode):
    """
    Generates VM code for the given AST node.
    """
    reset_and_initialize_generator_state()
    
    # Start visiting from the root node
    node_visitors.visit(node)
    
    return list(ctx.code) # Return a copy of the generated code