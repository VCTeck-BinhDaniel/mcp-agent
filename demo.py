import streamlit as st
import requests
import os
import json
import uuid

st.set_page_config(page_title="AI Chat Demo", page_icon="🤖")

st.title("🤖 AI Chat Service Demo")
st.markdown("A fast Streamlit frontend connecting to the FastAPI backend with streaming.")

# Allow configuring the backend URL (useful for local vs docker)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Add a sidebar for settings
with st.sidebar:
    st.header("Settings")
    user_id = st.text_input("User ID", value=str(uuid.uuid4()))
    session_id = st.text_input("Session ID", value="demo-session")
    st.markdown(f"**Backend URL:** `{API_URL}`")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask something..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Request to the backend API stream endpoint
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        payload = {
            "message": prompt,
            "session_id": session_id,
            "user_id": user_id
        }
        
        try:
            with requests.post(
                f"{API_URL}/api/v1/chat/stream", 
                json=payload, 
                stream=True, 
                timeout=120
            ) as response:
                response.raise_for_status()
                
                # Iterate over the SSE stream
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:]
                            try:
                                data = json.loads(data_str)
                                # The SSE payload contains {"text": chunk} for delta events
                                if "text" in data:
                                    full_response += data["text"]
                                    message_placeholder.markdown(full_response + "▌")
                                elif "error" in data:
                                    st.error(f"Error: {data['error']}")
                            except json.JSONDecodeError:
                                pass
            
            # Final output update
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with the backend: {e}")
