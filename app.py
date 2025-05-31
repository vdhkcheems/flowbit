# app.py
import streamlit as st
from classifier_agent import classifier_agent
from email_agent import extract_and_store_from_email
from json_agent import extract_and_store_from_json
import redis
import json
import tempfile
import os

r = redis.Redis()

st.title("Flowbit File Processor")

uploaded_file = st.file_uploader("Upload a file (JSON, TXT, PDF)", type=["json", "txt", "pdf"])

if uploaded_file:
    # Save uploaded file to temp
    suffix = os.path.splitext(uploaded_file.name)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Run classifier
    format_, intent, key = classifier_agent(file_path)

    # Run appropriate agent
    if format_ == "JSON":
        extract_and_store_from_json(file_path, key)
    elif format_ in ["Email", "PDF"]:
        extract_and_store_from_email(file_path, key)
    else:
        st.error(f"Unsupported format: {format_}")
        os.remove(file_path)
        st.stop()

    # Show the logged info from Redis
    st.subheader("Extracted Information")
    log_data = r.hgetall(key)
    for k_bytes, v_bytes in log_data.items():
        k = k_bytes.decode("utf-8")
        v = v_bytes.decode("utf-8")

        try:
            parsed_value = json.loads(v)
            st.json({k: parsed_value})
        except json.JSONDecodeError:
            st.write(f"**{k}**: {v}")

    os.remove(file_path)
