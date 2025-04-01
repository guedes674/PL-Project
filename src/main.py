from analex import build_lexer

def main():
    print("Welcome to the Standard Pascal Compiler")
    print("Enter the Pascal code you want to compile.")
    print("You can also enter a file path to a .pas file.")
    print("Press Enter to use the default file: input/mock_pascal.pas")
    print("Press Ctrl+C to exit.")
    code = input(">> ")
    lexer = build_lexer()

    if code == "":
        code = "../input/mock_pascal.pas"

    file = open(code).read()
    lexer.input(file)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)

if __name__ == '__main__':
    main()