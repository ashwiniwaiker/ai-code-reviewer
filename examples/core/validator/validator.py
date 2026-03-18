import subprocess
import re
from radon.visitors import ComplexityVisitor
import ast

def validate_docstrings(file_path):
    """
    Validate docstrings for a module.

    Args:
        file_path (Any): The path to the module file to validate.

    Returns:
        Any: None
    """
    process = subprocess.run(
        ['pydocstyle', file_path], 
        capture_output=True, 
        text=True
    )
    
    violations = []
    lines = (process.stdout + process.stderr).split('\n')
    
    for line in lines:
        if line.strip().startswith('D'):
            violations.append(line.strip())
            
    return violations

def compute_complexity(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
        
    v = ComplexityVisitor.from_ast(tree)
    results = []
    for block in v.blocks:
        results.append({
            "name": block.name,
            "complexity": block.complexity
        })
    return results