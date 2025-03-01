import json
import logging

from anthropic import AnthropicError
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from groq import GroqError
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAIError

from .models import APIKey
from .models import GameStory
from .models import LLMConfig
from .models import StoryOption
from .models import StoryProgress
from .models import TextExplanation
from .story_graph import StoryGraph
from .tasks import generate_story_skeleton
from .utils import get_llm_model

logger = logging.getLogger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    START_GAME_SINCE_MILESTONE = 2

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
            }
            if story.details:
                initial_state["details_prompt"] = (
                    f"Please keep these details of the story: {story.details}"
                )

            # If skeleton exists, use it
            story_skeleton = await self.try_get_skeleton(story)
            if not story_skeleton or story_skeleton.status == "FAILED":
                # Start background skeleton generation
                await database_sync_to_async(generate_story_skeleton.delay)(
                    story.id,
                    initial_state,
                )

                # Send status update to client
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "skeleton_generation_started",
                            "message": "Story skeleton generation has started...",
                        },
                    ),
                )
                return
            if story_skeleton.status == "GENERATING":
                await self.send_error(
                    "Story skeleton is still generating, please retry later.",
                )
                return
            # If skeleton exists, continue with story processing
            await self.update_story_progress(story)

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
                await self.send_error(f"Invalid option_id: {option_id}")
                return

            is_valid_option = await database_sync_to_async(
                story.is_option_id_in_current_decision_point,
            )(option_id)
            if not is_valid_option:
                await self.send_error(f"Decision already made: {option_id}")
                return

            if not await self.can_proceed(story):
                await self.send_error(
                    "Skeleton is still generating, please retry later.",
                )
                return

            # Update the story progress with chosen option
            await self.handle_user_selection(story, option_id, option_text)

            await self.update_story_progress(story)

        except ValueError as e:
            await self.send_error(str(e))
            raise

    @database_sync_to_async
    def can_proceed(self, story):
        return story.can_proceed

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
                fake=settings.FAKE_LLM_REQUEST,
                name="text_explanation",
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
        name_to_purpose = {
            "skeleton": "story_skeleton_generation",
            "continuation": "story_continuation",
            "ending": "story_ending",
        }

        for name, purpose in name_to_purpose.items():
            config = LLMConfig.get_active_config(purpose=purpose)
            prompt = ChatPromptTemplate.from_template(config.system_prompt)
            model_name = config.model.name
            key = APIKey.get_available_key(model_name)

            llms[name] = prompt | get_llm_model(
                {
                    "model_name": model_name,
                    "llm_type": config.model.llm_type,
                    "url": config.model.url,
                    "temperature": config.temperature,
                    "key": key,
                },
                fake=settings.FAKE_LLM_REQUEST,
                name=name,
            )

        return llms

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

    def get_options(self, state):
        options = []
        current_decision_point_id = state.get("current_decision_point")
        if current_decision_point_id:
            skeleton = state["story_skeleton"]
            options = []

            # Find the current decision point and its options
            for milestone in skeleton["milestones"]:
                for decision_point in milestone.get("decision_points", []):
                    if decision_point["decision_point_id"] == current_decision_point_id:
                        return decision_point["options"]
        return options

    async def send_decision_point(self, state):
        """Send decision point to client"""
        # TODO: remove the consequence from the options (or use a unified interface)
        options = self.get_options(state)

        await self.send(
            text_data=json.dumps(
                {
                    "type": "send_decision_point",
                    "current_decision": state.get("current_decision_point"),
                    "options": options,
                },
            ),
        )

    @database_sync_to_async
    def handle_user_selection(self, story, option_id, option_text):
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

    async def update_story_progress(self, story):
        """Create the next progress entry."""
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
        async for mode, chunk in self.story_graph.astream(
            state,
            self.story_thread,
            stream_mode=["messages", "values"],
        ):
            if mode == "messages":
                msg, metadata = chunk
                await self.send(
                    text_data=json.dumps(
                        {"type": "story_update", "content": msg.content},
                    ),
                )
            elif mode == "values":
                new_state = chunk

        # Save progress
        await self.save_story_progress(story, new_state)

        # Send response to client
        await self.send_decision_point(new_state)

    async def skeleton_generation_progress(self, event):
        """Handle skeleton generation progress."""
        story_id = event["story_id"]
        story = await self.get_story(story_id)
        if event["n_milestones"] == self.START_GAME_SINCE_MILESTONE:
            # Start generating story when first milestone is generated
            logger.debug("Start generating the first story progress")
            await self.update_story_progress(story)

    async def skeleton_generation_completed(self, event):
        """Handle skeleton generation completion."""
        # No need to do anythin

    async def skeleton_generation_failed(self, event):
        """Handle skeleton generation failure."""
        await self.send_error(event["error"])
