import asyncio
import json
import logging
import re

from anthropic import AnthropicError
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from groq import GroqError
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAIError

from .fake_llms import get_fake_llm_model
from .models import APIKey
from .models import GameStory
from .models import LLMConfig
from .models import StoryOption
from .models import StoryProgress
from .models import StorySkeleton
from .models import TextExplanation
from .story_graph import StoryGraph
from .utils import get_llm_model

logger = logging.getLogger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.story_graph = None
        self.story_thread = {"configurable": {"thread_id": "1"}}

    async def connect(self):
        logger.debug("WebSocket connect attempt with scope: %s", self.scope)
        try:
            # Get story_id from URL route
            self.story_id = self.scope["url_route"]["kwargs"]["story_id"]
            self.room_group_name = f"game_{self.story_id}"
            self.story_thread = {"configurable": {"thread_id": self.story_id}}

            # Get story
            story = await self.get_story(self.story_id)

            # Initialize story graph
            await self.initialize_story_graph(story)

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )
            await self.accept()
            logger.debug("WebSocket connection accepted")
        except (KeyError, TypeError, ValueError):
            logger.exception("WebSocket connection error")
            raise

    async def disconnect(self, close_code):
        logger.debug("WebSocket disconnected with code: %s", close_code)
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        try:
            if message_type == "start_story":
                await self.handle_start_story()
            elif message_type == "interact":
                await self.handle_interaction(data)
            elif message_type == "explain_text":
                await self.handle_text_explanation(data)
        except (AnthropicError, OpenAIError, GroqError) as e:
            await self.send_error(str(e))
            raise

    async def handle_start_story(self):
        try:
            story = await self.get_story(self.story_id)

            if story.status != "INIT":
                await self.send_error("Story already started.")
                return

            initial_state = {
                "theme": story.genre,
                "cefr_level": story.cefr_level,
                "scene_text": story.scene_text,
                "details": story.details,
            }

            # If skeleton exists, use it
            story_skeleton = await self.try_get_skeleton(story)
            if not story_skeleton:
                # Generate skeleton if it doesn't exist
                skeleton_data = await database_sync_to_async(
                    self.story_graph.generate_skeleton,
                )(initial_state)

                await database_sync_to_async(StorySkeleton.objects.create)(
                    story=story,
                    background=skeleton_data["story_skeleton"]["story_background"],
                    raw_data=skeleton_data["story_skeleton"],
                )

            await self.process_story_state(story)

        except ValueError as e:
            await self.send_error(str(e))
            raise

    async def handle_interaction(self, data):
        try:
            story = await self.get_story(self.story_id)
            option_id = data.get("option_id")

            if not option_id:
                await self.send_error("option_id is required")
                return

            option_text = await database_sync_to_async(story.get_option_text)(option_id)
            if not option_text:
                await self.send_error("Invalid option_id")
                return

            # Update the story progress with chosen option
            await self.update_story_progress(story, option_id, option_text)

            await self.process_story_state(story)

        except ValueError as e:
            await self.send_error(str(e))
            raise

    async def handle_text_explanation(self, data):
        try:
            story = await self.get_story(self.story_id)
            selected_text = data.get("selected_text")
            context_text = data.get("context_text")
            client_explanation_id = data.get("explanation_id")

            if not all([selected_text, context_text]):
                await self.send_error("selected_text and context_text are required")
                return

            # Create explanation
            explanation = await self.create_text_explanation(
                story,
                selected_text,
                context_text,
            )

            # Send creation confirmation
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "explanation_created",
                        "client_id": client_explanation_id,
                        "explanation": await self.serialize_explanation(explanation),
                    },
                ),
            )

            # Process the explanation
            await self.process_explanation(story, explanation)

        except (ValueError, TextExplanation.DoesNotExist) as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def try_get_skeleton(self, story):
        # Using hasattr checks if the related object exists
        if hasattr(story, "skeleton") and story.skeleton is not None:
            return story.skeleton
        return None

    @database_sync_to_async
    def get_story(self, story_id):
        return GameStory.objects.get(id=story_id)

    @database_sync_to_async
    def get_config_model_name(self, config):
        return {
            "model_name": config.model.name,
            "temperature": config.temperature,
            "system_prompt": config.system_prompt,
        }

    async def get_fake_stream(self):
        fake_response = "This is a test response. " * 10
        words = re.split(r"(?<= )", fake_response)
        for word in words:
            await asyncio.sleep(0.05)
            yield word

    @staticmethod
    async def get_openai_stream(client, model_name, context):
        return await client.chat.completions.create(
            model=model_name,
            messages=context,
            stream=True,
        )

    async def send_error(self, error_message):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "error": error_message,
                },
            ),
        )

    @database_sync_to_async
    def create_text_explanation(self, story, selected_text, context_text):
        active_config = LLMConfig.get_active_config(purpose="text_explanation")

        return TextExplanation.objects.create(
            story=story,
            selected_text=selected_text,
            context_text=context_text,
            status="pending",
            model=active_config.model,
        )

    @database_sync_to_async
    def serialize_explanation(self, explanation):
        from .serializers import TextExplanationSerializer

        return TextExplanationSerializer(explanation).data

    async def process_explanation(self, story, explanation):
        try:
            if settings.FAKE_LLM_REQUEST:
                stream = self.get_fake_explanation_stream()
            else:
                active_config = await database_sync_to_async(
                    LLMConfig.get_active_config,
                )(purpose="text_explanation")

                config_data = await self.get_config_model_name(active_config)
                model_name = config_data["model_name"]
                temperature = config_data["temperature"]
                system_prompt = config_data["system_prompt"]

                key = await database_sync_to_async(
                    APIKey.get_available_key,
                )(model_name)
                prompt = ChatPromptTemplate.from_template(system_prompt)
                string_parser = StrOutputParser()
                llm = get_llm_model(
                    {
                        "model_name": model_name,
                        "llm_type": active_config.model.llm_type,
                        "url": active_config.model.url,
                        "temperature": temperature,
                        "key": key,
                    },
                )
                chain = prompt | llm | string_parser
                stream = chain.astream(
                    {
                        "selected_text": explanation.selected_text,
                        "context_text": explanation.context_text,
                    },
                )

            # Update status to streaming when starting to process
            explanation.status = "streaming"
            await database_sync_to_async(explanation.save)()

            # Send status update
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "explanation_status",
                        "explanation_id": explanation.id,
                        "status": "streaming",
                    },
                ),
            )

            explanation_text = ""
            async for chunk in stream:
                if chunk:
                    explanation_text += chunk
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "explanation_stream",
                                "explanation_id": explanation.id,
                                "content": chunk,
                            },
                        ),
                    )

            # Update explanation with final content
            explanation.explanation = explanation_text
            explanation.status = "completed"
            await database_sync_to_async(explanation.save)()

            # Send completion message
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "explanation_completed",
                        "explanation": await self.serialize_explanation(explanation),
                    },
                ),
            )

        except (ValueError, TextExplanation.DoesNotExist) as e:
            explanation.status = "failed"
            explanation.error = str(e)
            await database_sync_to_async(explanation.save)()
            await self.send_error(str(e))

    async def get_fake_explanation_stream(self):
        fake_response = "This is a fake explanation of the selected text. " * 3
        words = re.split(r"(?<= )", fake_response)
        for word in words:
            await asyncio.sleep(0.05)
            yield word

    async def initialize_story_graph(self, story):
        """Initialize the story graph with the current story state"""

        # Create LLM models dictionary
        llm_models = await self.create_story_graph_llms()

        # Create story graph
        self.story_graph = StoryGraph(llm_models)

    @database_sync_to_async
    def create_story_graph_llms(self):
        """Create LLM models for story graph nodes.

        Returns:
            Dictionary mapping node types to configured LLM models
        """
        llms = {}

        # Get configs for each purpose
        node_name_to_purpose = {
            "skeleton": "story_skeleton_generation",
            "continuation": "story_continuation",
            "ending": "story_ending",
            "cefr": "cefr_check",
        }

        for node_name, purpose in node_name_to_purpose.items():
            config = LLMConfig.get_active_config(purpose=purpose)
            prompt = ChatPromptTemplate.from_template(config.system_prompt)
            model_name = config.model.name
            key = APIKey.get_available_key(model_name)
            if settings.FAKE_LLM_REQUEST:
                llms[node_name] = prompt | get_fake_llm_model(node_name)
            else:
                llms[node_name] = prompt | get_llm_model(
                    {
                        "model_name": model_name,
                        "llm_type": config.model.llm_type,
                        "url": config.model.url,
                        "temperature": config.temperature,
                        "key": key,
                    },
                )

        return llms

    def get_options(self, state):
        options = []
        current_decision_point_id = state.get("current_decision_point")
        if current_decision_point_id:
            skeleton = state["story_skeleton"]
            options = []

            # Find the current decision point and its options
            for chapter in skeleton["chapters"]:
                for milestone in chapter["milestones"]:
                    for decision_point in milestone["decision_points"]:
                        if (
                            decision_point["decision_point_id"]
                            == current_decision_point_id
                        ):
                            options = decision_point["options"]
                            break
        return options

    async def save_story_progress(self, story, state):
        """Save story progress to database"""
        if story_text := state.get("story_text"):
            # Create the progress entry
            progress = await database_sync_to_async(StoryProgress.objects.create)(
                story=story,
                content=story_text,
                decision_point_id=state.get("current_decision_point"),
            )

            options = self.get_options(state)

            if options:
                # Create option objects
                for option in options:
                    await database_sync_to_async(StoryOption.objects.create)(
                        progress=progress,
                        option_id=option["option_id"],
                        option_name=option["option_name"],
                    )

            story.status = state["status"]
            await database_sync_to_async(story.save)()

    async def send_story_update(self, state):
        """Send story update to client"""
        # TODO: remove the consequence from the options (or use a unified interface)
        options = self.get_options(state)

        await self.send(
            text_data=json.dumps(
                {
                    "type": "story_update",
                    "content": state.get("story_text"),
                    "status": state.get("status"),
                    "current_decision": state.get("current_decision_point"),
                    "options": options,
                },
            ),
        )

    @database_sync_to_async
    def update_story_progress(self, story, option_id, option_text):
        """Update the story progress with the chosen option"""
        from .models import StoryProgress

        # Get the latest progress
        latest_progress = (
            StoryProgress.objects.filter(
                story=story,
            )
            .order_by("-created_at")
            .first()
        )

        if latest_progress:
            # Update with chosen option
            latest_progress.set_chosen_option(option_id, option_text)

    async def process_story_state(self, story):
        """Process the current story state and send updates."""
        # Get current story state
        state = await database_sync_to_async(lambda: story.story_state)()

        # Add chosen decisions if they exist
        if hasattr(story, "progress_entries"):
            chosen_decisions = await database_sync_to_async(
                lambda: [
                    entry.chosen_option_id
                    for entry in story.progress_entries.all()
                    if entry.chosen_option_id
                ],
            )()
            if chosen_decisions:
                state["chosen_decisions"] = chosen_decisions

        # Run the graph
        new_state = await database_sync_to_async(self.story_graph.invoke)(
            state,
            self.story_thread,
        )

        # Save progress
        await self.save_story_progress(story, new_state)

        # Send response to client
        await self.send_story_update(new_state)
