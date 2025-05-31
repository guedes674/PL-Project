class FunctionDeclaration:
    def __init__(self, name, parameter_list, return_type=None, block=None):
        """
        Represents a function declaration.

        :param name: The name of the function.
        :param parameter_list: A list of parameters for the function.
        :param return_type: The return type of the function.
        :param block: The block of code associated with the function.
        """
        self.name = name
        self.parameter_list = parameter_list
        self.return_type = return_type
        self.block = block

    def __repr__(self):
        return (f"FunctionDeclaration(name={self.name}, parameters={self.parameter_list}, "f"return_type={self.return_type}, block={self.block})")

class ProcedureDeclaration:
    def __init__(self, name, parameter_list, block):
        """
        Represents a procedure declaration.

        :param name: The name of the procedure.
        :param parameter_list: A list of parameters for the procedure.
        :param block: The block of code associated with the procedure.
        """
        self.name = name
        self.parameter_list = parameter_list
        self.block = block

    def __repr__(self) -> str:
        return (f"ProcedureDeclaration(name={self.name}, parameters={self.parameter_list}, "f"block={self.block})")
    
class Program:
    def __init__(self, header, block):
        """Represents a complete program."""
        self.header = header
        self.block = block

    def __repr__(self):
        return f"Program(header={self.header}, block={self.block})"

class ProgramHeader:
    def __init__(self, name, id_list=None):
        """Represents a program header (PROGRAM name (id_list);)."""
        self.name = name
        self.id_list = id_list or []

    def __repr__(self):
        return f"ProgramHeader(name={self.name}, id_list={self.id_list})"

class Block:
    def __init__(self, declarations, compound_statement):
        """Represents a block with declarations and statements."""
        self.declarations = declarations
        self.compound_statement = compound_statement

    def __repr__(self):
        return f"Block(declarations={self.declarations}, compound_statement={self.compound_statement})"

class VariableDeclaration:
    def __init__(self, variable_list):
        """Represents a variable declaration section."""
        self.variable_list = variable_list

    def __repr__(self):
        return f"VariableDeclaration(variables={self.variable_list})"

class Variable:
    def __init__(self, id_list, var_type):
        """Represents a variable with its type."""
        self.id_list = id_list
        self.var_type = var_type

    def __repr__(self):
        return f"Variable(ids={self.id_list}, type={self.var_type})"

class ConstantDeclaration:
    def __init__(self, constant_list):
        """Represents a constant declaration section."""
        self.constant_list = constant_list

    def __repr__(self):
        return f"ConstantDeclaration(constants={self.constant_list})"

class Constant:
    def __init__(self, name, value):
        """Represents a single constant definition."""
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Constant(name={self.name}, value={self.value})"

class TypeDeclaration:
    def __init__(self, type_list):
        """Represents a type declaration section."""
        self.type_list = type_list

    def __repr__(self):
        return f"TypeDeclaration(types={self.type_list})"

class TypeDefinition:
    def __init__(self, name, type_spec):
        """Represents a single type definition."""
        self.name = name
        self.type_spec = type_spec

    def __repr__(self):
        return f"TypeDefinition(name={self.name}, type={self.type_spec})"

class ArrayType:
    def __init__(self, index_range, element_type):
        """Represents an array type."""
        self.index_range = index_range  # tuple (start, end)
        self.element_type = element_type

    def __repr__(self):
        return f"ArrayType(range={self.index_range}, element_type={self.element_type})"

class RecordType:
    def __init__(self, field_list):
        """Represents a record type."""
        self.field_list = field_list

    def __repr__(self):
        return f"RecordType(fields={self.field_list})"

class Field:
    def __init__(self, id_list, field_type):
        """Represents a field in a record."""
        self.id_list = id_list
        self.field_type = field_type

    def __repr__(self):
        return f"Field(ids={self.id_list}, type={self.field_type})"

class Parameter:
    def __init__(self, id_list, param_type, is_var=False):
        """Represents a parameter in a function/procedure."""
        self.id_list = id_list
        self.param_type = param_type
        self.is_var = is_var  # for VAR parameters

    def __repr__(self):
        return f"Parameter(ids={self.id_list}, type={self.param_type}, is_var={self.is_var})"

class CompoundStatement:
    def __init__(self, statement_list):
        """Represents a compound statement (BEGIN...END)."""
        self.statement_list = statement_list

    def __repr__(self):
        return f"CompoundStatement(statements={self.statement_list})"

class AssignmentStatement:
    def __init__(self, variable, expression):
        """Represents an assignment statement."""
        self.variable = variable
        self.expression = expression

    def __repr__(self):
        return f"AssignmentStatement(var={self.variable}, expr={self.expression})"

class IfStatement:
    def __init__(self, condition, then_statement, else_statement=None):
        """Represents an if statement."""
        self.condition = condition
        self.then_statement = then_statement
        self.else_statement = else_statement

    def __repr__(self):
        return f"IfStatement(condition={self.condition}, then={self.then_statement}, else={self.else_statement})"

class WhileStatement:
    def __init__(self, condition, statement):
        """Represents a while loop."""
        self.condition = condition
        self.statement = statement

    def __repr__(self):
        return f"WhileStatement(condition={self.condition}, statement={self.statement})"

class RepeatStatement:
    def __init__(self, statement_list, condition):
        """Represents a repeat-until loop."""
        self.statement_list = statement_list
        self.condition = condition

    def __repr__(self):
        return f"RepeatStatement(statements={self.statement_list}, until={self.condition})"

class ForStatement:
    def __init__(self, control_variable, start_expression, end_expression, statement, downto=False):
        """Represents a for loop."""
        self.control_variable = control_variable  # Identifier node
        self.start_expression = start_expression  # Expression node
        self.end_expression = end_expression    # Expression node
        self.statement = statement                # Statement node
        self.downto = downto                      # Boolean

    def __repr__(self):
        return f"ForStatement(var={self.control_variable}, start={self.start_expression}, end={self.end_expression}, downto={self.downto}, statement={self.statement})"

class CaseStatement:
    def __init__(self, expression, case_list):
        """Represents a case statement."""
        self.expression = expression
        self.case_list = case_list

    def __repr__(self):
        return f"CaseStatement(expr={self.expression}, cases={self.case_list})"

class CaseElement:
    def __init__(self, constant_list, statement):
        """Represents a single case in a case statement."""
        self.constant_list = constant_list
        self.statement = statement

    def __repr__(self):
        return f"CaseElement(constants={self.constant_list}, statement={self.statement})"

class FunctionCall:
    def __init__(self, name, arguments=None):
        """Represents a function/procedure call."""
        self.name = name
        self.arguments = arguments or []

    def __repr__(self):
        return f"FunctionCall(name={self.name}, args={self.arguments})"

class IOCall:
    def __init__(self, operation, arguments):
        """Represents an I/O operation (read, write, etc.)."""
        self.operation = operation  # 'read', 'readln', 'write', 'writeln'
        self.arguments = arguments

    def __repr__(self):
        return f"IOCall(op={self.operation}, args={self.arguments})"

class BinaryOperation:
    def __init__(self, left, operator, right):
        """Represents a binary operation."""
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"BinaryOperation({self.left} {self.operator} {self.right})"

class UnaryOperation:
    def __init__(self, operator, operand):
        """Represents a unary operation."""
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"UnaryOperation({self.operator} {self.operand})"

class Literal:
    def __init__(self, value, literal_type=None):
        """Represents a literal value."""
        self.value = value
        self.literal_type = literal_type  # 'number', 'string', 'boolean', etc.

    def __repr__(self):
        return f"Literal(value={self.value}, type={self.literal_type})"

class Identifier:
    def __init__(self, name):
        """Represents an identifier/variable reference."""
        self.name = name

    def __repr__(self):
        return f"Identifier(name={self.name})"

class ArrayAccess:
    def __init__(self, array, index):
        self.array = array  # Identifier node for the array variable
        self.index = index  # Expression node for the index

    def __repr__(self):
        return f"ArrayAccess(array={self.array}, index={self.index})"

class FieldAccess:
    def __init__(self, record, field):
        """Represents field access (record.field)."""
        self.record = record
        self.field = field

    def __repr__(self):
        return f"FieldAccess(record={self.record}, field={self.field})"