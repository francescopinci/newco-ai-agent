"""
Centralized logging utility for the LLM Chat Agent.
Provides structured logging with different levels and error tracking.
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Configure logging
def setup_logging():
    """Setup logging configuration for Streamlit Cloud."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Streamlit Cloud logs to stdout
        ]
    )
    
    # Set specific loggers
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('supabase').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

class ErrorLogger:
    """Centralized error logging with context."""
    
    @staticmethod
    def log_error(
        error: Exception, 
        context: str, 
        additional_data: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Log an error with full context for debugging.
        
        Args:
            error: The exception that occurred
            context: Description of where the error occurred
            additional_data: Additional context data
            user_message: User-friendly error message
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        if additional_data:
            error_data["additional_data"] = additional_data
            
        if user_message:
            error_data["user_message"] = user_message
        
        # Log to console (Streamlit Cloud logs)
        logger.error(f"ERROR in {context}: {type(error).__name__}: {str(error)}")
        logger.error(f"Additional data: {json.dumps(additional_data or {}, indent=2)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return error_data
    
    @staticmethod
    def log_warning(message: str, context: str, additional_data: Optional[Dict[str, Any]] = None):
        """Log a warning with context."""
        logger.warning(f"WARNING in {context}: {message}")
        if additional_data:
            logger.warning(f"Additional data: {json.dumps(additional_data, indent=2)}")
    
    @staticmethod
    def log_info(message: str, context: str, additional_data: Optional[Dict[str, Any]] = None):
        """Log an info message with context."""
        logger.info(f"INFO in {context}: {message}")
        if additional_data:
            logger.info(f"Additional data: {json.dumps(additional_data, indent=2)}")

def log_function_call(func_name: str, args: Optional[Dict[str, Any]] = None):
    """Decorator to log function calls for debugging."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Function {func_name} completed successfully")
                return result
            except Exception as e:
                ErrorLogger.log_error(e, f"Function {func_name}", {"args": args, "kwargs": kwargs})
                raise
        return wrapper
    return decorator

def safe_execute(func, context: str, default_return=None, *args, **kwargs):
    """
    Safely execute a function with error handling and logging.
    
    Args:
        func: Function to execute
        context: Context description for logging
        default_return: Value to return if function fails
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result or default_return if error occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ErrorLogger.log_error(e, context)
        return default_return
