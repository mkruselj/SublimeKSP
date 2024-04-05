from collections import defaultdict, deque, OrderedDict
import utils

voice_logic_taskfunc_title = 'taskfunc ivls.{}.VoiceLogic(var self, var self_invalid, nenv)'
voice_logic_taskfunc_pre_on = '''
        declare node_id := NodeEnv[nenv].node_id
        declare thread := Voice[self].thread

        if Voice[self].input = ivls.input_type.VOICE_ON
'''
voice_logic_taskfunc_post_on = '''
        else if Voice[self].input = ivls.input_type.VOICE_OFF
'''
voice_logic_taskfunc_post_off = '''
        end if
    end taskfunc
'''

voice_logic_case = '''
case ivls.node.{0}
    ivls.{0}.VoiceLogic(self, self_invalid, nenv)
'''

voice_pass_taskfunc_title = 'taskfunc ivls.{}.VoicePass(var self)'
voice_pass_taskfunc_pre_pass = '''
        declare node_id := ivls.flows[Voice[self].flow, Voice[self].stage]
        declare thread := Voice[self].thread
'''
voice_pass_taskfunc_post_pass = '''
    end taskfunc
'''

voice_pass_case = '''
case ivls.node.{0}
    ivls.{0}.VoicePass(self)
'''

node_ui_switcher = '''
    if ivls.node.{0} = (ivls.NodeUI -> value)
        {1}
    else
        {2}
    end if
'''

def make_line_obj(code):
    from ksp_compiler import Line, ParseException
    return [Line(l, None, None) for l in code.split('\n')]
    
def parse_node_macros(code_lines, define_cache):
    from ksp_compiler import Line, ParseException

    node_cb = OrderedDict()

    current_node = None
    current_callback = None

    node_names = []
    for define_constant in define_cache:
        if define_constant.name == 'IVLS_ALL_NODES':
            node_order = define_constant.value
            node_names = utils.split_args(node_order, 0)
            break

    node_passes = {}
    for name in node_names:
        node_cb[name] = defaultdict(list)
        node_passes[name] = False
    
    # Extract the node callbacks
    pruned_node_code = deque()
    ivls_syntax = False
    for line_obj in code_lines:
        line = line_obj.command.strip()
        
        if line.startswith("macro Node."):
            if ivls_syntax:
                raise ParseException(line_obj, 'You may not use SublimeKSP macros inside of IVLS nodes!')
            
            parts = line.split(".")
            current_node = ".".join(parts[1:-1])
            current_callback = parts[-1].split("(")[0]
            
            if current_callback in node_cb[current_node]:
                raise ParseException(line_obj, 'Callback {} has been declared twice in node {}!'.format(current_callback, current_node))
            
            if current_callback == 'NotePass':
                if 'NoteOn' in node_cb[current_node] or 'NoteOff' in node_cb[current_node]:
                    raise ParseException(line_obj, 'Can not add NotePass callback to Node with NoteOn/NoteOff callback!'.format(current_callback, current_node))
            elif current_callback == 'NoteOn' or current_callback == 'NoteOff':
                if 'NotePass' in node_cb[current_node]:
                    raise ParseException(line_obj, 'Can not add NoteOn or NoteOff callback to Node with NotePass callback!'.format(current_callback, current_node))
            
        elif line.startswith('macro '):
            if ivls_syntax:
                raise ParseException(line_obj, 'You may not use SublimeKSP macros inside of IVLS nodes!')
            else:
                pruned_node_code.append(line_obj)
        elif line.startswith("node "):
            if not line.endswith(':'):
                raise ParseException(line_obj, 'Node declaration must end in \':\'! \n {}')
            
            ivls_syntax = True
            name = line.strip('node').strip(':').strip()
            if current_node:
                raise ParseException(line_obj, 'You can not nest nodes! Found \'{}\' inside of \'{}\''.format(name, current_node))
            
            current_node = name
        elif line.startswith("cb "):
            if not line.endswith(':'):
                raise ParseException(line_obj, 'Node declaration must end in \':\'!')
            
            name = line.strip('cb').strip(':').strip()
            
            if not current_node:
                raise ParseException(line_obj, 'Callback must be inside a node!')
            elif name in node_cb[current_node]:
                raise ParseException(line_obj, 'Callback {} has been declared twice in node {}!'.format(name, current_node))
            
            if name == 'NotePass':
                if 'NoteOn' in node_cb[current_node] or 'NoteOff' in node_cb[current_node]:
                    raise ParseException(line_obj, 'Can not add NotePass callback to Node with NoteOn/NoteOff callback!'.format(name, current_node))
            elif name == 'NoteOn' or name == 'NoteOff':
                if 'NotePass' in node_cb[current_node]:
                    raise ParseException(line_obj, 'Can not add NoteOn or NoteOff callback to Node with NotePass callback!'.format(name, current_node))
            
            current_callback = name
        elif "end node" in line:
            if not current_node:
                raise ParseException(line_obj, 'Invalid end node!')
            
            ivls_syntax = False
            current_node = None
        elif line.startswith("end macro"):
            if ivls_syntax:
                raise ParseException(line_obj, 'You may not use SublimeKSP macros inside of IVLS nodes!')
            if not current_node:
                pruned_node_code.append(line_obj)

            current_node = None
            current_callback = None
        else:
            if current_node and current_callback and current_node in node_order:
                if current_callback == 'NotePass':
                    node_passes[current_node] = True
                
                line_obj.source_locations = line_obj.locations
                if current_callback != 'Functions':
                    line_obj.node_cb = (current_node, current_callback)

                if line.startswith('message('):
                    line_obj.command = line_obj.command.replace('message(', 'message("[ {} | {} ] " & '.format(current_node, current_callback))
                
                node_cb[current_node][current_callback].append(line_obj)
                
                if current_callback == 'NotePass':
                    if ('ivls.play' in line or 'ivls.pass' in line):
                        raise ParseException(line_obj, 'You may not use ivls.play() variants or ivls.pass in NotePass callbacks!')
                
                if current_callback == 'NoteOff' and ('ivls.play(' in line or 'ivls.pass' in line):
                    raise ParseException(line_obj, 'You may not use ivls.play() or ivls.pass() in NoteOff callbacks! Use ivls.play.oneshot() to prevent hangs.')
            else:
                if not current_node:
                    pruned_node_code.append(line_obj)

    for n in node_cb:
        print(n)

    # Inject Nodes directly in where IVLS commands are found
    pre_assembly_lines = deque()
    voiced_nodes = []
    for line_obj in pruned_node_code:
        line = line_obj.command.lstrip()
        
        if line.startswith("__RUN_CB__"):
            cb_name = line.split('(')[1].split(')')[0]
            for node in node_cb:
                if cb_name in node_cb[node]:
                    for cb_l in node_cb[node][cb_name]:
                        pre_assembly_lines.append(cb_l)
        elif line.startswith("__CACHE_PASSES__"):
            for n in node_cb:
                if node_passes[n] == True:
                    pre_assembly_lines.append(Line('ivls.node_passes[ivls.node.{}] := TRUE'.format(n), None, None))
        elif line.startswith("__DECLARE_VOICE_LOGIC__"):
            for n in node_cb:
                note_on_lines = None
                note_off_lines = None

                if 'NoteOn' in node_cb[n]:
                    note_on_lines = node_cb[n]['NoteOn']
                if 'NoteOff' in node_cb[n]:
                    note_off_lines = node_cb[n]['NoteOff']

                if not (note_on_lines == None and note_off_lines == None):
                    voiced_nodes.append(n)
                    new_func_lines = deque()
                    new_func_lines.append(Line(voice_logic_taskfunc_title.format(n), None, None))
                    new_func_lines += make_line_obj(voice_logic_taskfunc_pre_on)
                    if note_on_lines:
                        new_func_lines += note_on_lines
                    new_func_lines += make_line_obj(voice_logic_taskfunc_post_on)
                    if note_off_lines:
                        new_func_lines += note_off_lines
                    new_func_lines += make_line_obj(voice_logic_taskfunc_post_off)
                        
                    pre_assembly_lines.extend(new_func_lines)
        elif line.startswith("__SELECT_VOICE_LOGIC__"):
            for n in node_cb:
                if n in voiced_nodes:
                    new_case = voice_logic_case.format(n)
                    for cb_l in new_case.split('\n'):
                        pre_assembly_lines.append(Line(cb_l, None, None))
        else:
            pre_assembly_lines.append(line_obj)

    # Catch node callback commands which were assembled inward
    post_assembly_lines = deque()
    for line_obj in pre_assembly_lines:
        line = line_obj.command.lstrip()

        if line.startswith("__RUN_CB__"):
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
        elif line.startswith("__DECLARE_VOICE_PASS__"):
            for n in node_passes:
                if node_passes[n] == True:
                    note_pass_lines = None
                
                    if 'NotePass' in node_cb[n]:
                        note_pass_lines = node_cb[n]['NotePass']

                    if not (note_pass_lines == None):
                        voiced_nodes.append(n)
                        new_func_lines = deque()
                        new_func_lines.append(Line(voice_pass_taskfunc_title.format(n), None, None))
                        new_func_lines += make_line_obj(voice_pass_taskfunc_pre_pass)
                        if note_pass_lines:
                            new_func_lines += note_pass_lines
                        new_func_lines += make_line_obj(voice_pass_taskfunc_post_pass)
                            
                        post_assembly_lines.extend(new_func_lines)
        elif line.startswith("__SELECT_VOICE_PASS__"):
            for n in node_cb:
                if node_passes[n] == True:
                    new_case = voice_pass_case.format(n)
                    for cb_l in new_case.split('\n'):
                        post_assembly_lines.append(Line(cb_l, None, None))
        else:
            post_assembly_lines.append(line_obj)
            
    return post_assembly_lines

import subprocess
import os

def execute_scripts(base_dir, code_lines):
    new_lines = deque()

    for lobj in code_lines:
        line = lobj.command
        if line.startswith("__SCRIPT__"):
            # Extract the script path and arguments from the line
            script_parts = line.strip("__SCRIPT__").strip("()").split(",")
            script_path = script_parts[0].strip('"')
            script_args = [arg.strip() for arg in script_parts[1:]]

            # Execute the script with the provided arguments
            print("Running {} with args {}".format(script_path, script_args))
            code_cache_path = os.path.join(base_dir, 'code_cache.ksp')
            with open(code_cache_path, 'w') as f:
                f.write('\n'.join([line.command for line in code_lines]))
            subprocess.call(["python", os.path.join(base_dir, script_path)] + [code_cache_path] + script_args)
        else:
            new_lines.append(lobj)

    return new_lines

def ivls_node_assemble(line_obj_list, define_cache):
    return parse_node_macros(line_obj_list, define_cache)

def script_injection(base_dir, line_obj_list):
    return execute_scripts(base_dir, line_obj_list)
