"""
Main Streamlit application for the LLM Chat Agent.
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.supabase_client import save_conversation_with_summary, generate_session_id
from utils.openai_client import get_chat_response, create_messages_with_system_prompt

# Load environment variables
load_dotenv()

# Page configuration (MUST BE FIRST Streamlit command)
st.set_page_config(
    page_title="NewCO AI Agent",
    page_icon="🤖",
    layout="wide"
)

# Hide Streamlit UI elements for cleaner chat experience
st.markdown("""
<style>
    /* Hide main menu */
    #MainMenu {visibility: hidden;}
    
    /* Hide footer */
    footer {visibility: hidden;}
    
    /* Hide header */
    header {visibility: hidden;}
    
    /* Hide deploy button */
    .stDeployButton {display:none;}
    
    /* Hide decoration */
    #stDecoration {display:none;}
    
    /* Hide toolbar (includes rerun and print buttons) */
    .stApp > div[data-testid="stToolbar"] {display:none;}
    
    /* Hide settings button decoration */
    .stApp > div[data-testid="stDecoration"] {display:none;}
    
    /* Custom styling for cleaner look */
    .stApp {
        margin-top: -80px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with proper error handling
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    try:
        st.session_state.session_id = generate_session_id()
    except Exception as e:
        st.error(f"Failed to generate session ID: {str(e)}")
        st.stop()
if "conversation_ended" not in st.session_state:
    st.session_state.conversation_ended = False

def start_new_conversation():
    """Start a new conversation session."""
    st.session_state.messages = []
    try:
        st.session_state.session_id = generate_session_id()
        st.session_state.conversation_ended = False
        st.rerun()
    except Exception as e:
        st.error(f"Failed to start new conversation: {str(e)}")

def end_conversation():
    """End the current conversation and save to database."""
    if st.session_state.messages:
        try:
            # Save conversation with summary and evaluation
            success = save_conversation_with_summary(
                st.session_state.session_id,
                st.session_state.messages
            )
            
            if success:
                st.session_state.conversation_ended = True
                st.success("Thank you for the conversation! Your chat has been saved.")
            else:
                st.error("Failed to save conversation. Please try again.")
                
        except Exception as e:
            st.error(f"Error saving conversation: {str(e)}")

def display_chat_message(role: str, content: str):
    """Display a chat message in the UI."""
    with st.chat_message(role):
        st.markdown(content)

def main():
    """Main application function."""
    
    # Header
    st.title("🎯 The Unfair Advantage Scout")
    st.markdown("Expert mentor and interviewer for aspiring startup founders")
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your environment variables.")
        return
    
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        st.warning("Supabase credentials not found. Conversations will not be saved.")
    
    # Sidebar with controls
    with st.sidebar:
        st.header("Controls")
        
        if st.button("🔄 Start New Conversation", use_container_width=True):
            start_new_conversation()
        
        if st.button("✅ End Conversation", use_container_width=True, disabled=st.session_state.conversation_ended):
            end_conversation()
        
        st.markdown("---")
        st.markdown(f"**Session ID:** `{st.session_state.session_id}`")
        
        if st.session_state.conversation_ended:
            st.success("✅ Conversation ended and saved")
    
    # Main chat interface
    if not st.session_state.conversation_ended:
        # Display chat history
        for message in st.session_state.messages:
            display_chat_message(message["role"], message["content"])
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            display_chat_message("user", prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Prepare messages with system prompt
                try:
                    messages_with_system = create_messages_with_system_prompt(st.session_state.messages)
                except ValueError as e:
                    message_placeholder.markdown(f"Error: {str(e)}")
                    full_response = f"Error: {str(e)}"
                else:
                    # Stream response from OpenAI
                    for chunk in get_chat_response(messages_with_system):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                
                # Update placeholder with final response
                message_placeholder.markdown(full_response)
            
            # Add assistant response to session state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    else:
        # Conversation ended state
        st.markdown("### Conversation Ended")
        st.markdown("This conversation has been saved and summarized.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start New Conversation", use_container_width=True):
                start_new_conversation()
        
        with col2:
            if st.button("📋 View Session ID", use_container_width=True):
                st.code(st.session_state.session_id)

if __name__ == "__main__":
    main()
