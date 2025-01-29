import logging
import time
from dataclasses import dataclass

import openai
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from pydantic import BaseModel

from .models import APIRequest
from .models import GameInteraction
from .models import OpenAIKey

logger = logging.getLogger(__name__)


def get_openai_client():
    key = OpenAIKey.get_available_key()
    if not key:
        msg = (
            "No active OpenAI API key found."
            " Please add an API key in the admin interface."
        )
        raise ValueError(msg)
    return openai.OpenAI(api_key=key.key)


class EssayScore(BaseModel):
    score: float


@dataclass
class LLMRequestParams:
    request_id: int
    model_name: str
    temperature: float
    system_prompt: str
    user_prompt_template: str


@shared_task(bind=True)
def process_openai_request(
    self,
    request_params_dict: dict,
    delay_seconds=0,
):
    # Convert dict back to dataclass
    request_params = LLMRequestParams(**request_params_dict)

    if delay_seconds > 0:
        msg = f"Delaying LLM request by {delay_seconds} seconds"
        logger.info(msg)
        time.sleep(delay_seconds)

    try:
        try:
            api_request = APIRequest.objects.get(id=request_params.request_id)
        except APIRequest.DoesNotExist as e:
            try:
                self.retry(countdown=2**self.request.retries)
            except MaxRetriesExceededError:
                msg = f"APIRequest with id {request_params.request_id} not found"
                logger.exception(msg)
                raise ValueError(msg) from e

        api_request.task_id = self.request.id

        if settings.FAKE_LLM_REQUEST:
            api_request.result = '{"score": 4.0}'
            api_request.score = 4.0
            api_request.status = "COMPLETED"
            api_request.save()
            return True

        # Format prompt using the provided template
        user_prompt = request_params.user_prompt_template.format(
            essay=api_request.essay,
        )

        client = get_openai_client()
        response = client.chat.completions.create(
            model=request_params.model_name,
            messages=[
                {"role": "system", "content": request_params.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=request_params.temperature,
            response_format={"type": "json_object"},
        )

        # Extract and parse response manually
        result = response.choices[0].message.content
        api_request.result = result
        # Assuming the older models return JSON-like content that can be parsed
        try:
            parsed_result = EssayScore.model_validate_json(result)
            api_request.score = parsed_result.score
        except ValueError as e:
            msg = "Failed to parse response from model"
            raise ValueError(msg) from e

        api_request.status = "COMPLETED"
        api_request.save()
    except (openai.OpenAIError, KeyError, ValueError) as e:
        api_request.status = "FAILED"
        api_request.error = str(e)
        api_request.save()
        return False
    else:
        return True


@dataclass
class GameInteractionParams:
    interaction_id: int
    model_name: str
    system_prompt: str
    context: list[dict]
    temperature: float = 0.7


@shared_task(bind=True)
def process_game_interaction(
    self,
    interaction_params_dict: dict,
    delay_seconds=0,
):
    if delay_seconds > 0:
        msg = f"Delaying game interaction by {delay_seconds} seconds"
        logger.info(msg)
        time.sleep(delay_seconds)

    interaction_id = interaction_params_dict["interaction_id"]

    try:
        try:
            interaction = GameInteraction.objects.select_related("story").get(
                id=interaction_id,
            )
        except GameInteraction.DoesNotExist as e:
            try:
                self.retry(countdown=2**self.request.retries)
            except MaxRetriesExceededError:
                msg = f"GameInteraction with id {interaction_id} not found"
                logger.exception(msg)
                raise ValueError(msg) from e

        params = GameInteractionParams(**interaction_params_dict)

        if settings.FAKE_LLM_REQUEST:
            interaction.system_response = "This is a test response."
            interaction.status = "completed"
            interaction.save()
            return True

        client = get_openai_client()
        response = client.chat.completions.create(
            model=params.model_name,
            messages=params.context,
            temperature=params.temperature,
        )

        system_response = response.choices[0].message.content
        interaction.system_response = system_response
        interaction.status = "completed"
        interaction.save()

    except (openai.OpenAIError, ValueError) as e:
        interaction.status = "failed"
        interaction.error = str(e)
        interaction.save()
        return False
    else:
        return True
