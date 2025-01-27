import re
from collections import defaultdict

class LexicalAnalyzer:
    def __init__(self, input_text):
        self.input_text = input_text
        self.position = 0
        self.current_line = 1
        self.reserved_words = {
            'int', 'float', 'void', 'return', 'while', 'cin', 'cout',
            'continue', 'break', 'main'
        }
        self.symbols = {
            '{', '}', '(', ')', ',', ';', '+', '-', '*', '/',
            '==', '!=', '>', '>=', '<', '<=', '=', '<<', '>>'
        }
        self.ignore_keywords = {'#include', '<', '>', 'using', 'namespace', 'std', 'iostream'}

    def tokenize(self):
        tokens = []
        while self.position < len(self.input_text):
            current_char = self.input_text[self.position]

            if current_char == '\n':
                self.current_line += 1
                self.position += 1
                continue

            if current_char.isspace():
                self.position += 1
                continue

            if current_char in self.ignore_keywords:
                self._skip_ignored()
                continue

            if current_char.isdigit():
                token = self.read_number()
                tokens.append(('NUMBER', token, self.current_line))
                continue

            if current_char.isalpha() or current_char == '_':
                token = self.read_identifier()
                if token in self.reserved_words:
                    tokens.append(('RESERVED_WORD', token, self.current_line))
                else:
                    tokens.append(('IDENTIFIER', token, self.current_line))
                continue

            if current_char == '"':
                token = self.read_string()
                tokens.append(('STRING', token, self.current_line))
                continue

            if current_char in self.symbols:
                combined = self.check_combined_symbols()
                if combined:
                    tokens.append(('SYMBOL', combined, self.current_line))
                else:
                    tokens.append(('SYMBOL', current_char, self.current_line))
                continue

            self.position += 1

        return tokens

    def _skip_ignored(self):
        while self.position < len(self.input_text) and self.input_text[self.position] in self.ignore_keywords:
            self.position += 1

    def read_number(self):
        number = ''
        while self.position < len(self.input_text) and self.input_text[self.position].isdigit():
            number += self.input_text[self.position]
            self.position += 1
        return number

    def read_identifier(self):
        identifier = ''
        while self.position < len(self.input_text) and (self.input_text[self.position].isalnum() or self.input_text[self.position] == '_'):
            identifier += self.input_text[self.position]
            self.position += 1
        return identifier

    def read_string(self):
        string = ''
        self.position += 1
        while self.position < len(self.input_text) and self.input_text[self.position] != '"':
            string += self.input_text[self.position]
            self.position += 1
        self.position += 1
        return string

    def check_combined_symbols(self):
        double_char = self.input_text[self.position:self.position+2]
        if double_char in ('==', '!=', '>=', '<=', '<<', '>>'):
            self.position += 2
            return double_char
        self.position += 1
        return None

class ParseTable:
    def __init__(self):
        self.non_terminals = ['Start', 'S', 'N', 'M', 'T', 'V', 'Id', 'L', 'Z', 'Operation', 'P', 'O', 'W', 'Assign', 'Expression', 'K', 'Loop', 'Input', 'F', 'Output', 'H', 'C']
        self.terminals = [
            '#include', 'using', 'namespace', 'std', ';', 'int', 'float', 'main',
            '(', ')', '{', '}', 'return', '0', 'while', 'cin', 'cout', '>>', '<<',
            'string', 'number', 'identifier', '==', '>=', '<=', '!=', '+', '-', '*',
            ',', '"', '$', '='
        ]
        self.productions = {
            'Start': [['S', 'N', 'M']],
            'S': [['#include', 'S'], ['ε']],
            'N': [['using', 'namespace', 'std', ';'], ['ε']],
            'M': [['int', 'main', '(', ')', '{', 'T', 'V', '}']],
            'T': [['Id', 'T'], ['L', 'T'], ['Loop', 'T'], ['Input', 'T'], ['Output', 'T'], ['ε']],
            'V': [['return', '0', ';']],
            'Id': [['int', 'L'], ['float', 'L']],
            'L': [['identifier', 'Assign', 'Z']],
            'Z': [[',', 'identifier', 'Assign', 'Z'], [';']],
            'Operation': [['number', 'P'], ['identifier', 'P']],
            'P': [['O', 'W', 'P'], ['ε']],
            'O': [['+'], ['-'], ['*']],
            'W': [['number'], ['identifier']],
            'Assign': [['=', 'Operation'], ['ε']],
            'Expression': [['Operation', 'K', 'Operation']],
            'K': [['=='], ['>='], ['<='], ['!=']],
            'Loop': [['while', '(', 'Expression', ')', '{', 'T', '}']],
            'Input': [['cin', '>>', 'identifier', 'F', ';']],
            'F': [['>>', 'identifier', 'F'], ['ε']],
            'Output': [['cout', '<<', 'C', 'H', ';']],
            'H': [['<<', 'C', 'H'], ['ε']],
            'C': [['number'], ['string'], ['identifier']]
        }
        self.first = {}
        self.follow = {}
        self._compute_first()
        self._compute_follow()
        self.table = defaultdict(dict)
        self._build_table()

    def _compute_first(self):
        for terminal in self.terminals:
            self.first[terminal] = {terminal}

        for nt in self.non_terminals:
            self.first[nt] = set()

        updated = True
        while updated:
            updated = False
            for nt in self.non_terminals:
                for production in self.productions[nt]:
                    first_set = self._get_first_of_sequence(production)
                    if not first_set.issubset(self.first[nt]):
                        self.first[nt] |= first_set
                        updated = True

    def _get_first_of_sequence(self, sequence):
        first_set = set()
        for symbol in sequence:
            if symbol == 'ε':
                first_set.add('ε')
                break
            if symbol in self.terminals:
                first_set.add(symbol)
                break
            if symbol in self.non_terminals:
                first_set |= self.first[symbol] - {'ε'}
                if 'ε' not in self.first[symbol]:
                    break
        else:
            first_set.add('ε')
        return first_set

    def _compute_follow(self):
        for nt in self.non_terminals:
            self.follow[nt] = set()
        self.follow['Start'].add('$')

        updated = True
        while updated:
            updated = False
            for nt in self.non_terminals:
                for production in self.productions[nt]:
                    for i, symbol in enumerate(production):
                        if symbol in self.non_terminals:
                            next_symbols = production[i+1:]
                            first_of_next = self._get_first_of_sequence(next_symbols)
                            if 'ε' in first_of_next:
                                first_of_next.remove('ε')
                                if not first_of_next.issubset(self.follow[symbol]):
                                    self.follow[symbol] |= first_of_next | self.follow[nt]
                                    updated = True
                            else:
                                if not first_of_next.issubset(self.follow[symbol]):
                                    self.follow[symbol] |= first_of_next
                                    updated = True

    def _build_table(self):
        for nt in self.non_terminals:
            for production in self.productions.get(nt, []):
                first_alpha = self._get_first_of_sequence(production)
                for terminal in first_alpha:
                    if terminal != 'ε':
                        self.table[nt][terminal] = production
                if 'ε' in first_alpha:
                    for terminal in self.follow[nt]:
                        self.table[nt][terminal] = production

    def get_production(self, non_terminal, terminal):
        return self.table.get(non_terminal, {}).get(terminal, None)

    def display(self):
        print("\nParse Table:")
        print("Non-Terminal\tTerminal\tProduction")
        for nt in self.non_terminals:
            for t in self.terminals + ['$']:
                prod = self.table[nt].get(t, None)
                if prod:
                    print(f"{nt}\t\t{t}\t\t{' '.join(prod)}")

class ParseTreeNode:
    def __init__(self, name, value=None, line=None):
        self.name = name
        self.value = value
        self.line = line
        self.children = []

class ParseTree:
    def __init__(self, tokens, productions):
        self.root = ParseTreeNode("Start")
        self.tokens = tokens
        self.build_tree(productions)

    def build_tree(self, productions):
        stack = [self.root]
        token_ptr = 0

        for prod in productions:
            non_terminal, rhs = prod.split(" → ")
            rhs_elements = rhs.split()

            current_node = stack.pop()

            for elem in reversed(rhs_elements):
                new_node = ParseTreeNode(elem)
                if elem in ['int', 'float', 'identifier', 'number', 'string']:
                    if token_ptr < len(self.tokens):
                        new_node.value = self.tokens[token_ptr][1]
                        new_node.line = self.tokens[token_ptr][2]
                        token_ptr += 1
                current_node.children.append(new_node)
                if elem in ['M', 'T', 'Id', 'Loop', 'Input', 'Output']:
                    stack.append(new_node)

    def display(self):
        print("\nParse Tree:")
        self._print_tree(self.root, 0)

    def _print_tree(self, node, level):
        node_info = node.name
        if node.value:
            node_info += f" ({node.value}, Line: {node.line})"
        print("  " * level + node_info)
        for child in node.children:
            self._print_tree(child, level + 1)

class PredictiveParser:
    def __init__(self, parse_table):
        self.parse_table = parse_table
        self.productions = []

    def parse(self, tokens):
        stack = ['$', 'M']
        input_tokens = []
        for token in tokens:
            if token[0] == 'IDENTIFIER':
                input_tokens.append('identifier')
            elif token[0] == 'RESERVED_WORD':
                input_tokens.append(token[1])
            else:
                input_tokens.append(token[1])
        input_tokens.append('$')

        input_index = 0

        while len(stack) > 0:
            top = stack[-1]
            current_token = input_tokens[input_index]

            print(f"Stack: {stack}")
            print(f"Current token: {current_token}")

            if top == current_token:
                stack.pop()
                input_index += 1
            elif top in self.parse_table.table:
                production = self.parse_table.get_production(top, current_token)
                if production:
                    print(f"Applying production: {top} → {' '.join(production)}")
                    stack.pop()
                    if production != ['ε']:
                        self.productions.append(f"{top} → {' '.join(production)}")
                        stack.extend(reversed(production))
                else:
                    print(f"No production found for {top} and {current_token}")
                    raise ValueError(f"Syntax Error: No production found for {top} and {current_token}")
            else:
                print(f"unexpected token '{current_token}' at position {input_index}")
                raise ValueError(f"Syntax Error: unexpected token '{current_token}' at position {input_index}")

        print("\nProduction sequence:")
        for prod in self.productions:
            print(prod)
        return self.productions

class TableDrivenPredictiveParser:
    def __init__(self, parse_table):
        self.parse_table = parse_table

    def parse(self, input_tokens):
        stack = ['$', 'Start']
        input_tokens.append('$')
        input_index = 0
        output_productions = []

        while len(stack) > 0:
            X = stack[-1]
            a = input_tokens[input_index]

            if X == a:
                stack.pop()
                input_index += 1
            elif X in self.parse_table.terminals:
                raise ValueError(f"Syntax Error: Unexpected token '{a}' at position {input_index}")
            else:
                production = self.parse_table.get_production(X, a)
                if production is None:
                    raise ValueError(f"Syntax Error: No production found for {X} and {a}")

                output_productions.append(f"{X} → {' '.join(production)}")
                stack.pop()
                if production != ['ε']:
                    stack.extend(reversed(production))

        return output_productions

class TokenTable:
    def __init__(self):
        self.table = {}

    def add_token(self, token_name, value):
        key = hash((token_name, value))
        self.table[key] = (token_name, value)

    def display(self):
        print("\nToken Table:")
        print("Hash Key\t\tToken Name\tValue")
        for key, (name, val) in self.table.items():
            print(f"{abs(key):<16}\t{name}\t\t{val}")

    def error_handling(self):
        errors = []
        for token in self.parse_tree.tokens:
            if token[1] == '=' and token[0] == 'SYMBOL':
                if not any(t[0] in ['NUMBER', 'IDENTIFIER'] for t in self.parse_tree.tokens if t[2] == token[2]):
                    errors.append(f"Error at line {token[2]}: Invalid assignment")
        for error in errors:
            print(error)

class Bonus:
    def __init__(self, parse_tree):
        self.parse_tree = parse_tree

    def find_first_definition(self, identifier):
        def dfs(node):
            if node.name == 'L' and node.children:
                id_node = node.children[0]
                if id_node.value == identifier:
                    return id_node.line
            for child in node.children:
                result = dfs(child)
                if result:
                    return result
            return None

        line = dfs(self.parse_tree.root)
        return f"First definition of '{identifier}' at line {line}" if line else f"'{identifier}' is not defined"

if __name__ == "__main__":
    input_text = """
    #include <iostream>
    using namespace std;
    int main(){
        int x;
        int s=0, t=10;
        while (t >= 0){
            cin>>x;
            t = t - 1;
            s = s + x;
        }
        cout<<"sum="<<s;
        return 0;
    }
    """

    lexer = LexicalAnalyzer(input_text)
    tokens = lexer.tokenize()

    print("\nTokens:")
    for token in tokens:
        print(token)

    token_table = TokenTable()
    for token in tokens:
        token_table.add_token(token[0], token[1])
    token_table.display()
    parse_table = ParseTable()
    parse_table.display()

    parser = PredictiveParser(parse_table)
    productions = parser.parse(tokens)

    parse_tree = ParseTree(tokens, productions)
    parse_tree.display()



    token_table.error_handling()

    bonus = Bonus(parse_tree)
    print(bonus.find_first_definition("s"))
