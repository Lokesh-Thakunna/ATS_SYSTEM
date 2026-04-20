import logging


class IgnoreBrokenPipeFilter(logging.Filter):
    """Silence noisy broken pipe lines from Django's development server."""

    def filter(self, record):
        message = record.getMessage()
        return "Broken pipe from" not in message
