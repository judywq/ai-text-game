from django.db import migrations

def init_game_scenarios(apps, schema_editor):
    GameScenario = apps.get_model('llm_caller', 'GameScenario')
    # Clear existing scenarios
    GameScenario.objects.all().delete()

    # Get settings module
    from django.conf import settings

    # Create scenarios from PRE_GAME_GENRE
    for order, genre in enumerate(settings.PRE_GAME_GENRE):
        GameScenario.objects.create(
            category=genre['category'].lower(),  # Convert to lowercase to match model choices
            name=genre['name'],
            example=genre['example'],
            order=order,
            is_active=True
        )

def reverse_init_game_scenarios(apps, schema_editor):
    GameScenario = apps.get_model('llm_caller', 'GameScenario')
    GameScenario.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('llm_caller', '0014_remove_gamescenario_genre_remove_gamescenario_title_and_more'),
    ]

    operations = [
        migrations.RunPython(init_game_scenarios, reverse_init_game_scenarios),
    ]
