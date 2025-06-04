# PL-Project
Pratical Project for the Language Processing class

## Autores

<div style="display: flex; justify-content: space-between; margin: 20px 0;">
  <div style="text-align: center; width: 30%;">
    <p><strong>Tiago Carneiro</strong><br>A93207</p>
    <img src="media/a93207.jpg" alt="Tiago Carneiro" width="200">
  </div>
  
  <div style="text-align: center; width: 30%;">
    <p><strong>Tiago Guedes</strong><br>A97369</p>
    <img src="https://github.com/user-attachments/assets/c90bfde7-55cc-41ed-927c-8bc988d84250" alt="Tiago Guedes" width="250">
  </div>
  
  <div style="text-align: center; width: 30%;">
    <p><strong>Diogo Gonçalves</strong><br>A101919</p>
    <img src="media/diogo.jpg" alt="Diogo Gonçalves" width="180">
  </div>
</div>


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