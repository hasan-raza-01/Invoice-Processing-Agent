"""Custom exception handling"""
import sys
from typing import Any


def get_error_message(error: Exception, sys_info: Any) -> str:
    """Format detailed error message with traceback info"""
    _, _, exc_traceback = sys_info.exc_info()
    
    if exc_traceback:
        file_name = exc_traceback.tb_frame.f_code.co_filename
        line_number = exc_traceback.tb_lineno
        error_message = (
            f"Error occurred in script: {file_name}\n"
            f"Line number: {line_number}\n"
            f"Error message: {str(error)}"
        )
    else:
        error_message = str(error)
    
    return error_message


class InvoiceAgentException(Exception):
    """Custom exception for Invoice Agent"""
    
    def __init__(self, error_message: str, error_detail: Any):
        super().__init__(error_message)
        self.error_message = get_error_message(
            Exception(error_message), 
            error_detail
        )
    
    def __str__(self):
        return self.error_message
