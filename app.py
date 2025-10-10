import io
import pandas as pd
from flask import Flask, request, jsonify, render_template
import dspy

def build_multi_sheet_preview(xls_bytes: bytes, per_sheet_rows: int = 120) -> str:
    """
    Return a single string that concatenates CSV previews of EVERY sheet.
    Each block is prefixed with '### SHEET: <name>' so the model sees the tab.
    """
    # Try openpyxl first (xlsx). If it fails (e.g., .xls), fall back to pandas default engine.
    try:
        xl = pd.ExcelFile(io.BytesIO(xls_bytes), engine="openpyxl")
    except Exception:
        xl = pd.ExcelFile(io.BytesIO(xls_bytes))

    blocks = []
    for name in xl.sheet_names:
        try:
            df = xl.parse(name)
            if df is None or df.empty:
                blocks.append(f"### SHEET: {name}\n(empty)\n")
            else:
                blocks.append(f"### SHEET: {name}\n" + df.head(per_sheet_rows).to_csv(index=False))
        except Exception as e:
            blocks.append(f"### SHEET: {name}\n(ERROR reading sheet: {e})\n")
    return "\n".join(blocks)
# This is what creates the flask app
app = Flask(__name__)

# This is what determines the LM, "ollama_chat/gemma3:4b" is the model I am using, you can change it to whatever you are using
lm = dspy.LM("ollama_chat/gemma3:4b", api_base="http://localhost:11434", api_key="")

# Sets the lm to be the lm we are using
dspy.configure(lm=lm)

# Renders the HTML index
@app.route("/")
def index():
    return render_template("index.html")

# This is the main function for ai processing
@app.route("/analyze", methods=["POST"])
def analyze():

    # Check for an actual file uploaded
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # This is what is setting up the ai to analyze, this is what we are working on changing
    file = request.files["file"]
    try:

        file_bytes = file.read()
        preview_text = build_multi_sheet_preview(file_bytes, per_sheet_rows=120)

        prompt = (
            "You are a data analyst AI. Analyze this Excel data and provide a summary, "
            "including trends, insights, or anomalies:\n\n" + preview_text
        )

        # This is the function that actually runs the ai processing
        response = lm(prompt)

        return jsonify({"analysis": response})
    
    # Error handling
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Add this new route (paste it below your /analyze route) ---
@app.route("/ask", methods=["POST"])
def ask():
    # Expect the same file plus a free-text question (sent by your front end)
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    question = request.form.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    file = request.files["file"]
    try:
        # Read the Excel, same style as /analyze (engine hint is robust)
        file_bytes = file.read()
        preview_text = build_multi_sheet_preview(file_bytes, per_sheet_rows=200)

        prompt = (
            "You are a careful analyst. Answer ONLY using the data below from all Excel sheets. "
            "If the answer isn't present, say you cannot find it.\n\n"
            f"QUESTION:\n{question}\n\n"
            "DATA (CSV previews per sheet):\n"
            f"{preview_text}"
        )

        resp = lm(prompt)

        # Inline, minimal-safe extractor (handles list/str/dict/object)
        def _xt(r):
            if r is None:
                return ""
            if isinstance(r, str):
                return r
            if isinstance(r, list):
                return _xt(r[0]) if r else ""
            if isinstance(r, dict):
                for k in ("text", "content", "message", "response"):
                    if k in r and r[k] is not None:
                        return _xt(r[k])
                return str(r)
            return getattr(r, "text", str(r))

        answer = _xt(resp)
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Idk what this does exactly, I think this is just what sets up the website to actually be running idrk
if __name__ == "__main__":
    app.run(debug=True)
