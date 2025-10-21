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
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=1000
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        yield f"Error: {str(e)}"

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
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": SUMMARY_PROMPT.format(conversation=conversation_text)}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

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
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": EVALUATION_PROMPT.format(conversation=conversation_text)}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        # Parse JSON response
        evaluation_text = response.choices[0].message.content.strip()
        return json.loads(evaluation_text)
        
    except json.JSONDecodeError:
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
    return [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + conversation_messages
