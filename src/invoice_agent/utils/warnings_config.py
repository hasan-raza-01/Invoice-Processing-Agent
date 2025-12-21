"""Warning configuration for Invoice Processing Agent

This module provides centralized warning management to suppress known benign warnings
and configure warning filters for development vs production environments.
"""
import warnings
import sys


def configure_warnings(mode: str = "production"):
    """Configure warning filters based on environment mode
    
    Args:
        mode: 'production' (suppress benign warnings) or 'development' (show all warnings)
    """
    if mode == "production":
        # Suppress known benign Streamlit warnings in standalone/bare mode
        warnings.filterwarnings(
            "ignore",
            message=".*ThreadPoolExecutor.*",
            category=DeprecationWarning,
            module="streamlit.*"
        )
        warnings.filterwarnings(
            "ignore",
            message=".*script run context.*",
            category=Warning,
            module="streamlit.*"
        )
        warnings.filterwarnings(
            "ignore",
            message=".*ScriptRunContext.*",
            category=RuntimeWarning
        )
        
        # Suppress datetime UTC warnings (we're handling timezone properly now)
        warnings.filterwarnings(
            "ignore",
            message=".*datetime.datetime.utcnow.*",
            category=DeprecationWarning
        )
        warnings.filterwarnings(
            "ignore",
            message=".*datetime.utcnow.*",
            category=DeprecationWarning
        )
        
        # Suppress resource warnings for unclosed sockets/connections
        warnings.filterwarnings(
            "ignore",
            message=".*unclosed.*",
            category=ResourceWarning
        )
        warnings.filterwarnings(
            "ignore",
            category=ResourceWarning,
            module=".*socket.*"
        )
        
        # Suppress tracemalloc warnings
        warnings.filterwarnings(
            "ignore",
            message=".*tracemalloc.*",
            category=RuntimeWarning
        )
        
    elif mode == "development":
        # Show all warnings in development
        warnings.simplefilter("always")
    
    elif mode == "testing":
        # Show deprecation warnings but suppress resource warnings
        warnings.filterwarnings("always", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)


def reset_warnings():
    """Reset warning filters to default state"""
    warnings.resetwarnings()


# Auto-configure on import in production mode (unless explicitly in test mode)
if "pytest" not in sys.modules and "unittest" not in sys.modules:
    configure_warnings("production")
