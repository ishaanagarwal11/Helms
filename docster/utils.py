# utils.py

import re

def chunk_logs(log_data: str, chunk_size: int) -> list:
    """
    Splits a large log string into a list of chunks.
    Each chunk is a list of log lines with a maximum length of 'chunk_size'.

    Args:
        log_data (str): The raw log data as a single string.
        chunk_size (int): Number of lines per chunk.

    Returns:
        list: A list of chunks, where each chunk is a list of strings (log lines).
    """
    # Split the raw log data into individual lines
    lines = log_data.splitlines()
    
    # Create chunks of the specified size
    chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
    return chunks


def mask_sensitive_data(text: str) -> str:
    """
    Masks sensitive data (e.g., passwords, tokens) in the provided text.
    This is a simple implementation that replaces common patterns with '***'.

    Args:
        text (str): The text to be processed.

    Returns:
        str: The text with sensitive data masked.
    """
    # Mask patterns such as "password: somevalue" or "token: somevalue"
    text = re.sub(r'(?i)(password\s*:\s*)(\S+)', r'\1***', text)
    text = re.sub(r'(?i)(token\s*:\s*)(\S+)', r'\1***', text)
    return text


def summarize_output(text: str, max_lines: int = 10) -> str:
    """
    Provides a summary of the provided text by returning the first 'max_lines' lines.
    This is useful for creating a brief overview of large outputs.

    Args:
        text (str): The text to summarize.
        max_lines (int, optional): Maximum number of lines for the summary. Defaults to 10.

    Returns:
        str: A summary string containing only the first 'max_lines' lines.
    """
    lines = text.splitlines()
    summary = "\n".join(lines[:max_lines])
    return summary
