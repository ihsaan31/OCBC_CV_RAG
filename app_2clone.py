import streamlit as st
from dataclasses import dataclass
from typing import Literal
from rag_chain import caller_cv, caller_question
import os
import base64
import time
import random
import string
import PyPDF2
from ocr_extractor import extract_text_from_pdf
from paddleocr import PaddleOCR

# Environment Variables
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_ID = os.getenv('AZURE_OPENAI_DEPLOYMENT_ID')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')

@dataclass
class Message:
    """Class for keeping track of a chat message."""
    origin: Literal["human", "ai"]
    message: str
    file: str = ""  # Optional field for file paths or names

def load_css():
    st.markdown("""
    <style>
    .chat-row {
        display: flex;
        margin: 5px;
        width: 100%;
        align-items: flex-start;
    }
    .row-reverse {
        flex-direction: row-reverse;
    }
    .chat-bubble {
        font-family: "Source Sans Pro", sans-serif, "Segoe UI", "Roboto", sans-serif;
        border: 1px solid transparent;
        padding: 8px 12px;
        margin: 0px 5px;
        max-width: 60%;
        font-size: 14px;
    }
    .ai-bubble {
        background: rgb(240, 242, 246);
        border-radius: 8px;
    }
    .human-bubble {
        background: linear-gradient(135deg, rgb(0, 178, 255) 0%, rgb(0, 106, 255) 100%);
        color: white;
        border-radius: 16px;
    }
    .chat-icon {
        border-radius: 4px;
        width: 35px;
        height: 35px;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def initialize_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "cv_uploaded" not in st.session_state:
        st.session_state.cv_uploaded = False

def process_cv(uploaded_file):
    pdf_text = ""
    ocr_id = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=True)
    pdf_text += extract_text_from_pdf(uploaded_file, ocr_id, 0.8)
    cv_response = caller_cv(pdf_text)
    st.session_state.messages.append(Message(
        origin="ai", message=cv_response
    ))
    st.session_state.cv_uploaded = True
    st.experimental_rerun()

def on_submit():
    human_prompt = st.session_state.human_prompt
    
    if st.session_state.cv_uploaded:
        llm_response = caller_question(human_prompt)
    else:
        st.warning("Please upload your CV first.")
        return

    # Add messages to the history
    st.session_state.messages.append(Message(
        origin="human", message=human_prompt
    ))
    st.session_state.messages.append(Message(
        origin="ai", message=llm_response
    ))
    
    # Clear input box
    st.session_state.human_prompt = ""

def main():
    load_css()
    initialize_session()

    st.title("Welcome to OCBC's Job Recommender Chatbot!")
    st.markdown("""
    ### Simply drop your CV below, and we'll instantly analyze it to see if you're a perfect fit for any of our current job openings.
    Let us help you take the next step in your career with **OCBC**!
    """)

    # Load and encode the images
    user_image = get_image_base64("static/user_icon.png")
    bot_image = get_image_base64("static/logo.png")

    # Display chat history
    for message in st.session_state.messages:
        file_link = f"<br><a href='uploaded_files/{message.file}' target='_blank'>View Uploaded File</a>" if message.file else ""
        bubble_class = "human-bubble" if message.origin == "human" else "ai-bubble"
        image_src = user_image if message.origin == "human" else bot_image
        st.markdown(f"""
            <div class="chat-row {'row-reverse' if message.origin == 'human' else ''}">
                <img src="data:image/png;base64,{image_src}" class="chat-icon">
                <div class="chat-bubble {bubble_class}">{message.message}{file_link}</div>
            </div>
        """, unsafe_allow_html=True)

    # File uploader for CV
    uploaded_file = st.file_uploader("Upload your CV", type=["pdf"], key="file_uploader")
    if uploaded_file and not st.session_state.cv_uploaded:
        process_cv(uploaded_file)

    # Chat input form with button
    with st.form(key='chat_form', clear_on_submit=True):
        st.markdown("**Chat**")
        st.text_input("Chat", value="", label_visibility="collapsed", key="human_prompt")
        st.form_submit_button("Submit", type="primary", on_click=on_submit)

if __name__ == "__main__":
    main()