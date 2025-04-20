from lark import Lark, Transformer

mini_lang_grammar = r"""

    ?program: statement+

    ?statement: assignment ";"
            | print_stmt ";"

    assignment: NAME "=" expression

    print_stmt: "print" expression

    ?expression: sum

    ?sum: product
        | sum "+" product    -> add
        | sum "-" product    -> sub

    ?product: atom
        | product "*" atom   -> mul
        | product "/" atom   -> div

    ?atom: NUMBER            -> number
        | NAME               -> variable
        | "-" atom           -> neg
        | "(" expression ")"

    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

class MiniLangInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.variables = {}
    
    def assignment(self, args):
        name, value = args
        self.variables[name] = value
        return value
    
    def print_stmt(self, args):
        value = args[0]
        print(value)
        return value
    
    def add(self, args):
        left, right = args
        return left + right
    
    def sub(self, args):
        left, right = args
        return left - right
    
    def mul(self, args):
        left, right = args
        return left * right
    
    def div(self, args):
        left, right = args
        return left / right
    
    def neg(self, args):
        return -args[0]
    
    def number(self, args):
        return float(args[0])
    
    def variable(self, args):
        name = args[0]
        if name not in self.variables:
            raise NameError(f"Variable '{name}' not defined")
        return self.variables[name]

parser = Lark(mini_lang_grammar, parser='lalr', transformer=MiniLangInterpreter(), start='program')

program = """
    x = 130;
    y = 20;
    z = x + y * 2;
    print z;
"""

parser.parse(program)  # 50.0