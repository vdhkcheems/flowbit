from pathlib import Path
from classifier_agent import classifier_agent
from email_agent import extract_and_store_from_email
from json_agent import extract_and_store_from_json

filepath = input("insert file path: ")
if not Path(filepath).exists():
    print("Invalid file path.")
    exit()

format_, intent, key = classifier_agent(file_path=filepath)

if format_ == "JSON":
    extract_and_store_from_json(file_path=filepath, key=key)
    print(key)
elif format_ in ['Email', 'PDF']:
    extract_and_store_from_email(file_path=filepath, key=key)
    print(key)
else:
    print(f"No handler for format: {format_}")

