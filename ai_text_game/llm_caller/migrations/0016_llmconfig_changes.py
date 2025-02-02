from django.db import migrations, models
import django.core.validators
from llm_caller.utils import read_prompt_template


def init_llm_configs(apps, schema_editor):
    LLMConfig = apps.get_model('llm_caller', 'LLMConfig')

    # Clear existing configs
    LLMConfig.objects.all().delete()

    # Create configs for each purpose
    templates = {
        "scene_generation": {
            "template": "pre_game_prompt.txt",
            "temperature": 0.7
        },
        "adventure_gameplay": {
            "template": "gameplay_prompt.txt",
            "temperature": 0.7
        },
        "text_explanation": {
            "template": "text_explanation_prompt.txt",
            "temperature": 0.1
        }
    }

    for purpose, config in templates.items():
        try:
            system_prompt = read_prompt_template(config["template"])
            LLMConfig.objects.create(
                purpose=purpose,
                system_prompt=system_prompt,
                temperature=config["temperature"],
                is_active=True
            )
        except Exception as e:
            print(f"Failed to create config for {purpose}: {str(e)}")


def reverse_init_llm_configs(apps, schema_editor):
    LLMConfig = apps.get_model('llm_caller', 'LLMConfig')
    LLMConfig.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('llm_caller', '0015_init_game_scenarios'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gameinteraction',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='llmconfig',
            name='temperature',
            field=models.FloatField(default=0.7, help_text='Value between 0 and 2', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(2.0)]),
        ),
        migrations.RemoveField(
            model_name='llmconfig',
            name='user_prompt_template',
        ),
        migrations.AddField(
            model_name='llmconfig',
            name='purpose',
            field=models.CharField(
                choices=[
                    ('scene_generation', 'Scene Generation'),
                    ('adventure_gameplay', 'Adventure Gameplay'),
                    ('text_explanation', 'Text Explanation')
                ],
                default='scene_generation',
                help_text='The purpose of this configuration',
                max_length=20
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='llmconfig',
            name='is_active',
            field=models.BooleanField(
                default=False,
                help_text='Only one config can be active per purpose'
            ),
        ),
        migrations.AlterField(
            model_name='llmconfig',
            name='system_prompt',
            field=models.TextField(
                help_text='The system prompt for the LLM.'
            ),
        ),
        migrations.RunPython(init_llm_configs, reverse_init_llm_configs),
    ]
