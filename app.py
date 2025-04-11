from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def home():
    return "✅ Resume Scanner Backend is Running!"

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    if not text.strip():
        raise ValueError("Could not extract text from the PDF. Please try another file.")
    return text

@app.route("/evaluate", methods=["POST"])
def evaluate_resume():
    if "resume" not in request.files or "jd" not in request.form:
        return jsonify({"error": "Missing resume or job description"}), 400

    resume_file = request.files["resume"]
    jd = request.form["jd"]

    try:
        resume_text = input_pdf_text(resume_file)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    input_prompt = f"""
    Hey Act Like a skilled or very experienced ATS (Application Tracking System)
    with a deep understanding of the tech field, software engineering, data science,
    data analysis, and big data engineering. Your task is to evaluate the resume 
    based on the given job description. 

    Consider that the job market is very competitive, and you should provide
    the best assistance for improving the resume. Assign the percentage matching 
    based on the JD and the missing keywords with high accuracy.
    
    resume: {resume_text}
    description: {jd}

    Provide the response in JSON format:
    {{"JD Match":"%", "MissingKeywords":[],"Profile Summary":""}}
    """

    response = get_gemini_response(input_prompt)
    return jsonify({"evaluation": response, "resume_text": resume_text})

@app.route("/extract_text", methods=["POST"])
def extract_text():
    """Extract text from uploaded PDF file"""
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    resume_file = request.files["resume"]
    
    if resume_file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    try:
        resume_text = input_pdf_text(resume_file)
        return jsonify({"text": resume_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
