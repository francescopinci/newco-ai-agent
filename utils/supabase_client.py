"""
Supabase client for storing conversations and summaries.
"""

import os
import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from .openai_client import generate_summary, generate_evaluation
from .logger import ErrorLogger, logger

# Module-level variable to store the client (singleton pattern)
_supabase_client = None

def get_supabase_client():
    """Get or create Supabase client (singleton pattern)."""
    global _supabase_client
    if _supabase_client is None:
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
            
            # Configure client options with timeout
            options = ClientOptions(
                timeout=30,  # 30 second timeout for reliability
                auto_refresh_token=True,
                persist_session=True
            )
            
            _supabase_client = create_client(supabase_url, supabase_key, options)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            ErrorLogger.log_error(e, "Supabase client initialization")
            raise
    return _supabase_client

def save_conversation(
    session_id: str, 
    messages: List[Dict[str, str]], 
    summary: Optional[str] = None,
    evaluation: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Save conversation to Supabase.
    
    Args:
        session_id: Unique session identifier
        messages: List of conversation messages
        summary: Optional conversation summary
        evaluation: Optional structured evaluation
        
    Returns:
        bool: True if successful, False otherwise
    """
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Validate inputs
            if not session_id or not isinstance(session_id, str):
                raise ValueError("Session ID must be a non-empty string")
            
            if not messages or not isinstance(messages, list):
                raise ValueError("Messages must be a non-empty list")
            
            # Validate message structure
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    raise ValueError(f"Message {i} must have 'role' and 'content' keys")
            
            supabase = get_supabase_client()
            
            data = {
                "session_id": session_id,
                "messages": messages,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ended_at": datetime.now(timezone.utc).isoformat()
            }
            
            if summary:
                data["summary"] = summary
            if evaluation:
                data["evaluation"] = evaluation
            
            logger.info(f"Saving conversation with session_id: {session_id}, messages_count: {len(messages)}")
            
            result = supabase.table("conversations").insert(data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Conversation saved successfully with session_id: {session_id}")
                return True
            else:
                ErrorLogger.log_warning("No data returned from Supabase insert", "Save conversation", {
                    "session_id": session_id,
                    "attempt": attempt + 1
                })
                return False
                
        except Exception as e:
            ErrorLogger.log_error(e, "Save conversation", {
                "session_id": session_id,
                "messages_count": len(messages),
                "attempt": attempt + 1,
                "max_retries": max_retries,
                "has_summary": summary is not None,
                "has_evaluation": evaluation is not None
            })
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                return False

def save_conversation_with_summary(
    session_id: str, 
    messages: List[Dict[str, str]]
) -> bool:
    """
    Save conversation and generate summary/evaluation.
    
    Args:
        session_id: Unique session identifier
        messages: List of conversation messages
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not messages:
            ErrorLogger.log_warning("Empty messages list provided for conversation saving")
            return False
        
        logger.info(f"Starting conversation save with summary for session_id: {session_id}")
        
        # Generate summary and evaluation with error handling
        summary = None
        evaluation = None
        
        try:
            summary = generate_summary(messages)
            logger.info("Summary generated successfully")
        except Exception as e:
            ErrorLogger.log_error(e, "Summary generation in save_conversation_with_summary", {
                "session_id": session_id,
                "messages_count": len(messages)
            })
            # Continue without summary
        
        try:
            evaluation = generate_evaluation(messages)
            logger.info("Evaluation generated successfully")
        except Exception as e:
            ErrorLogger.log_error(e, "Evaluation generation in save_conversation_with_summary", {
                "session_id": session_id,
                "messages_count": len(messages)
            })
            # Continue without evaluation
        
        # Save to database
        success = save_conversation(session_id, messages, summary, evaluation)
        
        if success:
            logger.info(f"Conversation with summary saved successfully for session_id: {session_id}")
        else:
            ErrorLogger.log_warning("Failed to save conversation with summary", "Save conversation with summary", {
                "session_id": session_id,
                "messages_count": len(messages),
                "summary_generated": summary is not None,
                "evaluation_generated": evaluation is not None
            })
        
        return success
        
    except Exception as e:
        ErrorLogger.log_error(e, "Save conversation with summary", {
            "session_id": session_id,
            "messages_count": len(messages) if messages else 0
        })
        return False

def get_conversation(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve conversation by session ID.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict: Conversation data or None if not found
    """
    try:
        if not session_id or not isinstance(session_id, str):
            ErrorLogger.log_warning("Invalid session_id provided for conversation retrieval", "Get conversation")
            return None
        
        supabase = get_supabase_client()
        logger.info(f"Retrieving conversation for session_id: {session_id}")
        
        result = supabase.table("conversations").select("*").eq("session_id", session_id).execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"Conversation retrieved successfully for session_id: {session_id}")
            return result.data[0]
        else:
            logger.info(f"No conversation found for session_id: {session_id}")
            return None
        
    except Exception as e:
        ErrorLogger.log_error(e, "Get conversation", {
            "session_id": session_id
        })
        return None

def get_all_conversations(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve all conversations.
    
    Args:
        limit: Maximum number of conversations to retrieve
        
    Returns:
        List[Dict]: List of conversation data
    """
    try:
        if not isinstance(limit, int) or limit <= 0:
            ErrorLogger.log_warning(f"Invalid limit provided: {limit}", "Get all conversations")
            limit = 100
        
        supabase = get_supabase_client()
        logger.info(f"Retrieving all conversations with limit: {limit}")
        
        result = supabase.table("conversations").select("*").order("created_at", desc=True).limit(limit).execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} conversations successfully")
            return result.data
        else:
            logger.info("No conversations found")
            return []
        
    except Exception as e:
        ErrorLogger.log_error(e, "Get all conversations", {
            "limit": limit
        })
        return []

def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        str: Unique session identifier
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Generated new session ID: {session_id}")
        return session_id
    except Exception as e:
        ErrorLogger.log_error(e, "Session ID generation")
        # Fallback to timestamp-based ID
        fallback_id = f"session_{int(time.time())}"
        logger.warning(f"Using fallback session ID: {fallback_id}")
        return fallback_id
