import os
import re
import pprint

def parse_method(text, base):
    name_pattern = "[\\w.#]+"
    arg_pattern = "[^,()]+"
    
    pattern = f'(?i){base}'
    pattern += '\\s+'
    pattern += f'({name_pattern})'
    pattern += '(?:'
    pattern += '\\(\\s*\\)'
    pattern += '|'
    pattern += '(?:'
    pattern += '\\('
    pattern += f'({arg_pattern}(?:\\s*,\\s*{arg_pattern})*)'
    pattern += '\\)'
    pattern += ')'
    pattern += ')'
    pattern += '.?'
    
    match = re.match(pattern, text.strip())
    
    if match:
        # Split the names on dots
        names = match.group(1).split('.')
        # Split the args on commas if they exist
        args = [arg.strip() for arg in match.group(2).split(',')] if match.group(2) else []
        return names, args
    return None

def parse_node(text):
    pattern = r"(?i)node\s+(\w+)(?:\s+from\s+(\w+))?\s*:"
    match = re.match(pattern, text)
    if match:
        return match.groups()  # (node_name, base_name or None)
    return None

class Macro():
    def __init__(self, name, args):
        self.name = name
        self.args = args
        
class Function():
    def __init__(self, name, args, node, macro):
        self.name = name
        self.args = args
        self.node = node
        self.macro = macro
        
class Node():
    def __init__(self, name, base):
        self.name = name
        self.base = base

macros = []
functions = []
nodes = []
code_tree = {}
for r, d, files in os.walk('G:/Dropbox/Work/Impact Soundworks/Repositories/_IVLS'):
    for f in files:
        if '.ksp' in f:
            with open(os.path.join(r, f), 'r') as code_file:
                code = code_file.readlines()
                
                parent_node = None
                parent_macro = None
                
                for l in code:
                    if 'end macro' in l:
                        parent_macro = None

                    if 'end macro' in l:
                        parent_node = None
                    
                    match = parse_method(l, 'macro')
                    if match:
                        names, args = match
                        
                        head = code_tree
                        for n in names:
                            head['has_children'] = True
                            if not n in head.keys():
                                head[n] = {'has_children': False}
                            head = head[n]
                        
                        head['data'] = Macro(".".join(names), args)
                        parent_macro = head['data']
                        macros.append(head['data'])
                        
                        print(f'Macro {parent_macro.name}, id {parent_macro}')

                    match = parse_method(l, 'function')
                    if match:
                        names, args = match
                        
                        head = code_tree
                        for n in names:
                            head['has_children'] = True
                            if not n in head.keys():
                                head[n] = {'has_children': False}
                            head = head[n]
                            
                        func = head['data'] = Function(".".join(names), args, parent_node, parent_macro)
                        functions.append(func)
                        
                    match = parse_node(l)
                    if match:
                        name, base = match
                        
                        head = code_tree
                        for n in names:
                            head['has_children'] = True
                            if not n in head.keys():
                                head[n] = {'has_children': False}
                            head = head[n]
                        
                        parent_node = head['data'] = Node(".".join(names), base)
                        nodes.append(head['data'])

memory_macro = None
memory_node = None

with open('names.txt', 'w') as fout:
    def write(s):
        fout.write(s + '\n')
    
    def print_obj(obj, obj_filter=None):
        if obj_filter and not obj_filter(obj):
            return
            
        global memory_macro
        global memory_node
        
        if isinstance(obj, Macro):
            write(f'{obj.name} - {obj.args}')
        elif isinstance(obj, Function):
                o = f'{obj.name} - {obj.args}'
                
                if obj.node:
                    o = f'                => ' + o
                    if memory_node != obj.node:
                        memory_node = obj.node
                        o = f'{obj.node.name} ::\n' + o
                        
                if obj.macro:
                    print(f'Macro {obj.macro.name}, id {obj.macro}')
                    o = f'                => ' + o
                    if memory_macro != obj.macro:
                        memory_macro = obj.macro
                        o = f'{obj.macro.name} ::\n' + o

                write(o)
        elif isinstance(obj, Node):
            write(f'{obj.name} extends from {obj.base}')

    def print_code_family(family, type, obj_filter=None):
        for item in family.keys():
            result = family[item]
            if isinstance(result, dict):
                if result['has_children']:
                    print_code_family(result, type, obj_filter)
                    continue

                print_obj(result['data'], obj_filter)

    for n in nodes:
        print_code_family(code_tree, Function, (lambda obj, m=n: isinstance(obj, Function) and obj.node == m))
        
    for n in macros:
        print_code_family(code_tree, Function, (lambda obj, m=n: isinstance(obj, Function) and obj.macro == m))
