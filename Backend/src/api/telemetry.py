import os
import logging

from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger("brand-video-telemetry")

def setup_telemetry():
    """
    Sets up telemetry for the application using Azure MOonitor and OpenTelemetry. 
    it gives many more results than langsmith , like no of requests , performative metrics ,etc.
    """

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not connection_string:
        logger.error("APPLICATIONINSIGHTS_CONNECTION_STRING is not set. Check again")

    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name = "brand-video-telemetry",
        )
        logger.info("Azure Monitor telemetry configured successfully.")
    except Exception as e:
        logger.error(f"failed to configure azure monitor telemetry due to : {e}")
    
