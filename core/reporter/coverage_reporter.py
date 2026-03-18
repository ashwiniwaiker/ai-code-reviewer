def compute_coverage(parsed_data, threshold=90):
    total = sum(len(file_data.get("functions", [])) for file_data in parsed_data)
    documented = sum(1 for file_data in parsed_data for fn in file_data.get("functions", []) if fn.get("has_docstring"))
    
    pct = (documented / total * 100) if total > 0 else 0
    return {
        "aggregate": {
            "total_functions": total,
            "documented": documented,
            "coverage_percent": pct,
            "meets_threshold": pct >= threshold
        }
    }