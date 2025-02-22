import asyncio
import json
import logging
import re

import anyio
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .models import GameInteraction
from .models import GameStory
from .models import OpenAIKey
from .models import TextExplanation
from .serializers import GameInteractionSerializer
from .utils import get_openai_client_async

logger = logging.getLogger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.debug("WebSocket connect attempt with scope: %s", self.scope)
        try:
            # Get story_id from URL route
            self.story_id = self.scope["url_route"]["kwargs"]["story_id"]
            self.room_group_name = f"game_{self.story_id}"

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

        if message_type == "interact":
            await self.handle_interaction(data)
        elif message_type == "start_story":
            await self.handle_start_story()
        elif message_type == "explain_text":
            await self.handle_text_explanation(data)

    async def handle_interaction(self, data):
        try:
            story = await self.get_story(self.story_id)
            content = data.get("content")
            client_interaction_id = data.get("interaction_id")

            if not content:
                await self.send_error("content is required")
                return

            # Create user interaction
            user_interaction = await self.create_user_interaction(story, content)

            # Send creation confirmation
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "interaction_created",
                        "client_id": client_interaction_id,
                        "interaction": GameInteractionSerializer(user_interaction).data,
                    },
                ),
            )

            # Create assistant interaction
            assistant_interaction = await self.create_assistant_interaction(story)

            # Send assistant interaction creation
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "interaction_created",
                        "interaction": GameInteractionSerializer(
                            assistant_interaction,
                        ).data,
                    },
                ),
            )

            # Stream the response
            await self.stream_response(story, assistant_interaction)

        except (ValueError, GameInteraction.DoesNotExist) as e:
            await self.send_error(str(e))

    async def handle_start_story(self):
        try:
            story = await self.get_story(self.story_id)
            system_interaction = await self.get_system_interaction(story)

            if not system_interaction:
                await self.send_error("System interaction not found")
                return

            if system_interaction.status != "pending":
                await self.send_error("System interaction already completed")
                return

            system_interaction.status = "completed"
            await database_sync_to_async(system_interaction.save)()

            # Create assistant interaction for initial response
            assistant_interaction = await self.create_assistant_interaction(story)

            # Send assistant interaction creation
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "interaction_created",
                        "interaction": GameInteractionSerializer(
                            assistant_interaction,
                        ).data,
                    },
                ),
            )

            # Stream the response
            await self.stream_response(story, assistant_interaction)

        except (ValueError, GameInteraction.DoesNotExist) as e:
            await self.send_error(str(e))

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
    def get_story(self, story_id):
        return GameStory.objects.get(id=story_id)

    @database_sync_to_async
    def get_story_model_name(self, story):
        return story.model.name

    @database_sync_to_async
    def create_user_interaction(self, story, content):
        return GameInteraction.objects.create(
            story=story,
            role="user",
            content=content,
            status="completed",
        )

    @database_sync_to_async
    def create_assistant_interaction(self, story):
        return GameInteraction.objects.create(
            story=story,
            role="assistant",
            content="",
            status="pending",
        )

    @database_sync_to_async
    def get_system_interaction(self, story):
        try:
            return story.interactions.get(role="system")
        except GameInteraction.DoesNotExist:
            return None

    async def stream_response(self, story, interaction):
        try:
            if settings.FAKE_LLM_REQUEST:
                stream = self.get_fake_stream()
            else:
                key = await database_sync_to_async(OpenAIKey.get_available_key)()
                client = get_openai_client_async(key)
                context = await database_sync_to_async(story.get_context)()
                model_name = await self.get_story_model_name(story)
                stream = await self.get_openai_stream(client, model_name, context)

            content = ""
            async for chunk in stream:
                delta = ""
                if settings.FAKE_LLM_REQUEST:
                    delta = chunk
                elif chunk and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content

                if delta:
                    content += delta
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "stream",
                                "interaction_id": interaction.id,
                                "content": delta,
                            },
                        ),
                    )

            interaction.content = content
            interaction.status = "completed"
            await database_sync_to_async(interaction.save)()

            # Send completion message
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "interaction_completed",
                        "interaction": GameInteractionSerializer(interaction).data,
                    },
                ),
            )

        except ValueError as e:
            await self.send_error(json.dumps({"type": "error", "error": str(e)}))

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

    @database_sync_to_async
    def update_interaction(self, interaction, output, status, error=""):
        interaction.content = output
        interaction.status = status
        interaction.error = error
        interaction.save()

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
        from .models import LLMConfig

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
                key = await database_sync_to_async(OpenAIKey.get_available_key)()
                client = get_openai_client_async(key)
                model_name = await self.get_story_model_name(story)
                stream = await self.get_explanation_stream(
                    client,
                    model_name,
                    explanation.selected_text,
                    explanation.context_text,
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
                delta = ""
                if settings.FAKE_LLM_REQUEST:
                    delta = chunk
                elif chunk and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content

                if delta:
                    explanation_text += delta
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "explanation_stream",
                                "explanation_id": explanation.id,
                                "content": delta,
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

    @staticmethod
    async def get_explanation_stream(client, model_name, selected_text, context_text):
        fn = "ai_text_game/llm_caller/templates/prompts/text_explanation_prompt.txt"
        async with await anyio.open_file(fn) as f:
            prompt_template = await f.read()

        prompt = prompt_template.format(
            selected_text=selected_text,
            context_text=context_text,
        )

        return await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
