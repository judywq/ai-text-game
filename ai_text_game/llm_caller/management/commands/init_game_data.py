from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ai_text_game.llm_caller.models import GameScenario
from ai_text_game.llm_caller.models import LLMConfig
from ai_text_game.llm_caller.models import LLMModel
from ai_text_game.llm_caller.utils import read_prompt_template


class Command(BaseCommand):
    help = "Initialize game data including scenarios, LLM models, and LLM configs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force initialization even if data already exists",
        )

    def init_game_scenarios(self, force=False):  # noqa: FBT002
        if force:
            GameScenario.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing game scenarios"))

        # Create scenarios from INIT_GAME_GENRE
        for order, genre in enumerate(settings.INIT_GAME_GENRE):
            _, created = GameScenario.objects.get_or_create(
                category=genre[
                    "category"
                ].lower(),  # Convert to lowercase to match model choices
                name=genre["name"],
                example=genre["example"],
                order=order,
                is_active=True,
            )
            if created:
                msg = f'Created scenario: {genre["name"]}'
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                msg = f'Scenario already exists: {genre["name"]}'
                self.stdout.write(self.style.WARNING(msg))

    def init_llm_models(self, force=False):  # noqa: FBT002
        if force:
            LLMModel.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing LLM models"))

        for model in settings.INIT_LLM_MODELS:
            try:
                _, created = LLMModel.objects.get_or_create(**model)
                if created:
                    msg = f"Created LLM model: {model['name']}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"LLM model already exists: {model['name']}"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create LLM model: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    def init_llm_configs(self, force=False):  # noqa: FBT002
        if force:
            LLMConfig.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing LLM configs"))

        for purpose, config in settings.INIT_LLM_CONFIGS.items():
            try:
                model_name = config["model"]
                model = LLMModel.objects.filter(name=model_name).first()
                if not model:
                    msg = f"Model {model_name} not found"
                    self.stderr.write(self.style.WARNING(msg))

                system_prompt = read_prompt_template(config["template"])
                _, created = LLMConfig.objects.get_or_create(
                    purpose=purpose,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=config["temperature"],
                    is_active=True,
                )
                if created:
                    msg = f"Created LLM config for: {purpose}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"LLM config for {purpose} already exists"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create config for {purpose}: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    @transaction.atomic
    def handle(self, *args, **kwargs):
        force = kwargs.get("force", False)

        self.stdout.write("Starting game data initialization...")

        try:
            self.init_game_scenarios(force)
            self.init_llm_models(force)
            self.init_llm_configs(force)
            msg = "Successfully initialized game data"
            self.stdout.write(self.style.SUCCESS(msg))
        except (ValueError, TypeError) as e:
            msg = f"Failed to initialize game data: {e!s}"
            self.stderr.write(self.style.ERROR(msg))
