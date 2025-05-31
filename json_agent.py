import json
import redis
import time
from pathlib import Path
from dotenv import load_dotenv
import os
import re
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Redis setup
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Prompt for reformulating into general schema
REFORMAT_PROMPT = """
You are an expert data extraction assistant.

You will receive:
1. The **intent** of the document.
2. A list of **5 expected fields** for that intent.
3. The **input JSON** object.

Your task is to extract the values of those 5 expected fields **if they are present and clear** in the input JSON. Otherwise, mark them as **missing**.

You must return a JSON object in the following structure:

{
  "intent": "change it from unknown to one of the $ mentioned below that suits the best",
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
Now process the following JSON:
"""


# Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

def clean_json_block(response_text: str) -> str:
    # Remove ```json ... ``` or ``` ... ```
    return re.sub(r"^```(?:json)?\n|\n```$", "", response_text.strip())

def extract_and_store_from_json(file_path: str, key):
    path = Path(file_path)
    if not path.exists() or path.suffix != ".json":
        print("[JSON Agent] Invalid file.")
        return

    with open(path, "r") as f:
        original_data = json.load(f)

    # Prepare prompt
    prompt = REFORMAT_PROMPT + "\n" + json.dumps(original_data, indent=2)
    response = model.generate_content(prompt)
    raw_text = response.text
    cleaned_text = clean_json_block(raw_text)
    
    try:
        parsed_output = json.loads(cleaned_text)
    except json.JSONDecodeError:
        print("[JSON Agent] Gemini returned invalid JSON.")
        return


    # Update Redis entry
    r.hset(key, mapping={
        "entities": json.dumps(parsed_output.get("entities", [])),
        "fields": json.dumps(parsed_output.get("fields", {})),
        "missing_fields": json.dumps(parsed_output.get("missing_fields", [])),
        "comments": parsed_output.get("comments", ""),
        "intent": parsed_output.get("intent", "")
    })

# Example usage
if __name__ == "__main__":
    test_file = "data/json_complaint.json"  # Change as needed
    extract_and_store_from_json(test_file)
