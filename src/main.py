from anasin import parse_program
from anasem import semantic_check, SymbolTable
from vm_generator import CodeGenerator

def read_input():
    print("Welcome to the Standard Pascal Compiler")
    print("Enter the Pascal code you want to compile.")
    print("You can also enter a file path to a .pas file.")
    print("Press Enter to use the default file: input/mock_pascal.pas")
    print("Press Ctrl+C to exit.")

    code_input = input(">> ")
    program_content = ""

    if code_input == "":
        file_path = "../input/mock_pascal.pas"
    elif code_input.lower().endswith(".pas"):
        file_path = code_input
    else:
        return code_input

    try:
        with open(file_path, 'r') as f:
            print(f"Reading from file: {file_path}")
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def compile_pascal_code(code):
    if not code.strip():
        print("No code to compile.")
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
        print(f"Semantic error: {e}")
        return

    print("Generating VM code...")
    try:
        generator = CodeGenerator()
        vm_code = generator.generate(ast)

        print("\n--- Generated VM Code ---")
        for instruction in vm_code:
            print(instruction)

        output_file = "output.vm"
        with open(output_file, 'w') as f:
            for instruction in vm_code:
                f.write(instruction + "\n")
        print(f"\nVM code saved to {output_file}")
    except Exception as e:
        print(f"Code generation error: {e}")

def main():
    program_code = read_input()
    if program_code is not None:
        compile_pascal_code(program_code)

if __name__ == '__main__':
    main()