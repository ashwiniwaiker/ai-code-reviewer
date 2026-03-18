# 🚀 AI Code Reviewer & Documentation Generator

An intelligent, interactive codebase analysis tool built with Python and Streamlit. This application uses Abstract Syntax Tree (AST) parsing and the Groq API (Llama 3) to automatically analyze code complexity, validate formatting standards, and natively generate and inject PEP 257-compliant docstrings directly into your source code.

## 🌟 Why This Helps
Writing documentation and tracking technical debt is traditionally a slow, manual process. This tool solves that by providing:
* **Instant Documentation:** Replaces hours of manual typing by reading your functions and generating perfect Google, NumPy, or reST style docstrings.
* **Direct File Injection:** It doesn't just suggest code; it safely modifies your Python files to inject the generated docstrings with perfect indentation.
* **Actionable Metrics:** Highlights exactly where your code is getting too complex (Cyclomatic Complexity) or lacking documentation.
* **Code Standard Enforcement:** Automatically audits your codebase against PEP 257 rules to ensure a uniform style across all developers.

---

## ⚙️ Installation & Setup

### 1. Prerequisites
* Python 3.8 or higher
* A free [Groq API Key](https://console.groq.com/)

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/ashwiniwaiker/ai-code-reviewer.git
cd ai-code-reviewer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install required dependencies
pip install streamlit pandas radon pydocstyle pytest python-dotenv groq altair
```

### 3\. Environment Variables

To keep your API keys secure, this project uses a `.env` file.

1.  Create a file named `.env` in the root directory.
2.  Add your Groq API key:

<!-- end list -->

```text
GROQ_API_KEY=your_actual_api_key_here
```

### 4\. Run the Application

```bash
streamlit run ui/app.py
```

-----

## 🔍 Feature Deep Dive

### 1\. AST Code Parsing

Instead of relying on brittle text-matching (Regex), this app uses Python's built-in `ast` module to read your source code structurally. It accurately identifies classes, functions, arguments, and line numbers, ensuring completely safe analysis regardless of your code's formatting.

### 2\. AI Docstring Engine (Groq Integration)

Select any undocumented function, and the app sends its metadata to the **Llama 3** model via the Groq API. It intelligently infers the purpose of the function, parameters, and return types, outputting a strictly formatted docstring.

  * **Interactive Editing:** Review and tweak the AI's suggestion in a side-by-side UI.
  * **One-Click Apply:** Click "Accept & Apply" to safely inject the docstring directly into your source file without breaking surrounding code.

### 3\. PEP 257 Validation

Using `pydocstyle` under the hood, the Validation tab scans every file in your project and generates a compliance report. It highlights missing docstrings, incorrect blank lines, and formatting violations, complete with visualizations to track your overall compliance score.

### 4\. Complexity Metrics

Powered by `radon`, the Metrics tab calculates the Cyclomatic Complexity of every function in your codebase. It flags "High Complexity" functions (score \> 5) so you know exactly which parts of your code are getting too deeply nested and might require refactoring.

### 5\. Advanced Dashboard & Testing

A centralized hub for project management:

  * **Filter & Search:** Instantly locate undocumented functions or search by name.
  * **Test Integration:** Run your `pytest` suite directly from the UI to see pass/fail rates natively visualized in the browser.
  * **Export:** Download your codebase analysis reports in JSON or CSV formats.

-----

## 📁 Project Structure

```text
.
├── core/                       # Decoupled business logic
│   ├── docstring_engine/       # LLM integration and file modification
│   ├── parser/                 # AST parsing logic
│   ├── reporter/               # Coverage calculations
│   └── validator/              # PEP 257 and complexity checks
├── dashboard_ui/               # Test compatibility stubs
├── examples/                   # Sample code for testing
├── tests/                      # Comprehensive pytest suite
├── ui/                         # Streamlit application
│   └── app.py
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Project configuration
└── README.md                   # You are here
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/ashwiniwaiker/ai-code-reviewer/blob/main/LICENSE>) file for details.
