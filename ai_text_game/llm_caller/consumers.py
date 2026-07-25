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

from ai_text_game.users.models import UserProfile

from .models import APIKey
from .models import GameStory
from .models import LLMConfig
from .models import StoryOption
from .models import StoryProgress
from .models import StorySkeleton
from .models import TextExplanation
from .story_graph import StoryGraph
from .tasks import generate_story_skeleton
from .utils import generate_image
from .utils import generate_story_image_prompt
from .utils import get_llm_model

logger = logging.getLogger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    START_GAME_SINCE_MILESTONE = 2
    START_GAME_SINCE_MILESTONE_DEMO = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.story_graph = None
        self.story_thread = {"configurable": {"thread_id": "1"}}
        self._joined_group = False
        self._story_progress_started = False

    async def connect(self):
        logger.debug("WebSocket connect attempt with scope: %s", self.scope)
        try:
            self.story_id = self.scope["url_route"]["kwargs"]["story_id"]
            self.room_group_name = f"game_{self.story_id}"
            self.story_thread = {"configurable": {"thread_id": self.story_id}}

            await self.get_story(self.story_id)

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )
            self._joined_group = True
            await self.accept()
            logger.debug("WebSocket connection accepted")
        except GameStory.DoesNotExist:
            logger.exception("WebSocket connection error: story not found")
            await self.close(code=4004)
        except Exception:
            logger.exception("WebSocket connection error")
            await self.close(code=1011)

    async def disconnect(self, close_code):
        logger.debug("WebSocket disconnected with code: %s", close_code)
        if self._joined_group:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )
            self._joined_group = False

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
                "genre": story.genre,
                "language_level": story.language_level,
                "scene_text": story.scene_text,
                "details_prompt": "",
                "theme": story.theme or "",
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

            # Summarize the segment and decision
            await self.summarize_latest_progress(story)

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
            native_language_override = data.get("native_language")

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
            await self.process_explanation(story, explanation, native_language_override)

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
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "error": error_message,
                    },
                ),
            )
        except RuntimeError:
            # Connection already closed, log the error instead
            logger.exception(
                "Cannot send error message, connection closed: %s",
                error_message,
            )

    @database_sync_to_async
    def create_text_explanation(self, story, selected_text, context_text):
        # Check if user is demo account
        is_demo = False
        if story.created_by and hasattr(story.created_by, "userprofile"):
            is_demo = story.created_by.userprofile.is_demo_account

        active_config = LLMConfig.get_active_config_with_demo_fallback(
            purpose="text_explanation",
            is_demo=is_demo,
        )

        return TextExplanation.objects.create(
            story=story,
            selected_text=selected_text,
            context_text=context_text,
            status="pending",
            model=active_config.model,
            created_by=self.scope["user"],
        )

    @database_sync_to_async
    def serialize_explanation(self, explanation):
        from .serializers import TextExplanationSerializer

        return TextExplanationSerializer(explanation).data

    async def process_explanation(self, story, explanation, native_language_override=None):
        try:
            is_demo = await database_sync_to_async(
                lambda: (
                    story.created_by.userprofile.is_demo_account
                    if story.created_by and hasattr(story.created_by, "userprofile")
                    else False
                ),
            )()

            active_config = await database_sync_to_async(
                LLMConfig.get_active_config_with_demo_fallback,
            )(purpose="text_explanation", is_demo=is_demo)

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
            stream_inputs = {
                "selected_text": explanation.selected_text,
                "context_text": explanation.context_text,
            }
            if "{native_language}" in system_prompt:
                if native_language_override:
                    code = native_language_override
                else:
                    code = await database_sync_to_async(
                        lambda: (
                            explanation.created_by.userprofile.native_language
                            if explanation.created_by
                            and hasattr(explanation.created_by, "userprofile")
                            else None
                        ),
                    )()
                stream_inputs["native_language"] = (
                    UserProfile.native_language_prompt_label(code)
                )
            stream = chain.astream(stream_inputs)

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

    async def ensure_story_graph_initialized(self, story=None):
        """Lazily initialize the story graph on first use."""
        if self.story_graph is not None:
            return
        if story is None:
            story = await self.get_story(self.story_id)
        await self.initialize_story_graph(story)

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
            "summary": "story_summary",
        }

        # Check if user is demo account
        is_demo = False
        if hasattr(self, "story_id"):
            try:
                story = GameStory.objects.get(id=self.story_id)
                if story.created_by and hasattr(story.created_by, "userprofile"):
                    is_demo = story.created_by.userprofile.is_demo_account
            except (GameStory.DoesNotExist, AttributeError):
                pass

        for name, purpose in name_to_purpose.items():
            config = LLMConfig.get_active_config_with_demo_fallback(
                purpose=purpose,
                is_demo=is_demo,
            )
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

            # Get character base images for reference
            character_images = await database_sync_to_async(
                lambda: story.skeleton.character_base_images
                if hasattr(story, "skeleton")
                else {},
            )()
            reference_images = (
                list(character_images.values()) if character_images else []
            )

            # Get character descriptions to reinforce the reference images
            characters = await database_sync_to_async(
                lambda: story.skeleton.raw_data.get("characters", [])
                if hasattr(story, "skeleton")
                else [],
            )()

            # # Add last progress image (uncomment to use the n-1 image as reference)
            # last_image = await database_sync_to_async(
            #     lambda: StoryProgress.objects.filter(story=story, image_url__isnull=False)
            #     .exclude(id=progress.id)
            #     .order_by("-created_at")
            #     .values_list("image_url", flat=True)
            #     .first(),
            # )()
            # if last_image:
            #     reference_images.append(last_image)

            # Get image generation config
            image_config = await database_sync_to_async(
                LLMConfig.get_active_config_with_demo_fallback,
            )(purpose="image_generation", is_demo=False)

            image_model_name = await database_sync_to_async(
                lambda: image_config.model.name,
            )()
            image_llm_type = await database_sync_to_async(
                lambda: image_config.model.llm_type,
            )()
            image_api_key = await database_sync_to_async(
                lambda: APIKey.get_available_key(image_model_name),
            )()

            # Generate image for this segment
            image_prompt = await database_sync_to_async(generate_story_image_prompt)(
                story_text=story_text,
                has_reference_images=bool(reference_images),
                characters=characters,
            )
            image_url = await database_sync_to_async(generate_image)(
                llm_type=image_llm_type,
                prompt=image_prompt,
                story_id=story.id,
                image_type="progress",
                progress_id=progress.id,
                reference_image_urls=reference_images if reference_images else None,
                api_key=image_api_key.key if image_api_key else None,
                model_name=image_model_name,
            )

            if image_url:
                progress.image_url = image_url
                await database_sync_to_async(progress.save)()

                # Send image_ready message to frontend
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "image_ready",
                            "progress_id": progress.id,
                            "image_url": image_url,
                        }
                    ),
                )
            await database_sync_to_async(story.save)()

    def get_options(self, state):
        options = []
        current_decision_point_id = state.get("current_decision_point")
        if current_decision_point_id:
            skeleton = state.get("story_skeleton", {})
            options = []

            # Find the current decision point and its options
            for milestone in skeleton.get("milestones", []):
                for decision_point in milestone.get("decision_points", []):
                    if (
                        decision_point.get("decision_point_id")
                        == current_decision_point_id
                    ):
                        return decision_point.get("options", [])
        return options

    async def send_decision_point(self, state):
        """Send decision point to client"""
        # TODO: remove the consequence from the options (or use a unified interface)
        options = self.get_options(state)

        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "send_decision_point",
                        "current_decision": state.get("current_decision_point"),
                        "options": options,
                        "status": state.get("status", "IN_PROGRESS"),
                    },
                ),
            )
        except RuntimeError:
            # Connection already closed
            logger.exception("Cannot send decision point, connection closed")

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

    async def summarize_latest_progress(self, story):
        """Generate and store summary of the latest progress entry."""
        from .models import StoryProgress

        # Get the latest progress entry
        latest_progress = await database_sync_to_async(
            lambda: StoryProgress.objects.filter(story=story)
            .order_by("-created_at")
            .first(),
        )()

        if not latest_progress or not latest_progress.chosen_option_text:
            return

        await self.ensure_story_graph_initialized(story)

        # Generate summary using the story graph
        summary = await self.story_graph.summarize_segment(
            story_segment=latest_progress.content,
            player_decision=latest_progress.chosen_option_text,
            language_level=story.language_level,
        )

        # Store the summary
        await database_sync_to_async(
            lambda: StoryProgress.objects.filter(id=latest_progress.id).update(
                summary=summary,
            ),
        )()

    @database_sync_to_async
    def has_progress_entries(self, story) -> bool:
        return story.progress_entries.exists()

    @database_sync_to_async
    def get_start_game_milestone_threshold(self, story) -> int:
        is_demo = False
        if story.created_by and hasattr(story.created_by, "userprofile"):
            is_demo = story.created_by.userprofile.is_demo_account
        if is_demo:
            return self.START_GAME_SINCE_MILESTONE_DEMO
        return self.START_GAME_SINCE_MILESTONE

    @database_sync_to_async
    def get_skeleton_readiness(self, story) -> tuple[int, bool]:
        skeleton = getattr(story, "skeleton", None)
        if not skeleton or not skeleton.raw_data:
            return 0, False
        raw_data = skeleton.raw_data
        return (
            StorySkeleton.count_complete_milestones(raw_data),
            StorySkeleton.is_ready_for_story_start(raw_data),
        )

    async def maybe_start_story_progress(
        self,
        story,
        n_milestones: int | None = None,
        *,
        force: bool = False,
    ) -> None:
        """Start first story progress once skeleton has enough milestones."""
        if await self.has_progress_entries(story):
            return
        if self._story_progress_started:
            return

        complete_count, ready = await self.get_skeleton_readiness(story)

        if not force:
            threshold = await self.get_start_game_milestone_threshold(story)
            if complete_count < threshold:
                logger.info(
                    "Skeleton progress for story %s: %s complete milestones "
                    "(%s reported, threshold %s), waiting",
                    story.id,
                    complete_count,
                    n_milestones,
                    threshold,
                )
                return
            if not ready:
                logger.info(
                    "Skeleton for story %s has enough milestones but "
                    "first decision point is not ready yet",
                    story.id,
                )
                return
        elif not ready:
            logger.warning(
                "Skeleton completed for story %s but is not valid for story start",
                story.id,
            )
            await self.send_error(
                "Story structure generation produced invalid data. Please try again.",
            )
            return

        self._story_progress_started = True
        logger.info(
            "Starting first story progress for story %s "
            "(n_milestones=%s, force=%s)",
            story.id,
            n_milestones,
            force,
        )
        await self.update_story_progress(story)
        if not await self.has_progress_entries(story):
            self._story_progress_started = False

    async def update_story_progress(self, story):
        """Create the next progress entry."""
        try:
            logger.info("Starting update_story_progress for story %s", story.id)
            await self.ensure_story_graph_initialized(story)

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

            # Add previous images for multimodal LLM context
            previous_images = await database_sync_to_async(
                lambda: list(
                    story.progress_entries.filter(image_url__isnull=False)
                    .order_by("created_at")
                    .values_list("image_url", flat=True),
                ),
            )()
            if previous_images:
                state["previous_images"] = previous_images

            # Run the graph
            new_state = None

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

            if new_state is None:
                msg = "Failed to generate story content, please try again later"
                raise ValueError(msg)  # noqa: TRY301

            # Save progress
            await self.save_story_progress(story, new_state)

            # Send response to client
            await self.send_decision_point(new_state)
            logger.info("Completed update_story_progress for story %s", story.id)

        except Exception as e:
            self._story_progress_started = False
            await self.revert_user_choice(story)
            logger.exception("Error in update_story_progress")
            await self.send_error(
                f"Failed to generate story content, please try again later: {e}",
            )

    @database_sync_to_async
    def revert_user_choice(self, story):
        """Revert the user's choice when story generation fails"""
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
            # Clear the chosen option
            latest_progress.chosen_option_id = ""
            latest_progress.chosen_option_text = ""
            latest_progress.save()

    async def skeleton_generation_progress(self, event):
        """Handle skeleton generation progress."""
        story_id = event["story_id"]
        n_milestones = event["n_milestones"]
        logger.info(
            "Skeleton generation progress for story %s: %s milestones",
            story_id,
            n_milestones,
        )
        story = await self.get_story(story_id)
        await self.maybe_start_story_progress(story, n_milestones)

    async def skeleton_generation_completed(self, event):
        """Handle skeleton generation completion."""
        logger.info("Skeleton generation completed for story %s", self.story_id)
        story = await self.get_story(self.story_id)
        await self.maybe_start_story_progress(story, force=True)

    async def skeleton_generation_failed(self, event):
        """Handle skeleton generation failure."""
        await self.send_error(event["error"])
