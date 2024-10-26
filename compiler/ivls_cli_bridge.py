import yaml
import os
from pathlib import Path

def get_ivls_project_root(path):
    """Navigate to IVLS project root."""
    compiler_wd = os.getcwd()

    os.chdir(path)
    cwd = path

    if os.name == 'nt':
        root = Path(cwd).anchor  # This gets "G:\" instead of "/"
    else:
        root = Path(cwd).root  # Standard Unix "/"
    
    new = None
    while(not os.path.exists('./ivls.yml')):
        if os.getcwd() == root:
            return None
        os.chdir('..')
        new = os.getcwd()
        
    os.chdir(compiler_wd)

    return new

def get_libs(path):
    libs = []
    with open(os.path.join(path, 'ivls.yml'), 'r') as f:
        data = yaml.safe_load(f)

        if data and 'libs' in data.keys():
            if data['libs']:
                for l in data['libs'].keys():
                    libs.append(l)

    return libs