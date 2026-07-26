# Generated manually for genre → theme hierarchy

import django.db.models.deletion
from django.db import migrations, models


def migrate_subgenre_to_theme(apps, schema_editor):
    GameScenario = apps.get_model("llm_caller", "GameScenario")
    GameScenario.objects.filter(category="sub-genre").update(category="theme")


def reverse_theme_to_subgenre(apps, schema_editor):
    GameScenario = apps.get_model("llm_caller", "GameScenario")
    GameScenario.objects.filter(category="theme").update(category="sub-genre")


class Migration(migrations.Migration):

    dependencies = [
        ("llm_caller", "0022_vocabularyquizsubmission_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamescenario",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Short description of what this theme is",
            ),
        ),
        migrations.AddField(
            model_name="gamescenario",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                help_text="Parent genre for theme rows; null for top-level genres",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="themes",
                to="llm_caller.gamescenario",
            ),
        ),
        migrations.AlterField(
            model_name="gamescenario",
            name="category",
            field=models.CharField(
                choices=[("genre", "Genre"), ("theme", "Theme")],
                default="genre",
                help_text="Category of the scenario",
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="gamescenario",
            name="example",
            field=models.TextField(
                blank=True,
                help_text="Example movies/books/etc. of this genre/theme",
            ),
        ),
        migrations.AlterModelOptions(
            name="gamescenario",
            options={"ordering": ["order", "name"]},
        ),
        migrations.AddConstraint(
            model_name="gamescenario",
            constraint=models.UniqueConstraint(
                fields=("parent", "name"),
                name="unique_gamescenario_parent_name",
            ),
        ),
        migrations.RunPython(migrate_subgenre_to_theme, reverse_theme_to_subgenre),
    ]
