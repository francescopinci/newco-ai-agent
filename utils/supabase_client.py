"""
Supabase client for storing conversations and summaries.
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from .openai_client import generate_summary, generate_evaluation
from openai import OpenAI

# Module-level variable to store the client (singleton pattern)
_supabase_client = None

def get_supabase_client():
    """Get or create Supabase client (singleton pattern)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
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
    try:
        supabase = get_supabase_client()
        data = {
            "session_id": session_id,
            "messages": messages,
            "created_at": datetime.utcnow().isoformat(),
            "ended_at": datetime.utcnow().isoformat()
        }
        
        if summary:
            data["summary"] = summary
        if evaluation:
            data["evaluation"] = evaluation
            
        result = supabase.table("conversations").insert(data).execute()
        return len(result.data) > 0
        
    except Exception as e:
        print(f"Error saving conversation: {e}")
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
        # Generate summary and evaluation
        summary = generate_summary(messages)
        evaluation = generate_evaluation(messages)
        
        # Save to database
        return save_conversation(session_id, messages, summary, evaluation)
        
    except Exception as e:
        print(f"Error saving conversation with summary: {e}")
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
        supabase = get_supabase_client()
        result = supabase.table("conversations").select("*").eq("session_id", session_id).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error retrieving conversation: {e}")
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
        supabase = get_supabase_client()
        result = supabase.table("conversations").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data
        
    except Exception as e:
        print(f"Error retrieving conversations: {e}")
        return []

def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        str: Unique session identifier
    """
    return str(uuid.uuid4())
