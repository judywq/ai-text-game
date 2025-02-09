from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ai_text_game.llm_caller.models import GameScenario
from ai_text_game.llm_caller.models import LLMConfig
from ai_text_game.llm_caller.utils import read_prompt_template


class Command(BaseCommand):
    help = "Initialize game data including scenarios and LLM configs"

    def init_game_scenarios(self):
        # Clear existing scenarios
        GameScenario.objects.all().delete()
        self.stdout.write("Cleared existing game scenarios")

        # Create scenarios from PRE_GAME_GENRE
        for order, genre in enumerate(settings.PRE_GAME_GENRE):
            GameScenario.objects.create(
                category=genre[
                    "category"
                ].lower(),  # Convert to lowercase to match model choices
                name=genre["name"],
                example=genre["example"],
                order=order,
                is_active=True,
            )
            msg = f'Created scenario: {genre["name"]}'
            self.stdout.write(self.style.SUCCESS(msg))

    def init_llm_configs(self):
        # Clear existing configs
        LLMConfig.objects.all().delete()
        self.stdout.write("Cleared existing LLM configs")

        # Create configs for each purpose
        templates = {
            "scene_generation": {
                "template": "pre_game_prompt.txt",
                "temperature": 0.7,
            },
            "adventure_gameplay": {
                "template": "gameplay_prompt.txt",
                "temperature": 0.7,
            },
            "text_explanation": {
                "template": "text_explanation_prompt.txt",
                "temperature": 0.1,
            },
        }

        for purpose, config in templates.items():
            try:
                system_prompt = read_prompt_template(config["template"])
                LLMConfig.objects.create(
                    purpose=purpose,
                    system_prompt=system_prompt,
                    temperature=config["temperature"],
                    is_active=True,
                )
                msg = f"Created LLM config for: {purpose}"
                self.stdout.write(self.style.SUCCESS(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create config for {purpose}: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Starting game data initialization...")

        try:
            self.init_game_scenarios()
            self.init_llm_configs()
            msg = "Successfully initialized game data"
            self.stdout.write(self.style.SUCCESS(msg))
        except (ValueError, TypeError) as e:
            msg = f"Failed to initialize game data: {e!s}"
            self.stderr.write(self.style.ERROR(msg))
