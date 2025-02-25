from datetime import timedelta
from pathlib import Path

from django.utils import timezone
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI


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


def read_prompt_template(template_filename):
    template_path = f"ai_text_game/llm_caller/templates/prompts/{template_filename}"
    try:
        with Path(template_path).open("r") as f:
            return f.read()
    except FileNotFoundError as e:
        msg = f"Prompt template file not found: {template_path}"
        raise FileNotFoundError(msg) from e


def get_llm_model(config):
    llm_type = config.get("llm_type")
    model_name = config.get("model_name")
    key = config.get("key")
    url = config.get("url")
    temperature = config.get("temperature", 0.7)
    if llm_type == "openai":
        return ChatOpenAI(model=model_name, api_key=key.key, temperature=temperature)
    if llm_type == "anthropic":
        return ChatAnthropic(
            model=model_name,
            api_key=key.key,
            max_tokens=8000,
            temperature=temperature,
        )
    if llm_type == "custom":
        return ChatOpenAI(
            model=model_name,
            api_key=key.key,
            base_url=url,
            temperature=temperature,
        )
    msg = f"Invalid LLM type: {llm_type}"
    raise ValueError(msg)
