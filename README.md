<img src='uminho_eng.png' width="30%"/>

<h3 align="center">Licenciatura em Engenharia Informática <br> Trabalho prático de Processamento de Linguagens <br> 2024/2025 </h3>

---
<h3 align="center"> Colaboradores &#129309 </h2>

<div align="center">

| Nome             | Número  |
|------------------|---------|
| Tiago Carneiro   | A93207  |
| Tiago Guedes     | A97369  |
| Diogo Gonçalves  | A101919 |

Nota : 20

</div>
# RC2425-Grupo-89

Construir um analizador léxico para a linguagem Pascal

## Lista de Resultados

### Source Code (src/)
- [main.py](src/main.py) - Main program entry point
- [anasin.py](src/anasin.py) - Syntax analyzer for Pascal
  - Contains parsing rules and grammar definitions
  - Implements program structure, expressions, statements parsing
- [parsetab.py](src/parsetab.py) - Generated parser tables

### Input Examples (input/)
- [example1.pas](input/example1.pas) - Simple "Hello World" program
- [example2.pas](input/example2.pas) - Finding maximum of three numbers
- [example3.pas](input/example3.pas) - Factorial calculation
- [example4.pas](input/example4.pas) - Prime number checker
- [example5.pas](input/example5.pas) - Array sum calculation
- [example6.pas](input/example6.pas) - Binary to integer conversion
- [example7.pas](input/example7.pas) - Binary to integer with function
- [mock_pascal.pas](input/mock_pascal.pas) - Example Pascal program
- [mock_pascal2.pas](input/mock_pascal2.pas) - Example Pascal program
- [mock_pascal3.pas](input/mock_pascal3.pas) - Example Pascal program

### Compiled Output (output/)
- VM code files (.vm) corresponding to each input example
- Generated virtual machine instructions for execution
  - Stack manipulation (PUSH/POP operations)
  - Control flow (jumps, conditionals)
  - Function calls and returns
  - I/O operations
