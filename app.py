import io
import pandas as pd
from flask import Flask, request, jsonify, render_template
import dspy

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

        # This is where the excel sheet is read in and saved as a dataframe
        df = pd.read_excel(io.BytesIO(file.read()))

        # This saves only the first 50 rows of the dataframe to a csvfor processing, I think this is where you should sub out for the python object class creation
        preview_text = df.head(50).to_csv(index=False)

        prompt = (
            "You are a data analyst AI. Analyze this Excel data and provide a summary, "
            "including trends, insights, or anomalies:\n\n" + preview_text
        )

        # This is the function that actually runs the ai processing
        response = lm(prompt)

        return jsonify({"analysis": response.text})
    
    # Error handling
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Idk what this does exactly, I think this is just what sets up the website to actually be running idrk
if __name__ == "__main__":
    app.run(debug=True)
