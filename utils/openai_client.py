"""
OpenAI API client for chat functionality and summarization.
"""

import json
import os
from typing import List, Dict, Any, Generator
from openai import OpenAI
from .prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, EVALUATION_PROMPT

# Module-level variable to store the client (singleton pattern)
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client (singleton pattern)."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client

def get_chat_response(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """
    Get streaming response from OpenAI for chat.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        
    Yields:
        str: Streaming response chunks
    """
    try:
        client = get_openai_client()
        stream = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            stream=True,
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        # Log the error but don't yield it as content
        print(f"OpenAI API error: {str(e)}")
        yield "I apologize, but I'm experiencing technical difficulties. Please try again later."

def generate_summary(messages: List[Dict[str, str]]) -> str:
    """
    Generate a summary of the conversation.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        str: Generated summary
    """
    try:
        client = get_openai_client()
        # Format conversation for summary
        conversation_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in messages 
            if msg['role'] in ['user', 'assistant']
        ])
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "user", "content": SUMMARY_PROMPT.format(conversation=conversation_text)}
            ],
            temperature=float(os.getenv("OPENAI_SUMMARY_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("OPENAI_SUMMARY_MAX_TOKENS", "500"))
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return "Unable to generate summary due to technical difficulties."

def generate_evaluation(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate structured evaluation of the conversation.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Dict: Structured evaluation data
    """
    try:
        client = get_openai_client()
        # Format conversation for evaluation
        conversation_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in messages 
            if msg['role'] in ['user', 'assistant']
        ])
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "user", "content": EVALUATION_PROMPT.format(conversation=conversation_text)}
            ],
            temperature=float(os.getenv("OPENAI_EVALUATION_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("OPENAI_EVALUATION_MAX_TOKENS", "800"))
        )
        
        # Parse JSON response
        evaluation_text = response.choices[0].message.content.strip()
        return json.loads(evaluation_text)
        
    except json.JSONDecodeError:
        print("Failed to parse evaluation JSON")
        return {
            "sentiment": "neutral",
            "key_topics": [],
            "user_satisfaction": 5,
            "conversation_quality": 5,
            "main_concerns": [],
            "resolution_status": "unresolved",
            "error": "Failed to parse evaluation JSON"
        }
    except Exception as e:
        print(f"Error generating evaluation: {str(e)}")
        return {
            "sentiment": "neutral",
            "key_topics": [],
            "user_satisfaction": 5,
            "conversation_quality": 5,
            "main_concerns": [],
            "resolution_status": "unresolved",
            "error": f"Error generating evaluation: {str(e)}"
        }

def create_messages_with_system_prompt(conversation_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Create message list with system prompt for OpenAI API.
    
    Args:
        conversation_messages: List of user/assistant messages
        
    Returns:
        List[Dict]: Messages with system prompt prepended
    """
    # Validate input
    if not conversation_messages:
        raise ValueError("Conversation messages cannot be empty")
    
    # Validate message structure
    for msg in conversation_messages:
        if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
            raise ValueError("Invalid message format: each message must have 'role' and 'content' keys")
        if not isinstance(msg['content'], str) or not msg['content'].strip():
            raise ValueError("Message content cannot be empty")
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + conversation_messages
