from datetime import timedelta
from pathlib import Path

import openai
from django.utils import timezone


def get_today_date_range():
    """
    Returns the start and end datetime for the current local day.

    Returns:
        tuple: (today_start, today_end) datetime objects in local timezone
    """
    now = timezone.localtime(timezone.now())
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    return today_start, today_end


def get_openai_client(key):
    if not key:
        msg = (
            "No active OpenAI API key found."
            " Please add an API key in the admin interface."
        )
        raise ValueError(msg)
    return openai.OpenAI(api_key=key.key)


def read_prompt_template(template_name):
    template_path = f"ai_text_game/llm_caller/templates/prompts/{template_name}.txt"
    try:
        with Path(template_path).open("r") as f:
            return f.read()
    except FileNotFoundError as e:
        msg = f"Prompt template file not found: {template_path}"
        raise FileNotFoundError(msg) from e
