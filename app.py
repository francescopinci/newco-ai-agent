"""
Main Streamlit application for the LLM Chat Agent.
"""

import streamlit as st
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
from utils.supabase_client import save_conversation_with_summary, generate_session_id
from utils.openai_client import get_chat_response, create_messages_with_system_prompt
from utils.logger import ErrorLogger, logger

# Load environment variables
try:
    load_dotenv()
    logger.info("Environment variables loaded successfully")
except Exception as e:
    ErrorLogger.log_error(e, "Environment variable loading")

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
def initialize_session_state():
    """Initialize session state with error handling."""
    try:
        if "messages" not in st.session_state:
            st.session_state.messages = []
            logger.info("Initialized messages in session state")
        
        if "session_id" not in st.session_state:
            try:
                st.session_state.session_id = generate_session_id()
                logger.info(f"Generated session ID: {st.session_state.session_id}")
            except Exception as e:
                ErrorLogger.log_error(e, "Session ID generation in initialization")
                st.error(f"Failed to generate session ID: {str(e)}")
                st.stop()
        
        if "conversation_ended" not in st.session_state:
            st.session_state.conversation_ended = False
            logger.info("Initialized conversation_ended in session state")
        
        if "error_count" not in st.session_state:
            st.session_state.error_count = 0
            logger.info("Initialized error_count in session state")
            
    except Exception as e:
        ErrorLogger.log_error(e, "Session state initialization")
        st.error("Failed to initialize application. Please refresh the page.")
        st.stop()

# Initialize session state
initialize_session_state()

def start_new_conversation():
    """Start a new conversation session."""
    try:
        logger.info("Starting new conversation")
        st.session_state.messages = []
        st.session_state.session_id = generate_session_id()
        st.session_state.conversation_ended = False
        st.session_state.error_count = 0
        logger.info(f"New conversation started with session ID: {st.session_state.session_id}")
        st.rerun()
    except Exception as e:
        ErrorLogger.log_error(e, "Start new conversation")
        st.error(f"Failed to start new conversation: {str(e)}")

def end_conversation():
    """End the current conversation and save to database with summary generation."""
    try:
        if not st.session_state.messages:
            ErrorLogger.log_warning("Attempted to end conversation with no messages", "End conversation")
            st.warning("No conversation to end.")
            return
        
        logger.info(f"Ending conversation with {len(st.session_state.messages)} messages")
        
        # Show clear instructions to user
        st.info("**Please wait while we process your conversation...**")
        st.warning("**Important**: Please keep this tab open until you see the confirmation message. Closing the tab now may result in data loss.")
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Save conversation data
        status_text.text("Saving conversation...")
        progress_bar.progress(33)
        
        # Step 2: Generate summary
        status_text.text("Generating conversation summary...")
        progress_bar.progress(66)
        
        # Step 3: Complete save with summary and evaluation
        status_text.text("Finalizing and saving everything...")
        progress_bar.progress(90)
        
        # Save conversation with summary and evaluation
        success = save_conversation_with_summary(
            st.session_state.session_id,
            st.session_state.messages
        )
        
        # Complete progress
        progress_bar.progress(100)
        status_text.text("Complete!")
        
        if success:
            st.session_state.conversation_ended = True
            logger.info(f"Conversation ended and saved successfully for session: {st.session_state.session_id}")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Show success message with clear instructions
            st.success("**Conversation Successfully Saved!**")
            st.info("Your conversation has been saved with a complete summary and analysis.")
            st.success("**It's now safe to close this tab or start a new conversation.**")
            
        else:
            ErrorLogger.log_warning("Failed to save conversation", "End conversation", {
                "session_id": st.session_state.session_id,
                "messages_count": len(st.session_state.messages)
            })
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.error("**Failed to save conversation. Please try again.**")
            st.warning("If the problem persists, please contact support with your Session ID.")
            
    except Exception as e:
        ErrorLogger.log_error(e, "End conversation", {
            "session_id": st.session_state.session_id,
            "messages_count": len(st.session_state.messages) if st.session_state.messages else 0
        })
        
        # Clear any progress indicators
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()
            
        st.error("**An error occurred while saving your conversation.**")
        st.error(f"Error details: {str(e)}")
        st.warning("Please try again or contact support if the problem persists.")

def display_chat_message(role: str, content: str):
    """Display a chat message in the UI."""
    try:
        if not content or not content.strip():
            ErrorLogger.log_warning(f"Empty content for {role} message", "Display chat message")
            content = "[Empty message]"
        
        with st.chat_message(role):
            st.markdown(content)
    except Exception as e:
        ErrorLogger.log_error(e, "Display chat message", {
            "role": role,
            "content_length": len(content) if content else 0
        })
        # Fallback display
        st.write(f"**{role.title()}:** {content or '[Error displaying message]'}")

def validate_environment():
    """Validate required environment variables."""
    missing_vars = []
    
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    if not os.getenv("SUPABASE_URL"):
        missing_vars.append("SUPABASE_URL")
    
    if not os.getenv("SUPABASE_KEY"):
        missing_vars.append("SUPABASE_KEY")
    
    if missing_vars:
        ErrorLogger.log_warning(f"Missing environment variables: {missing_vars}", "Environment validation")
        return False, missing_vars
    
    logger.info("All required environment variables are present")
    return True, []

def main():
    """Main application function."""
    try:
        logger.info("Starting main application")
        
        # Header
        st.title("The Unfair Advantage Scout")
        st.markdown("Expert mentor and interviewer for aspiring startup founders")
        
        # Validate environment variables
        env_valid, missing_vars = validate_environment()
        
        if not env_valid:
            st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            st.error("Please set these variables in your environment or .env file.")
            return
        
        # Check for OpenAI API key specifically
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your environment variables.")
            return
        
        # Check for Supabase credentials
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            st.warning("Supabase credentials not found. Conversations will not be saved.")
            logger.warning("Supabase credentials missing - conversations will not be saved")
    
        # Sidebar with controls
        with st.sidebar:
            st.header("Controls")
            
            if st.button("Start New Conversation", use_container_width=True):
                start_new_conversation()
            
            if st.button("End Conversation", use_container_width=True, disabled=st.session_state.conversation_ended):
                end_conversation()
            
            # Warning about keeping tab open
            if not st.session_state.conversation_ended:
                st.markdown("---")
                st.warning("**Important**: When ending a conversation, please keep this tab open until you see the confirmation message. Closing the tab too early may result in data loss.")
            
            st.markdown("---")
            st.markdown(f"**Session ID:** `{st.session_state.session_id}`")
            
            if st.session_state.conversation_ended:
                st.success("Conversation ended and saved")
            
            # Error count display (for debugging)
            if hasattr(st.session_state, 'error_count') and st.session_state.error_count > 0:
                st.warning(f"Errors encountered: {st.session_state.error_count}")
    
        # Main chat interface
        if not st.session_state.conversation_ended:
            # Display chat history with error handling
            try:
                for i, message in enumerate(st.session_state.messages):
                    if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                        ErrorLogger.log_warning(f"Invalid message format at index {i}", "Display chat history", {
                            "message": str(message)[:100] if message else "None"
                        })
                        continue
                    
                    display_chat_message(message["role"], message["content"])
            except Exception as e:
                ErrorLogger.log_error(e, "Display chat history")
                st.error("Error displaying chat history. Please refresh the page.")
            
            # Chat input with comprehensive error handling
            try:
                if prompt := st.chat_input("Type your message here..."):
                    if not prompt.strip():
                        ErrorLogger.log_warning("Empty prompt received", "Chat input")
                        st.warning("Please enter a message.")
                        return
                    
                    logger.info(f"User input received: {prompt[:50]}...")
                    
                    # Add user message to session state
                    try:
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        display_chat_message("user", prompt)
                    except Exception as e:
                        ErrorLogger.log_error(e, "Add user message to session state")
                        st.error("Failed to add your message. Please try again.")
                        return
                    
                    # Generate and display assistant response
                    try:
                        with st.chat_message("assistant"):
                            message_placeholder = st.empty()
                            full_response = ""
                            
                            # Prepare messages with system prompt
                            try:
                                messages_with_system = create_messages_with_system_prompt(st.session_state.messages)
                                logger.info(f"Created messages with system prompt: {len(messages_with_system)} total messages")
                            except ValueError as e:
                                ErrorLogger.log_error(e, "Create messages with system prompt")
                                message_placeholder.markdown(f"Error: {str(e)}")
                                full_response = f"Error: {str(e)}"
                                st.session_state.error_count += 1
                            else:
                                # Stream response from OpenAI
                                try:
                                    chunk_count = 0
                                    for chunk in get_chat_response(messages_with_system):
                                        if chunk:  # Only process non-empty chunks
                                            chunk_count += 1
                                            full_response += chunk
                                            message_placeholder.markdown(full_response + "▌")
                                    
                                    logger.info(f"Received {chunk_count} chunks from OpenAI")
                                    
                                except Exception as e:
                                    ErrorLogger.log_error(e, "OpenAI streaming response")
                                    full_response = "I apologize, but I'm experiencing technical difficulties. Please try again later."
                                    message_placeholder.markdown(full_response)
                                    st.session_state.error_count += 1
                            
                            # Update placeholder with final response
                            message_placeholder.markdown(full_response)
                        
                        # Add assistant response to session state
                        try:
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                            logger.info(f"Added assistant response to session state: {len(full_response)} characters")
                        except Exception as e:
                            ErrorLogger.log_error(e, "Add assistant message to session state")
                            st.error("Failed to save the response. Please try again.")
                            st.session_state.error_count += 1
                    
                    except Exception as e:
                        ErrorLogger.log_error(e, "Assistant response generation")
                        st.error("Failed to generate response. Please try again.")
                        st.session_state.error_count += 1
                        
            except Exception as e:
                ErrorLogger.log_error(e, "Chat input processing")
                st.error("Error processing your input. Please try again.")
                st.session_state.error_count += 1
    
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
        
        logger.info("Main application completed successfully")
        
    except Exception as e:
        ErrorLogger.log_error(e, "Main application", {
            "session_id": st.session_state.session_id if hasattr(st.session_state, 'session_id') else "unknown",
            "conversation_ended": st.session_state.conversation_ended if hasattr(st.session_state, 'conversation_ended') else "unknown",
            "messages_count": len(st.session_state.messages) if hasattr(st.session_state, 'messages') else 0
        })
        st.error("A critical error occurred. Please refresh the page and try again.")
        st.error(f"Error details: {str(e)}")
        
        # Increment error count if possible
        if hasattr(st.session_state, 'error_count'):
            st.session_state.error_count += 1

if __name__ == "__main__":
    main()
