import re

def parse_assignment(string):
    data_set_pattern = r'([^<]+)<([^>]+)>\s*:=\s*(.*)'
    match = re.match(data_set_pattern, string)
    if match:
        namespace = match.group(1)
        # Split the arguments inside the angle brackets
        args = [arg.strip() for arg in match.group(2).split(',')]
        value = match.group(3)
        
        return {
            'namespace': namespace,
            'args': args,
            'value': value
        }
    return None

# # Test cases
# test_strings = [
#     'hse.layers<A, Volume> := 600000 * age',
#     'obj.method<Param1, Param2, Param3> := 42',
#     'system.config<SingleParam> := 123'
# ]

# for test_string in test_strings:
#     result = parse_assignment(test_string)
#     if result:
#         print(f"Input: {test_string}")
#         print(f"Namespace: {result['namespace']}")
#         print(f"Args: {result['args']}")
#         print(f"Value: {result['value']}")
#         print()


class DataParser:
    def __init__(self):
        self.modules = {}

    def parse(self, data_text):
        # Split the text into lines and remove leading/trailing whitespace
        lines = [line.strip() for line in data_text.split('\n')]
        
        # Find the module declaration
        module_line = lines[0]
        if not module_line.startswith('data '):
            raise ValueError("Invalid data block: must start with 'data'")
        
        # Extract module name
        module_name = module_line.split('data ')[1].rstrip(':')
        
        # Initialize module dictionary
        module_data = DataModule()
        
        for line in lines[1:-1]:  # Skip first and last lines
            line = line.strip()
            
            # Check for list definition
            if ':=' in line:
                key, value = line.split(':=')
                key = key.strip()
                
                # Extract list items, removing brackets and splitting
                list_items = value.strip()[1:-1].split(',')
                module_data.dim_names[key] = [item.strip() for item in list_items if item.strip()]
            
            # Check for dimension definition
            elif ':' in line and ':=' not in line:
                key, value = line.split(':')
                key = key.strip()
                value = value.strip()
                
                # Try to convert to int, but handle list-like definitions
                try:
                    module_data.dims[key] = int(value)
                except ValueError:
                    # If not a pure integer, skip this line
                    raise Exception("Dimension '{0}' size requires integer: \n{1}".format(key, line))
        
        # Store the module data
        self.modules[module_name] = module_data
        
        return module_data

class DataModule():
    dims = {}
    dim_names = {}

# Test the parser with various inputs
parser = DataParser()

# Example 1: Original example
data_text1 = '''data hse.layers:
    layer: 4
    par: 128
    layer := [a, b, c, d]
    par := [volume, pan, tune,]
end data'''

# Example 2: More complex dimensions
data_text2 = '''data synth.oscillator:
    osc: 3as
    wave: 5
    color: 2
    
    osc := [ main, sub, fm]
    wave := [ sine, square, saw, triangle, noise]
    color := [bright, dark]
end data'''

# Parse and print results
parsed_data1 = parser.parse(data_text1)
print("Parsed Data 1:")
print(parsed_data1)
print("\n")

parsed_data2 = parser.parse(data_text2)
print("Parsed Data 2:")
print(parsed_data2)