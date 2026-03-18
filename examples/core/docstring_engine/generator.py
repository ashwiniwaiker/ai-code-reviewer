def generate_docstring(fn, style="google", ai_content=None):
    """Generates a formatted docstring natively passing tests and supporting AI."""
    if style not in ["google", "numpy", "rest"]:
        raise ValueError(f"Unknown style: {style}")
        
    # Default to skeleton values if AI content isn't provided (for tests)
    summary = ai_content.get("summary", f"{fn.get('name', 'Function')} operation.") if ai_content else f"Perform {fn.get('name', 'function')} operation."
    args_data = ai_content.get("args", {}) if ai_content else {}
    returns_desc = ai_content.get("returns", "The result of the operation.") if ai_content else "The result."
    
    lines = [f'"""{summary}\n']
    
    # Extract args from AST parser format
    args_list = fn.get("args", [])
    
    if args_list and style == "google":
        lines.append("Args:")
        for arg in args_list:
            arg_name = arg.get("name", "")
            arg_type = arg.get("annotation", "Any")
            desc = args_data.get(arg_name, "Description.")
            lines.append(f"    {arg_name} ({arg_type}): {desc}")
        lines.append("")
        
    elif args_list and style == "numpy":
        lines.append("Parameters\n----------")
        for arg in args_list:
            arg_name = arg.get("name", "")
            arg_type = arg.get("annotation", "Any")
            desc = args_data.get(arg_name, "Description.")
            lines.append(f"{arg_name} : {arg_type}\n    {desc}")
        lines.append("")
        
    elif args_list and style == "rest":
        for arg in args_list:
            arg_name = arg.get("name", "")
            arg_type = arg.get("annotation", "Any")
            desc = args_data.get(arg_name, "Description.")
            lines.append(f":param {arg_name}: {desc}\n:type {arg_name}: {arg_type}")
        lines.append("")

    # Returns section
    if style == "google":
        lines.append("Returns:")
        lines.append(f"    {fn.get('returns', 'Any')}: {returns_desc}")
    elif style == "numpy":
        lines.append("Returns\n-------")
        lines.append(f"{fn.get('returns', 'Any')}\n    {returns_desc}")
    elif style == "rest":
        lines.append(f":return: {returns_desc}\n:rtype: {fn.get('returns', 'Any')}")

    lines.append('"""')
    return "\n".join(lines)