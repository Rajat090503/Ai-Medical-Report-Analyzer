from flask import Flask, render_template, request
import os

from utils.ocr import extract_text
from utils.analyzer import analyze_report
from models.risk_model import predict_health_risk

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    if "report" not in request.files:
        return "No file selected"

    file = request.files["report"]

    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    # Extract text
    extracted_text = extract_text(filepath)

    print("\n" + "=" * 50)
    print("EXTRACTED TEXT")
    print("=" * 50)
    print(extracted_text)
    print("=" * 50)

    # Analyze report
    
    report = analyze_report(extracted_text)

    risk, confidence, health_score = predict_health_risk(report)

    print("\nANALYSIS RESULT:")
    print(report)

    return render_template(
    "result.html",
    filename=file.filename,
    text=extracted_text,
    report=report,
    risk=risk,
    confidence=confidence,
    health_score=health_score
)


if __name__ == "__main__":
    app.run(debug=True)