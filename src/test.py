from anasin import parse_program

def test_simple_program():
    code = """
    program HelloWorld;
    var
        x: Integer;
    begin
        x := 5;
        Write(x);
    end.
    """
    
    ast = parse_program(code)
    if ast:
        print("AST generated successfully:")
        print(ast)
        
        # Navigate the AST
        print(f"Program name: {ast.header.name}")
        print(f"Variables: {ast.block.declarations}")
        print(f"Statements: {ast.block.compound_statement.statement_list}")
    else:
        print("Failed to parse program")

if __name__ == "__main__":
    test_simple_program()