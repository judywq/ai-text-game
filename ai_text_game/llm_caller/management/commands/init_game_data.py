from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ai_text_game.llm_caller.models import APIKey
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

        for genre in settings.INIT_GAME_GENRE:
            parent, created = GameScenario.objects.get_or_create(
                category="genre",
                parent=None,
                name=genre["name"],
                defaults={
                    "order": genre["order"],
                    "is_active": True,
                },
            )
            if not created:
                parent.order = genre["order"]
                parent.is_active = True
                parent.save(update_fields=["order", "is_active", "updated_at"])
                msg = f'Scenario already exists: {genre["name"]}'
                self.stdout.write(self.style.WARNING(msg))
            else:
                msg = f'Created genre: {genre["name"]}'
                self.stdout.write(self.style.SUCCESS(msg))

            for theme in genre.get("themes", []):
                _, theme_created = GameScenario.objects.update_or_create(
                    category="theme",
                    parent=parent,
                    name=theme["name"],
                    defaults={
                        "description": theme.get("description", ""),
                        "example": theme.get("example", ""),
                        "order": theme["order"],
                        "is_active": True,
                    },
                )
                if theme_created:
                    msg = f'Created theme: {genre["name"]} / {theme["name"]}'
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f'Theme already exists: {genre["name"]} / {theme["name"]}'
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
                found = LLMConfig.objects.filter(
                    purpose=purpose,
                ).exists()
                if not found:
                    LLMConfig.objects.create(
                        purpose=purpose,
                        system_prompt=system_prompt,
                        model=model,
                        temperature=config["temperature"],
                        is_active=True,
                    )
                    msg = f"Created LLM config for: {purpose}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"LLM config for {purpose} already exists"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create config for {purpose}: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    def init_llm_api_keys(self, force=False):  # noqa: FBT002
        if force:
            APIKey.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing LLM API keys"))

        for key in settings.INIT_API_KEYS:
            try:
                _, created = APIKey.objects.get_or_create(**key)
                if created:
                    msg = f"Created API key: {key['name']}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"API key already exists: {key['name']}"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create API key: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    @transaction.atomic
    def handle(self, *args, **kwargs):
        force = kwargs.get("force", False)

        self.stdout.write("Starting game data initialization...")

        try:
            self.init_game_scenarios(force)
            self.init_llm_models(force)
            self.init_llm_configs(force)
            self.init_llm_api_keys(force)
            msg = "Successfully initialized game data"
            self.stdout.write(self.style.SUCCESS(msg))
        except (ValueError, TypeError) as e:
            msg = f"Failed to initialize game data: {e!s}"
            self.stderr.write(self.style.ERROR(msg))
