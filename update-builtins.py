import fileinput
import os
import re
import sys

class Node():
    def __init__(self, data):
        self.data = data
        self.children = {}
        self.parent = None
        self.is_end = False

def add_builtin(tree : Node, input_tokens : list[str]):
    head = input_tokens[0]

    if head not in tree.children.keys():
        tree.children[head] = Node(head)

    if len(input_tokens) > 1:
        add_builtin(tree.children[head], input_tokens[1:])
    else:
        tree.children[head].is_end = True

def print_tree(node: Node):
    if len(node.children.keys()) == 0:
        return node.data
    else:
        child_str = []

        for name, child in node.children.items():
            if child.is_end:
                child_str.append(child.data)

            if len(list(child.children.keys())) != 0:
                child_str.append(print_tree(child))

        if len(child_str) <= 1:
            if node.data == '':
                return f'{node.data}({child_str[0]})'
            else:
                return f'{node.data}_{child_str[0]}'
        else:
            s = '|'.join(child_str)

            if node.data == '':
                return f'{node.data}({s})'
            else:
                return f'{node.data}_({s})'


constants    = set()
variables    = set()
functions    = set()
control_pars = set()
event_pars   = set()

data = {
           'constants'    : constants,
           'variables'    : variables,
           'functions'    : functions,
           'control_pars' : control_pars,
           'event_pars'   : event_pars,
       }

section = None

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'compiler'))

from ksp_builtins_data import builtins_data

lines = builtins_data.replace('\r\n', '\n').split('\n')

for line in lines:
    line = line.strip()

    if line.startswith('['):
        section = line[1:-1].strip()
    elif line:
        if section in data:
            if section == 'functions':
                m = re.match(r'(?P<name>\w+)\(?', line)
                data[section].add(m.group('name'))
                continue

            if section == 'constants':
                m = re.match(r'(?P<control_par>\$CONTROL_PAR_\w+?)|(?P<event_par>\$EVENT_PAR_\w+?)', line)

                if m:
                    control_par, event_par = m.group('control_par'), m.group('event_par')

                    if control_par:
                        control_pars.add(line)
                    elif event_par:
                        event_pars.add(line)

            data[section].add(line)

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

all_builtins = sorted(list(constants.union(variables)), key=natsort)
all_functions = sorted(list(functions), key=natsort)
control_pars = sorted(list(control_pars), key=natsort)
event_pars = sorted(list(event_pars), key=natsort)

prefixes = '$@~%!?'

_int = Node('')
_real = Node('')
_str = Node('')
_intarray = Node('')
_strarray = Node('')
_funs = Node('')
_funs_legacy = Node('')

tree = {'$' : _int,
        '~' : _real,
        '@' : _str,
        '%' : _intarray,
        '!' : _strarray,
        'f' : _funs,
        'l' : _funs_legacy,
        }

for item in all_builtins:
    prefix = ''
    name = ''

    if item[0] in prefixes:
        prefix = item[0]
        name = item[1:]
    else:
        name = item

    add_builtin(tree[prefix], name.split('_'))

for item in all_functions:
    s = item.split('_')

    if item.startswith('_'):
        s[0] = '_'
        add_builtin(tree['l'], s)
    else:
        add_builtin(tree['f'], s)

cp         = ''
ep         = ''
funs       = ''
constsvars = ''

for p in tree:
    s = print_tree(tree[p])

    if p not in 'fl':
        prefix = p

        if p == '$':
            prefix = '\\$'

        constsvars += f'({prefix})?\\b{s}\\b'

        if p in '$~@%':
            constsvars += '|'
    else:
        if p == 'f':
            funs += f'\\b{s}|'
        else:
            s = s.replace('__', '_')
            funs += f'{s}\\b'

cp_remap = {'pos_x' : '(pos_)?x', 'pos_y' : '(pos_)?y', 'max_value' : 'max(_value)?', 'min_value' : 'min(_value)?', 'default_value' : 'default(_value)?'}
ep_remap = {'0' : '(par_)?0', '1' : '(par_)?1', '2' : '(par_)?2', '3' : '(par_)?3'}

def print_ctrl_or_event_pars_as_regex(par_list, remap):
    out = ''

    for i, item in enumerate(par_list):

        sep = '|' if i != len(par_list) - 1 else ''

        m = re.match(r'(\$CONTROL_PAR_|\$EVENT_PAR_)(\w+)', item)

        if m:
            item = m.group(2).lower()

            if item in remap:
                item = remap[item]

            out += f'{item}{sep}'

    return out

cp = print_ctrl_or_event_pars_as_regex(control_pars, cp_remap)
ep = print_ctrl_or_event_pars_as_regex(event_pars, ep_remap)

# with fileinput.input('KSP.sublime-syntax', inplace = True) as f:
#     for line in f:
#         if line.startswith('  builtin_const'):
#             modified_line = f'  builtin_consts_and_vars: \'{constsvars}\''
#             print(modified_line)
#         elif line.startswith('  builtin_fun'):
#             modified_line = f'  builtin_functions: \'{funs}\''
#             print(modified_line)
#         elif line.startswith('  builtin_par'):
#             modified_line = f'  builtin_param_shorthands: \'(->)\\s*({cp}|{ep})\\b\''
#             print(modified_line)
#         else:
#             print(line, end = '')