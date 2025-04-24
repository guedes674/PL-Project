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