class ASTNode:
    def __init__(self, lineno=None): # Add lineno attribute
        self.lineno = lineno
        # ... other common attributes ...

class FunctionDeclaration(ASTNode):
    def __init__(self, name, parameter_list, return_type=None, block=None, lineno=None):
        """
        Represents a function declaration.

        :param name: The name of the function.
        :param parameter_list: A list of parameters for the function.
        :param return_type: The return type of the function.
        :param block: The block of code associated with the function.
        """
        super().__init__(lineno)
        self.name = name
        self.parameter_list = parameter_list
        self.return_type = return_type
        self.block = block

    def __repr__(self):
        return (f"FunctionDeclaration(name={self.name}, parameters={self.parameter_list}, "f"return_type={self.return_type}, block={self.block})")

class ProcedureDeclaration(ASTNode):
    def __init__(self, name, parameter_list, block, lineno=None):
        """
        Represents a procedure declaration.

        :param name: The name of the procedure.
        :param parameter_list: A list of parameters for the procedure.
        :param block: The block of code associated with the procedure.
        """
        super().__init__(lineno)
        self.name = name
        self.parameter_list = parameter_list
        self.block = block

    def __repr__(self) -> str:
        return (f"ProcedureDeclaration(name={self.name}, parameters={self.parameter_list}, "f"block={self.block})")
    
class Program(ASTNode):
    def __init__(self, header, block, lineno=None):
        """Represents a complete program."""
        super().__init__(lineno)
        self.header = header
        self.block = block

    def __repr__(self):
        return f"Program(header={self.header}, block={self.block})"

class ProgramHeader(ASTNode):
    def __init__(self, name, id_list=None, lineno=None):
        """Represents a program header (PROGRAM name (id_list);)."""
        super().__init__(lineno)
        self.name = name
        self.id_list = id_list or []

    def __repr__(self):
        return f"ProgramHeader(name={self.name}, id_list={self.id_list})"

class Block(ASTNode):
    def __init__(self, declarations, compound_statement, lineno=None):
        """Represents a block with declarations and statements."""
        super().__init__(lineno)
        self.declarations = declarations
        self.compound_statement = compound_statement

    def __repr__(self):
        return f"Block(declarations={self.declarations}, compound_statement={self.compound_statement})"

class VariableDeclaration(ASTNode):
    def __init__(self, variable_list, lineno=None):
        """Represents a variable declaration section."""
        super().__init__(lineno)
        self.variable_list = variable_list

    def __repr__(self):
        return f"VariableDeclaration(variables={self.variable_list})"

class Variable(ASTNode):
    def __init__(self, id_list, var_type, lineno=None):
        """Represents a variable with its type."""
        super().__init__(lineno)
        self.id_list = id_list
        self.var_type = var_type

    def __repr__(self):
        return f"Variable(ids={self.id_list}, type={self.var_type})"

class ConstantDeclaration(ASTNode):
    def __init__(self, constant_list, lineno=None):
        """Represents a constant declaration section."""
        super().__init__(lineno)
        self.constant_list = constant_list

    def __repr__(self):
        return f"ConstantDeclaration(constants={self.constant_list})"

class Constant(ASTNode):
    def __init__(self, name, value, lineno=None):
        """Represents a single constant definition."""
        super().__init__(lineno)
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Constant(name={self.name}, value={self.value})"

class TypeDeclaration(ASTNode):
    def __init__(self, type_list, lineno=None):
        """Represents a type declaration section."""
        super().__init__(lineno)
        self.type_list = type_list

    def __repr__(self):
        return f"TypeDeclaration(types={self.type_list})"

class TypeDefinition(ASTNode):
    def __init__(self, name, type_spec, lineno=None):
        """Represents a single type definition."""
        super().__init__(lineno)
        self.name = name
        self.type_spec = type_spec

    def __repr__(self):
        return f"TypeDefinition(name={self.name}, type={self.type_spec})"

class ArrayType(ASTNode):
    def __init__(self, index_range, element_type, lineno=None):
        """Represents an array type."""
        super().__init__(lineno)
        self.index_range = index_range  # tuple (start, end)
        self.element_type = element_type

    def __repr__(self):
        return f"ArrayType(range={self.index_range}, element_type={self.element_type})"

class RecordType(ASTNode):
    def __init__(self, field_list, lineno=None):
        """Represents a record type."""
        super().__init__(lineno)
        self.field_list = field_list

    def __repr__(self):
        return f"RecordType(fields={self.field_list})"

class Field(ASTNode):
    def __init__(self, id_list, field_type, lineno=None):
        """Represents a field in a record."""
        super().__init__(lineno)
        self.id_list = id_list
        self.field_type = field_type

    def __repr__(self):
        return f"Field(ids={self.id_list}, type={self.field_type})"

class Parameter(ASTNode):
    def __init__(self, id_list, param_type, is_var=False, lineno=None):
        """Represents a parameter in a function/procedure."""
        super().__init__(lineno)
        self.id_list = id_list
        self.param_type = param_type
        self.is_var = is_var  # for VAR parameters

    def __repr__(self):
        return f"Parameter(ids={self.id_list}, type={self.param_type}, is_var={self.is_var})"

class CompoundStatement(ASTNode):
    def __init__(self, statement_list, lineno=None):
        """Represents a compound statement (BEGIN...END)."""
        super().__init__(lineno)
        self.statement_list = statement_list

    def __repr__(self):
        return f"CompoundStatement(statements={self.statement_list})"

class AssignmentStatement(ASTNode):
    def __init__(self, variable, expression, lineno=None):
        """Represents an assignment statement."""
        super().__init__(lineno)
        self.variable = variable
        self.expression = expression

    def __repr__(self):
        return f"AssignmentStatement(var={self.variable}, expr={self.expression})"

class IfStatement(ASTNode):
    def __init__(self, condition, then_statement, else_statement=None, lineno=None):
        """Represents an if statement."""
        super().__init__(lineno)
        self.condition = condition
        self.then_statement = then_statement
        self.else_statement = else_statement

    def __repr__(self):
        return f"IfStatement(condition={self.condition}, then={self.then_statement}, else={self.else_statement})"

class WhileStatement(ASTNode):
    def __init__(self, condition, statement, lineno=None):
        """Represents a while loop."""
        super().__init__(lineno)
        self.condition = condition
        self.statement = statement

    def __repr__(self):
        return f"WhileStatement(condition={self.condition}, statement={self.statement})"

class RepeatStatement(ASTNode):
    def __init__(self, statement_list, condition, lineno=None):
        """Represents a repeat-until loop."""
        super().__init__(lineno)
        self.statement_list = statement_list
        self.condition = condition

    def __repr__(self):
        return f"RepeatStatement(statements={self.statement_list}, until={self.condition})"

class ForStatement(ASTNode):
    def __init__(self, control_variable, start_expression, end_expression, statement, downto=False, lineno=None):
        """Represents a for loop."""
        super().__init__(lineno)
        self.control_variable = control_variable  # Identifier node
        self.start_expression = start_expression  # Expression node
        self.end_expression = end_expression    # Expression node
        self.statement = statement                # Statement node
        self.downto = downto                      # Boolean

    def __repr__(self):
        return f"ForStatement(var={self.control_variable}, start={self.start_expression}, end={self.end_expression}, downto={self.downto}, statement={self.statement})"

class CaseStatement(ASTNode):
    def __init__(self, expression, case_list, lineno=None):
        """Represents a case statement."""
        super().__init__(lineno)
        self.expression = expression
        self.case_list = case_list

    def __repr__(self):
        return f"CaseStatement(expr={self.expression}, cases={self.case_list})"

class CaseElement(ASTNode):
    def __init__(self, constant_list, statement, lineno=None):
        """Represents a single case in a case statement."""
        super().__init__(lineno)
        self.constant_list = constant_list
        self.statement = statement

    def __repr__(self):
        return f"CaseElement(constants={self.constant_list}, statement={self.statement})"

class FunctionCall(ASTNode):
    def __init__(self, name, arguments=None, lineno=None):
        """Represents a function/procedure call."""
        super().__init__(lineno)
        self.name = name
        self.arguments = arguments or []

    def __repr__(self):
        return f"FunctionCall(name={self.name}, args={self.arguments})"

class IOCall(ASTNode):
    def __init__(self, operation, arguments, lineno=None):
        """Represents an I/O operation (read, write, etc.)."""
        super().__init__(lineno)
        self.operation = operation  # 'read', 'readln', 'write', 'writeln'
        self.arguments = arguments

    def __repr__(self):
        return f"IOCall(op={self.operation}, args={self.arguments})"

class BinaryOperation(ASTNode):
    def __init__(self, left, operator, right, lineno=None):
        """Represents a binary operation."""
        super().__init__(lineno)
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"BinaryOperation({self.left} {self.operator} {self.right})"

class UnaryOperation(ASTNode):
    def __init__(self, operator, operand, lineno=None):
        """Represents a unary operation."""
        super().__init__(lineno)
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"UnaryOperation({self.operator} {self.operand})"

class Literal(ASTNode):
    def __init__(self, value, literal_type=None, lineno=None):
        """Represents a literal value."""
        super().__init__(lineno)
        self.value = value
        self.literal_type = literal_type  # 'number', 'string', 'boolean', etc.

    def __repr__(self):
        return f"Literal(value={self.value}, type={self.literal_type})"

class Identifier(ASTNode):
    def __init__(self, name, lineno=None):
        """Represents an identifier/variable reference."""
        super().__init__(lineno)
        self.name = name

    def __repr__(self):
        return f"Identifier(name={self.name})"

class ArrayAccess(ASTNode):
    def __init__(self, array, index, lineno=None):
        self.array = array  # Identifier node for the array variable
        self.index = index  # Expression node for the index
        super().__init__(lineno)

    def __repr__(self):
        return f"ArrayAccess(array={self.array}, index={self.index})"

class FieldAccess(ASTNode):
    def __init__(self, record, field, lineno=None):
        """Represents field access (record.field)."""
        self.record = record
        self.field = field
        super().__init__(lineno)

    def __repr__(self):
        return f"FieldAccess(record={self.record}, field={self.field})"