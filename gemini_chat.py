import google.generativeai as genai
import streamlit as st
from streamlit_chat import message
import os

def setup_gemini():
    """Setup Gemini API with the provided API key"""
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
    
    if not api_key:
        st.warning("⚠️ Gemini API key not found. Please set the GEMINI_API_KEY environment variable or in streamlit secrets.")
        st.info("You can get a Gemini API key from https://ai.google.dev/")
        return False
    
    genai.configure(api_key=api_key)
    return True

def initialize_chat_session():
    """Initialize the chat session state variables if they don't exist"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "gemini_model" not in st.session_state:
        try:
            st.session_state.gemini_model = genai.GenerativeModel('gemini-pro')
            st.session_state.gemini_chat = st.session_state.gemini_model.start_chat(
                history=[],
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
        except Exception as e:
            st.error(f"Error initializing Gemini model: {e}")
            return False
    
    return True

def display_chat_history():
    """Display the chat history"""
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            message(msg["content"], is_user=True, key=f"user_msg_{i}")
        else:
            message(msg["content"], is_user=False, key=f"assistant_msg_{i}")

def add_message(role, content):
    """Add a message to the chat history"""
    st.session_state.messages.append({"role": role, "content": content})

def get_gemini_response(user_input, context=None):
    """Get a response from Gemini model"""
    try:
        if context:
            prompt = f"Context about lease data: {context}\n\nUser question: {user_input}\n\nPlease provide a helpful response about this oil lease data."
        else:
            prompt = user_input
            
        response = st.session_state.gemini_chat.send_message(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error getting response from Gemini: {e}")
        return "I'm sorry, I encountered an error processing your request. Please try again."

def render_chat_ui(lease_data=None):
    """Render the chat UI component"""
    st.subheader("💬 Ask about your lease data")
    
    # Setup API
    if not setup_gemini():
        st.stop()
    
    # Initialize chat session
    if not initialize_chat_session():
        st.stop()
    
    # Display chat history
    display_chat_history()
    
    # Chat input
    user_input = st.chat_input("Ask a question about your lease data...")
    
    if user_input:
        # Add user message to chat
        add_message("user", user_input)
        
        with st.spinner("Thinking..."):
            # Get response from Gemini
            context = str(lease_data) if lease_data is not None else None
            response = get_gemini_response(user_input, context)
            
            # Add assistant message to chat
            add_message("assistant", response)
            
            # Force a rerun to display the new messages
            st.rerun()
