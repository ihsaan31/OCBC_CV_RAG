import streamlit as st
import time
import random
import string
import PyPDF2
from rag_chain import caller_cv, caller_question
from ocr_extractor import extract_text_from_pdf
from paddleocr import PaddleOCR

# sess_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
sess_id = "W56PNA34XM"

# Streamlit page configuration with custom logo
st.set_page_config(
    page_title="OCBC Job Recommender",
    layout="wide",
    page_icon= r"C:\Users\san\Documents\Documents\OCBC\Github_ocbc_workspace\OCBC_CV_RAG\logo.png"  # Replace with the path to your PNG file
)

# Rest of your code remains the same
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to OCBC's Job Recommender Chatbot! Simply drop your CV below, and we'll instantly analyze it to see if you're a perfect fit for any of our current job openings. Let us help you take the next step in your career with OCBC!"}
    ]

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

pdf_text = ""

if not st.session_state.file_uploaded:
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    
    if uploaded_file is not None:
    # Process the PDF file
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()
        
        st.session_state.messages.append(
            {"role": "user", "content": pdf_text}
        )
        with st.chat_message("user"):
            st.markdown(pdf_text)
        with st.spinner("Thinking ..."):
            response = caller_cv(pdf_text)
        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )
        with st.chat_message("assistant"):
            st.markdown(response)
        st.write("Extracted text from the PDF:")
        st.text(pdf_text)
        print(pdf_text)
        st.session_state.file_uploaded = True
        st.rerun()
else:
    st.success("File uploaded successfully!")

if user_prompt := st.chat_input("Your message here", key="user_input"):
    st.session_state.messages.append(
        {"role": "user", "content": user_prompt}
    )
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.spinner("Thinking ..."):
        response = caller_question(user_prompt)
    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )
    with st.chat_message("assistant"):
        st.markdown(response)