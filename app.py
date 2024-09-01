import streamlit as st
import time
import random
import string
import PyPDF2
from rag_chain import caller

# sess_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
sess_id = "W56PNA34XM"

# Streamlit page configuration
st.set_page_config(page_title="Chat Application", layout="wide")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to OCBC's Job Recommender Chatbot! Simply drop your CV below, and we'll instantly analyze it to see if you're a perfect fit for any of our current job openings. Let us help you take the next step in your career with OCBC!"}
    ]

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

# Initialize a state variable for file upload
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False

# We loop through each message in the session state and render it as
# a chat message.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

pdf_text = []
# Only show the file uploader and link input if no file has been uploaded
if not st.session_state.file_uploaded:
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    # link_input = st.text_input("Enter a link here")
    
    if uploaded_file is not None:
    # Process the PDF file
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() 
        
        st.session_state.messages.append(
        {"role": "user", "content": pdf_text}
    )

    # Add our input to the chat window
        with st.chat_message("user"):
            st.markdown(pdf_text)

        with st.spinner("Thinking ..."):
            response = caller(pdf_text)
        # Add the response to the session state
        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

        # Add the response to the chat window
        with st.chat_message("assistant"):
            st.markdown(response)

        # Optionally, you can display the extracted textssd
        st.write("Extracted text from the PDF:")
        st.text(pdf_text)
        print(pdf_text)


        # Set the file_uploaded state to True
        st.session_state.file_uploaded = True
        st.rerun()  # This will rerun the app and hide the uploader

else:
    st.success("File uploaded successfully!")
# We take questions/instructions from the chat input to pass to the LLM
if user_prompt := st.chat_input("Your message here", key="user_input"):

    # Add our input to the session state
    st.session_state.messages.append(
        {"role": "user", "content": user_prompt}
    )

    # Add our input to the chat window
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.spinner("Thinking ..."):
        response = caller(user_prompt)
    # Add the response to the session state
    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    # Add the response to the chat window
    with st.chat_message("assistant"):
        st.markdown(response)