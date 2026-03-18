import ast

def apply_docstring_to_file(file_path, function_name, new_docstring):
    """Safely injects a docstring into a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
        
    clean_doc = new_docstring.strip()
    while clean_doc.startswith('"""') or clean_doc.startswith("'''"):
        clean_doc = clean_doc[3:].strip()
    while clean_doc.endswith('"""') or clean_doc.endswith("'''"):
        clean_doc = clean_doc[:-3].strip()

    lines = source.split('\n')
    out_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        
        if line.lstrip().startswith(f"def {function_name}(") or line.lstrip().startswith(f"def {function_name}:"):
            while i < len(lines) and not lines[i].rstrip().endswith(":"):
                i += 1
                out_lines.append(lines[i])
            
            base_indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            indent = base_indent + "    "
            
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
                
            if i < len(lines):
                stripped_line = lines[i].strip()
                if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                    quote_type = stripped_line[:3]
                    if stripped_line.endswith(quote_type) and len(stripped_line) > 3:
                        i += 1 
                    else:
                        i += 1
                        while i < len(lines) and quote_type not in lines[i]:
                            i += 1
                        i += 1
            
            out_lines.append(f'{indent}"""')
            for dline in clean_doc.split('\n'):
                out_lines.append(f"{indent}{dline}" if dline.strip() else "")
            out_lines.append(f'{indent}"""')
            i -= 1 
        i += 1

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))