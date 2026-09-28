import html
import re
import json
import logging
from typing import Any, Optional
from passlib.context import CryptContext

logger = logging.getLogger("edugenie.security")

# Password Hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password securely using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def sanitize_input_text(text: str, max_chars: int = 20000) -> str:
    """
    Sanitize untrusted user input string:
    - Trims whitespace
    - Limits character count
    - Strips dangerous control / null bytes
    """
    if not text:
        return ""
    # Strip null bytes and control chars except newlines & tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
    cleaned = cleaned.strip()
    return cleaned[:max_chars]


def escape_html(text: str) -> str:
    """Escape HTML characters to prevent Cross-Site Scripting (XSS)."""
    if not text:
        return ""
    return html.escape(text, quote=True)


def clean_and_extract_json(raw_text: str) -> Any:
    """
    Robust JSON parser for LLM responses.
    Handles:
    - ```json ... ``` blocks
    - Leading/trailing commentary text
    - Nested brackets / braces
    """
    if not raw_text:
        raise ValueError("Empty response received from AI model")

    text = raw_text.strip()

    # 1. Check for standard Markdown code block ```json ... ```
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if json_match:
        text = json_match.group(1).strip()

    # 2. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Find outermost matching {...} or [...]
    first_bracket = text.find('[')
    first_brace = text.find('{')

    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        last_bracket = text.rfind(']')
        if last_bracket != -1 and last_bracket > first_bracket:
            substring = text[first_bracket:last_bracket + 1]
            try:
                return json.loads(substring)
            except json.JSONDecodeError:
                pass
    elif first_brace != -1:
        last_brace = text.rfind('}')
        if last_brace != -1 and last_brace > first_brace:
            substring = text[first_brace:last_brace + 1]
            try:
                return json.loads(substring)
            except json.JSONDecodeError:
                pass

    # 4. Final attempt: clean trailing commas before closing braces
    cleaned_trailing = re.sub(r',\s*([\]}])', r'\1', text)
    try:
        return json.loads(cleaned_trailing)
    except json.JSONDecodeError as err:
        logger.error("Failed to parse JSON from AI response. Raw output: %s", raw_text)
        raise ValueError(f"AI response did not contain valid structured data: {err}")
