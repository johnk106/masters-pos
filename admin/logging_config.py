"""
Logging configuration for admin project
Reduces ngrok warnings and enhances error tracking
"""

import logging

def configure_logging():
    """Configure logging to reduce ngrok warnings and add better error tracking"""
    
    # Suppress ngrok update warnings
    logging.getLogger('pyngrok.process.ngrok').setLevel(logging.ERROR)
    logging.getLogger('pyngrok').setLevel(logging.WARNING)
    
    # Configure main loggers
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Specific logger for order creation debugging
    order_logger = logging.getLogger('sales.order_creation')
    order_logger.setLevel(logging.DEBUG)
    
    # Specific logger for ngrok operations
    ngrok_logger = logging.getLogger('sales.ngrok')
    ngrok_logger.setLevel(logging.INFO)

# Call this function to apply the configuration
configure_logging()