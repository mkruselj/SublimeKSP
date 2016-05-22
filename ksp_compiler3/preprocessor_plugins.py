# preprocessor_plugins.py
# Written by Sam Windell
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version:
# http://www.gnu.org/licenses/gpl-2.0.html
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


#=================================================================================================
#=================================================================================================
# TO DO:
# 	Write function to replace lines deque since this something often done.
#	This should throw an exception, a non constant is used in the array initialisation:
#		declare array[6] := (get_ui_id(silder), 0) 

# IDEAS:
#	-	multidimensional ui arrays
#	-	+=, -=
#	-	add alternative to pers keyword that reads the persistent variable as well.
#	-	iterate_macro to work with single like commands as well as macros:
#			iterate_macro(add_menu_item(lfoDesination#n#, destinationMenuNames[i], i)) := 0 to NUM_OSC - 1
#	-	built in bounds checking for arrays/pgs, the compiler auto adds print() messages to check that you 
#		accessing valid elements.

import re
import collections
import ksp_compiler 


#=================================================================================================
# Regular expressions
var_prefix_re = r"[%!@$]"

string_or_placeholder_re =  r'({\d+}|\"[^"]*\")'
varname_re_string = r'((\b|[$%!@])[0-9]*[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_0-9]+)*)\b'
variable_or_int = r"[^\]]+"

commas_not_in_parenth = re.compile(r",(?![^\(\)\[\]]*[\)\]])") # All commas that are not in parenthesis
list_add_re = re.compile(r"^\s*list_add\s*\(")

# 'Regular expressions for 'blocks'
for_re = re.compile(r"^((\s*for)(\(|\s+))")
end_for_re = re.compile(r"^\s*end\s+for")
while_re = re.compile(r"^((\s*while)(\(|\s+))")
end_while_re = re.compile(r"^\s*end\s+while")
if_re = re.compile(r"^\s*if(\s+|\()")
end_if_re = re.compile(r"^\s*end\s+if")
init_re = r"^\s*on\s+init"

ui_type_re = r"(?<=)(ui_button|ui_switch|ui_knob|ui_label|ui_level_meter|ui_menu|ui_slider|ui_table|ui_text_edit|ui_waveform|ui_value_edit)(?=\s)"
keywords_re = r"(?<=)(declare|const|pers|polyphonic|list)(?=\s)"


#=================================================================================================
# These functions are called by the main compiler.

# For these, the macros have not yet been expaned.
def pre_macro_functions(lines):
	remove_print(lines)
	handle_define_lines(lines)
	handle_iterate_macro(lines)

# For these, the macros have been expaned.
def post_macro_functions(lines):
	handle_const_block(lines)
	handle_ui_arrays(lines)
	inline_declare_assignment(lines)
	multi_dimensional_arrays(lines)
	find_list_block(lines)
	handle_lists(lines)
	variable_persistence_shorthand(lines)
	ui_property_functions(lines)
	calculate_open_size_array(lines)
	expand_string_array_declaration(lines)	


#=================================================================================================
# For all of these functions, the 'lines' argument is a collections.deque of Line objects. All 
# code of this deque has already been imported with the 'import' command, and all comments have 
# been removed.


def remove_print(lines):
	print_line_numbers = []
	logger_active_flag = False
	for i in range(len(lines)):
		line = lines[i].command
		if re.search(r"^\s*activate_logger\s*\(", line):
			logger_active_flag = True
		if re.search(r"^\s*print\s*\(", line):
			print_line_numbers.append(i)

	if logger_active_flag == False:
		for i in range(len(print_line_numbers)):
			lines[print_line_numbers[i]].command = ""


# Create multidimentional arrays. 
# This functions replaces the multidimensional array declaration with a property with appropriate
# get and set functions to be sorted by the compiler further down the line.
def multi_dimensional_arrays(lines):
	dimensions = []
	num_dimensions = []
	name = []
	line_numbers = []
	new_declare = []

	for i in range(len(lines)):
		line = lines[i].command.strip()
		m = re.search(r"^\s*declare\s+(pers\s+)?" + varname_re_string + "\s*\[" + variable_or_int + "\s*(,\s*" + variable_or_int + "\s*)+\]", line)
		if m:
			variable_name = m.group(2)
			prefix = m.group(3)
			if prefix:
				variable_name = variable_name[1:]
			else:
				prefix = ""
			name.append(variable_name)

			dimensions_split = line[line.find("[") + 1 : line.find("]")].split(",") 
			num_dimensions.append(len(dimensions_split))
			dimensions.append(dimensions_split)

			line_numbers.append(i)

			new_text = line.replace(variable_name, prefix + "_" + variable_name)
			new_text = new_text.replace("[", "[(").replace("]", ")]").replace(",", ")*(")
			lines[i].command = new_text
			

	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):
	
			for ii in range(num_dimensions[i]):
				current_text = "declare const " + name[i] + ".SIZE_D" + str(ii + 1) + " := " + dimensions[i][ii]
				new_lines.append(lines[line_numbers[i]].copy(current_text))

			# start property
			current_text = "property " + name[i]
			new_lines.append(lines[i].copy(current_text))

			# start get function
			# it might look something like this: function get(v1, v2, v3) -> result
			current_text = "function get(v1"
			for ii in range(1, num_dimensions[i]):
				current_text = current_text + ", v" + str(ii + 1) 
			current_text = current_text + ") -> result"
			new_lines.append(lines[i].copy(current_text))

			# get function body
			current_text = "result := _" + name[i] + "["
			for ii in range(num_dimensions[i]):
				if ii != num_dimensions[i] - 1: 
					for iii in range(num_dimensions[i] - 1, ii, -1):
						current_text = current_text + dimensions[i][iii] + " * "
				current_text = current_text + "v" + str(ii + 1)
				if ii != num_dimensions[i] - 1:
					current_text = current_text + " + "
			current_text = current_text + "]"
			new_lines.append(lines[i].copy(current_text))

			# end get function
			new_lines.append(lines[i].copy("end function"))

			# start set function
			# it might look something like this: function set(v1, v2, v3, val)
			current_text = "function set(v1"
			for ii in range(1, num_dimensions[i]):
				current_text = current_text + ", v" + str(ii + 1) 
			current_text = current_text + ", val)"
			new_lines.append(lines[i].copy(current_text))

			# set function body
			current_text = "_" + name[i] + "["
			for ii in range(num_dimensions[i]):
				if ii != num_dimensions[i] - 1: 
					for iii in range(num_dimensions[i] - 1, ii, -1):
						current_text = current_text + dimensions[i][iii] + " * "
				current_text = current_text + "v" + str(ii + 1)
				if ii != num_dimensions[i] - 1:
					current_text = current_text + " + "
			current_text = current_text + "] := val"
			new_lines.append(lines[i].copy(current_text))

			# end set function
			new_lines.append(lines[i].copy("end function"))		

			# end property
			new_lines.append(lines[i].copy("end property"))


			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	




def ui_property_functions(lines):
	ui_control_properties = [
	"set_slider_properties(ui-id, default, picture, mouse_behaviour)",
	"set_switch_properties(ui-id, text, picture, text_alignment, font_type, textpos_y)",
	"set_label_properties(ui-id, text, picture, text_alignment, font_type, textpos_y)",
	"set_menu_properties(ui-id, picture, font_type, text_alignment, textpos_y)",
	"set_table_properties(ui-id, bar_color, zero_line_color)",
	"set_button_properties(ui-id, text, picture, text_alignment, font_type, textpos_y)",
	"set_level_meter_properties(ui-id, bg_color, off_color, on_color, overload_color)",
	"set_waveform_properties(ui-id, bar_color, zero_line_color)",
	"set_knob_properties(ui-id, text, default)",
	"set_bounds(ui-id, x, y, width, height)"
	]

	ui_func_names = []
	ui_func_args = []
	ui_func_size = []

	for ui_func in ui_control_properties:
		m = re.search(r"^\s*\w*", ui_func)
		ui_func_names.append(m.group(0))
		m = re.search(r"(?<=ui\-id,).*(?=\))", ui_func)
		arg_list = m.group(0).replace(" ", "").split(",")
		ui_func_args.append(arg_list)
		ui_func_size.append(len(arg_list))


	line_numbers = []
	prop_numbers = []
	var_names = []
	num_params = []
	params = []

	for i in range(len(lines)):
		line = lines[i].command.strip()
		for ii in range(len(ui_func_names)):
			if re.search(r"^\s*" + ui_func_names[ii] + r"\s*\(", line):
				comma_sep = line[line.find("(") + 1 : len(line) - 1].strip()
				line_numbers.append(i)
				prop_numbers.append(ii)

				string_list = re.split(commas_not_in_parenth, comma_sep)
				variable_name = string_list[0]
				var_names.append(variable_name)
				param_list = string_list[1:]

				params.append(param_list)
				num_params.append(len(param_list))
				if len(param_list) > ui_func_size[ii]:
					raise ksp_compiler.ParseException(lines[i], "Too many arguments, expected %d, got %d.\n" % (ui_func_size[ii], len(param_list)))
				elif len(param_list) == 0:
					raise ksp_compiler.ParseException(lines[i], "Function requires at least 2 arguments.\n")
				lines[i].command = ""

	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):
	
			sum_max = 0			
			for ii in range(0, prop_numbers[i]):
				sum_max += ui_func_size[ii]

			for ii in range(num_params[i]):
				current_text = var_names[i] + " -> " + ui_func_args[prop_numbers[i]][ii] + " := " + params[i][ii]
				new_lines.append(lines[line_numbers[i]].copy(current_text))	

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	


def inline_declare_assignment(lines):
	line_numbers = []
	var_text = []

	for i in range(len(lines)):
		line = lines[i].command.strip()
		ls_line = re.sub(r"\s", "", line)
		m = re.search(r"^\s*declare\s+(polyphonic|pers|global|local)?\s*" + varname_re_string + "\s*:=", line)
		if m:
			int_flag = False
			value = line[line.find(":=") + 2 :]
			if not "{" in value:
				try:
					eval(value)
					int_flag = True
				except:
					pass

			if int_flag == False:
				pre_assignment_text = line[: line.find(":=")]
				variable_name = m.group(2)
				line_numbers.append(i)
				var_text.append(variable_name + " " + line[line.find(":=") :])
				lines[i].command = pre_assignment_text

	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):

			# new_lines.append(Line(var_text[i], [(filename, int(line_numbers[i]) + 2)]))	
			new_lines.append(lines[line_numbers[i]].copy(var_text[i]))	
			# lines[i].copy(var_text[i])

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	

def handle_const_block(lines):
	line_number = None
	num_elements = None
	const_block = False
	current_val = None
	const_block_name = None
	current_assignment_list = []

	for i in range(len(lines)):
		line = lines[i].command
		m = re.search(r"^\s*const\s+" + varname_re_string, line) 
		if m:
			const_block = True
			lines[i].command = "declare " + m.group(1) + "[]"
			const_block_name = m.group(1)
			line_number = i
			current_val = "0"
			num_elements = 0
			current_assignment_list = []
			print("got here")
		elif re.search(r"^\s*end\s+const", line):
			const_block = False

			assignment_text = "("
			for ii in range(len(current_assignment_list)):
				assignment_text = assignment_text + current_assignment_list[ii]
				if not ii == len(current_assignment_list) - 1:
					assignment_text = assignment_text + ", "
			assignment_text = assignment_text + ")"

			lines[line_number].command = lines[line_number].command.replace("]", str(num_elements) + "]")
			lines[line_number].command = lines[line_number].command + " := " + assignment_text

			lines[i].command = ""
		elif const_block:
			assignment_text = current_val
			text = line.strip()
			if ":=" in line:
				assignment_text = line[line.find(":=") + 2 :]
				text = line[: line.find(":=")].strip()

			lines[i].command = "declare const " + const_block_name + "." + text + " := " + assignment_text
			current_assignment_list.append(current_val)
			current_val = assignment_text + "+1"
			try:
				eval(current_val)
			except:
				pass
			num_elements += 1


def find_list_block(lines):

	list_block = False
	list_name = None

	for i in range(len(lines)):
		line = lines[i].command
		m = re.search(r"^\s*list\s+" + varname_re_string, line)
		if m:
			list_block = True
			list_name = m.group(1)
			lines[i].command = "declare list " + list_name + "[]"
		elif list_block:
			if re.search(r"^\s*end\s+list", line):
				list_block = False
				lines[i].command = ""
			else:
				lines[i].command = "list_add(" + list_name + ", " + lines[i].command + ")"


def handle_lists(lines):
	list_names = []
	line_numbers = []
	init_flag = None
	loop_flag = None
	iterators = []

	for i in range(len(lines)):
		line = lines[i].command
		m = re.search(r"^\s*declare\s+(pers\s+)?list\s*" + varname_re_string, line)
		if re.search(r"^\s*on\s+init", line):
			init_flag = True
		elif re.search(r"^\s*end\s+on", line):
			if init_flag == True:
				for ii in range(len(iterators)):
					list_declare_line = lines[line_numbers[ii]].command
					square_bracket_pos = list_declare_line.find("[]") + 1
					lines[line_numbers[ii]].command = list_declare_line[: square_bracket_pos] + str(iterators[ii]) + "]"
				init_flag = False
		elif re.search(for_re, line) or re.search(while_re, line) or re.search(if_re, line):
			loop_flag = True
		elif re.search(end_for_re, line) or re.search(end_while_re, line) or re.search(end_if_re, line):
			loop_flag = False
		elif m:
			name = m.group(2)
			is_pers = ""
			if m.group(1):
				is_pers = " pers "
			list_names.append(name)
			line_numbers.append(i)
			iterators.append(0)
			# The number of elements is populated once the whole init callback is scanned.
			lines[i].command = "declare " + is_pers + name + "[]"
		else:
			if re.search(list_add_re, line):
				find_list_name = False
				for ii in range(len(list_names)):
					list_title = re.sub(var_prefix_re, "", list_names[ii])
					if re.search(r"list_add\s*\(\s*[$%!@]?" + list_title + r"\b", line): #re.sub(var_prefix_re, "", list_names[ii]) in line:
						find_list_name = True
						if loop_flag == True:
							raise ksp_compiler.ParseException(lines[i], "list_add() cannot be used in loops or if statements.\n")
						if init_flag == False:
							raise ksp_compiler.ParseException(lines[i], "list_add() can only be used in the init callback.\n")

						value = line[line.find(",") + 1 : len(line) - 1]
						lines[i].command = list_names[ii] + "[" + str(iterators[ii]) + "] := " + value
						iterators[ii] += 1
						break
				if not find_list_name:
					undeclared_name = line[line.find("(") + 1 : line.find(",")]
					raise ksp_compiler.ParseException(lines[i], undeclared_name + " had not been declared.\n") 

	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):

			list_name = re.sub(r"[$%!@]", "", list_names[i])
			current_text = "declare const " + list_name + ".SIZE := " + str(iterators[i])
			new_lines.append(lines[line_numbers[i]].copy(current_text))

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	
		
def calculate_open_size_array(lines):
	array_name = []
	strings = []
	line_numbers = []
	num_ele = []

	for i in range(len(lines)):
		line = lines[i].command
		ls_line = re.sub(r"\s", "", line)
		if "[]:=(" in ls_line:
			comma_sep = ls_line[ls_line.find("(") + 1 : len(ls_line) - 1]
			string_list = re.split(commas_not_in_parenth, comma_sep)
			num_elements = len(string_list)
			name = line[: line.find("[")].replace("declare", "").strip()
			name = re.sub(var_prefix_re, "", name)

			lines[i].command = line[: line.find("[") + 1] + str(num_elements) + line[line.find("[") + 1 :]

			array_name.append(name)
			line_numbers.append(i)
			num_ele.append(num_elements)


	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):

			current_text = "declare const " + array_name[i] + ".SIZE := " + str(num_ele[i])
			new_lines.append(lines[line_numbers[i]].copy(current_text))

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	


def expand_string_array_declaration(lines):
	string_var_names = []
	strings = []
	line_numbers = []
	num_ele = []



	for i in range(len(lines)):
		line = lines[i].command.strip()
		# convert text array declaration to multiline
		# m = re.search(r"^\s*declare\s+" + varname_re_string + r"\s*\[\s*" + variable_or_int + r"\s*\]\s*:=\s*\(\s*{\d+}(\s*,\s*{\d+})*\s*\)", line)
		m = re.search(r"^\s*declare\s+" + varname_re_string + r"\s*\[\s*" + variable_or_int + r"\s*\]\s*:=\s*\(\s*" + string_or_placeholder_re + r"(\s*,\s*" + string_or_placeholder_re + r")*\s*\)", line)
		if m:
			if m.group(2) == "!":
				comma_sep = line[line.find("(") + 1 : len(line) - 1]
				string_list = re.split(commas_not_in_parenth, comma_sep)
				num_elements = len(string_list)
				
				search_obj = re.search(r'\s+!' + varname_re_string, line)
				string_var_names.append(search_obj.group(0))

				num_ele.append(num_elements)
				strings.append(string_list)
				line_numbers.append(i)
			else:
				raise ksp_compiler.ParseException(lines[i], "Expected integers, got strings.\n")

			
	# for some reason this doesnt work in the loop above...?
	for lineno in line_numbers: 
		lines[lineno].command = lines[lineno].command[: lines[lineno].command.find(":")]


	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):

			for ii in range(num_ele[i]):
				current_text = string_var_names[i] + "[" + str(ii) + "] := " + strings[i][ii] 
				new_lines.append(lines[line_numbers[i]].copy(current_text))

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	



def variable_persistence_shorthand(lines):
	line_numbers = []
	variable_names = []

	for i in range(len(lines)):
		line = lines[i].command.strip()
		if re.search(r"^\s*declare\s+pers\s+", line):
			variable_name = line
			variable_name = re.sub(ui_type_re, "", variable_name)
			variable_name = re.sub(keywords_re, "", variable_name)

			if variable_name.find("[") != -1:
				variable_name = variable_name.replace(variable_name[variable_name.find("[") : ], "")
			if variable_name.find("(") != -1:
				variable_name = variable_name.replace(variable_name[variable_name.find("(") : ], "")
			if variable_name.find(":=") != -1:
				variable_name = variable_name.replace(variable_name[variable_name.find(":=") : ], "")

			variable_names.append(variable_name.strip())
			line_numbers.append(i)
			lines[i].command = lines[i].command.replace("pers", "")

	if line_numbers:
		# add the text from the start of the file to the first declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each declaration create the elements and fill in the gaps
		for i in range(len(variable_names)):

			current_text = "make_persistent(" + variable_names[i] + ")"
			new_lines.append(lines[line_numbers[i]].copy(current_text))

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	



def handle_iterate_macro(lines):
	min_val = []
	max_val = []
	step_val = []
	macro_name = []
	line_numbers = []
	downto = []
	is_single_line = []

	for index in range(len(lines)):
		line = lines[index].command
		if re.search(r"^\s*iterate_macro\s*\(", line):
			m = re.search(r"^\s*iterate_macro\s*\((.+)\)\s*(:=.+)", line)
			name = m.group(1)
			params = m.group(2)
			try:

				find_n = False
				if "#n#" in name:
					find_n = True
				is_single_line.append(find_n)

				if "downto" in params:
					to_stmt = "downto"
					downto.append(True)
				elif "to" in params:
					to_stmt = "to"
					downto.append(False)

				minv = eval(params[params.find(":=") + 2 : params.find(to_stmt)])
				if "step" in params:
					step = eval(params[params.find("step") + 4 :])
					maxv = eval(params[params.find(to_stmt) + len(to_stmt) : params.find("step")])
				else:
					step = 1
					maxv = eval(params[params.find(to_stmt) + len(to_stmt) :])

				if (minv > maxv and to_stmt == "to") or (minv < maxv and to_stmt == "downto"):
					raise ksp_compiler.ParseException(lines[index], "Min and max values are incorrectly weighted (For example, min > max when it should be min < max)./n")

			except:
				raise ksp_compiler.ParseException(lines[index], "Incorrect values in iterate_macro statement. Normal 'declare const' variables cannot be used here, instead a 'define' const must be used. " + \
						"The macro you are iterating must have only have 1 integer parameter, this will be replaced by the values in the chosen range.\n")

			macro_name.append(name)
			min_val.append(minv)
			max_val.append(maxv)
			step_val.append(step)
			line_numbers.append(index)

			lines[index].command = re.sub(r'[^\r\n]', '', line)

	if line_numbers:
		# add the text from the start of the file to the first array declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each array declaration create the elements and fill in the gaps
		for i in range(len(line_numbers)):

			step = int(step_val[i])
			offset = 1
			if downto[i]:
				step = -step
				offset = -1

			for ii in range(int(min_val[i]), int(max_val[i]) + offset, step):
				current_text = macro_name[i] + "(" + str(ii) + ")"
				if is_single_line[i]:
					current_text = macro_name[i].replace("#n#", str(ii))
				new_lines.append(lines[line_numbers[i]].copy(current_text))

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last array declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)	


def handle_define_lines(lines):
	define_titles = []
	define_values = []
	define_line_pos = []
	for index in range(len(lines)):
		line = lines[index].command 
		if re.search(r"^\s*define\s+", line):
			if re.search(r"^\s*define\s+" + varname_re_string + r"\s*:=", line):
				text_without_define = re.sub(r"^\s*define\s*", "", line)
				colon_bracket_pos = text_without_define.find(":=")

				# before the assign operator is the title
				title = text_without_define[ : colon_bracket_pos].strip()
				define_titles.append(title)

				# after the assign operator is the value
				value = text_without_define[colon_bracket_pos + 2 : ].strip()
				define_values.append(value)

				define_line_pos.append(index)
				# remove the line
				lines[index].command = re.sub(r'[^\r\n]', '', line)
			else:
				raise ksp_compiler.ParseException(lines[index], "Syntax error in define.\n")

	# if at least one define const exsists
	if define_titles:
		# check each of the values to see if they contain any other define consts
		for i in range(len(define_values)):
			for ii in range(len(define_titles)):
				if define_titles[ii] in define_values[i]:
					define_values[i] = define_values[i].replace(define_titles[ii], define_values[ii])

		# do any maths if needed
		for i in range(len(define_values)):
			try:
				if not re.search(r"^#.*#$", define_values[i]):
					define_values[i] = re.sub(r"\s+mod\s+", " % ", define_values[i])
					define_values[i] = eval(define_values[i])
				else:
					define_values[i] = define_values[i][1 : len(define_values[i]) - 1]
			except:
				raise ksp_compiler.ParseException(lines[define_line_pos[i]], "Undeclared variable in define statement.\n")

		# scan the code can replace any occurances of the variable with it's value
		for line_obj in lines:
			line = line_obj.command 
			for index, item in enumerate(define_titles):
				if re.search(r"\b" + item + r"\b", line):
					# character_before = line[line.find(item) - 1 : line.find(item)]  
					# if character_before.isalpha() == False and character_before.isdiget() == False:  
					line_obj.command = line_obj.command.replace(item, str(define_values[index]))


def handle_ui_arrays(lines):
	ui_declaration = []
	variable_names = []
	line_numbers = []
	num_elements = []
	table_elements = []
	pers_state = []

	# find all of the array declarations
	for index in range(len(lines)):
		line = lines[index].command 
		ls_line = line.lstrip() # remove whitespace from beginning
		# if re.search(r"^\s*declare\s+", line) and line.find("[") != -1 :
		m = re.search(r"^\s*declare\s+(pers\s+)?" + ui_type_re + "\s*" + varname_re_string + "\s*\[[^\]]+\]", ls_line)
		if m:
			is_pers = False
			if m.group(1):
				is_pers = True
			ui_type = m.group(2).strip()
			var_name = m.group(3).strip()
			variable_name_no_pre = re.sub(var_prefix_re, "", var_name)

			# Check that if it is a table, it is actually an array.
			proceed = True
			if ui_type == "ui_table":
				if not re.search(r"\[[^\]]+\]\s*\[", ls_line):
					proceed = False

			if proceed == True:
				try:
					num_element = eval(ls_line[ls_line.find("[") + 1 : ls_line.find("]")])
				except:
					raise ksp_compiler.ParseException(lines[index], "Invalid number of elements. Native 'declare const' variables cannot be used here, instead a 'define' const must be used.\n")			

				pers_state.append(is_pers)
				# if there are parameters
				if "(" in ls_line:
					if ui_type == "ui_table":
						first_close_bracket = ls_line.find("]") + 1
						table_elements = ls_line[ls_line.find("[", first_close_bracket) + 1 : ls_line.find("]", first_close_bracket)]
						ui_declaration.append("declare " + ui_type + " " + var_name + "[" + table_elements + "]" + ls_line[ls_line.find("(") : ls_line.find(")") + 1]) 
					else:
						ui_declaration.append("declare " + ui_type + " " + var_name + ls_line[ls_line.find("(") : ls_line.find(")") + 1]) 
				else:
					ui_declaration.append("declare " + ui_type + " " + var_name) 
				line_numbers.append(index)
				num_elements.append(num_element)
				variable_names.append(variable_name_no_pre)
				lines[index].command  = "declare " + variable_name_no_pre + "[" + str(num_element) + "]"

	# if at least one ui array exsists
	if ui_declaration:
		# add the text from the start of the file to the first array declaration
		new_lines = collections.deque()
		for i in range(0, line_numbers[0] + 1):
			new_lines.append(lines[i])

		# for each array declaration create the elements and fill in the gaps
		for i in range(len(ui_declaration)):

			num_eles = int(num_elements[i])

			for ii in range(0, num_eles):

				if "(" in ui_declaration[i]:
					if "[" in ui_declaration[i]:
						parameter_start = ui_declaration[i].find("[")
					else:
						parameter_start = ui_declaration[i].find("(")
					current_text = ui_declaration[i][:parameter_start] + str(ii) + ui_declaration[i][parameter_start:]
				else:
					current_text = ui_declaration[i] + str(ii)

				if pers_state[i] == True:
					current_text = current_text.strip()
					current_text = current_text[: 7] + " pers " + current_text[8 :]


				# add individual ui declaration
				new_lines.append(lines[line_numbers[i]].copy(current_text))

				# add ui to array
				add_to_array_text = variable_names[i] + "[" + str(ii) + "]" + " := get_ui_id(" + variable_names[i] + str(ii) + ")"
				new_lines.append(lines[i].copy(add_to_array_text))

			if i + 1 < len(line_numbers):
				for ii in range(line_numbers[i] + 1, line_numbers[i + 1] + 1):
					new_lines.append(lines[ii])

		# add the text from the last array declaration to the end of the document
		for i in range(line_numbers[len(line_numbers) - 1] + 1, len(lines)):
			new_lines.append(lines[i])

		# both lines and new lines are deques of Line objects, replace lines with new lines
		for i in range(len(lines)):
			lines.pop()
		lines.extend(new_lines)
