from collections import defaultdict, deque, OrderedDict
import utils

voice_logic_taskfunc = '''
    taskfunc ivls.{}.VoiceLogic(var self, var self_invalid, nenv)
        declare node_id := NodeEnv[nenv].node_id
        declare thread := Voice[self].thread

        if Voice[self].input = ivls.input_type.VOICE_ON
            {}
        else if Voice[self].input = ivls.input_type.VOICE_OFF
            {}
        end if
    end taskfunc
'''

voice_logic_case = '''
case ivls.node.{0}
    ivls.{0}.VoiceLogic(self, self_invalid, nenv)
'''

node_ui_switcher = '''
    if ivls.node.{0} = (ivls.NodeUI -> value)
        {1}
    else
        {2}
    end if
'''

def parse_node_macros(code_lines, define_cache):
    node_cb = OrderedDict()

    current_node = None
    current_callback = None

    node_names = []
    for define_constant in define_cache:
        if define_constant.name == 'IVLS_ALL_NODES':
            node_order = define_constant.value
            node_names = utils.split_args(node_order, 0)
            break

    for name in node_names:
        node_cb[name] = defaultdict(list)

    pruned_node_code = deque()
    for line_obj in code_lines:
        line = line_obj.command.lstrip()
        
        if line.startswith("macro Node."):
            parts = line.split(".")
            current_node = ".".join(parts[1:-1])
            current_callback = parts[-1].split("(")[0]
        elif line.startswith("end macro"):
            if not current_node:
                pruned_node_code.append(line_obj)
            
            current_node = None
            current_callback = None
        else:
            if current_node and current_callback and current_node in node_order:
                if line.startswith('message('):
                    line_obj.command = line_obj.command.replace('message(', 'message("[ {} | {} ]" & '.format(current_node, current_callback))
                node_cb[current_node][current_callback].append(line_obj)
            else:
                if not current_node:
                    pruned_node_code.append(line_obj)

    from ksp_compiler import Line
    pre_assembly_lines = deque()
    voiced_nodes = []
    for line_obj in pruned_node_code:
        line = line_obj.command.lstrip()
        if line.startswith('ivls.AddNodeCallback'):
            pass
        elif line.startswith("ivls.RunNodeCallback"):
            cb_name = line.split('(')[1].split(')')[0]
            for node in node_cb:
                if cb_name in node_cb[node]:
                    for cb_l in node_cb[node][cb_name]:
                        pre_assembly_lines.append(cb_l)

        elif line.startswith("literate_macro(Voice.NodeCB)"):
            for n in node_cb:
                note_on_lines = ''
                note_off_lines = ''
                
                if 'NoteOn' in node_cb[n]:
                    note_on_lines = '\n'.join([l.command for l in node_cb[n]['NoteOn']])
                if 'NoteOff' in node_cb[n]:
                    note_off_lines = '\n'.join([l.command for l in node_cb[n]['NoteOff']])
                
                if not (note_on_lines == '' and note_off_lines == ''):
                    voiced_nodes.append(n)
                    new_func_str = voice_logic_taskfunc.format(n, note_on_lines, note_off_lines)
                    for cb_l in new_func_str.split('\n'):
                        pre_assembly_lines.append(Line(cb_l, None, None))

        elif line.startswith("literate_macro(ivls.voice_logic_select)"):
            for n in voiced_nodes:
                new_case = voice_logic_case.format(n)
                for cb_l in new_case.split('\n'):
                    pre_assembly_lines.append(Line(cb_l, None, None))
        else:
            pre_assembly_lines.append(line_obj)
        
    post_assembly_lines = deque()
    for line_obj in pre_assembly_lines:
        line = line_obj.command.lstrip()

        if line.startswith('ivls.AddNodeCallback'):
            pass
        elif line.startswith("ivls.RunNodeCallback"):
            cb_name = line.split('(')[1].split(')')[0]
            for node in node_cb:
                if cb_name in node_cb[node]:
                    for cb_l in node_cb[node][cb_name]:
                        post_assembly_lines.append(cb_l)
        elif "__COMPILE_NODE_SWITCHER__" in line:
            for n in node_cb:
                open_lines = ''
                close_lines = ''
                
                if 'UIOpen' in node_cb[n]:
                    open_lines = '\n'.join([l.command for l in node_cb[n]['UIOpen']])
                if 'UIClose' in node_cb[n]:
                    close_lines = '\n'.join([l.command for l in node_cb[n]['UIClose']])
                
                if not (open_lines == '' and close_lines == ''):
                    node_ui_case = node_ui_switcher.format(n, open_lines, close_lines)
                    
                    for cb_l in node_ui_case.split('\n'):
                        post_assembly_lines.append(Line(cb_l, None, None))
        else:
            post_assembly_lines.append(line_obj)

    return post_assembly_lines

def ivls_node_assemble(lines, define_cache):
    return parse_node_macros(lines, define_cache)
