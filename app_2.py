import streamlit as st
from dataclasses import dataclass
from typing import Literal
from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationChain
import os
import base64

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

def initialize_conversation():
    if "conversation" not in st.session_state:
        st.session_state.conversation = ConversationChain(
            llm=AzureChatOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                azure_deployment=AZURE_OPENAI_DEPLOYMENT_ID,
                api_version=AZURE_API_VERSION,
                api_key=AZURE_OPENAI_KEY,
                temperature=0.0,
                verbose=True
            )
        )
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "file_name" not in st.session_state:
        st.session_state.file_name = ""

def handle_file_upload(uploaded_file):
    if uploaded_file:
        file_path = f"uploaded_files/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        return uploaded_file.name
    return ""

def on_submit():
    human_prompt = st.session_state.human_prompt
    llm_response = st.session_state.conversation.run(human_prompt)
    
    # Add messages to the history
    st.session_state.messages.append(Message(
        origin="human", message=human_prompt, file=st.session_state.file_name
    ))
    st.session_state.messages.append(Message(
        origin="ai", message=llm_response
    ))
    
    # Clear input box and file uploader
    st.session_state.human_prompt = ""
    st.session_state.file_name = ""

def main():
    load_css()
    initialize_conversation()

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

    # Chat input form with button and file uploader
    with st.form(key='chat_form', clear_on_submit=True):
        st.markdown("**Chat**")
        st.text_input("Chat", value="", label_visibility="collapsed", key="human_prompt")
        st.form_submit_button("Submit", type="primary", on_click=on_submit)
        uploaded_file = st.file_uploader("Upload a file", type=["pdf"], key="file_uploader")
        st.session_state.file_name = handle_file_upload(uploaded_file)

if __name__ == "__main__":
    main()
