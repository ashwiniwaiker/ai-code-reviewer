import ast
import os

def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"file_path": file_path, "functions": [], "classes": [], "error": "Syntax Error"}

    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            # Extract arguments for the tests
            args_list = [{"name": arg.arg} for arg in node.args.args]
            
            functions.append({
                "name": node.name,
                "type": "function",
                "has_docstring": bool(docstring),
                "current_docstring": docstring,
                "args": args_list,
                "lineno": node.lineno,
                "end_lineno": getattr(node, 'end_lineno', node.lineno),
                "source_segment": ast.get_source_segment(source, node)
            })

    return {"file_path": file_path, "functions": functions}

def parse_path(project_path):
    results = []
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                results.append(parse_file(file_path))
    return results