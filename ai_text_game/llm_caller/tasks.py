import json
import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from langchain_core.output_parsers.json import JsonOutputParser

from .models import APIKey
from .models import GameStory
from .models import LLMConfig
from .models import StorySkeleton
from .utils import get_llm_model

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_story_skeleton(self, story_id: int, initial_state: dict) -> None:  # noqa: PLR0915
    """Generate story skeleton in background."""
    skeleton = None
    try:
        # Get story
        story = GameStory.objects.filter(id=story_id).first()

        if story is None:
            logger.warning("Story %s not found, skipping generation", story_id)
            return

        skeleton = getattr(story, "skeleton", None)
        if skeleton is not None:
            if skeleton.status in ["COMPLETED", "GENERATING"]:
                logger.warning(
                    "Story %s already has a skeleton, skipping generation",
                    story_id,
                )
                return
            skeleton.status = "GENERATING"
            skeleton.save()
        else:
            skeleton = StorySkeleton.objects.create(
                story=story,
                status="GENERATING",
            )

        # Get LLM config and model
        config = LLMConfig.get_active_config(purpose="story_skeleton_generation")
        key = APIKey.get_available_key(model_name=config.model.name)

        # Create chain
        llm = get_llm_model(
            {
                "model_name": config.model.name,
                "llm_type": config.model.llm_type,
                "url": config.model.url,
                "temperature": config.temperature,
                "key": key,
            },
            fake=settings.FAKE_LLM_REQUEST,
            name="skeleton",
        )
        json_parser = JsonOutputParser()
        chain = config.get_prompt_template() | llm | json_parser

        channel_layer = get_channel_layer()

        # Add at the beginning of the task
        logger.info("Starting skeleton generation for story %s", story_id)
        prev_milestones = 0

        # Generate skeleton
        skeleton_data = None
        stream = chain.stream(initial_state)
        for chunk in stream:
            skeleton_data = chunk
            # Save skeleton on receiving every milestone
            n_milestones = StorySkeleton.count_milestones(skeleton_data)
            if n_milestones > prev_milestones:
                skeleton.background = skeleton_data["story_background"]
                skeleton.raw_data = skeleton_data
                skeleton.save()

                async_to_sync(channel_layer.group_send)(
                    f"game_{story_id}",
                    {
                        "type": "skeleton_generation_progress",
                        "n_milestones": n_milestones,
                        "story_id": story_id,
                    },
                )
                prev_milestones = n_milestones

        # Save the final skeleton to database
        if skeleton_data:
            logger.info("Completed skeleton generation for story %s", story_id)
            skeleton.background = skeleton_data["story_background"]
            skeleton.raw_data = skeleton_data
            skeleton.status = "COMPLETED"
            skeleton.save()

            # Send completion notification
            async_to_sync(channel_layer.group_send)(
                f"game_{story_id}",
                {
                    "type": "skeleton_generation_completed",
                    "skeleton": json.dumps(skeleton_data),
                },
            )
        else:
            logger.warning(
                "No skeleton data received, skipping completion notification",
            )
            skeleton.status = "FAILED"
            skeleton.save()

    except Exception as e:
        logger.exception("Error generating story skeleton")
        # Update story status to indicate failure
        try:
            if skeleton is not None:
                skeleton.status = "FAILED"
                skeleton.save()
        except Exception:
            logger.exception(
                "Failed to update skeleton status after skeleton generation failure",
            )

        # Notify consumer about error
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"game_{story_id}",
            {
                "type": "skeleton_generation_failed",
                "error": str(e),
            },
        )
        raise
