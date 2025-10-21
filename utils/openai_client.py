"""
OpenAI API client for chat functionality and summarization.
"""

import json
import os
import time
from typing import List, Dict, Any, Generator, Optional
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, AuthenticationError
from .prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, EVALUATION_PROMPT
from .logger import ErrorLogger, logger

# Module-level variable to store the client (singleton pattern)
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client (singleton pattern)."""
    global _openai_client
    if _openai_client is None:
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            _openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            ErrorLogger.log_error(e, "OpenAI client initialization")
            raise
    return _openai_client

def get_chat_response(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """
    Get streaming response from OpenAI for chat.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        
    Yields:
        str: Streaming response chunks
    """
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            client = get_openai_client()
            
            # Validate environment variables
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
            
            logger.info(f"Starting OpenAI chat completion with model: {model}")
            
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=5  # 5 second timeout
            )
            
            chunk_count = 0
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
            
            logger.info(f"OpenAI streaming completed successfully with {chunk_count} chunks")
            return
            
        except RateLimitError as e:
            ErrorLogger.log_error(e, "OpenAI rate limit", {
                "attempt": attempt + 1,
                "max_retries": max_retries,
                "retry_delay": retry_delay
            })
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                yield "I'm currently experiencing high demand. Please try again in a few moments."
                return
                
        except APITimeoutError as e:
            ErrorLogger.log_error(e, "OpenAI API timeout", {
                "attempt": attempt + 1,
                "max_retries": max_retries
            })
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                yield "The request timed out. Please try again."
                return
                
        except APIConnectionError as e:
            ErrorLogger.log_error(e, "OpenAI API connection error", {
                "attempt": attempt + 1,
                "max_retries": max_retries
            })
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                yield "I'm having trouble connecting. Please check your internet connection and try again."
                return
                
        except AuthenticationError as e:
            ErrorLogger.log_error(e, "OpenAI authentication error", {
                "user_message": "Authentication failed - please check API key configuration"
            })
            yield "Authentication error. Please contact support."
            return
            
        except Exception as e:
            ErrorLogger.log_error(e, "OpenAI API error", {
                "attempt": attempt + 1,
                "max_retries": max_retries,
                "messages_count": len(messages)
            })
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                yield "I apologize, but I'm experiencing technical difficulties. Please try again later."
                return

def generate_summary(messages: List[Dict[str, str]]) -> str:
    """
    Generate a summary of the conversation.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        str: Generated summary
    """
    try:
        if not messages:
            ErrorLogger.log_warning("Empty messages list provided for summary generation")
            return "No conversation to summarize."
        
        client = get_openai_client()
        
        # Format conversation for summary
        conversation_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in messages 
            if msg['role'] in ['user', 'assistant'] and msg.get('content', '').strip()
        ])
        
        if not conversation_text.strip():
            ErrorLogger.log_warning("No valid conversation content found for summary")
            return "No meaningful conversation content to summarize."
        
        logger.info(f"Generating summary for conversation with {len(messages)} messages")
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "user", "content": SUMMARY_PROMPT.format(conversation=conversation_text)}
            ],
            temperature=float(os.getenv("OPENAI_SUMMARY_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("OPENAI_SUMMARY_MAX_TOKENS", "500")),
            timeout=30
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info("Summary generated successfully")
        return summary
        
    except Exception as e:
        ErrorLogger.log_error(e, "Summary generation", {
            "messages_count": len(messages),
            "conversation_length": len(conversation_text) if 'conversation_text' in locals() else 0
        })
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
        if not messages:
            ErrorLogger.log_warning("Empty messages list provided for evaluation generation")
            return {
                "sentiment": "neutral",
                "key_topics": [],
                "user_satisfaction": 5,
                "conversation_quality": 5,
                "main_concerns": [],
                "resolution_status": "unresolved",
                "error": "No conversation to evaluate"
            }
        
        client = get_openai_client()
        
        # Format conversation for evaluation
        conversation_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in messages 
            if msg['role'] in ['user', 'assistant'] and msg.get('content', '').strip()
        ])
        
        if not conversation_text.strip():
            ErrorLogger.log_warning("No valid conversation content found for evaluation")
            return {
                "sentiment": "neutral",
                "key_topics": [],
                "user_satisfaction": 5,
                "conversation_quality": 5,
                "main_concerns": [],
                "resolution_status": "unresolved",
                "error": "No meaningful conversation content to evaluate"
            }
        
        logger.info(f"Generating evaluation for conversation with {len(messages)} messages")
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "user", "content": EVALUATION_PROMPT.format(conversation=conversation_text)}
            ],
            temperature=float(os.getenv("OPENAI_EVALUATION_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("OPENAI_EVALUATION_MAX_TOKENS", "800")),
            timeout=30
        )
        
        # Parse JSON response
        evaluation_text = response.choices[0].message.content.strip()
        logger.info("Evaluation generated successfully")
        
        try:
            evaluation_data = json.loads(evaluation_text)
            # Validate required fields
            required_fields = ["sentiment", "key_topics", "user_satisfaction", "conversation_quality", "main_concerns", "resolution_status"]
            for field in required_fields:
                if field not in evaluation_data:
                    ErrorLogger.log_warning(f"Missing required field '{field}' in evaluation response")
                    evaluation_data[field] = None if field in ["key_topics", "main_concerns"] else 5 if field in ["user_satisfaction", "conversation_quality"] else "neutral" if field == "sentiment" else "unresolved"
            
            return evaluation_data
            
        except json.JSONDecodeError as json_error:
            ErrorLogger.log_error(json_error, "JSON parsing in evaluation", {
                "evaluation_text": evaluation_text[:200] + "..." if len(evaluation_text) > 200 else evaluation_text
            })
            return {
                "sentiment": "neutral",
                "key_topics": [],
                "user_satisfaction": 5,
                "conversation_quality": 5,
                "main_concerns": [],
                "resolution_status": "unresolved",
                "error": "Failed to parse evaluation JSON",
                "raw_response": evaluation_text[:200] + "..." if len(evaluation_text) > 200 else evaluation_text
            }
        
    except Exception as e:
        ErrorLogger.log_error(e, "Evaluation generation", {
            "messages_count": len(messages),
            "conversation_length": len(conversation_text) if 'conversation_text' in locals() else 0
        })
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
        
    Raises:
        ValueError: If input validation fails
    """
    try:
        # Validate input
        if not conversation_messages:
            raise ValueError("Conversation messages cannot be empty")
        
        if not isinstance(conversation_messages, list):
            raise ValueError("Conversation messages must be a list")
        
        # Validate message structure and content
        for i, msg in enumerate(conversation_messages):
            if not isinstance(msg, dict):
                raise ValueError(f"Message {i} must be a dictionary")
            
            if 'role' not in msg or 'content' not in msg:
                raise ValueError(f"Message {i} must have 'role' and 'content' keys")
            
            if not isinstance(msg['role'], str) or not isinstance(msg['content'], str):
                raise ValueError(f"Message {i} role and content must be strings")
            
            if msg['role'] not in ['user', 'assistant']:
                raise ValueError(f"Message {i} role must be 'user' or 'assistant'")
            
            if not msg['content'].strip():
                ErrorLogger.log_warning(f"Empty content in message {i}", "Message validation")
        
        logger.info(f"Creating messages with system prompt for {len(conversation_messages)} conversation messages")
        
        return [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + conversation_messages
        
    except Exception as e:
        ErrorLogger.log_error(e, "Message validation and system prompt creation", {
            "conversation_messages_count": len(conversation_messages) if conversation_messages else 0,
            "conversation_messages_type": type(conversation_messages).__name__
        })
        raise
