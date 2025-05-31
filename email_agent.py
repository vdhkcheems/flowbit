import os
import json
import redis
import time
import google.generativeai as genai
from dotenv import load_dotenv
from classifier_agent import extract_text_from_pdf, extract_text_from_txt

# Gemini setup
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

REFORMAT_PROMPT = """
You are an expert data extraction assistant.

You will receive:
1. The **intent** of the document.
2. A list of **5 expected fields** for that intent.
3. The **input text** object.

Your task is to extract the values of those 5 expected fields **if they are present and clear** in the input JSON. Otherwise, mark them as **missing**.

You must return a JSON object in the following structure:

{
  "intent": "keep it the same as intent given to you",
  "fields": {
    "<field1>": "<value1>", 
    ...
  },
  "missing_fields": [ "<field3>", ... ],
  "entities": [ list of any named people, companies, or identifiers ],
  "comments": "Optional notes or extraction challenges"
}

Do not invent or guess missing data. Just be precise and minimal.

Now here are your field requirements:

INTENT: Complaint  
FIELDS: ["customer_name", "issue_type", "product", "date_of_incident", "resolution_requested"]

INTENT: Invoice  
FIELDS: ["invoice_number", "date", "total_amount", "sender", "recipient"]

INTENT: RFQ  
FIELDS: ["requested_items", "quantity", "delivery_date", "budget", "contact_person"]

INTENT: Regulation  
FIELDS: ["regulation_name", "effective_date", "issuing_authority", "scope", "compliance_deadline"]

Use only this field list for matching.
Now process the text
"""


def clean_response_text(text):
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```"):].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def extract_and_store_from_email(file_path: str, key):
    log_data = r.hgetall(key)
    format_ = log_data.get("format")
    intent = log_data.get("intent")

    if format_ not in ["Email", "PDF"]:
        print(f"[Email Agent] Skipping format: {format_}")
        return

    if format_ == 'PDF':
        input_text = extract_text_from_pdf(file_path)
    elif format_ == "Email":
        input_text = extract_text_from_txt(file_path)

    if input_text is None:
        return

    prompt = f"{REFORMAT_PROMPT}\n\n{{\"intent\": \"{intent}\", \"content\": \"\"\"{input_text}\"\"\"}}"

    try:
        response = model.generate_content(prompt)
        parsed_output = json.loads(clean_response_text(response.text))
    except Exception as e:
        print(f"[Email Agent] Error during Gemini response: {e}")
        return

    # Update Redis
    r.hset(key, mapping={
        "entities": json.dumps(parsed_output.get("entities", [])),
        "fields": json.dumps(parsed_output.get("fields", {})),
        "missing_fields": json.dumps(parsed_output.get("missing_fields", [])),
        "comments": parsed_output.get("comments", ""),
        "intent": parsed_output.get("intent", intent)  # fallback to original if not modified
    })

if __name__ == "__main__":
    main()
