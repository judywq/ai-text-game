import logging
import time
from dataclasses import dataclass

import openai
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings

from .models import OpenAIKey
from .models import TextExplanation
from .utils import get_openai_client

logger = logging.getLogger(__name__)


@dataclass
class TextExplanationParams:
    explanation_id: int
    model_name: str
    system_prompt: str
    context_text: str
    selected_text: str
    temperature: float = 0.7


@shared_task(bind=True)
def process_text_explanation(
    self,
    explanation_params_dict: dict,
    delay_seconds=0,
):
    if delay_seconds > 0:
        msg = f"Delaying text explanation by {delay_seconds} seconds"
        logger.info(msg)
        time.sleep(delay_seconds)

    try:
        params = TextExplanationParams(**explanation_params_dict)
        try:
            explanation = TextExplanation.objects.get(id=params.explanation_id)
        except TextExplanation.DoesNotExist as e:
            try:
                self.retry(countdown=2**self.request.retries)
            except MaxRetriesExceededError:
                msg = f"TextExplanation with id {params.explanation_id} not found"
                logger.exception(msg)
                raise ValueError(msg) from e

        if settings.FAKE_LLM_REQUEST:
            explanation.explanation = (
                "This is a fake explanation based on the provided context."
            )
            explanation.status = "completed"
            explanation.save()
            return True

        prompt = params.system_prompt.format(
            context_text=params.context_text,
            selected_text=params.selected_text,
        )

        key = OpenAIKey.get_available_key()
        client = get_openai_client(key)
        response = client.chat.completions.create(
            model=params.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=params.temperature,
        )

        explanation_text = response.choices[0].message.content.strip()
        explanation.explanation = explanation_text
        explanation.status = "completed"
        explanation.save()

    except (openai.OpenAIError, ValueError) as e:
        explanation.status = "failed"
        explanation.error = str(e)
        explanation.save()
        return False
    else:
        return True
