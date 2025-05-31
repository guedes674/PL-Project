import os
import sys # Import sys for path manipulation if needed, though os.path should suffice
from anasin import parse_program
from anasem import semantic_check, SymbolTable
from vm_generator import CodeGenerator

OUTPUT_DIR = "../output"

def read_input():
    print("Welcome to the Standard Pascal Compiler")
    print("Enter the path to a Pascal (.pas) file or a folder containing .pas files.")
    print("Press Ctrl+C to exit.")

    path_input = input(">> ")
    return path_input.strip()

def ensure_output_directory():
    """Ensures the output directory exists, creating it if necessary."""
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creating output directory {OUTPUT_DIR}: {e}")
            return False
    return True

def get_output_filepath(input_filepath):
    """Generates the output .vm filepath based on the input .pas filepath."""
    base_name = os.path.basename(input_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)
    output_filename = f"{file_name_without_ext}.vm"
    return os.path.join(OUTPUT_DIR, output_filename)

def compile_pascal_file(file_path):
    """Compiles a single Pascal file."""
    print(f"\n--- Compiling: {file_path} ---")
    try:
        with open(file_path, 'r') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    if not code.strip():
        print(f"No code to compile in {file_path}.")
        return

    print("Parsing program...")
    ast = parse_program(code)
    if not ast:
        print("Parsing failed.")
        return

    print("AST generated successfully.")
    print("Performing semantic analysis...")

    try:
        global_scope = SymbolTable()
        semantic_check(ast, global_scope)
        print("Semantic check passed.")
    except Exception as e:
        print(f"Semantic error in {file_path}: {e}")
        return

    print("Generating VM code...")
    try:
        generator = CodeGenerator()
        vm_code = generator.generate(ast)

        output_vm_filepath = get_output_filepath(file_path)
        print(f"\n--- Generated VM Code for {os.path.basename(file_path)} ---")
        for instruction in vm_code:
            print(instruction)

        with open(output_vm_filepath, 'w') as f:
            for instruction in vm_code:
                f.write(instruction + "\n")
        print(f"\nVM code saved to {output_vm_filepath}")
    except Exception as e:
        print(f"Code generation error in {file_path}: {e}")

def main():
    user_path = read_input()

    if not user_path:
        print("No input path provided. Exiting.")
        return

    if not ensure_output_directory():
        return # Stop if output directory cannot be created

    if os.path.isdir(user_path):
        print(f"Processing folder: {user_path}")
        pas_files_found = False
        for item in os.listdir(user_path):
            if item.lower().endswith(".pas"):
                pas_files_found = True
                full_file_path = os.path.join(user_path, item)
                compile_pascal_file(full_file_path)
        if not pas_files_found:
            print(f"No .pas files found in folder: {user_path}")
    elif os.path.isfile(user_path):
        if user_path.lower().endswith(".pas"):
            compile_pascal_file(user_path)
        else:
            print(f"Input file '{user_path}' is not a .pas file. Please provide a .pas file or a folder.")
    else:
        print(f"The path '{user_path}' is not a valid file or folder. Please check the path and try again.")

if __name__ == '__main__':
    main()