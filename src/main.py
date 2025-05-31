from anasin import parse_program
from vm_generator import CodeGenerator

def main():
    print("Welcome to the Standard Pascal Compiler")
    print("Enter the Pascal code you want to compile.")
    print("You can also enter a file path to a .pas file.")
    print("Press Enter to use the default file: input/mock_pascal.pas")
    print("Press Ctrl+C to exit.")
    code_input = input(">> ")

    program_content = ""
    if code_input == "":
        file_path = "../input/example6.pas"
        try:
            with open(file_path, 'r') as f:
                program_content = f.read()
            print(f"Using default file: {file_path}")
        except FileNotFoundError:
            print(f"Error: Default file {file_path} not found.")
            return
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return
    elif code_input.lower().endswith(".pas"): # Basic check if it's a file path
        file_path = code_input
        try:
            with open(file_path, 'r') as f:
                program_content = f.read()
            print(f"Reading from file: {file_path}")
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
            return
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return
    else:
        program_content = code_input

    if not program_content.strip():
        print("No code to parse.")
        return

    ast = parse_program(program_content)
    if ast:
        print("AST generated successfully:")
        print("\nGenerating VM code...")
        generator = CodeGenerator()
        try:
            vm_code = generator.generate(ast)
            print("\n--- Generated VM Code ---")
            for instruction in vm_code:
                print(instruction)
            
            # optionally, write to a .vm file
            output_vm_file = "output.vm"
            with open(output_vm_file, 'w') as f:
                for instruction in vm_code:
                    f.write(instruction + "\n")
            print(f"\nVM code also saved to {output_vm_file}")

        except Exception as e:
            print(f"\nError during VM code generation: {e}")

    else:
        print("Failed to parse program")

if __name__ == '__main__':
    main()