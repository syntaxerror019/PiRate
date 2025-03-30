import logging
import sys

# ANSI escape codes
LOG_COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "RESET": "\033[0m"      # Reset to default
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_color = LOG_COLORS.get(record.levelname, LOG_COLORS["RESET"])
        record.msg = f"{log_color}{record.msg}{LOG_COLORS['RESET']}"
        return super().format(record)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file (no colors)
        logging.StreamHandler(sys.stdout)  # log to console
    ]
)

# colored formatting to console logs only
console_handler = logging.getLogger().handlers[1]  # Second handler (StreamHandler)
console_handler.setFormatter(ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s"))

if __name__ == "__main__":
    # Test the logger
    logging.debug("This is a debug message")
    logging.info("This is an info message")
    logging.warning("This is a warning")
    logging.error("This is an error")
    logging.critical("This is a critical error")