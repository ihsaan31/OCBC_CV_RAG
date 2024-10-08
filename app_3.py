import streamlit as st
from dataclasses import dataclass
from typing import Literal
from langchain import OpenAI
from langchain.chains import ConversationChain
from langchain_openai import AzureChatOpenAI
import os
import base64

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_ID = os.getenv('AZURE_OPENAI_DEPLOYMENT_ID')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

@dataclass
class Message:
    """Class for keeping track of a chat message."""
    origin: Literal["human", "ai"]
    message: str

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

def initialize_conversation(chat_name):
    if chat_name not in st.session_state.chat_histories:
        llm = AzureChatOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_DEPLOYMENT_ID,
            api_version=AZURE_API_VERSION,
            api_key=AZURE_OPENAI_KEY,
            temperature=0.0,
            verbose=True,
        )
        st.session_state.chat_histories[chat_name] = {
            "conversation": ConversationChain(llm=llm),
            "messages": []
        }

def switch_chat(chat_name):
    if chat_name != st.session_state.selected_chat:
        st.session_state.selected_chat = chat_name
        initialize_conversation(chat_name)

def create_new_chat(chat_name):
    if chat_name and chat_name not in st.session_state.chat_histories:
        initialize_conversation(chat_name)
        st.session_state.selected_chat = chat_name

def on_click_callback():
    human_prompt = st.session_state.human_prompt
    chat = st.session_state.chat_histories[st.session_state.selected_chat]
    llm_response = chat["conversation"].run(human_prompt)
    
    # Add messages to the history
    chat["messages"].append(Message(origin="human", message=human_prompt))
    chat["messages"].append(Message(origin="ai", message=llm_response))
    
    # Clear the input box
    st.session_state.human_prompt = ""

def main():
    load_css()

    # Initialize the session state
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}
    
    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = "Default"
        initialize_conversation(st.session_state.selected_chat)

    st.sidebar.title("Chat History")

    # Add a form for creating a new chat
    with st.sidebar.form(key="new_chat_form", clear_on_submit=True):
        new_chat_name = st.text_input("New Chat Name", "")
        create_chat_button = st.form_submit_button("Create New Chat")
        if create_chat_button:
            create_new_chat(new_chat_name)

    # Display the list of existing chats
    chat_names = list(st.session_state.chat_histories.keys())
    selected_chat = st.sidebar.radio("Select a chat:", options=chat_names)
    
    switch_chat(selected_chat)
    
    st.title(f"Chat with {selected_chat}")

    # Load and encode the images
    user_image = get_image_base64("static/user_icon.png")
    bot_image = get_image_base64("static/logo.png")

    # Display chat history
    chat = st.session_state.chat_histories[st.session_state.selected_chat]
    for message in chat["messages"]:
        if message.origin == "human":
            st.markdown(f"""
                <div class="chat-row row-reverse">
                    <img src="data:image/png;base64,{user_image}" class="chat-icon">
                    <div class="chat-bubble human-bubble">{message.message}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-row">
                    <img src="data:image/png;base64,{bot_image}" class="chat-icon">
                    <div class="chat-bubble ai-bubble">{message.message}</div>
                </div>
            """, unsafe_allow_html=True)

    # Chat input form with button
    with st.form(key='chat_form', clear_on_submit=True):
        st.markdown("**Chat**")
        cols = st.columns((6, 1))
        with cols[0]:
            st.text_input(
                "Chat",
                value="",
                label_visibility="collapsed",
                key="human_prompt",
            )
        with cols[1]:
            st.form_submit_button(
                "Send",
                type="primary",
                on_click=on_click_callback,
            )

if __name__ == "__main__":
    main()
