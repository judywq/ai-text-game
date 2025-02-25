import re
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_deepseek import ChatDeepSeek
from langchain_groq import ChatGroq
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

    is_fixed_temperature = model_name in settings.FIXED_TEMPERATURE_LLM_MODELS
    # OpenAI reasoning models only support temperature of 1
    temperature = 1 if is_fixed_temperature else config.get("temperature", 0.7)

    llm = None
    if llm_type == "openai":
        llm = ChatOpenAI(
            model=model_name,
            api_key=key.key,
            temperature=temperature,
        )
    elif llm_type == "anthropic":
        llm = ChatAnthropic(
            model=model_name,
            api_key=key.key,
            max_tokens=8000,
            temperature=temperature,
        )
    elif llm_type == "groq":
        llm = ChatGroq(
            model=model_name,
            api_key=key.key,
            temperature=temperature,
        )
    elif llm_type == "deepseek":
        llm = ChatDeepSeek(
            model=model_name,
            api_key=key.key,
            temperature=temperature,
        )
    elif llm_type == "custom":
        llm = ChatOpenAI(
            model=model_name,
            api_key=key.key,
            base_url=url,
            temperature=temperature,
        )

    if llm is None:
        msg = f"Invalid LLM type: {llm_type}"
        raise ValueError(msg)

    if model_name in settings.REASONING_LLM_MODELS:
        # Remove the think tags from reasoning models
        return llm | think_tag_parser
    return llm


def think_tag_parser(ai_message: AIMessage | str) -> str:
    """Remove the <think> and </think> tags from the AI message."""
    think_tag_pattern = r"<think>(.*<\/think>\s*)?"
    if isinstance(ai_message, AIMessage):
        ai_message.content = re.sub(
            think_tag_pattern,
            "",
            ai_message.content,
            flags=re.DOTALL,
        )
        return ai_message
    return re.sub(think_tag_pattern, "", ai_message, flags=re.DOTALL)
