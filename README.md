# Multi-Agent Information Extraction System

This is a multi-agent system that classifies uploaded files, extracts structured information using LLMs (Gemini), and logs the outputs to a Redis database. It supports multiple formats and intents, and provides a Streamlit web interface for reviewing the extracted data.

---

## Agents

- **Classifier Agent**: Detects file format (PDF, Email, JSON, etc.) and classifies the document's intent (e.g., Complaint, Invoice, Regulation, RFQ).
- **JSON Agent**: Reformats structured `.json` input using Gemini based on the intent and extracts required fields.
- **Email Agent**: Extracts relevant fields from unstructured `.txt` (Email) or `.pdf` files using Gemini.
- **Streamlit App**: Web UI for uploading files and visualizing extracted info from Redis.

---

## Supported Intents & Fields

Each intent expects 5 key fields:

- **Complaint**: `customer_name`, `issue_type`, `product`, `date_of_incident`, `resolution_requested`
- **Invoice**: `invoice_number`, `date`, `total_amount`, `sender`, `recipient`
- **RFQ**: `requested_items`, `quantity`, `delivery_date`, `budget`, `contact_person`
- **Regulation**: `customer_name`, `question`, `product_mentioned`, `urgency_level`, `preferred_contact_method`

The agents extract as many of these fields as possible and mark the rest as missing.

---

## Redis Logging Format

Each processed file generates a Redis hash key: 
```log:<timestamp>```

---

## How to Setup
1. Install dependencies  in a new virtual environment and set it as source
   ```bash
   pip install -r requirements.txt
   ```
2. Make sure you have redis installed and running in your system.

3. Create a .env file with your ```GOOGLE_API_KEY```

4. run this for web interface and then drag drop your files
    ```bash
    streamlit run app.py
    ```
5. run this for cli, It will ask for the filepath and then provide the key. You can check the logs using the key is "redis-cli".
   ```bash
   python main.py
   ```

---

## [Demo Video](https://drive.google.com/file/d/18SXXpD1nKgxVQAHec4YqQog8fc_yR9iK/view?usp=drive_link)

---

## Output Screenshorts
![Screenshot_20250531_221234](https://github.com/user-attachments/assets/3fdd94d4-f153-4276-bda5-b6c3af06a77e)

![Screenshot_20250531_221330](https://github.com/user-attachments/assets/fb34b8fe-7e3b-42ce-91e0-04839fd1c5f6)

![Screenshot_20250531_221303](https://github.com/user-attachments/assets/6eed522c-2630-40bd-b825-8aa99773915e)
