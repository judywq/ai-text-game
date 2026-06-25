import base64
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
from openai import OpenAI
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
            # temperature=temperature,
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
    """Generate image prompt based on story content.

    Args:
        story_text: The story segment text
        has_reference_images: Whether reference images are provided

    Returns:
        Formatted prompt for image generation
    """
    if has_reference_images:
        return (
            "Create a NEW illustration for this story scene. Use the reference "
            "images provided to maintain CONSISTENT character appearances (same "
            "faces, colors, body types) and the same art style. However, create a "
            "DIFFERENT scene showing the NEW story events described below. Do not "
            "just copy the reference images. The characters should be doing DIFFERENT "
            "actions in a DIFFERENT setting based on the new story text. Style: "
            "Children's storybook illustration, colorful, engaging for ages 8-9. "
            "Do NOT include any text, options, or choices in the image."
            f"\n\nNEW STORY SCENE TO ILLUSTRATE:\n{story_text}"
        )
    return (
        "Create a children's storybook illustration for this story scene. Style: "
        "Colorful, engaging, appropriate for ages 8-9, warm and inviting. Show the "
        "characters and setting clearly. Do NOT include any text, options, or choices "
        "in the image."
        f"\n\nSTORY SCENE TO ILLUSTRATE:\n{story_text}"
    )


def _load_reference_images(
    reference_image_urls: list[str] | None,
) -> list[Image.Image]:
    """Load reference images from local media paths or remote URLs."""
    if not reference_image_urls:
        return []

    images: list[Image.Image] = []
    for ref_url in reference_image_urls:
        try:
            if "/media/" in ref_url:
                media_path = ref_url.split("/media/")[-1]
                full_path = Path(settings.MEDIA_ROOT) / media_path
                images.append(Image.open(full_path))
            else:
                response = requests.get(ref_url, timeout=10)
                if response.status_code == HTTP_OK:
                    images.append(Image.open(BytesIO(response.content)))
        except (OSError, requests.RequestException) as e:
            logger.warning(
                "Failed to load reference image %s, skipping: %s",
                ref_url,
                e,
            )
    return images


def _save_image_to_storage(
    image: Image.Image,
    *,
    story_id: int,
    image_type: str,
    progress_id: int | None = None,
    character_id: str | None = None,
) -> str:
    """Save a PIL image to media storage and return its full URL."""
    if image_type == "stock":
        filename = f"story_{story_id}_stock.png"
    elif image_type == "character":
        filename = f"story_{story_id}_char_{character_id}.png"
    else:
        filename = f"story_{story_id}_progress_{progress_id}.png"

    img_buffer = BytesIO()
    image.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    path = default_storage.save(
        f"images/{filename}",
        ContentFile(img_buffer.read()),
    )

    domain = settings.DOMAIN_NAME
    if not domain.startswith("http"):
        domain = f"http://{domain}"
    full_url = f"{domain}/media/{path}"
    logger.info("Generated image: %s (full URL: %s)", path, full_url)
    return full_url


def _pil_image_to_upload_file(
    image: Image.Image,
    name: str,
) -> tuple[str, BytesIO, str]:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return (name, buffer, "image/png")


def _openai_image_response_to_bytes(response) -> bytes | None:
    """Extract image bytes from an OpenAI ImagesResponse."""
    if not response.data:
        return None

    image_data = response.data[0]
    if image_data.b64_json:
        return base64.b64decode(image_data.b64_json)

    if image_data.url:
        download_response = requests.get(image_data.url, timeout=30)
        if download_response.status_code == HTTP_OK:
            return download_response.content

    return None


def generate_image(  # noqa: PLR0913
    *,
    llm_type: str,
    prompt: str,
    story_id: int,
    api_key: str | None = None,
    model_name: str | None = None,
    image_type: str = "progress",
    progress_id: int | None = None,
    character_id: str | None = None,
    reference_image_urls: list[str] | None = None,
) -> str:
    """Generate an image using the configured provider and save to media storage."""
    if llm_type == "gemini":
        return generate_image_with_gemini(
            prompt=prompt,
            story_id=story_id,
            image_type=image_type,
            progress_id=progress_id,
            character_id=character_id,
            reference_image_urls=reference_image_urls,
            api_key=api_key,
            model_name=model_name,
        )
    if llm_type == "openai":
        return generate_image_with_openai(
            prompt=prompt,
            story_id=story_id,
            image_type=image_type,
            progress_id=progress_id,
            character_id=character_id,
            reference_image_urls=reference_image_urls,
            api_key=api_key,
            model_name=model_name,
        )

    logger.warning("Unsupported image model type: %s", llm_type)
    return ""


def generate_character_image(
    character: dict,
    story_id: int,
    *,
    llm_type: str,
    api_key: str | None = None,
    model_name: str | None = None,
) -> str:
    """Generate base image for a character.

    Args:
        character: Character dict with id, name, gender, description, role
        story_id: The story ID
        llm_type: Provider type (e.g. openai, gemini)
        api_key: API key for the image provider
        model_name: Image model name

    Returns:
        URL to the saved character image
    """
    prompt = (
        f"Create a character portrait for a children's storybook. "
        f"Name: {character.get('character_name')}. "
        f"Gender: {character.get('character_gender')}. "
        f"Role: {character.get('role')}. "
        f"Description: {character.get('character_description')}. "
        f"Style: Colorful, engaging, appropriate for ages 8-9. "
        f"Show the character clearly with consistent features. "
        f"Plain or simple background. Do NOT include any text."
    )
    return generate_image(
        llm_type=llm_type,
        prompt=prompt,
        story_id=story_id,
        image_type="character",
        character_id=character.get("character_id"),
        api_key=api_key,
        model_name=model_name,
    )


def generate_image_with_openai(  # noqa: PLR0913
    prompt: str,
    story_id: int,
    image_type: str = "progress",
    progress_id: int | None = None,
    character_id: str | None = None,
    reference_image_urls: list[str] | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
) -> str:
    """Generate image using OpenAI and save to media folder."""
    try:
        if not api_key:
            api_key = settings.OPENAI_API_KEY
        if not model_name:
            model_name = "gpt-image-2"

        client = OpenAI(api_key=api_key)
        reference_images = _load_reference_images(reference_image_urls)

        if reference_images:
            upload_files = [
                _pil_image_to_upload_file(image, f"reference_{index}.png")
                for index, image in enumerate(reference_images)
            ]
            response = client.images.edit(
                model=model_name,
                image=upload_files if len(upload_files) > 1 else upload_files[0],
                prompt=prompt,
            )
        else:
            response = client.images.generate(
                model=model_name,
                prompt=prompt,
                size="1024x1024",
                quality="medium",
            )

        image_bytes = _openai_image_response_to_bytes(response)
        if not image_bytes:
            logger.warning("No image data in OpenAI response")
            return ""

        image = Image.open(BytesIO(image_bytes))
        return _save_image_to_storage(
            image,
            story_id=story_id,
            image_type=image_type,
            progress_id=progress_id,
            character_id=character_id,
        )

    except Exception:
        logger.exception("Error generating image with OpenAI")
        return ""


def generate_image_with_gemini(  # noqa: PLR0913
    prompt: str,
    story_id: int,
    image_type: str = "progress",
    progress_id: int | None = None,
    character_id: str | None = None,
    reference_image_urls: list[str] | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
) -> str:
    """Generate image using Gemini and save to media folder.

    Args:
        prompt: The image generation prompt
        story_id: The story ID
        image_type: Type of image ('stock', 'character', or 'progress')
        progress_id: Progress entry ID (required for progress images)
        reference_image_urls: Optional list of reference image URLs for consistency
        api_key: Gemini API key (optional, uses settings if not provided)
        model_name: Gemini model name (optional, uses default if not provided)

    Returns:
        Full URL to the saved image
    """
    try:
        if not api_key:
            api_key = settings.GEMINI_API_KEY
        if not model_name:
            model_name = "gemini-2.5-flash-image"

        client = genai.Client(api_key=api_key)

        contents: list[Image.Image | str] = list(
            _load_reference_images(reference_image_urls),
        )
        contents.append(prompt)

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image = Image.open(BytesIO(part.inline_data.data))
                return _save_image_to_storage(
                    image,
                    story_id=story_id,
                    image_type=image_type,
                    progress_id=progress_id,
                    character_id=character_id,
                )

    except Exception:
        logger.exception("Error generating image with Gemini")
        return ""

    else:
        logger.warning("No image data in Gemini response")
        return ""
