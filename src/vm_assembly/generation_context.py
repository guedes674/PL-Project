from anasem import SymbolTable # SymbolTable is used for type hinting current_scope

# --- Global-like state for code generation ---
code = []  # List to hold generated VM code
label_count = 0  # Counter for unique label generation
current_scope = None # Initialized by the main generator
globals_handled_pre_start = set()  # To track globals processed before START
temp_var_count = 0 # Counter for temporary variable offsets (though new_temp_var_offset uses scope)

def reset_context():
    """Resets all shared generation state."""
    global code, label_count, current_scope, globals_handled_pre_start, temp_var_count
    code.clear()
    label_count = 0
    current_scope = None # Will be re-initialized by the main generator
    globals_handled_pre_start.clear()
    temp_var_count = 0 # Reset if used directly, though new_temp_var_offset relies on scope

# --- Core functions to manipulate state ---
def emit(instruction, comment=None):
    """Emits a VM instruction with an optional comment."""
    global code
    indent = "    "
    if comment:
        code.append(f"{indent}{instruction} // {comment}")
    else:
        code.append(f"{indent}{instruction}")

def emit_label(label):
    """Emits a label for jumps."""
    global code
    code.append(f"{label}:")

def new_label(prefix="L"):
    """Generates a new unique label."""
    global label_count
    label_count += 1
    return f"{prefix}{label_count - 1}"

def push_scope(scope_name="local"):
    """Pushes a new scope onto the stack."""
    global current_scope
    if current_scope is None:
        raise Exception("Cannot push_scope: current_scope is not initialized.")
    new_scope = SymbolTable(parent=current_scope, scope_name=scope_name)
    current_scope = new_scope

def pop_scope():
    """Pops the current scope, returning to the parent scope."""
    global current_scope
    if current_scope is None:
        raise Exception("Cannot pop_scope: current_scope is not initialized.")
    if current_scope.parent:
        # Ensure we don't pop past the main global scope established after builtins
        # This logic might need adjustment based on how SymbolTable parentage is set up
        # For now, assume direct parent access is fine.
        if current_scope.parent.scope_name == "global_init_phase": # Special name for the pre-global scope
             # If the parent is the 'global_init_phase', it means the current scope is 'global'.
             # Popping 'global' should ideally not happen or be handled carefully.
             # For simplicity, we allow popping back to 'global_init_phase' if it's the direct parent.
             # The main generator logic should prevent popping beyond the true 'global' scope during execution.
            current_scope = current_scope.parent
        elif current_scope.parent is not None: # General case
            current_scope = current_scope.parent
        else:
            print("Warning: Attempting to pop beyond the initial scope.") # Should not happen
    else:
        print("Warning: Popping global scope (or uninitialized scope).")