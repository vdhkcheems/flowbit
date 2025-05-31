import os
import time
import redis
from pathlib import Path
from dotenv import load_dotenv

import google.generativeai as genai
import fitz  # PyMuPDF for PDF extraction

# Load env variables (make sure GOOGLE_API_KEY is set in .env)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Redis setup
r = redis.Redis(host='localhost', port=6379, db=0)

# === Format Detection ===
def detect_format(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return "PDF"
    elif suffix == ".json":
        return "JSON"
    elif suffix in [".txt", ".eml"]:
        return "Email"
    else:
        return "Unknown"

# === Text Extraction ===
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print("[ERROR] PDF extraction failed:", e)
    return text

def extract_text_from_txt(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print("[ERROR] TXT extraction failed:", e)
        return ""

# === Intent Detection using Gemini ===
def classify_intent_with_gemini(text: str) -> str:
    prompt = f"""
You are an intelligent document classifier.

Your task is to classify the INTENT of the given document content into one of the following categories:
- Invoice
- RFQ
- Complaint
- Regulation

If the content matches none of the specific categories, classify it as 'Unknown'.

Document content:
{text[:3000]}

Return ONLY the category name.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Unknown"

# === Main Classifier Agent ===
def classifier_agent(file_path: str):
    file_format = detect_format(file_path)
    
    if file_format == "PDF":
        content = extract_text_from_pdf(file_path)
    elif file_format == "Email":
        content = extract_text_from_txt(file_path)
    elif file_format == "JSON":
        content = None  # JSON Agent will handle structured parsing
    else:
        raise ValueError("Unsupported file format")

    intent = classify_intent_with_gemini(content) if content else "Unknown"

    log_key = f"log:{int(time.time())}"
    r.hset(log_key, mapping={
        "source": file_path,
        "format": file_format,
        "intent": intent,
        "timestamp": str(time.time())
    })

    return file_format, intent, log_key

# === Run Example ===
if __name__ == "__main__":
    test_file = "data/pdf_complaint.txt.pdf"  # Replace with your file
    classifier_agent(test_file)
