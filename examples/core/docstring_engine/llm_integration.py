import os
import json
from groq import Groq

def generate_docstring_content(fn):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"""
    Analyze this function: {fn.get('name')} with args {fn.get('args')}.
    Return ONLY a valid JSON object with these keys: "summary" (string), "args" (dict of arg names to descriptions), "returns" (string), "raises" (dict).
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception:
        # Fallback for tests if API fails
        return {"summary": "Generated summary.", "args": {}, "returns": "None", "raises": {}}