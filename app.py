import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import pandas as pd
import io

app = Flask(__name__)

client = OpenAI(api_key="")
DEFAULT_MODEL = "gpt-4o-mini"

# This part renders the actual page and adds the ui elements
@app.route("/")
def index():
    return render_template("index.html")

# This is the analyzing part
@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Requesting from the html script
    file = request.files["file"]
    try:
        # Read Excel into pandas DataFrame
        df = pd.read_excel(io.BytesIO(file.read()))
        
        # Convert the first 50 rows to text for AI analysis (or adjust as needed)
        preview_text = df.to_csv(index=False)
        instructions = (
            "You are a data analyst AI. Analyze this Excel data and provide a summary, "
            "including any trends, insights, or anomalies you notice."
        )

        response = client.responses.create(
            model=DEFAULT_MODEL,
            instructions=instructions,
            input=preview_text,
            max_output_tokens=1000
        )

        return jsonify({"analysis": response.output_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
