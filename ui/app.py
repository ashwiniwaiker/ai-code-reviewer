import sys
import os
import streamlit as st
import pandas as pd
import subprocess
from dotenv import load_dotenv 

load_dotenv() 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.parser.python_parser import parse_path
from core.validator.validator import validate_docstrings, compute_complexity
from core.docstring_engine.llm_integration import generate_docstring_content
from core.docstring_engine.generator import generate_docstring
from core.docstring_engine.modifier import apply_docstring_to_file
from core.reporter.coverage_reporter import compute_coverage

# --- Page Config ---
st.set_page_config(page_title="AI Code Reviewer", layout="wide", page_icon="🚀")

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'project_path' not in st.session_state:
    st.session_state.project_path = "./"

# --- Sidebar ---
with st.sidebar:
    st.title("🚀 AI Code Reviewer")
    view = st.selectbox("Navigation", ["Home", "Docstrings", "Validation", "Metrics", "Dashboard"])
    
    st.header("Configuration")
    project_path = st.text_input("Project Path", value=st.session_state.project_path)
    
    if st.button("Scan Project", type="primary", use_container_width=True):
        with st.spinner("Scanning project files..."):
            st.session_state.project_path = project_path
            # Natively use the core parser
            raw_parsed_data = parse_path(project_path)
            
            # Map the list to a dictionary for the UI
            formatted_results = {}
            for file_data in raw_parsed_data:
                file_path = file_data["file_path"]
                # Natively add complexity from core validator
                with open(file_path, 'r', encoding='utf-8') as f:
                    complexities = {c["name"]: c["complexity"] for c in compute_complexity(f.read())}
                for fn in file_data.get("functions", []):
                    fn["complexity"] = complexities.get(fn["name"], 1)
                formatted_results[file_path] = file_data
                
            st.session_state.scan_results = formatted_results
        st.success(f"Project scanned: {len(st.session_state.scan_results)} files analyzed.")

def get_stats():
    if not st.session_state.scan_results:
        return 0, 0, 0
    # Natively use the coverage reporter
    parsed_list = list(st.session_state.scan_results.values())
    report = compute_coverage(parsed_list)
    return report["aggregate"]["total_functions"], report["aggregate"]["documented"], report["aggregate"]["coverage_percent"]

total_funcs, documented, cov = get_stats()

# --- Views ---
if view == "Home":
    st.title("Quick Statistics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Documentation Coverage", f"{cov:.1f}%")
    col2.metric("Total Functions", total_funcs)
    col3.metric("Documented", documented)
    
    st.subheader("Overview")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Files Scanned:** {len(st.session_state.scan_results) if st.session_state.scan_results else 0}")
    with col_b:
        st.warning(f"**Work Needed:** {total_funcs - documented} functions missing docs.")

elif view == "Docstrings":
    st.title("Docstring Generation Workspace")
    
    style = st.radio("Select Docstring Style", ["google", "numpy", "rest"], horizontal=True)
    
    if not st.session_state.scan_results:
        st.info("Please scan a project from the sidebar first.")
    else:
        col1, col2 = st.columns([1, 3]) # Give the right side more room for the text areas
        
        with col1:
            st.subheader("Project Files")
            selected_file = st.selectbox("Select a file", list(st.session_state.scan_results.keys()))
            
        with col2:
            st.subheader("Function Review")
            if selected_file and "functions" in st.session_state.scan_results[selected_file]:
                # We now allow viewing ALL functions, not just undocumented ones
                funcs = st.session_state.scan_results[selected_file]["functions"]
                
                if not funcs:
                    st.info("No functions found in this file.")
                else:
                    selected_func_name = st.selectbox("Select function to review", [f["name"] for f in funcs])
                    selected_func = next((f for f in funcs if f["name"] == selected_func_name), None)
                    
                    if selected_func:
                        # Grab current docstring to display
                        current_doc = selected_func.get("current_docstring")
                        display_current = f'"""\n{current_doc}\n"""' if current_doc else "No docstring currently exists."
                        
                        st.write(f"**Target:** `{selected_func_name}`")
                        
                        if st.button("✨ Generate New Docstring with AI", type="primary"):
                            with st.spinner("Generating via LLM..."):
                                # 1. Get AI content via API
                                ai_content = generate_docstring_content(selected_func)
                                # 2. Format it into a perfect docstring string natively
                                generated_doc = generate_docstring(selected_func, style=style, ai_content=ai_content)
                                st.session_state[f"generated_{selected_func_name}"] = generated_doc
                        
                        # Set up the side-by-side comparison
                        doc_col1, doc_col2 = st.columns(2)
                        
                        with doc_col1:
                            st.text_area("Current Docstring", display_current, height=300, disabled=True)
                        
                        with doc_col2:
                            # Safely get the generated text from session state, default to empty
                            gen_val = st.session_state.get(f"generated_{selected_func_name}", "")
                            
                            # We make the generated side editable so you can tweak it before applying!
                            new_doc = st.text_area("Generated Suggestion", gen_val, height=300)
                            
                            if gen_val: # Only show the Apply/Discard buttons if we actually generated something
                                c_acc, c_rej = st.columns(2)
                                if c_acc.button("✔️ Accept & Apply"):
                                    # Use the new decoupled modifier tool
                                    apply_docstring_to_file(selected_file, selected_func_name, new_doc)
                                    
                                    # Restore the green success message and clean up state
                                    st.success("✅ Applied! Please click 'Scan Project' in the sidebar to refresh the UI.")
                                    del st.session_state[f"generated_{selected_func_name}"]
                                if c_rej.button("❌ Discard"):
                                    del st.session_state[f"generated_{selected_func_name}"]
                                    st.rerun()

elif view == "Validation":
    st.title("PEP 257 Validation")
    
    # Initialize session state for validation to prevent disappearing UI
    if "audit_run" not in st.session_state:
        st.session_state.audit_run = False
        st.session_state.violations = {}
    
    if st.button("Run PEP 257 Audit", type="primary"):
        with st.spinner("Auditing codebase..."):
            violations = {}
            # Natively iterate and validate each file
            for file_path in st.session_state.scan_results.keys():
                file_errors = validate_docstrings(file_path)
                if file_errors:
                    violations[file_path] = file_errors
            
            st.session_state.violations = violations
            st.session_state.audit_run = True
            
    if st.session_state.audit_run:
        violations = st.session_state.violations
        
        # Calculate metrics
        total_funcs_scanned = sum(len(data.get("functions", [])) for data in st.session_state.scan_results.values()) if st.session_state.scan_results else 0
        total_violations = sum(len(v) for v in violations.values())
        compliant = max(0, total_funcs_scanned - len(violations.keys())) 
        
        # 1. Top Cards
        c1, c2 = st.columns(2)
        c1.metric("PEP 257 compliant", compliant)
        c2.metric("Violations Found", total_violations)
        
        # 2. Charts Section
        st.subheader("Compliant vs violation")
        chart_type = st.selectbox("Select Chart Type", ["Bar Graph", "Pie Chart"])
        
        import altair as alt
        import pandas as pd
        
        chart_data = pd.DataFrame({
            "Status": ["Compliant", "Violations"],
            "Count": [compliant, total_violations]
        })
        
        color_scale = alt.Scale(domain=["Compliant", "Violations"], range=["#28a745", "#dc3545"])
        
        if chart_type == "Bar Graph":
            base = alt.Chart(chart_data).encode(
                x=alt.X('Status:N', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Count:Q', title='Count'),
                color=alt.Color('Status:N', scale=color_scale, legend=None)
            )
            bar = base.mark_bar()
            text = base.mark_text(dy=-10, size=16, fontWeight='bold').encode(text='Count:Q')
            c = (bar + text).properties(height=350)
            st.altair_chart(c, use_container_width=True)
        else:
            base = alt.Chart(chart_data).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Status", type="nominal", scale=color_scale)
            )
            pie = base.mark_arc(innerRadius=0)
            text = base.mark_text(radiusOffset=20, size=16, fontWeight='bold').encode(text='Count:Q')
            c = (pie + text).properties(height=350)
            st.altair_chart(c, use_container_width=True)
            
        # 3. Violation Details Section
        st.subheader("Violation details")
        
        if not st.session_state.scan_results:
            st.info("Please scan a project from the sidebar to view detailed file compliance.")
        else:
            # Iterate through EVERY file that was scanned
            for file in st.session_state.scan_results.keys():
                file_violations = violations.get(file, [])
                
                if file_violations:
                    # If it has errors, show them in red inside an expander
                    with st.expander(f"📄 {file} ({len(file_violations)} issues)", expanded=True):
                        for error in file_violations:
                            st.error(error)
                else:
                    # If it has NO errors, show a beautiful green success box
                    st.success(f"✅ **{file}**\n\nAll docstrings follow PEP 257 standards.")

elif view == "Metrics":
    st.title("Code Complexity Metrics")
    
    if st.session_state.scan_results:
        # Calculate overall metrics
        total_items = 0
        total_complexity = 0
        high_complexity = 0
        documented = 0
        
        for file, data in st.session_state.scan_results.items():
            for f in data.get("functions", []):
                total_items += 1
                c = f.get("complexity", 1)
                total_complexity += c
                if c > 5:  # Standard threshold for "High" complexity warning
                    high_complexity += 1
                if f.get("has_docstring"):
                    documented += 1
                    
        avg_comp = total_complexity / total_items if total_items > 0 else 0
        
        # 1. Top 4 Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total items", total_items)
        c2.metric("Avg complexity", f"{avg_comp:.2f}")
        c3.metric("High complexity", high_complexity)
        c4.metric("Documented", documented)
        
        # 2. Detailed Function Metrics (JSON format)
        st.subheader("Detailed function metrics")
        selected_file = st.selectbox("Select a Python file", list(st.session_state.scan_results.keys()))
        
        if selected_file:
            file_data = st.session_state.scan_results[selected_file]
            json_output = []
            
            for f in file_data.get("functions", []):
                json_output.append({
                    "file": os.path.basename(selected_file),
                    "type": f.get("type", "function"),
                    "name": f.get("name"),
                    "complexity": f.get("complexity", 1),
                    "start_line": f.get("lineno", "N/A"),
                    "end_line": f.get("end_lineno", "N/A"),
                    "has_docstring": f.get("has_docstring", False)
                })
                
            # Render as interactive JSON block
            st.json(json_output)
    else:
        st.info("Scan a project to view metrics.")
elif view == "Dashboard":
    st.title("Dashboard")
    st.caption("Advanced tool for code analysis and management")

    st.subheader("Dashboard Navigation")
    
    # Session state to handle the internal button clicks
    if "dash_nav" not in st.session_state:
        st.session_state.dash_nav = "Home"

    cols = st.columns(5)
    if cols[0].button("Filter", use_container_width=True): st.session_state.dash_nav = "Filter"
    if cols[1].button("Search", use_container_width=True): st.session_state.dash_nav = "Search"
    if cols[2].button("Test", use_container_width=True): st.session_state.dash_nav = "Test"
    if cols[3].button("Export", use_container_width=True): st.session_state.dash_nav = "Export"
    if cols[4].button("Help", use_container_width=True): st.session_state.dash_nav = "Help"

    st.divider()

    # Pre-calculate data for Filter, Search, and Export tabs
    all_funcs = []
    if st.session_state.scan_results:
        for file, data in st.session_state.scan_results.items():
            for f in data.get("functions", []):
                all_funcs.append({
                    "File": file,
                    "Function": f["name"],
                    "Docstring": "Yes" if f["has_docstring"] else "No",
                    "Complexity": f.get("complexity", 1)
                })
    df_all = pd.DataFrame(all_funcs) if all_funcs else pd.DataFrame(columns=["File", "Function", "Docstring", "Complexity"])

    # 1. HOME VIEW (Default)
    if st.session_state.dash_nav == "Home":
        st.info("Select a feature")
        st.markdown("""
        * **Advanced Filters** - Filter functions by documenting status
        * **Search** - Find functions by name across your project
        * **Test Result** - View pytest test results and coverage
        * **Export** - Download reports in json and csv format
        * **Help & Tips** - Complete usage guide and best practices
        """)

    # 2. FILTER VIEW
    elif st.session_state.dash_nav == "Filter":
        st.subheader("Filter function by docstring status")
        st.write("Select documentation Status")
        
        filter_opt = st.radio("Status", ["All functions", "Has Docstring", "Missing Docstring"], horizontal=True, label_visibility="collapsed")
        
        if not df_all.empty:
            if filter_opt == "Has Docstring":
                df_filtered = df_all[df_all["Docstring"] == "Yes"]
            elif filter_opt == "Missing Docstring":
                df_filtered = df_all[df_all["Docstring"] == "No"]
            else:
                df_filtered = df_all
            
            st.subheader("Filter results")
            c1, c2, c3 = st.columns(3)
            total = len(df_all)
            showing = len(df_filtered)
            pct = (showing / total * 100) if total > 0 else 0
            
            c1.metric("Total function", total)
            c2.metric("Showing", showing)
            c3.metric("Percentage", f"{pct:.1f}%")
            
            st.write("### Function list")
            st.dataframe(df_filtered[["File", "Function", "Docstring"]], use_container_width=True)
        else:
            st.warning("No data found. Please scan the project first.")

    # 3. SEARCH VIEW
    elif st.session_state.dash_nav == "Search":
        st.subheader("Search")
        query = st.text_input("Find functions by name across your project:")
        if query and not df_all.empty:
            df_search = df_all[df_all["Function"].str.contains(query, case=False, na=False)]
            st.dataframe(df_search[["File", "Function", "Docstring"]], use_container_width=True)
        elif not df_all.empty:
            st.dataframe(df_all[["File", "Function", "Docstring"]], use_container_width=True)

    # 4. TEST VIEW
    elif st.session_state.dash_nav == "Test":
        st.subheader("Test Result")
        if st.button("Run All Tests", type="primary"):
            with st.spinner("Running tests..."):
                # Run pytest in verbose mode
                result = subprocess.run(['pytest', 'tests/', '-v'], capture_output=True, text=True)
                
                passed_tests = []
                failed_tests = []
                test_stats = {}
                
                # Parse the real pytest output line by line
                for line in result.stdout.split('\n'):
                    # 1. Handle normal test executions
                    if '::' in line and any(status in line for status in ['PASSED', 'FAILED', 'ERROR']):
                        parts = line.split()
                        test_path = parts[0]
                        status = parts[1]
                        
                        file_name, test_name = test_path.split('::')
                        mod_name = file_name.replace('tests/test_', '').replace('.py', '')
                        
                        if mod_name not in test_stats:
                            test_stats[mod_name] = {"pass": 0, "fail": 0}
                            
                        if 'PASSED' in status:
                            test_stats[mod_name]["pass"] += 1
                            passed_tests.append(f"**{test_name}** `({file_name})`")
                        else:
                            test_stats[mod_name]["fail"] += 1
                            failed_tests.append(f"**{test_name}** `({file_name})`")

                    # 2. Handle the Collection/Import Errors you are currently getting
                    elif line.startswith("ERROR tests/"):
                        file_name = line.split(" ")[1]
                        mod_name = file_name.replace('tests/test_', '').replace('.py', '')
                        
                        if mod_name not in test_stats:
                            test_stats[mod_name] = {"pass": 0, "fail": 1} # Count errors as fails
                        else:
                            test_stats[mod_name]["fail"] += 1
                            
                        failed_tests.append(f"**Import/Collection Error** `({file_name})`")
                
                # Failsafe if absolutely nothing runs
                if not test_stats:
                    test_stats = {"suite": {"pass": 0, "fail": 0}}
                
                # Calculate dynamic totals
                total_t = sum(s["pass"] + s["fail"] for s in test_stats.values())
                passed_t = sum(s["pass"] for s in test_stats.values())
                failed_t = sum(s["fail"] for s in test_stats.values())
                rate = (passed_t / total_t * 100) if total_t > 0 else 0
                
                # Render top metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Test", total_t)
                c2.metric("Passed", passed_t)
                c3.metric("Failed", failed_t)
                c4.metric("Pass rate", f"{rate:.1f}%")
                
                st.divider()
                
                # Render dynamic charts
                col_l, col_r = st.columns(2)
                with col_l:
                    st.subheader("Test result by file")
                    chart_df = pd.DataFrame([
                        {"Module": k, "Passed": v["pass"], "Failed": v["fail"]}
                        for k, v in test_stats.items()
                    ]).set_index("Module")
                    st.bar_chart(chart_df, color=["#28a745", "#dc3545"])
                    
                with col_r:
                    st.subheader("Test Suites")
                    for mod, stats in test_stats.items():
                        tot = stats['pass'] + stats['fail']
                        if stats['fail'] > 0:
                            st.warning(f"**{mod}**: {stats['pass']}/{tot} passed")
                        else:
                            st.success(f"**{mod}**: {stats['pass']}/{tot} passed")
                            
                # Render detailed lists
                st.divider()
                st.subheader("Detailed Test Breakdown")
                
                list_col1, list_col2 = st.columns(2)
                
                with list_col1:
                    with st.expander(f"❌ Failed / Error Tests ({len(failed_tests)})", expanded=bool(failed_tests)):
                        for t in failed_tests:
                            st.error(t)
                        if not failed_tests:
                            st.write("Awesome! No failed tests.")
                            
                with list_col2:
                    with st.expander(f"✅ Passed Tests ({len(passed_tests)})", expanded=True):
                        for t in passed_tests:
                            st.success(t)
                        if not passed_tests:
                            st.write("No passed tests found.")
                            
                with st.expander("View Raw Pytest Output"):
                    st.code(result.stdout)

    # 5. EXPORT VIEW
    elif st.session_state.dash_nav == "Export":
        st.subheader("Export Analysis report")
        st.write("### Project summary")
        
        total = len(df_all)
        docs = len(df_all[df_all["Docstring"] == "Yes"]) if not df_all.empty else 0
        missing = total - docs
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total function", total)
        c2.metric("Documented", docs)
        c3.metric("Missing", missing)
        
        st.write("### Download reports")
        if not df_all.empty:
            json_data = df_all.to_json(orient="records")
            csv_data = df_all.to_csv(index=False)
            
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                st.download_button("Download Json Report", data=json_data, file_name="report.json", mime="application/json")
            with btn_c2:
                st.download_button("Download CSV Report", data=csv_data, file_name="report.csv", mime="text/csv")
        else:
            st.info("Scan project first to export data.")

    # 6. HELP VIEW
    elif st.session_state.dash_nav == "Help":
        hc1, hc2, hc3 = st.columns(3)
        hc1.info("**Project Scanning**\n\nAnalyzes Python files for functions and classes.")
        hc2.info("**Ai Docstring generation**\n\nUses LLM to write documentation automatically.")
        hc3.info("**Review and apply workflow**\n\nPreview AI suggestions before saving to file.")
        
        hc4, hc5, hc6 = st.columns(3)
        hc4.info("**direct file modification**\n\nInjects accepted docstrings right into your source code.")
        hc5.info("**coverage tracking**\n\nMonitors percentage of documented functions.")
        hc6.info("**PEP 257 validation**\n\nChecks docstrings against Python formatting standards.")
        
        st.write("### enhanced feature guide")
        ec1, ec2, ec3, ec4 = st.columns(4)
        ec1.success("**Advanced filters**\n\nQuickly find functions missing documentation.")
        ec2.success("**Search functions**\n\nLocate specific methods across your entire codebase.")
        ec3.success("**Export report**\n\nSave analysis data to JSON and CSV formats.")
        ec4.success("**Testing integration**\n\nRun your test suite directly from the UI.")
        
        st.write("### docstring style references")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.write("**Google Style**")
            st.code('"""\nSummary line.\n\nArgs:\n    param1 (int): Description.\n"""', language='python')
        with tc2:
            st.write("**NumPy Style**")
            st.code('"""\nSummary line.\n\nParameters\n----------\nparam1 : int\n    Description.\n"""', language='python')
        with tc3:
            st.write("**reST Style**")
            st.code('"""\nSummary line.\n\n:param param1: Description.\n:type param1: int\n"""', language='python')
            
        st.warning("💡 **Pro tip**: Always review AI-generated docstrings to ensure the business logic is accurately described before applying them to your codebase!")