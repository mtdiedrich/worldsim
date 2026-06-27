"""Wrapper around the Anthropic API."""

import os
from dotenv import load_dotenv
import anthropic
from worldsim.config import MODEL


# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client
_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def call_llm(system: str, user: str) -> str:
    """
    Call the Anthropic API with the given system and user prompts.
    
    Args:
        system: System prompt
        user: User prompt
        
    Returns:
        The text response from the model
    """
    msg = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=1.0,  # Agents should vary
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # Concatenate text blocks from the response
    return "".join(b.text for b in msg.content if b.type == "text")
