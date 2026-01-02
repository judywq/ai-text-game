import logging
import re
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.utils import timezone
from google import genai
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from PIL import Image

from .fake_llms import get_fake_llm_model

logger = logging.getLogger(__name__)

# Constants
HTTP_OK = 200


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
    lang = settings.PROMPT_LANGUAGE_CODE

    template_path = (
        f"ai_text_game/llm_caller/templates/prompts/{lang}/{template_filename}"
    )
    try:
        with Path(template_path).open("r") as f:
            return f.read()
    except FileNotFoundError as e:
        msg = f"Prompt template file not found: {template_path}"
        raise FileNotFoundError(msg) from e


def get_llm_model(config, fake=False, name=None):  # noqa: FBT002
    if fake:
        return get_fake_llm_model(name)

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
    elif llm_type == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=key.key,
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


def format_datetime(datetime_obj: timezone.datetime) -> str:
    """
    Formats a datetime object to a string in the local timezone.
    """
    return timezone.localtime(datetime_obj).strftime("%Y-%m-%d %H:%M:%S %Z")


def illegal_char_remover(data):
    """Remove ILLEGAL CHARACTER."""
    if isinstance(data, str):
        return ILLEGAL_CHARACTERS_RE.sub("", data)
    return data


def generate_excel_response(rows, filename):
    """
    Generate an Excel response from a list of rows.
    """
    df_data = pd.DataFrame(rows)
    df_data = df_data.applymap(illegal_char_remover)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_data.to_excel(writer, index=False)

    now = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename}_{now}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def generate_story_image_prompt(
    story_text: str,
    *,
    has_reference_images: bool = False,
) -> str:
    """Generate image prompt for Gemini based on story content.

    Args:
        story_text: The story segment text
        has_reference_images: Whether reference images are provided

    Returns:
        Formatted prompt for image generation
    """
    if has_reference_images:
        return (
            "Create an image for this story segment, maintaining consistent "
            "character appearance and art style from the reference images provided. "
            "Do not include ANY of the options texts, or choices in the image: "
            f"{story_text}"
        )
    return (
        "Create an image capturing the key story elements and scene. "
        "Do not include ANY of the options texts, or choices in the image: "
        f"{story_text}"
    )


def generate_image_with_gemini(  # noqa: C901, PLR0913, PLR0912
    prompt: str,
    story_id: int,
    image_type: str = "progress",
    progress_id: int | None = None,
    reference_image_urls: list[str] | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
) -> str:
    """Generate image using Gemini and save to media folder.

    Args:
        prompt: The image generation prompt
        story_id: The story ID
        image_type: Type of image ('stock' or 'progress')
        progress_id: Progress entry ID (required for progress images)
        reference_image_urls: Optional list of reference image URLs for consistency
        api_key: Gemini API key (optional, uses settings if not provided)
        model_name: Gemini model name (optional, uses default if not provided)

    Returns:
        Relative path to the saved image
    """
    try:
        if not api_key:
            api_key = settings.GEMINI_API_KEY
        if not model_name:
            model_name = "gemini-2.5-flash-image-preview"

        client = genai.Client(api_key=api_key)

        # Prepare contents for Gemini
        contents = []

        # Add all reference images if provided
        if reference_image_urls:
            for ref_url in reference_image_urls:
                try:
                    # Extract path from URL and load from filesystem
                    if "/media/" in ref_url:
                        # Get the path after /media/
                        media_path = ref_url.split("/media/")[-1]
                        full_path = Path(settings.MEDIA_ROOT) / media_path
                        ref_image = Image.open(full_path)
                        contents.append(ref_image)
                    else:
                        # Fallback to HTTP request
                        response = requests.get(ref_url, timeout=10)
                        if response.status_code == HTTP_OK:
                            ref_image = Image.open(BytesIO(response.content))
                            contents.append(ref_image)
                except (OSError, requests.RequestException) as e:
                    logger.warning(
                        "Failed to load reference image %s, skipping: %s",
                        ref_url,
                        e,
                    )

        # Add prompt after images
        contents.append(prompt)

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
        )

        # Extract image data from response
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image = Image.open(BytesIO(part.inline_data.data))

                # Generate filename
                if image_type == "stock":
                    filename = f"story_{story_id}_stock.png"
                else:
                    filename = f"story_{story_id}_progress_{progress_id}.png"

                # Save to media folder
                img_buffer = BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                path = default_storage.save(
                    f"images/{filename}",
                    ContentFile(img_buffer.read()),
                )

                # Get the full URL for the image
                domain = settings.DOMAIN_NAME
                # Ensure domain has protocol
                if not domain.startswith("http"):
                    domain = f"http://{domain}"
                full_url = f"{domain}/media/{path}"
                logger.info("Generated image: %s (full URL: %s)", path, full_url)
                return full_url

    except Exception:
        logger.exception("Error generating image with Gemini")
        return ""

    else:
        logger.warning("No image data in Gemini response")
        return ""
